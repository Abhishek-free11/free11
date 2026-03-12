"""
Analytics Engine for FREE11
Internal event tracking for DAU, contest rates, retention, funnels.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def track(self, event: str, user_id: str = "", properties: Optional[Dict] = None):
        await self.db.analytics_events.insert_one({
            "event": event,
            "user_id": user_id,
            "properties": properties or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def get_dau(self, days: int = 7) -> List[Dict]:
        results = []
        for i in range(days):
            day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            count = await self.db.analytics_events.count_documents({
                "event": "login",
                "timestamp": {"$gte": f"{day}T00:00:00", "$lt": f"{day}T23:59:59"},
            })
            results.append({"date": day, "dau": count})
        return results

    async def get_contest_join_rate(self) -> Dict:
        total_users = await self.db.users.count_documents({})
        users_with_contests = len(await self.db.contest_entries.distinct("user_id"))
        return {
            "total_users": total_users,
            "users_joined_contests": users_with_contests,
            "join_rate": round(users_with_contests / total_users * 100, 1) if total_users > 0 else 0,
        }

    async def get_freebucks_conversion(self) -> Dict:
        total_users = await self.db.users.count_documents({})
        paying_users = await self.db.payment_transactions.count_documents({"payment_status": "paid"})
        return {
            "total_users": total_users,
            "paying_users": paying_users,
            "conversion_rate": round(paying_users / total_users * 100, 1) if total_users > 0 else 0,
        }

    async def get_redemption_rate(self) -> Dict:
        total_users = await self.db.users.count_documents({})
        redeemers = len(await self.db.redemptions.distinct("user_id"))
        return {
            "total_users": total_users,
            "redeemers": redeemers,
            "redemption_rate": round(redeemers / total_users * 100, 1) if total_users > 0 else 0,
        }

    async def get_retention(self, days: int = 7) -> Dict:
        now = datetime.now(timezone.utc)
        d1 = (now - timedelta(days=days)).isoformat()
        d0 = (now - timedelta(days=days + 1)).isoformat()
        cohort = await self.db.users.count_documents({"created_at": {"$gte": d0, "$lt": d1}})
        if cohort == 0:
            return {"cohort_size": 0, "retained": 0, "retention_rate": 0}
        retained = await self.db.analytics_events.count_documents({
            "event": "login",
            "timestamp": {"$gte": (now - timedelta(days=1)).isoformat()},
        })
        return {
            "cohort_size": cohort,
            "retained": min(retained, cohort),
            "retention_rate": round(min(retained, cohort) / cohort * 100, 1),
        }

    async def get_dashboard(self) -> Dict:
        return {
            "dau": await self.get_dau(7),
            "contest_join_rate": await self.get_contest_join_rate(),
            "freebucks_conversion": await self.get_freebucks_conversion(),
            "redemption_rate": await self.get_redemption_rate(),
            "retention_7d": await self.get_retention(7),
            "total_users": await self.db.users.count_documents({}),
            "total_matches_synced": await self.db.matches.count_documents({}),
            "total_fantasy_teams": await self.db.fantasy_teams.count_documents({}),
            "total_predictions": await self.db.predictions.count_documents({}),
        }
