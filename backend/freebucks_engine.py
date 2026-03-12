"""
FREE Bucks Engine for FREE11
Prepaid utility wallet: non-transferable, non-withdrawable, feature-gating.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

EXPIRY_DAYS = 365
PACKAGES = {
    "starter": {"amount": 49.00, "bucks": 50, "label": "Starter Pack", "bonus": 0},
    "popular": {"amount": 149.00, "bucks": 160, "label": "Popular Pack", "bonus": 10},
    "value": {"amount": 499.00, "bucks": 550, "label": "Value Pack", "bonus": 50},
    "mega": {"amount": 999.00, "bucks": 1200, "label": "Mega Pack", "bonus": 200},
}


class FreeBucksEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_balance(self, user_id: str) -> int:
        wallet = await self.db.freebucks_wallets.find_one({"user_id": user_id}, {"_id": 0})
        if not wallet:
            return 0
        if wallet.get("frozen"):
            return 0
        return wallet.get("balance", 0)

    async def credit(self, user_id: str, amount: int, source: str, reference_id: str = "") -> Dict:
        now = datetime.now(timezone.utc)
        expiry = (now + timedelta(days=EXPIRY_DAYS)).isoformat()
        wallet = await self.db.freebucks_wallets.find_one({"user_id": user_id})
        if not wallet:
            await self.db.freebucks_wallets.insert_one({
                "user_id": user_id, "balance": 0, "total_purchased": 0,
                "total_spent": 0, "frozen": False, "created_at": now.isoformat(),
            })
        await self.db.freebucks_wallets.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount, "total_purchased": amount},
             "$set": {"updated_at": now.isoformat()}},
        )
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id, "user_id": user_id, "type": "credit", "amount": amount,
            "source": source, "reference_id": reference_id,
            "expires_at": expiry, "timestamp": now.isoformat(),
        }
        await self.db.freebucks_history.insert_one(entry)
        new_balance = await self.get_balance(user_id)
        return {"entry_id": entry_id, "new_balance": new_balance}

    async def debit(self, user_id: str, amount: int, feature: str, reference_id: str = "") -> Dict:
        balance = await self.get_balance(user_id)
        if balance < amount:
            raise ValueError(f"Insufficient FREE Bucks: have {balance}, need {amount}")
        now = datetime.now(timezone.utc).isoformat()
        await self.db.freebucks_wallets.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": -amount, "total_spent": amount},
             "$set": {"updated_at": now}},
        )
        entry_id = str(uuid.uuid4())
        await self.db.freebucks_history.insert_one({
            "id": entry_id, "user_id": user_id, "type": "debit", "amount": amount,
            "feature": feature, "reference_id": reference_id, "timestamp": now,
        })
        new_balance = await self.get_balance(user_id)
        return {"entry_id": entry_id, "new_balance": new_balance}

    async def get_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        entries = await self.db.freebucks_history.find(
            {"user_id": user_id}, {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return entries

    async def freeze(self, user_id: str):
        await self.db.freebucks_wallets.update_one(
            {"user_id": user_id}, {"$set": {"frozen": True}}
        )

    async def unfreeze(self, user_id: str):
        await self.db.freebucks_wallets.update_one(
            {"user_id": user_id}, {"$set": {"frozen": False}}
        )

    async def admin_adjust(self, user_id: str, amount: int, reason: str, admin_id: str) -> Dict:
        if amount > 0:
            return await self.credit(user_id, amount, f"admin_adjust:{reason}", admin_id)
        else:
            return await self.debit(user_id, abs(amount), f"admin_adjust:{reason}", admin_id)

    async def get_wallet(self, user_id: str) -> Dict:
        wallet = await self.db.freebucks_wallets.find_one({"user_id": user_id}, {"_id": 0})
        if not wallet:
            return {"user_id": user_id, "balance": 0, "total_purchased": 0, "total_spent": 0, "frozen": False}
        return wallet

    @staticmethod
    def get_packages() -> Dict:
        return PACKAGES
