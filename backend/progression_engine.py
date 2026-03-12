"""
Player Progression & Tier System for FREE11
Tiers: Bronze → Silver → Gold → Platinum → Diamond
Based on cumulative activity: contests, games, coins, missions, leaderboard.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

TIERS = [
    {"name": "Bronze", "min_xp": 0, "color": "#cd7f32", "store_level": 1, "coin_multiplier": 1.0},
    {"name": "Silver", "min_xp": 500, "color": "#c0c0c0", "store_level": 2, "coin_multiplier": 1.1},
    {"name": "Gold", "min_xp": 2000, "color": "#ffd700", "store_level": 3, "coin_multiplier": 1.25},
    {"name": "Platinum", "min_xp": 5000, "color": "#e5e4e2", "store_level": 4, "coin_multiplier": 1.5},
    {"name": "Diamond", "min_xp": 15000, "color": "#b9f2ff", "store_level": 5, "coin_multiplier": 2.0},
]

XP_RULES = {
    "contest_played": 20,
    "contest_won": 50,
    "game_played": 15,
    "game_won": 40,
    "prediction_correct": 10,
    "mission_completed": 30,
    "daily_login": 5,
    "referral_success": 100,
    "leaderboard_top10": 75,
}


class ProgressionEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def _get_tier(self, xp: int) -> Dict:
        tier = TIERS[0]
        for t in TIERS:
            if xp >= t["min_xp"]:
                tier = t
        return tier

    def _get_next_tier(self, xp: int) -> Optional[Dict]:
        for t in TIERS:
            if xp < t["min_xp"]:
                return t
        return None

    async def get_progression(self, user_id: str) -> Dict:
        prog = await self.db.player_progression.find_one({"user_id": user_id}, {"_id": 0})
        if not prog:
            prog = {"user_id": user_id, "total_xp": 0, "activity": {}}
            await self.db.player_progression.insert_one(prog)

        xp = prog.get("total_xp", 0)
        tier = self._get_tier(xp)
        next_tier = self._get_next_tier(xp)
        progress = 0
        if next_tier:
            range_xp = next_tier["min_xp"] - tier["min_xp"]
            current = xp - tier["min_xp"]
            progress = round(min(current / range_xp * 100, 100), 1) if range_xp > 0 else 100
        else:
            progress = 100

        return {
            "user_id": user_id,
            "total_xp": xp,
            "tier": tier,
            "next_tier": next_tier,
            "progress_percent": progress,
            "xp_to_next": (next_tier["min_xp"] - xp) if next_tier else 0,
            "activity": prog.get("activity", {}),
        }

    async def add_xp(self, user_id: str, action: str, amount: int = 0) -> Dict:
        xp = amount if amount > 0 else XP_RULES.get(action, 0)
        if xp <= 0:
            return await self.get_progression(user_id)

        now = datetime.now(timezone.utc).isoformat()
        await self.db.player_progression.update_one(
            {"user_id": user_id},
            {
                "$inc": {"total_xp": xp, f"activity.{action}": 1},
                "$set": {"updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

        prog = await self.get_progression(user_id)
        # Update user level/xp in users collection too
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"xp": prog["total_xp"], "tier": prog["tier"]["name"]}},
        )
        return prog

    @staticmethod
    def get_tiers():
        return TIERS

    @staticmethod
    def get_xp_rules():
        return XP_RULES
