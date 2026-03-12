"""
Cashfree Payments Integration for FREE11
=========================================
Faster activation than Razorpay — same packages, same FreeBucks reward logic.
Falls back gracefully when keys are not set.

API version: 2023-08-01
Docs: https://docs.cashfree.com/reference/pg-new-apis-endpoint
"""
import os
import hmac
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from server import db, get_current_user, User

logger = logging.getLogger(__name__)

cashfree_router = APIRouter(prefix="/cashfree", tags=["Cashfree Payments"])

CASHFREE_APP_ID     = os.environ.get("CASHFREE_APP_ID", "")
CASHFREE_SECRET_KEY = os.environ.get("CASHFREE_SECRET_KEY", "")
CASHFREE_ENV        = os.environ.get("CASHFREE_ENVIRONMENT", "sandbox")   # sandbox | production
CASHFREE_ENABLED    = bool(CASHFREE_APP_ID and CASHFREE_SECRET_KEY)

_BASE = {
    "sandbox":    "https://sandbox.cashfree.com/pg",
    "production": "https://api.cashfree.com/pg",
}[CASHFREE_ENV] if CASHFREE_ENV in ("sandbox", "production") else "https://sandbox.cashfree.com/pg"

_API_VERSION = "2023-08-01"

PACKAGES = {
    "starter": {"amount": 49,   "bucks": 50,   "label": "Starter Pack"},
    "popular": {"amount": 149,  "bucks": 160,  "label": "Popular Pack"},
    "value":   {"amount": 499,  "bucks": 550,  "label": "Value Pack"},
    "mega":    {"amount": 999,  "bucks": 1200, "label": "Mega Pack"},
}


def _headers() -> dict:
    return {
        "x-api-version":  _API_VERSION,
        "x-client-id":    CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "Content-Type":   "application/json",
    }


class CreateOrderReq(BaseModel):
    package_id: str


class VerifyPaymentReq(BaseModel):
    order_id: str


# ── Status ────────────────────────────────────────────────────────────────────

@cashfree_router.get("/status")
async def cashfree_status():
    return {
        "enabled":     CASHFREE_ENABLED,
        "environment": CASHFREE_ENV,
        "app_id":      CASHFREE_APP_ID[:8] + "..." if CASHFREE_ENABLED else None,
    }


@cashfree_router.get("/packages")
async def get_packages():
    return PACKAGES


# ── Create Order ──────────────────────────────────────────────────────────────

