"""
Quest Engine — Ration Hybrid Rebound System
Triggers an opt-in quest modal when prediction streak < 3.
Two paths: (A) Watch AdMob ad (+20 coins), (B) Router ration tease.
No locks, no forced engagement.
"""
import uuid
import logging
from datetime import datetime, timezone, date
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

QUEST_AD_REWARD_COINS = 20
QUEST_STREAK_THRESHOLD = 3  # Trigger if streak < 3


class QuestEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def check_eligibility(self, user_id: str) -> Dict:
        """Return whether a rebound quest should be offered to this user today."""
        today = date.today().isoformat()

        # Already offered/completed today?
        existing = await self.db.quest_sessions.find_one(
            {"user_id": user_id, "date": today}, {"_id": 0}
        )
        if existing:
            return {
                "eligible": False,
                "reason": "already_offered_today",
                "session": existing,
            }

        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "prediction_streak": 1, "coins_balance": 1})
        streak = (user or {}).get("prediction_streak", 0)

        eligible = streak < QUEST_STREAK_THRESHOLD
        return {
            "eligible": eligible,
            "streak": streak,
            "threshold": QUEST_STREAK_THRESHOLD,
            "reason": "low_streak" if eligible else "streak_ok",
        }

    async def offer_quest(self, user_id: str) -> Dict:
        """Create a quest session and return quest_id for the two opt-in paths."""
        today = date.today().isoformat()

        # Idempotent — return existing if already offered today
        existing = await self.db.quest_sessions.find_one(
            {"user_id": user_id, "date": today}, {"_id": 0}
        )
        if existing:
            return existing

        quest_id = str(uuid.uuid4())
        session = {
            "id": quest_id,
            "user_id": user_id,
            "date": today,
            "status": "offered",  # offered | ad_claimed | ration_viewed | dismissed
            "ad_claimed": False,
            "ration_viewed": False,
            "coins_earned": 0,
            "offered_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
        await self.db.quest_sessions.insert_one(session)
        return {k: v for k, v in session.items() if k != "_id"}

    async def claim_ad_reward(self, user_id: str, quest_id: str) -> Dict:
        """Path A: User watched an ad. Credit 20 coins."""
        session = await self.db.quest_sessions.find_one(
            {"id": quest_id, "user_id": user_id}, {"_id": 0}
        )
        if not session:
            raise ValueError("Quest session not found")
        if session.get("ad_claimed"):
            raise ValueError("Ad reward already claimed for this quest")

        now = datetime.now(timezone.utc).isoformat()
        await self.db.quest_sessions.update_one(
            {"id": quest_id},
            {"$set": {
                "ad_claimed": True,
                "coins_earned": QUEST_AD_REWARD_COINS,
                "status": "ad_claimed",
                "completed_at": now,
            }}
        )

        # Credit coins
        await self.db.users.update_one(
            {"id": user_id},
            {"$inc": {"coins_balance": QUEST_AD_REWARD_COINS, "total_earned": QUEST_AD_REWARD_COINS}}
        )
        await self.db.coin_transactions.insert_one({
            "user_id": user_id,
            "amount": QUEST_AD_REWARD_COINS,
            "type": "quest_ad",
            "description": "Rebound Quest: watched ad",
            "reference": quest_id,
            "timestamp": now,
        })

        logger.info(f"QUEST AD CLAIMED: user={user_id} quest={quest_id} coins={QUEST_AD_REWARD_COINS}")
        return {"success": True, "coins_earned": QUEST_AD_REWARD_COINS, "quest_id": quest_id}

    async def mark_ration_viewed(self, user_id: str, quest_id: str) -> Dict:
        """Path B: User saw the ration tease. Mark as viewed (no lock, they just browse)."""
        await self.db.quest_sessions.update_one(
            {"id": quest_id, "user_id": user_id},
            {"$set": {
                "ration_viewed": True,
                "status": "ration_viewed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }}
        )
        return {"success": True, "quest_id": quest_id}

    async def dismiss_quest(self, user_id: str, quest_id: str) -> Dict:
        """User dismissed the modal. No penalty."""
        await self.db.quest_sessions.update_one(
            {"id": quest_id, "user_id": user_id},
            {"$set": {"status": "dismissed", "completed_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"dismissed": True}

    async def get_history(self, user_id: str, limit: int = 10) -> list:
        docs = await self.db.quest_sessions.find(
            {"user_id": user_id}, {"_id": 0}
        ).sort("offered_at", -1).limit(limit).to_list(limit)
        return docs
