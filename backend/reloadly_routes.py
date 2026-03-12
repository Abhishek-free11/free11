"""
Reloadly Gift Cards Routes for FREE11
======================================
Endpoints:
  GET  /api/reloadly/catalog          – Full India gift card catalog
  GET  /api/reloadly/catalog/india    – India catalog (alias, with category filter)
  POST /api/reloadly/order            – Direct order (coin deduction + fulfillment)
  GET  /api/reloadly/orders           – User's Reloadly order history
  GET  /api/reloadly/status           – Integration health check
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone
import uuid

from server import db, get_current_user, User
from reloadly_provider import reloadly, RELOADLY_ENABLED, RELOADLY_ENV

reloadly_router = APIRouter(prefix="/reloadly", tags=["Reloadly Gift Cards"])


# ── Models ────────────────────────────────────────────────────────────────────

class ReloadlyOrderReq(BaseModel):
    product_id: int
    denomination: float           # INR display value (for records + coin deduction)
    recipient_email: str
    sku_label: Optional[str] = ""
    sender_usd: Optional[float] = None  # USD override; resolved live from catalog if omitted


# ── Catalog ───────────────────────────────────────────────────────────────────

@reloadly_router.get("/catalog")
async def get_catalog(
    country: str = Query("IN", description="ISO country code"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the full Reloadly gift card catalog for the given country.
    Uses cached data (6-hour TTL). Returns mock data when keys are not set.
    """
    catalog = await reloadly.get_catalog(country=country)

    if category and category != "all":
        catalog = [p for p in catalog if p.get("category") == category]

    return {
        "products":  catalog,
        "total":     len(catalog),
        "country":   country,
        "is_live":   RELOADLY_ENABLED,
        "env":       RELOADLY_ENV if RELOADLY_ENABLED else "mock",
    }


@reloadly_router.get("/catalog/india")
async def get_india_catalog(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Shortcut — India catalog with optional category filter."""
    catalog = await reloadly.get_catalog(country="IN")
    if category and category != "all":
        catalog = [p for p in catalog if p.get("category") == category]

    # Group by category for front-end convenience
    categories: dict = {}
    for p in catalog:
        cat = p.get("category", "vouchers")
        categories.setdefault(cat, []).append(p)

    return {
        "products":   catalog,
        "by_category": categories,
        "total":      len(catalog),
        "is_live":    RELOADLY_ENABLED,
    }


# ── Direct Order ──────────────────────────────────────────────────────────────

@reloadly_router.post("/order")
async def place_order(
    req: ReloadlyOrderReq,
    current_user: User = Depends(get_current_user),
):
    """
    Place a Reloadly gift card order.
    Deducts coins from user balance proportional to denomination.
    Coin rate: 1 INR ≈ 1.1 coins (10% platform fee).
    """
    coin_cost = int(req.denomination * 1.1)

    # Check balance
    if current_user.coins_balance < coin_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient coins. Need {coin_cost}, have {current_user.coins_balance}.",
        )

    # Deduct coins atomically
    updated = await db.users.find_one_and_update(
        {"id": current_user.id, "coins_balance": {"$gte": coin_cost}},
        {"$inc": {"coins_balance": -coin_cost, "total_redeemed": coin_cost}},
        return_document=True,
        projection={"_id": 0, "coins_balance": 1},
    )
    if not updated:
        raise HTTPException(status_code=400, detail="Insufficient coins.")

    custom_id = f"free11-{current_user.id[:8]}-{uuid.uuid4().hex[:6]}"

    # Resolve sender USD live from catalog (auto-updates when Reloadly changes rates)
    sender_usd = req.sender_usd
    if sender_usd is None:
        sender_usd = await reloadly.get_sender_usd(req.product_id, req.denomination)
    if sender_usd is None:
        raise HTTPException(status_code=400, detail="Could not resolve sender price for this product/denomination.")

    result = await reloadly.place_order(
        product_id=req.product_id,
        unit_price=sender_usd,
        recipient_email=req.recipient_email,
        sender_name="FREE11 Rewards",
        custom_identifier=custom_id,
    )

    now = datetime.now(timezone.utc).isoformat()

    # Record order
    order_doc = {
        "id":              str(uuid.uuid4()),
        "user_id":         current_user.id,
        "product_id":      req.product_id,
        "denomination":    req.denomination,
        "coin_cost":       coin_cost,
        "recipient_email": req.recipient_email,
        "sku_label":       req.sku_label,
        "custom_id":       custom_id,
        "status":          result.get("status", "failed"),
        "voucher_code":    result.get("voucher_code"),
        "voucher_pin":     result.get("voucher_pin"),
        "transaction_id":  result.get("transaction_id"),
        "mock":            result.get("mock", True),
        "created_at":      now,
    }
    await db.reloadly_orders.insert_one(order_doc)

    # Coin ledger entry
    await db.coin_transactions.insert_one({
        "id":          str(uuid.uuid4()),
        "user_id":     current_user.id,
        "amount":      -coin_cost,
        "type":        "spent",
        "description": f"Reloadly: {req.sku_label or f'Gift Card ₹{req.denomination}'}",
        "created_at":  now,
    })

    if result.get("status") != "delivered":
        # Coins already deducted — log for ops team; do not raise
        return {
            "success":     False,
            "error":       result.get("error", "Order failed"),
            "new_balance": updated["coins_balance"],
        }

    return {
        "success":      True,
        "voucher_code": result["voucher_code"],
        "voucher_pin":  result.get("voucher_pin"),
        "denomination": req.denomination,
        "coin_cost":    coin_cost,
        "new_balance":  updated["coins_balance"],
        "mock":         result.get("mock", True),
        "instructions": f"Voucher delivered to {req.recipient_email}.",
    }


# ── Order History ─────────────────────────────────────────────────────────────

@reloadly_router.get("/orders")
async def get_my_orders(current_user: User = Depends(get_current_user)):
    """Get current user's Reloadly gift card orders."""
    orders = await db.reloadly_orders.find(
        {"user_id": current_user.id},
        {"_id": 0, "voucher_code": 1, "voucher_pin": 1, "denomination": 1,
         "sku_label": 1, "status": 1, "created_at": 1, "mock": 1, "id": 1},
    ).sort("created_at", -1).to_list(50)

    return {"orders": orders, "total": len(orders)}


# ── Health / Status ───────────────────────────────────────────────────────────

@reloadly_router.get("/status")
async def get_status():
    """Integration health check — no auth required."""
    balance = await reloadly.get_balance()
    return {
        "enabled":     RELOADLY_ENABLED,
        "environment": RELOADLY_ENV if RELOADLY_ENABLED else "mock",
        "balance":     balance,
        "catalog_cached": reloadly._catalog_cache is not None,
    }
