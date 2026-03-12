"""
P2P + Referral Engine for FREE11
Unique invite codes, one-time bind, anti-fraud (self-referral, duplicate device)
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

REFERRAL_REWARD_REFERRER = 50  # coins for referrer
REFERRAL_REWARD_REFEREE = 25   # coins for new user
# Section 5: minimum activity before referral reward is granted
MIN_PREDICTIONS_FOR_REFERRAL = 3
MIN_CONTESTS_FOR_REFERRAL = 1


class ReferralEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def generate_referral_code(self, user_id: str) -> str:
        """Get or create a unique referral code for a user"""
        existing = await self.db.referral_codes.find_one({"user_id": user_id}, {"_id": 0})
        if existing:
            return existing["code"]

        code = f"F11-{uuid.uuid4().hex[:6].upper()}"
        await self.db.referral_codes.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "code": code,
            "uses": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return code

    async def bind_referral(
        self,
        referee_id: str,
        referral_code: str,
        device_fingerprint: Optional[str] = None,
    ) -> Dict:
        """
        Bind a referral code to a new user (one-time).
        Prevents: self-referral, duplicate bind, duplicate device.
        """
        # Find the referral code
        ref = await self.db.referral_codes.find_one({"code": referral_code.upper()}, {"_id": 0})
        if not ref:
            raise ValueError("Invalid referral code")

        referrer_id = ref["user_id"]

        # Prevent self-referral
        if referrer_id == referee_id:
            raise ValueError("Cannot use your own referral code")

        # Check if user already has a referral binding
        existing_bind = await self.db.referral_bindings.find_one({"referee_id": referee_id}, {"_id": 0})
        if existing_bind:
            raise ValueError("Referral code already applied")

        # Check duplicate device
        if device_fingerprint:
            device_used = await self.db.referral_bindings.find_one(
                {"device_fingerprint": device_fingerprint},
                {"_id": 0}
            )
            if device_used:
                raise ValueError("This device has already been used for a referral")

        # Create binding — status "pending" until referee meets minimum activity
        now = datetime.now(timezone.utc).isoformat()
        binding = {
            "id": str(uuid.uuid4()),
            "referrer_id": referrer_id,
            "referee_id": referee_id,
            "referral_code": referral_code.upper(),
            "device_fingerprint": device_fingerprint,
            "status": "pending",   # awaiting activity gate
            "created_at": now,
        }
        await self.db.referral_bindings.insert_one(binding)

        # Increment usage count
        await self.db.referral_codes.update_one(
            {"code": referral_code.upper()},
            {"$inc": {"uses": 1}}
        )

        logger.info(f"REFERRAL BIND (pending): referrer={referrer_id} referee={referee_id}")
        return {
            "referrer_reward": REFERRAL_REWARD_REFERRER,
            "referee_reward": REFERRAL_REWARD_REFEREE,
            "referrer_id": referrer_id,
            "status": "pending",
            "message": f"Make {MIN_PREDICTIONS_FOR_REFERRAL} predictions or join 1 contest to unlock the reward",
        }

    async def check_and_complete_referral(self, referee_id: str) -> Optional[Dict]:
        """
        Called after each prediction/contest join.
        If referee meets the activity gate, complete the referral and award coins.
        Returns payout info if reward was just issued, else None.
        """
        binding = await self.db.referral_bindings.find_one(
            {"referee_id": referee_id, "status": "pending"}, {"_id": 0}
        )
        if not binding:
            return None

        # Check activity gate
        predictions_count = await self.db.predictions_v2.count_documents({"user_id": referee_id})
        contests_joined = await self.db.contests.count_documents({"participants": referee_id})

        qualifies = (predictions_count >= MIN_PREDICTIONS_FOR_REFERRAL) or (contests_joined >= MIN_CONTESTS_FOR_REFERRAL)
        if not qualifies:
            return None

        now = datetime.now(timezone.utc).isoformat()
        # Mark completed
        await self.db.referral_bindings.update_one(
            {"referee_id": referee_id, "status": "pending"},
            {"$set": {"status": "completed", "completed_at": now}}
        )

        referrer_id = binding["referrer_id"]

        # Award referee
        await self.db.users.update_one({"id": referee_id}, {"$inc": {"coins_balance": REFERRAL_REWARD_REFEREE, "total_earned": REFERRAL_REWARD_REFEREE}})
        await self.db.coin_transactions.insert_one({
            "user_id": referee_id, "amount": REFERRAL_REWARD_REFEREE, "type": "referral_bonus",
            "description": "Referral reward: completed activity gate", "timestamp": now,
        })

        # Award referrer
        await self.db.users.update_one({"id": referrer_id}, {"$inc": {"coins_balance": REFERRAL_REWARD_REFERRER, "total_earned": REFERRAL_REWARD_REFERRER}})
        await self.db.coin_transactions.insert_one({
            "user_id": referrer_id, "amount": REFERRAL_REWARD_REFERRER, "type": "referral_bonus",
            "description": f"Referral reward: your invitee completed activity", "timestamp": now,
        })

        logger.info(f"REFERRAL COMPLETED: referrer={referrer_id} referee={referee_id}")
        return {"referrer_id": referrer_id, "referee_id": referee_id,
                "referrer_coins": REFERRAL_REWARD_REFERRER, "referee_coins": REFERRAL_REWARD_REFEREE}

    async def get_referral_stats(self, user_id: str) -> Dict:
        code_doc = await self.db.referral_codes.find_one({"user_id": user_id}, {"_id": 0})
        code = code_doc["code"] if code_doc else await self.generate_referral_code(user_id)

        referrals = await self.db.referral_bindings.find(
            {"referrer_id": user_id},
            {"_id": 0}
        ).to_list(1000)

        total_earned = len(referrals) * REFERRAL_REWARD_REFERRER

        return {
            "referral_code": code,
            "total_referrals": len(referrals),
            "total_earned": total_earned,
            "reward_per_referral": REFERRAL_REWARD_REFERRER,
        }
