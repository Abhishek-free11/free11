"""
Spin Wheel / Mystery Reward Box for FREE11
Daily spin with configurable probability distribution.
"""
import uuid
import random
import logging
from datetime import datetime, timezone
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

DEFAULT_REWARDS = [
    {"id": "coins_25", "label": "25 Coins", "type": "coins", "value": 25, "weight": 30},
    {"id": "coins_50", "label": "50 Coins", "type": "coins", "value": 50, "weight": 25},
    {"id": "coins_100", "label": "100 Coins", "type": "coins", "value": 100, "weight": 15},
    {"id": "coins_250", "label": "250 Coins", "type": "coins", "value": 250, "weight": 5},
    {"id": "booster_double", "label": "Double Coins Card", "type": "booster", "value": "double_up", "weight": 10},
    {"id": "booster_shield", "label": "Prediction Shield", "type": "booster", "value": "streak_shield", "weight": 8},
    {"id": "xp_50", "label": "50 XP Boost", "type": "xp", "value": 50, "weight": 5},
    {"id": "nothing", "label": "Better Luck Tomorrow!", "type": "none", "value": 0, "weight": 2},
]


class SpinWheelEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def can_spin(self, user_id: str) -> Dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        last = await self.db.spin_history.find_one({"user_id": user_id, "date": today})
        return {"can_spin": last is None, "next_spin": "tomorrow" if last else "now"}

    async def spin(self, user_id: str) -> Dict:
        check = await self.can_spin(user_id)
        if not check["can_spin"]:
            raise ValueError("Already spun today. Come back tomorrow!")

        # Weighted random selection
        config = await self.db.spin_config.find_one({"active": True}, {"_id": 0})
        rewards = config.get("rewards", DEFAULT_REWARDS) if config else DEFAULT_REWARDS

        total_weight = sum(r["weight"] for r in rewards)
        roll = random.uniform(0, total_weight)
        cumulative = 0
        selected = rewards[-1]
        for r in rewards:
            cumulative += r["weight"]
            if roll <= cumulative:
                selected = r
                break

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        await self.db.spin_history.insert_one({
            "user_id": user_id, "date": today, "reward": selected,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "reward": selected,
            "all_rewards": [{"id": r["id"], "label": r["label"], "type": r["type"]} for r in rewards],
        }

    async def get_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        return await self.db.spin_history.find(
            {"user_id": user_id}, {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)

    async def admin_set_config(self, rewards: List[Dict]) -> Dict:
        await self.db.spin_config.update_one(
            {"active": True},
            {"$set": {"rewards": rewards, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
        return {"updated": True}
