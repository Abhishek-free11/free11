"""
Mock Ads Provider for FREE11
Plug-replaceable: swap MockAdsProvider with real AdMob/Unity Ads later
"""
import uuid
from datetime import datetime, timezone, date
from typing import Dict


class AdsProvider:
    """Interface for ad providers"""
    async def start_ad(self, user_id: str) -> Dict:
        raise NotImplementedError

    async def complete_ad(self, user_id: str, ad_id: str) -> Dict:
        raise NotImplementedError


class MockAdsProvider(AdsProvider):
    """Mock implementation simulating rewarded video ads"""

    DAILY_AD_LIMIT = 5
    AD_REWARD_COINS = 10
    AD_DURATION_SECONDS = 10

    def __init__(self, db):
        self.db = db

    async def _get_daily_count(self, user_id: str) -> int:
        today = date.today().isoformat()
        return await self.db.ad_events.count_documents({
            "user_id": user_id,
            "date": today,
            "status": "completed"
        })

    async def start_ad(self, user_id: str) -> Dict:
        daily_count = await self._get_daily_count(user_id)
        if daily_count >= self.DAILY_AD_LIMIT:
            return {"error": "daily_limit_reached", "limit": self.DAILY_AD_LIMIT}

        ad_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        today = date.today().isoformat()

        await self.db.ad_events.insert_one({
            "id": ad_id,
            "user_id": user_id,
            "status": "started",
            "date": today,
            "started_at": now,
            "completed_at": None,
            "reward_coins": 0,
            "provider": "mock",
        })

        return {
            "ad_id": ad_id,
            "duration_seconds": self.AD_DURATION_SECONDS,
            "reward_coins": self.AD_REWARD_COINS,
            "remaining_today": self.DAILY_AD_LIMIT - daily_count - 1,
        }

    async def complete_ad(self, user_id: str, ad_id: str) -> Dict:
        ad = await self.db.ad_events.find_one(
            {"id": ad_id, "user_id": user_id, "status": "started"}, {"_id": 0}
        )
        if not ad:
            return {"error": "invalid_ad"}

        now = datetime.now(timezone.utc).isoformat()
        await self.db.ad_events.update_one(
            {"id": ad_id},
            {"$set": {
                "status": "completed",
                "completed_at": now,
                "reward_coins": self.AD_REWARD_COINS,
            }}
        )

        daily_count = await self._get_daily_count(user_id)
        return {
            "reward_coins": self.AD_REWARD_COINS,
            "remaining_today": max(0, self.DAILY_AD_LIMIT - daily_count),
        }

    async def get_ad_status(self, user_id: str) -> Dict:
        daily_count = await self._get_daily_count(user_id)
        return {
            "daily_limit": self.DAILY_AD_LIMIT,
            "watched_today": daily_count,
            "remaining_today": max(0, self.DAILY_AD_LIMIT - daily_count),
            "reward_per_ad": self.AD_REWARD_COINS,
        }
