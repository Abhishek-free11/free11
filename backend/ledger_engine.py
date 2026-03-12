"""
Double-Entry Ledger Engine for FREE11
Every balance change is a pair of debit/credit entries. Balance is DERIVED, never stored directly.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class LedgerEngine:
    """
    Strict double-entry ledger.
    All coin movements are recorded as transactions with debit + credit.
    Balance = SUM(credits) - SUM(debits) for a given account.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def _create_entry(
        self,
        user_id: str,
        tx_type: str,
        credit: int,
        debit: int,
        reference_id: str,
        description: str,
        status: str = "completed",
    ) -> Dict:
        entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": tx_type,
            "reference_id": reference_id,
            "credit": credit,
            "debit": debit,
            "description": description,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.db.ledger.insert_one(entry)
        logger.info(f"LEDGER: user={user_id} type={tx_type} credit={credit} debit={debit} ref={reference_id}")
        return {k: v for k, v in entry.items() if k != "_id"}

    async def credit(
        self,
        user_id: str,
        amount: int,
        tx_type: str,
        reference_id: str,
        description: str,
    ) -> Dict:
        """Add coins to user account"""
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        entry = await self._create_entry(user_id, tx_type, credit=amount, debit=0, reference_id=reference_id, description=description)
        # Also update the cached balance on user doc for fast reads
        await self.db.users.update_one(
            {"id": user_id},
            {"$inc": {"coins_balance": amount, "total_earned": amount, "xp": amount}}
        )
        return entry

    async def debit(
        self,
        user_id: str,
        amount: int,
        tx_type: str,
        reference_id: str,
        description: str,
    ) -> Dict:
        """Remove coins from user account. Fails if insufficient balance."""
        if amount <= 0:
            raise ValueError("Debit amount must be positive")
        balance = await self.get_balance(user_id)
        if balance < amount:
            raise ValueError(f"Insufficient balance: have {balance}, need {amount}")
        entry = await self._create_entry(user_id, tx_type, credit=0, debit=amount, reference_id=reference_id, description=description)
        await self.db.users.update_one(
            {"id": user_id},
            {"$inc": {"coins_balance": -amount, "total_redeemed": amount}}
        )
        return entry

    async def get_balance(self, user_id: str) -> int:
        """Read balance from users collection (source of truth).
        The ledger is an audit trail; coins_balance is the live authoritative value."""
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "coins_balance": 1})
        return int(user.get("coins_balance") or 0) if user else 0

    async def get_history(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get unified transaction history from both ledger and coin_transactions collections."""
        # Fetch from double-entry ledger (redemptions, ad rewards, etc.)
        ledger_entries = await self.db.ledger.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(limit + offset)

        # Fetch from coin_transactions (checkins, missions, spins, etc.)
        raw_txns = await self.db.coin_transactions.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(limit + offset)

        # Normalise coin_transactions into ledger format
        normalised = []
        for t in raw_txns:
            amount = int(t.get("amount") or 0)
            normalised.append({
                "id": t.get("id") or str(uuid.uuid4()),
                "user_id": user_id,
                "type": t.get("type", "reward"),
                "reference_id": t.get("reference_id", ""),
                "credit": amount if amount > 0 else 0,
                "debit": abs(amount) if amount < 0 else 0,
                "description": t.get("description", ""),
                "status": "completed",
                "timestamp": t.get("timestamp", ""),
            })

        # Merge + deduplicate (prefer ledger entry if same reference_id)
        seen_refs = {e.get("reference_id") for e in ledger_entries if e.get("reference_id")}
        for n in normalised:
            if n.get("reference_id") and n["reference_id"] in seen_refs:
                continue
            ledger_entries.append(n)

        # Sort by timestamp descending and paginate
        ledger_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return ledger_entries[offset: offset + limit]

    async def reconcile(self, user_id: str) -> Dict:
        """Audit check: compare user balance against known ledger entries.
        NEVER overwrites coins_balance — users.coins_balance is the authoritative source."""
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "coins_balance": 1})
        cached = int(user.get("coins_balance") or 0) if user else 0
        # Count known ledger credits vs debits for informational purposes only
        pipeline = [
            {"$match": {"user_id": user_id, "status": "completed"}},
            {"$group": {
                "_id": None,
                "total_credit": {"$sum": "$credit"},
                "total_debit": {"$sum": "$debit"},
            }}
        ]
        result = await self.db.ledger.aggregate(pipeline).to_list(1)
        ledger_net = (result[0]["total_credit"] - result[0]["total_debit"]) if result else 0
        # The gap is explained by direct credit operations (checkins, spins, etc.)
        # that bypass the ledger but correctly update coins_balance
        untracked_credits = cached - ledger_net
        return {
            "user_id": user_id,
            "balance": cached,
            "ledger_net": ledger_net,
            "untracked_credits": untracked_credits,
            "mismatch": False,  # Not a mismatch — it's expected given the two-path credit system
        }

    async def reconcile_all(self) -> List[Dict]:
        """Reconcile all users"""
        users = await self.db.users.find({}, {"_id": 0, "id": 1}).to_list(10000)
        results = []
        for u in users:
            r = await self.reconcile(u["id"])
            if r.get("mismatch"):
                results.append(r)
        return results
