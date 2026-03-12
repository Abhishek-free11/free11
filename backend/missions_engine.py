"""
Daily Missions System for FREE11
Missions refresh every 24h. Completion awards coins/XP.
"""
import uuid
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

MISSION_TEMPLATES = [
    {"id": "play_2_contests", "title": "Play 2 Contests", "desc": "Join and play 2 contests today", "target": 2, "metric": "contests_played", "reward_coins": 50, "reward_xp": 30},
    {"id": "play_1_game", "title": "Play 1 Card Game", "desc": "Play a round of Rummy, Teen Patti, or Poker", "target": 1, "metric": "games_played", "reward_coins": 30, "reward_xp": 15},
    {"id": "win_1_match", "title": "Win a Match", "desc": "Win any contest or card game", "target": 1, "metric": "wins", "reward_coins": 75, "reward_xp": 40},
    {"id": "earn_500_coins", "title": "Earn 500 Coins", "desc": "Earn 500 coins through any activity", "target": 500, "metric": "coins_earned", "reward_coins": 100, "reward_xp": 50},
    {"id": "invite_friend", "title": "Invite a Friend", "desc": "Share your referral code with a friend", "target": 1, "metric": "referrals", "reward_coins": 100, "reward_xp": 100},
    {"id": "make_3_predictions", "title": "Make 3 Predictions", "desc": "Submit 3 predictions during live matches", "target": 3, "metric": "predictions_made", "reward_coins": 40, "reward_xp": 20},
    {"id": "watch_2_ads", "title": "Watch 2 Ads", "desc": "Watch 2 rewarded ads", "target": 2, "metric": "ads_watched", "reward_coins": 25, "reward_xp": 10},
    {"id": "daily_checkin", "title": "Daily Check-in", "desc": "Complete your daily check-in", "target": 1, "metric": "checkins", "reward_coins": 20, "reward_xp": 5},
]

DAILY_MISSION_COUNT = 5


class MissionsEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_daily_missions(self, user_id: str) -> List[Dict]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        existing = await self.db.daily_missions.find_one({"user_id": user_id, "date": today}, {"_id": 0})

        if existing:
            return existing.get("missions", [])

        # Generate new missions for today
        selected = random.sample(MISSION_TEMPLATES, min(DAILY_MISSION_COUNT, len(MISSION_TEMPLATES)))
        missions = []
        for m in selected:
            missions.append({
                "id": m["id"],
                "title": m["title"],
                "desc": m["desc"],
                "target": m["target"],
                "metric": m["metric"],
                "progress": 0,
                "completed": False,
                "claimed": False,
                "reward_coins": m["reward_coins"],
                "reward_xp": m["reward_xp"],
            })

        await self.db.daily_missions.insert_one({
            "user_id": user_id, "date": today, "missions": missions, "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return missions

    async def update_progress(self, user_id: str, metric: str, amount: int = 1) -> List[Dict]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        doc = await self.db.daily_missions.find_one({"user_id": user_id, "date": today})
        if not doc:
            await self.get_daily_missions(user_id)
            doc = await self.db.daily_missions.find_one({"user_id": user_id, "date": today})
        if not doc:
            return []

        missions = doc.get("missions", [])
        updated = False
        for m in missions:
            if m["metric"] == metric and not m["completed"]:
                m["progress"] = min(m["progress"] + amount, m["target"])
                if m["progress"] >= m["target"]:
                    m["completed"] = True
                updated = True

        if updated:
            await self.db.daily_missions.update_one(
                {"user_id": user_id, "date": today},
                {"$set": {"missions": missions}},
            )
        return missions

    async def claim_reward(self, user_id: str, mission_id: str) -> Dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        doc = await self.db.daily_missions.find_one({"user_id": user_id, "date": today})
        if not doc:
            raise ValueError("No missions found")

        missions = doc.get("missions", [])
        for m in missions:
            if m["id"] == mission_id:
                if not m["completed"]:
                    raise ValueError("Mission not completed")
                if m["claimed"]:
                    raise ValueError("Already claimed")
                m["claimed"] = True
                await self.db.daily_missions.update_one(
                    {"user_id": user_id, "date": today},
                    {"$set": {"missions": missions}},
                )
                return {"coins": m["reward_coins"], "xp": m["reward_xp"]}

        raise ValueError("Mission not found")
