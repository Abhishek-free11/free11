"""
Payment Routes for FREE11 — Razorpay Only
Stripe has been removed. All payments go through /api/razorpay/*.
This file kept for backward compatibility of /api/payments/packages endpoint.
"""
from fastapi import APIRouter

payment_router = APIRouter(prefix="/api/payments", tags=["payments"])

PACKAGES = {
    "starter": {"amount": 49.00, "currency": "inr", "bucks": 50, "label": "Starter Pack", "bonus": 0},
    "popular": {"amount": 149.00, "currency": "inr", "bucks": 160, "label": "Popular Pack", "bonus": 10},
    "value": {"amount": 499.00, "currency": "inr", "bucks": 550, "label": "Value Pack", "bonus": 50},
    "mega": {"amount": 999.00, "currency": "inr", "bucks": 1200, "label": "Mega Pack", "bonus": 200},
}

def init_payment(db, freebucks_engine, notification_engine, analytics_engine):
    pass  # No-op — Razorpay handles everything now

@payment_router.get("/packages")
async def get_packages():
    return PACKAGES
