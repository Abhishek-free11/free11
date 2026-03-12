"""
Airtime / Mobile Recharge Routes for FREE11.
Endpoints: catalog, recharge, status.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
import re

from server import db, get_current_user, User

airtime_router = APIRouter(prefix="/api/airtime", tags=["airtime"])


class RechargeRequest(BaseModel):
    plan_id: str
    phone: str   # Indian mobile number (10 digits or +91...)


def _clean_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) != 10:
        raise ValueError(f"Invalid phone number: {phone}")
    return digits


@airtime_router.get("/catalog")
async def get_recharge_catalog():
    """Return all available recharge plans by carrier."""
    from providers.airtime_provider import airtime
    catalog = await airtime.get_catalog()
    return {"catalog": catalog, "currency": "INR", "powered_by": "Reloadly"}


@airtime_router.post("/recharge")
async def send_recharge(req: RechargeRequest, current_user: User = Depends(get_current_user)):
    """Redeem coins for a mobile recharge."""
    from providers.airtime_provider import airtime, _PLAN_LOOKUP

    plan = airtime.get_plan(req.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan_id")

    try:
        phone = _clean_phone(req.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    coins_needed = plan["coins"]
    user = await db.users.find_one({"_id": current_user.id}, {"_id": 0, "coins_balance": 1})
    balance = user.get("coins_balance", 0) if user else 0

    if balance < coins_needed:
        raise HTTPException(status_code=402, detail=f"Insufficient coins. Need {coins_needed}, have {balance}.")

    # Deduct coins
    await db.users.update_one(
        {"_id": current_user.id},
        {"$inc": {"coins_balance": -coins_needed}}
    )

    # Record transaction
    await db.coin_transactions.insert_one({
        "user_id":     str(current_user.id),
        "amount":      -coins_needed,
        "type":        "spend",
        "description": f"Mobile Recharge: {plan['carrier_name']} ₹{plan['inr']} — {phone}",
        "created_at":  datetime.now(timezone.utc),
    })

    # Send recharge via Reloadly
    result = await airtime.send_recharge(req.plan_id, phone, str(current_user.id))

    # Save order record
    order = {
        "user_id":        str(current_user.id),
        "type":           "airtime",
        "plan_id":        req.plan_id,
        "carrier":        plan.get("carrier_name", ""),
        "inr_amount":     plan["inr"],
        "phone":          phone,
        "coins_used":     coins_needed,
        "status":         result.get("status", "failed"),
        "transaction_id": result.get("transaction_id", ""),
        "mock":           result.get("mock", False),
        "created_at":     datetime.now(timezone.utc),
    }
    insert = await db.airtime_orders.insert_one(order)
    order_id = str(insert.inserted_id)

    if result.get("status") == "failed":
        # Refund coins on hard failure
        await db.users.update_one({"_id": current_user.id}, {"$inc": {"coins_balance": coins_needed}})
        raise HTTPException(status_code=500, detail="Recharge failed. Coins refunded.")

    return {
        "success":        True,
        "order_id":       order_id,
        "status":         result.get("status"),
        "transaction_id": result.get("transaction_id"),
        "carrier":        plan["carrier_name"],
        "inr_amount":     plan["inr"],
        "phone":          phone,
        "coins_used":     coins_needed,
        "mock":           result.get("mock", False),
        "message":        "Recharge queued — will be delivered once Reloadly account is activated." if result.get("mock") else f"₹{plan['inr']} recharge sent to {phone}!",
    }


@airtime_router.get("/orders")
async def get_my_recharge_orders(current_user: User = Depends(get_current_user)):
    """Get user's recharge order history."""
    orders = await db.airtime_orders.find(
        {"user_id": str(current_user.id)},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    return {"orders": orders}
