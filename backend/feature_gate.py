"""
Feature Gating Engine for FREE11
Server-side enforcement of premium features behind FREE Bucks.
"""
import logging
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

GATED_FEATURES = {
    "ad_free_join": {"cost": 5, "label": "Ad-Free Contest Join", "description": "Join contests without watching ads"},
    "advanced_stats": {"cost": 10, "label": "Advanced Stats", "description": "Player form, head-to-head, venue analysis"},
    "fast_lane_join": {"cost": 3, "label": "Fast-Lane Join", "description": "Priority contest slot reservation"},
}


class FeatureGate:
    def __init__(self, db: AsyncIOMotorDatabase, freebucks_engine):
        self.db = db
        self.freebucks = freebucks_engine

    async def check_access(self, user_id: str, feature: str) -> Dict:
        if feature not in GATED_FEATURES:
            return {"allowed": True, "reason": "free_feature"}
        balance = await self.freebucks.get_balance(user_id)
        cost = GATED_FEATURES[feature]["cost"]
        return {
            "allowed": balance >= cost,
            "feature": feature,
            "cost": cost,
            "balance": balance,
            "label": GATED_FEATURES[feature]["label"],
        }

    async def consume_feature(self, user_id: str, feature: str, reference_id: str = "") -> Dict:
        if feature not in GATED_FEATURES:
            return {"consumed": True, "cost": 0}
        access = await self.check_access(user_id, feature)
        if not access["allowed"]:
            raise ValueError(f"Insufficient FREE Bucks for {GATED_FEATURES[feature]['label']}. Need {GATED_FEATURES[feature]['cost']}, have {access['balance']}")
        result = await self.freebucks.debit(user_id, GATED_FEATURES[feature]["cost"], feature, reference_id)
        return {"consumed": True, "cost": GATED_FEATURES[feature]["cost"], "new_balance": result["new_balance"]}

    @staticmethod
    def get_gated_features() -> Dict:
        return GATED_FEATURES
