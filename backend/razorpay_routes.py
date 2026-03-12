"""
Razorpay Payment Integration for FREE11
Pluggable — works when RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are set in .env
Falls back to Stripe if Razorpay keys not available.
"""
import os
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

razorpay_router = APIRouter(prefix="/api/razorpay", tags=["razorpay"])

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)

PACKAGES = {
    "starter": {"amount": 4900, "bucks": 50, "label": "Starter Pack"},
    "popular": {"amount": 14900, "bucks": 160, "label": "Popular Pack"},
    "value": {"amount": 49900, "bucks": 550, "label": "Value Pack"},
    "mega": {"amount": 99900, "bucks": 1200, "label": "Mega Pack"},
}

_db = None
_freebucks = None
_notif = None


def init_razorpay(db, freebucks_engine, notif_engine):
    global _db, _freebucks, _notif
    _db = db
    _freebucks = freebucks_engine
    _notif = notif_engine


class CreateOrderReq(BaseModel):
    package_id: str


class VerifyPaymentReq(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@razorpay_router.get("/status")
async def razorpay_status():
    return {"enabled": RAZORPAY_ENABLED, "key_id": RAZORPAY_KEY_ID if RAZORPAY_ENABLED else None}


@razorpay_router.get("/packages")
async def get_packages():
    return PACKAGES


@razorpay_router.post("/create-order")
async def create_order(req: CreateOrderReq, request: Request):
    if not RAZORPAY_ENABLED:
        raise HTTPException(503, "Razorpay not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env")

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(401, "Authentication required")

    from server import SECRET_KEY
    import jwt as pyjwt
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(401, "Invalid token")

    if req.package_id not in PACKAGES:
        raise HTTPException(400, "Invalid package")

    pkg = PACKAGES[req.package_id]

    import httpx
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.razorpay.com/v1/orders",
                auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
                json={
                    "amount": pkg["amount"],
                    "currency": "INR",
                    "receipt": f"free11_{user_id[:8]}_{req.package_id}",
                    "notes": {"user_id": user_id, "package_id": req.package_id, "bucks": str(pkg["bucks"])},
                },
            )
            if r.status_code != 200:
                raise HTTPException(500, f"Razorpay order creation failed: {r.text}")
            order = r.json()
    except httpx.HTTPError as e:
        raise HTTPException(500, f"Razorpay error: {str(e)}")

    await _db.payment_transactions.insert_one({
        "provider": "razorpay",
        "order_id": order["id"],
        "user_id": user_id,
        "package_id": req.package_id,
        "amount": pkg["amount"] / 100,
        "currency": "INR",
        "bucks": pkg["bucks"],
        "payment_status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "order_id": order["id"],
        "amount": pkg["amount"],
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID,
        "package": pkg,
    }


@razorpay_router.post("/verify")
async def verify_payment(req: VerifyPaymentReq, request: Request):
    if not RAZORPAY_ENABLED:
        raise HTTPException(503, "Razorpay not configured")

    # Verify signature
    message = f"{req.razorpay_order_id}|{req.razorpay_payment_id}"
    expected = hmac.new(RAZORPAY_KEY_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()

    if expected != req.razorpay_signature:
        raise HTTPException(400, "Invalid payment signature")

    # Check idempotency
    existing = await _db.payment_transactions.find_one({
        "order_id": req.razorpay_order_id, "payment_status": "paid"
    })
    if existing:
        return {"status": "already_processed", "bucks": existing.get("bucks", 0)}

    txn = await _db.payment_transactions.find_one({"order_id": req.razorpay_order_id})
    if not txn:
        raise HTTPException(404, "Order not found")

    # Update transaction
    await _db.payment_transactions.update_one(
        {"order_id": req.razorpay_order_id},
        {"$set": {
            "payment_status": "paid",
            "razorpay_payment_id": req.razorpay_payment_id,
            "razorpay_signature": req.razorpay_signature,
            "paid_at": datetime.now(timezone.utc).isoformat(),
        }},
    )

    # Credit FREE Bucks
    bucks = txn.get("bucks", 0)
    user_id = txn.get("user_id", "")
    if bucks > 0 and user_id and _freebucks:
        await _freebucks.credit(user_id, bucks, "razorpay_purchase", req.razorpay_order_id)
        if _notif:
            await _notif.send(user_id, "payment_success", f"Payment successful! {bucks} FREE Bucks credited.")

    return {"status": "success", "bucks": bucks}


@razorpay_router.post("/webhook")
async def razorpay_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("X-Razorpay-Signature", "")

    if RAZORPAY_KEY_SECRET:
        expected = hmac.new(RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256).hexdigest()
        if expected != sig:
            return {"status": "invalid_signature"}

    import json
    try:
        event = json.loads(body)
    except Exception:
        return {"status": "invalid_body"}

    event_type = event.get("event", "")
    if event_type == "payment.captured":
        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment.get("order_id", "")
        payment_id = payment.get("id", "")

        txn = await _db.payment_transactions.find_one({"order_id": order_id})
        if txn and txn.get("payment_status") != "paid":
            await _db.payment_transactions.update_one(
                {"order_id": order_id},
                {"$set": {"payment_status": "paid", "razorpay_payment_id": payment_id, "paid_at": datetime.now(timezone.utc).isoformat()}},
            )
            bucks = txn.get("bucks", 0)
            user_id = txn.get("user_id", "")
            if bucks > 0 and user_id and _freebucks:
                await _freebucks.credit(user_id, bucks, "razorpay_webhook", order_id)

    return {"status": "ok"}
