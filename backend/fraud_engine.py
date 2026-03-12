"""
Fraud Prevention Engine for FREE11
Device fingerprinting, duplicate account detection, abuse protection.
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class FraudEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def compute_device_hash(self, user_agent: str, ip: str, accept_lang: str = "") -> str:
        raw = f"{user_agent}|{accept_lang}|{ip}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    async def record_login(self, user_id: str, ip: str, user_agent: str, accept_lang: str = ""):
        device_hash = self.compute_device_hash(user_agent, ip, accept_lang)
        now = datetime.now(timezone.utc).isoformat()
        await self.db.login_events.insert_one({
            "user_id": user_id,
            "ip": ip,
            "device_hash": device_hash,
            "user_agent": user_agent,
            "timestamp": now,
        })
        await self.db.users.update_one(
            {"id": user_id},
            {"$addToSet": {"known_devices": device_hash, "known_ips": ip},
             "$set": {"last_login_ip": ip, "last_login_at": now}},
        )
        return device_hash

    async def check_duplicate_account(self, device_hash: str, ip: str, exclude_user: str = "") -> List[Dict]:
        suspects = []
        device_matches = await self.db.users.find(
            {"known_devices": device_hash, "id": {"$ne": exclude_user}}, {"_id": 0, "id": 1, "email": 1, "name": 1}
        ).to_list(50)
        for u in device_matches:
            suspects.append({"user_id": u["id"], "email": u.get("email", ""), "reason": "same_device_hash"})

        ip_matches = await self.db.users.find(
            {"known_ips": ip, "id": {"$ne": exclude_user}}, {"_id": 0, "id": 1, "email": 1, "name": 1}
        ).to_list(50)
        for u in ip_matches:
            if not any(s["user_id"] == u["id"] for s in suspects):
                suspects.append({"user_id": u["id"], "email": u.get("email", ""), "reason": "same_ip"})

        return suspects

    async def flag_user(self, user_id: str, reason: str, flagged_by: str):
        now = datetime.now(timezone.utc).isoformat()
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"fraud_flagged": True, "fraud_reason": reason, "fraud_flagged_at": now, "fraud_flagged_by": flagged_by}},
        )
        await self.db.fraud_flags.insert_one({
            "user_id": user_id, "reason": reason, "flagged_by": flagged_by, "timestamp": now,
        })

    async def ban_user(self, user_id: str, reason: str, banned_by: str):
        now = datetime.now(timezone.utc).isoformat()
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"banned": True, "ban_reason": reason, "banned_at": now, "banned_by": banned_by}},
        )

    async def unban_user(self, user_id: str):
        await self.db.users.update_one(
            {"id": user_id},
            {"$unset": {"banned": 1, "ban_reason": 1, "banned_at": 1, "banned_by": 1}},
        )

    async def check_duplicate_contest_join(self, user_id: str, contest_id: str) -> bool:
        existing = await self.db.contest_entries.find_one(
            {"user_id": user_id, "contest_id": contest_id}
        )
        return existing is not None

    async def check_prediction_cutoff(self, match_id: str, over_number: int) -> bool:
        match = await self.db.matches.find_one({"match_id": match_id}, {"_id": 0, "status": 1})
        if not match or match.get("status") != "live":
            return False
        return True

    async def get_flagged_users(self) -> List[Dict]:
        return await self.db.users.find(
            {"$or": [{"fraud_flagged": True}, {"banned": True}]},
            {"_id": 0, "id": 1, "email": 1, "name": 1, "fraud_flagged": 1, "fraud_reason": 1, "banned": 1, "ban_reason": 1}
        ).to_list(1000)
