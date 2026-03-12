"""
Mock Payment Provider for FREE11
Plug-replaceable: swap MockPaymentProvider with real Stripe/Razorpay later
"""
import uuid
from datetime import datetime, timezone
from typing import Dict


class PaymentProvider:
    """Interface for payment providers"""
    async def create_payment(self, user_id: str, amount: int, description: str) -> Dict:
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    """Mock - FREE11 is free, this is for future premium features"""

    def __init__(self, db):
        self.db = db

    async def create_payment(self, user_id: str, amount: int, description: str) -> Dict:
        payment_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        payment = {
            "id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "description": description,
            "status": "completed",
            "provider": "mock",
            "created_at": now,
        }
        await self.db.payments.insert_one(payment)
        return {"id": payment_id, "status": "completed"}