@cashfree_router.post("/create-order")
async def create_order(req: CreateOrderReq, current_user: User = Depends(get_current_user)):
    if not CASHFREE_ENABLED:
        raise HTTPException(503, "Cashfree not configured. Add CASHFREE_APP_ID and CASHFREE_SECRET_KEY.")

    pkg = PACKAGES.get(req.package_id)
    if not pkg:
        raise HTTPException(400, "Invalid package_id")

    order_id = f"FREE11-{uuid.uuid4().hex[:12].upper()}"

    payload = {
        "order_id":       order_id,
        "order_amount":   pkg["amount"],
        "order_currency": "INR",
        "customer_details": {
            "customer_id":    current_user.id[:30],
            "customer_email": getattr(current_user, "email", "user@free11.com"),
            "customer_phone": getattr(current_user, "phone", "9999999999") or "9999999999",
            "customer_name":  getattr(current_user, "name", "FREE11 User") or "FREE11 User",
        },
        "order_meta": {
            "return_url":   f"https://free11.com/freebucks?cf_order_id={order_id}&payment_status=SUCCESS",
            "notify_url":   "https://free11.com/api/cashfree/webhook",
        },
        "order_tags": {
            "package_id": req.package_id,
            "user_id":    current_user.id,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{_BASE}/orders", json=payload, headers=_headers())
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        logger.error("Cashfree create order error %s: %s", e.response.status_code, e.response.text)
        raise HTTPException(502, f"Cashfree error: {e.response.text}")
    except Exception as e:
        logger.error("Cashfree create order exception: %s", e)
        raise HTTPException(502, "Payment gateway unavailable")

    # Persist pending order
    await db.cashfree_orders.insert_one({
        "order_id":   order_id,
        "user_id":    current_user.id,
        "package_id": req.package_id,
        "amount":     pkg["amount"],
        "bucks":      pkg["bucks"],
        "status":     "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "_id_excluded": True,
    })

    return {
        "order_id":           order_id,
        "payment_session_id": data.get("payment_session_id"),
        "amount":             pkg["amount"],
        "currency":           "INR",
        "package":            pkg,
        "environment":        CASHFREE_ENV,
    }


# ── Verify Payment ────────────────────────────────────────────────────────────

@cashfree_router.post("/verify")
async def verify_payment(req: VerifyPaymentReq, current_user: User = Depends(get_current_user)):
    if not CASHFREE_ENABLED:
        raise HTTPException(503, "Cashfree not configured.")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/orders/{req.order_id}/payments",
                headers=_headers(),
            )
            r.raise_for_status()
            payments = r.json()
    except Exception as e:
        logger.error("Cashfree verify error: %s", e)
        raise HTTPException(502, "Could not verify payment")

    # Find a successful payment
    success = next(
        (p for p in (payments if isinstance(payments, list) else [payments])
         if p.get("payment_status") == "SUCCESS"),
        None,
    )
    if not success:
        raise HTTPException(400, "Payment not successful")

    # Idempotency — check already credited
    existing = await db.cashfree_orders.find_one({"order_id": req.order_id, "_id": {"$exists": True}})
    if not existing:
        existing = await db.cashfree_orders.find_one({"order_id": req.order_id})

    if existing and existing.get("status") == "PAID":
        return {"success": True, "already_credited": True, "bucks": existing.get("bucks", 0)}

    # Find order record
    order_rec = await db.cashfree_orders.find_one({"order_id": req.order_id})
    if not order_rec:
        raise HTTPException(404, "Order not found")

    if order_rec["user_id"] != current_user.id:
        raise HTTPException(403, "Order does not belong to you")

    bucks = order_rec["bucks"]
    now   = datetime.now(timezone.utc).isoformat()

    # Credit FREE Bucks
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"free_bucks": bucks}},
    )

    # Mark order paid
    await db.cashfree_orders.update_one(
        {"order_id": req.order_id},
        {"$set": {"status": "PAID", "paid_at": now,
                  "cf_payment_id": success.get("cf_payment_id")}},
    )

    # Coin transaction ledger
    await db.coin_transactions.insert_one({
        "id":          str(uuid.uuid4()),
        "user_id":     current_user.id,
        "amount":      bucks,
        "type":        "purchase",
        "description": f"Cashfree: {order_rec['package_id']} — {bucks} FREE Bucks",
        "created_at":  now,
    })

    logger.info("Cashfree payment credited: user=%s bucks=%s order=%s", current_user.id, bucks, req.order_id)

    return {"success": True, "bucks_credited": bucks, "order_id": req.order_id}


# ── Webhook ───────────────────────────────────────────────────────────────────

@cashfree_router.post("/webhook")
async def cashfree_webhook(request: Request):
    """
    Cashfree sends payment events here.
    Signature verification: HMAC-SHA256(timestamp + rawBody, secret)
    """
    raw_body    = await request.body()
    timestamp   = request.headers.get("x-webhook-timestamp", "")
    signature   = request.headers.get("x-webhook-signature", "")

    if CASHFREE_SECRET_KEY and timestamp and signature:
        expected = hmac.new(
            CASHFREE_SECRET_KEY.encode(),
            (timestamp + raw_body.decode()).encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            logger.warning("Cashfree webhook signature mismatch")
            raise HTTPException(400, "Invalid signature")

    import json
    try:
        event = json.loads(raw_body)
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    event_type = event.get("type", "")
    if event_type == "PAYMENT_SUCCESS_WEBHOOK":
        data     = event.get("data", {})
        order_id = data.get("order", {}).get("order_id", "")
        if order_id:
            rec = await db.cashfree_orders.find_one({"order_id": order_id})
            if rec and rec.get("status") != "PAID":
                bucks = rec.get("bucks", 0)
                now   = datetime.now(timezone.utc).isoformat()
                await db.users.update_one({"id": rec["user_id"]}, {"$inc": {"free_bucks": bucks}})
                await db.cashfree_orders.update_one(
                    {"order_id": order_id},
                    {"$set": {"status": "PAID", "paid_at": now}},
                )
                logger.info("Cashfree webhook credited: order=%s bucks=%s", order_id, bucks)

    return {"status": "ok"}
