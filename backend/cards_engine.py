"""
Cards Engine for FREE11
Card inventory, activation, expiry, anti-exploit (no stacking, lock enforcement)
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Card definitions
CARD_TYPES = {
    "2x_coins": {
        "name": "Double Coins",
        "description": "Double your coins for the next correct prediction",
        "effect": "multiply_reward",
        "multiplier": 2,
        "duration_minutes": 0,
        "rarity": "common",
    },
    "shield": {
        "name": "Prediction Shield",
        "description": "Protect your streak if prediction is wrong",
        "effect": "protect_streak",
        "multiplier": 1,
        "duration_minutes": 0,
        "rarity": "rare",
    },
    "3x_coins": {
        "name": "Triple Coins",
        "description": "Triple your coins for the next correct prediction",
        "effect": "multiply_reward",
        "multiplier": 3,
        "duration_minutes": 0,
        "rarity": "epic",
    },
    "extra_prediction": {
        "name": "Extra Prediction",
        "description": "Get one extra prediction slot for this over",
        "effect": "extra_slot",
        "multiplier": 1,
        "duration_minutes": 0,
        "rarity": "rare",
    },
    "insight": {
        "name": "Match Insight",
        "description": "See prediction distribution before submitting",
        "effect": "show_distribution",
        "multiplier": 1,
        "duration_minutes": 5,
        "rarity": "common",
    },
}


class CardsEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ── Inventory ──

    async def grant_card(self, user_id: str, card_type: str, source: str = "reward") -> Dict:
        """Grant a card to user's inventory"""
        if card_type not in CARD_TYPES:
            raise ValueError(f"Invalid card type: {card_type}")

        card_def = CARD_TYPES[card_type]
        now = datetime.now(timezone.utc)
        card = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "card_type": card_type,
            "name": card_def["name"],
            "description": card_def["description"],
            "effect": card_def["effect"],
            "multiplier": card_def["multiplier"],
            "rarity": card_def["rarity"],
            "status": "inventory",
            "source": source,
            "prediction_id": None,
            "activated_at": None,
            "expires_at": (now + timedelta(days=7)).isoformat(),
            "created_at": now.isoformat(),
        }
        await self.db.cards.insert_one(card)
        logger.info(f"CARD GRANTED: user={user_id} type={card_type} source={source}")
        return {k: v for k, v in card.items() if k != "_id"}

    async def get_inventory(self, user_id: str) -> List[Dict]:
        """Get user's available cards (not expired, not used)"""
        now = datetime.now(timezone.utc).isoformat()
        cards = await self.db.cards.find({
            "user_id": user_id,
            "status": "inventory",
            "expires_at": {"$gt": now},
        }, {"_id": 0}).sort("created_at", -1).to_list(100)
        return cards

    # ── Activation (atomic) ──

    async def activate_card(self, user_id: str, card_id: str, prediction_id: str) -> Dict:
        """
        Activate a card for a specific prediction.
        Atomic: prevents stacking, double activation, post-lock activation.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Check card exists and belongs to user
        card = await self.db.cards.find_one({
            "id": card_id,
            "user_id": user_id,
            "status": "inventory",
        }, {"_id": 0})

        if not card:
            raise ValueError("Card not found or already used")

        # Check expiry
        if card.get("expires_at", "") < now:
            raise ValueError("Card has expired")

        # Check no other card active on this prediction (no stacking)
        existing_active = await self.db.cards.find_one({
            "prediction_id": prediction_id,
            "status": "active",
        }, {"_id": 0})
        if existing_active:
            raise ValueError("Another card is already active on this prediction (no stacking)")

        # Check the prediction is still pending (not locked/resolved)
        prediction = await self.db.predictions_v2.find_one(
            {"id": prediction_id, "user_id": user_id},
            {"_id": 0}
        )
        if not prediction:
            raise ValueError("Prediction not found")
        if prediction.get("status") != "pending":
            raise ValueError("Cannot activate card: prediction already resolved or voided")

        # Atomic activation
        result = await self.db.cards.update_one(
            {"id": card_id, "status": "inventory", "user_id": user_id},
            {"$set": {
                "status": "active",
                "prediction_id": prediction_id,
                "activated_at": now,
            }}
        )

        if result.modified_count == 0:
            raise ValueError("Failed to activate card (race condition)")

        logger.info(f"CARD ACTIVATED: user={user_id} card={card_id} prediction={prediction_id}")
        return {"activated": True, "card_type": card["card_type"], "effect": card["effect"]}

    # ── Apply card effects (called during resolution) ──

    async def get_active_card_for_prediction(self, prediction_id: str) -> Optional[Dict]:
        """Get the active card for a prediction (if any)"""
        card = await self.db.cards.find_one({
            "prediction_id": prediction_id,
            "status": "active",
        }, {"_id": 0})
        return card

    async def consume_card(self, card_id: str):
        """Mark card as consumed after prediction resolution"""
        await self.db.cards.update_one(
            {"id": card_id},
            {"$set": {"status": "consumed", "consumed_at": datetime.now(timezone.utc).isoformat()}}
        )

    # ── Expiry cleanup ──

    async def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        result = await self.db.cards.update_many(
            {"status": "inventory", "expires_at": {"$lt": now}},
            {"$set": {"status": "expired"}}
        )
        return result.modified_count

    # ── Card type info ──

    def get_card_types(self) -> Dict:
        return CARD_TYPES
