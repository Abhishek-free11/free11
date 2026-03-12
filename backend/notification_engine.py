"""
Notification Engine for FREE11
DB-backed notification queue with in-app notification center.
Ready for FCM plug-in.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

NOTIFICATION_TYPES = {
    "match_starting": {"title": "Match Starting Soon!", "priority": "high"},
    "contest_closing": {"title": "Contest Closing!", "priority": "high"},
    "match_completed": {"title": "Match Completed", "priority": "medium"},
    "leaderboard_update": {"title": "Leaderboard Updated", "priority": "medium"},
    "redemption_success": {"title": "Redemption Successful!", "priority": "high"},
    "payment_success": {"title": "Payment Successful!", "priority": "high"},
    "payment_failed": {"title": "Payment Failed", "priority": "high"},
    "team_scored": {"title": "Fantasy Points Updated!", "priority": "medium"},
    "daily_reminder": {"title": "Don't break your streak!", "priority": "low"},
    "referral_joined": {"title": "Referral Bonus!", "priority": "medium"},
}


class NotificationEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def send(self, user_id: str, ntype: str, body: str, data: Optional[Dict] = None) -> str:
        template = NOTIFICATION_TYPES.get(ntype, {"title": "FREE11", "priority": "medium"})
        notif_id = str(uuid.uuid4())
        notif = {
            "id": notif_id,
            "user_id": user_id,
            "type": ntype,
            "title": template["title"],
            "body": body,
            "data": data or {},
            "priority": template["priority"],
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.db.notifications.insert_one(notif)
        logger.info(f"NOTIFICATION: user={user_id} type={ntype}")
        return notif_id

    async def send_bulk(self, user_ids: List[str], ntype: str, body: str, data: Optional[Dict] = None):
        for uid in user_ids:
            await self.send(uid, ntype, body, data)

    async def get_notifications(self, user_id: str, limit: int = 50, unread_only: bool = False) -> List[Dict]:
        query = {"user_id": user_id}
        if unread_only:
            query["read"] = False
        return await self.db.notifications.find(
            query, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)

    async def mark_read(self, user_id: str, notif_id: str):
        await self.db.notifications.update_one(
            {"id": notif_id, "user_id": user_id}, {"$set": {"read": True}}
        )

    async def mark_all_read(self, user_id: str):
        await self.db.notifications.update_many(
            {"user_id": user_id, "read": False}, {"$set": {"read": True}}
        )

    async def get_unread_count(self, user_id: str) -> int:
        return await self.db.notifications.count_documents({"user_id": user_id, "read": False})

    async def delete_old(self, days: int = 30):
        cutoff = datetime.now(timezone.utc) - __import__("datetime").timedelta(days=days)
        result = await self.db.notifications.delete_many({"created_at": {"$lt": cutoff.isoformat()}})
        return result.deleted_count
