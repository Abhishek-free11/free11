"""
Surprise Reward Drops & Coin Economy Controls for FREE11
Random rewards after key events + economy stability controls.
"""
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

DAILY_COIN_CAP = 5000
DAILY_REDEEM_LIMIT = 3
BONUS_EXPIRY_DAYS = 30
TARGET_BURN_RATE = 0.65

SURPRISE_TRIGGERS = {
    "big_win": {"chance": 0.3, "rewards": [{"type": "coins", "min": 50, "max": 200}, {"type": "xp", "min": 20, "max": 50}]},
    "milestone": {"chance": 0.5, "rewards": [{"type": "coins", "min": 100, "max": 500}, {"type": "booster", "value": "double_up"}]},
    "streak_7": {"chance": 0.8, "rewards": [{"type": "coins", "min": 200, "max": 500}, {"type": "booster", "value": "streak_shield"}]},
    "streak_30": {"chance": 1.0, "rewards": [{"type": "coins", "min": 500, "max": 1000}]},
    "first_win": {"chance": 1.0, "rewards": [{"type": "coins", "min": 100, "max": 100}]},
}


class EconomyEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def check_daily_cap(self, user_id: str) -> Dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        earned = await self.db.daily_earnings.find_one({"user_id": user_id, "date": today})
        total = earned.get("total", 0) if earned else 0
        return {"earned_today": total, "cap": DAILY_COIN_CAP, "remaining": max(0, DAILY_COIN_CAP - total)}

    async def record_earning(self, user_id: str, amount: int, source: str):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        await self.db.daily_earnings.update_one(
            {"user_id": user_id, "date": today},
            {"$inc": {"total": amount}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
             "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )

    async def check_redeem_limit(self, user_id: str) -> Dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        count = await self.db.redemptions.count_documents({"user_id": user_id, "date": today})
        return {"redeemed_today": count, "limit": DAILY_REDEEM_LIMIT, "can_redeem": count < DAILY_REDEEM_LIMIT}

    async def try_surprise_reward(self, user_id: str, trigger: str) -> Optional[Dict]:
        config = SURPRISE_TRIGGERS.get(trigger)
        if not config:
            return None
        if random.random() > config["chance"]:
            return None

        reward = random.choice(config["rewards"])
        result = {"trigger": trigger, "type": reward["type"]}

        if reward["type"] == "coins":
            amount = random.randint(reward.get("min", 10), reward.get("max", 100))
            result["amount"] = amount
        elif reward["type"] == "xp":
            amount = random.randint(reward.get("min", 10), reward.get("max", 50))
            result["amount"] = amount
        elif reward["type"] == "booster":
            result["booster"] = reward.get("value", "double_up")

        await self.db.surprise_rewards.insert_one({
            "user_id": user_id, "trigger": trigger, "reward": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return result

    async def get_economy_stats(self) -> Dict:
        total_minted = await self.db.coin_transactions.aggregate([
            {"$match": {"type": {"$in": ["earned", "bonus", "reward", "prediction", "game_win", "referral"]}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]).to_list(1)
        total_burned = await self.db.coin_transactions.aggregate([
            {"$match": {"type": {"$in": ["spent", "redeem", "entry_fee"]}}},
            {"$group": {"_id": None, "total": {"$sum": {"$abs": "$amount"}}}},
        ]).to_list(1)

        minted = total_minted[0]["total"] if total_minted else 0
        burned = total_burned[0]["total"] if total_burned else 0
        burn_rate = round(burned / minted * 100, 1) if minted > 0 else 0

        return {
            "total_minted": minted,
            "total_burned": burned,
            "burn_rate": burn_rate,
            "target_burn_rate": TARGET_BURN_RATE * 100,
            "daily_cap": DAILY_COIN_CAP,
            "redeem_limit": DAILY_REDEEM_LIMIT,
            "bonus_expiry_days": BONUS_EXPIRY_DAYS,
        }
