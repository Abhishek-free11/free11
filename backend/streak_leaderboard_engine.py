"""
Login Streak & Leaderboard Engine for FREE11
Enhanced streak with progressive rewards. Daily/Weekly/Seasonal leaderboards.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

STREAK_REWARDS = {
    1: {"coins": 50, "xp": 5, "label": "Day 1"},
    2: {"coins": 75, "xp": 10, "label": "Day 2"},
    3: {"coins": 100, "xp": 15, "label": "Day 3"},
    4: {"coins": 100, "xp": 20, "booster": "streak_shield", "label": "Day 4 + Shield Card"},
    5: {"coins": 150, "xp": 25, "label": "Day 5"},
    6: {"coins": 150, "xp": 30, "label": "Day 6"},
    7: {"coins": 250, "xp": 50, "booster": "double_up", "label": "Week Complete! + Double Card"},
}

LEADERBOARD_REWARDS = {
    "daily": {1: 500, 2: 300, 3: 200, 4: 100, 5: 75, 6: 50, 7: 50, 8: 25, 9: 25, 10: 25},
    "weekly": {1: 2000, 2: 1000, 3: 750, 4: 500, 5: 300},
    "seasonal": {1: 10000, 2: 5000, 3: 3000},
}


class StreakEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_streak(self, user_id: str) -> Dict:
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "streak_days": 1, "last_checkin": 1})
        streak = user.get("streak_days", 0) if user else 0
        last = user.get("last_checkin") if user else None
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        can_checkin = last != today

        # Calculate rewards for each day
        rewards_preview = []
        for day in range(1, 8):
            r = STREAK_REWARDS.get(day, STREAK_REWARDS.get(7))
            rewards_preview.append({
                "day": day,
                "coins": r["coins"],
                "xp": r.get("xp", 0),
                "booster": r.get("booster"),
                "label": r["label"],
                "achieved": day <= streak,
                "current": day == streak + 1 and can_checkin,
            })

        return {
            "streak_days": streak,
            "last_checkin": last,
            "can_checkin": can_checkin,
            "today_reward": STREAK_REWARDS.get(min(streak + 1, 7), STREAK_REWARDS[7]) if can_checkin else None,
            "rewards_preview": rewards_preview,
        }

    async def checkin(self, user_id: str) -> Dict:
        streak_info = await self.get_streak(user_id)
        if not streak_info["can_checkin"]:
            raise ValueError("Already checked in today")

        user = await self.db.users.find_one({"id": user_id}, {"_id": 0})
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

        old_streak = user.get("streak_days", 0)
        last = user.get("last_checkin")

        # Continue streak if logged in yesterday, else reset
        new_streak = (old_streak + 1) if last == yesterday else 1
        capped = min(new_streak, 7)
        reward = STREAK_REWARDS.get(capped, STREAK_REWARDS[7])

        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"streak_days": new_streak, "last_checkin": today}},
        )

        return {
            "streak_days": new_streak,
            "coins_earned": reward["coins"],
            "xp_earned": reward.get("xp", 0),
            "booster": reward.get("booster"),
            "label": reward["label"],
        }


class LeaderboardEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_leaderboard(self, period: str = "daily", limit: int = 50) -> List[Dict]:
        now = datetime.now(timezone.utc)
        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        elif period == "weekly":
            start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        else:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        pipeline = [
            {"$match": {"timestamp": {"$gte": start}, "amount": {"$gt": 0}}},
            {"$group": {"_id": "$user_id", "total_coins": {"$sum": "$amount"}}},
            {"$sort": {"total_coins": -1}},
            {"$limit": limit},
        ]
        results = await self.db.coin_transactions.aggregate(pipeline).to_list(limit)

        leaderboard = []
        for i, r in enumerate(results):
            user = await self.db.users.find_one({"id": r["_id"]}, {"_id": 0, "name": 1, "tier": 1})
            leaderboard.append({
                "rank": i + 1,
                "user_id": r["_id"],
                "name": user.get("name", "Unknown") if user else "Unknown",
                "tier": user.get("tier", "Bronze") if user else "Bronze",
                "total_coins": r["total_coins"],
                "reward": LEADERBOARD_REWARDS.get(period, {}).get(i + 1, 0),
            })
        return leaderboard

    async def distribute_rewards(self, period: str) -> Dict:
        lb = await self.get_leaderboard(period, 10)
        distributed = 0
        for entry in lb:
            if entry["reward"] > 0:
                await self.db.users.update_one(
                    {"id": entry["user_id"]},
                    {"$inc": {"coins_balance": entry["reward"]}},
                )
                distributed += 1
        return {"period": period, "distributed": distributed}
