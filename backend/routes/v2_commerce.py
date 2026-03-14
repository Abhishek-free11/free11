"""
routes/v2_commerce.py — Commerce routes: Shop Redeem, Vouchers, Ledger, FreeBucks, Router, Wishlist, Push
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import time

from server import db, get_current_user, User
from v2_engines import ledger, voucher_provider, xoxoday

router = APIRouter()

ROUTER_SETTLE_LIMIT = 5  # max router settlements per user per minute

# ── Request Models ─────────────────────────────────────────────────────────────

class RedeemReq(BaseModel):
    product_id: str

class RedeemVoucherReq(BaseModel):
    product_id: str
    denomination: int
    mobile: str = ""

class PinWishlistReq(BaseModel):
    product_id: str

class PushRegisterReq(BaseModel):
    device_token: str
    device_type: str = "android"

class PushSendReq(BaseModel):
    title: str
    body: str
    user_id: Optional[str] = None
    deep_link: Optional[str] = None
    topic: Optional[str] = None

class RouterSettleReq(BaseModel):
    sku: str
    geo_state: Optional[str] = None
    delivery_address: Optional[str] = None

# ── Ledger ─────────────────────────────────────────────────────────────────────

@router.get("/ledger/balance")
async def get_ledger_balance(user: User = Depends(get_current_user)):
    balance = await ledger.get_balance(user.id)
    return {"balance": balance, "user_id": user.id}

@router.get("/ledger/history")
async def get_ledger_history(
    limit: int = Query(50, le=200), offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
):
    entries = await ledger.get_history(user.id, limit, offset)
    balance = await ledger.get_balance(user.id)
    return {"entries": entries, "balance": balance, "count": len(entries)}

@router.post("/ledger/reconcile")
async def reconcile_ledger(user: User = Depends(get_current_user)):
    return await ledger.reconcile(user.id)

# ── Mock Voucher Redeem ────────────────────────────────────────────────────────

@router.post("/redeem")
async def redeem_product(req: RedeemReq, user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": req.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(404, "Product not found")
    if product.get("stock", 0) <= 0:
        raise HTTPException(400, "Out of stock")
    try:
        await ledger.debit(user.id, product["coin_price"], "redemption",
                           req.product_id, f"Redeemed: {product['name']}")
    except ValueError as e:
        raise HTTPException(400, str(e))
    await db.products.update_one({"id": req.product_id}, {"$inc": {"stock": -1}})
    voucher = await voucher_provider.create_voucher(user.id, req.product_id, product["coin_price"])
    return {"success": True, "voucher": voucher, "product_name": product["name"], "coins_spent": product["coin_price"]}

@router.get("/redeem/status/{voucher_id}")
async def get_voucher_status(voucher_id: str, user: User = Depends(get_current_user)):
    status = await voucher_provider.check_status(voucher_id)
    if "error" in status:
        raise HTTPException(404, "Voucher not found")
    return status

@router.get("/redeem/my")
async def get_my_vouchers(user: User = Depends(get_current_user)):
    return await db.vouchers.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(100)

# ── Xoxoday Vouchers ───────────────────────────────────────────────────────────

@router.get("/vouchers/catalog")
async def voucher_catalog(category: str = ""):
    return await xoxoday.get_catalog(category)

@router.get("/vouchers/status")
async def voucher_status():
    from xoxoday_provider import XoxodayProvider
    return {"provider": "xoxoday" if XoxodayProvider.is_enabled() else "mock", "enabled": XoxodayProvider.is_enabled()}

@router.post("/vouchers/redeem")
async def redeem_voucher(req: RedeemVoucherReq, user: User = Depends(get_current_user)):
    user_data = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1, "email": 1, "mobile": 1})
    coin_cost = req.denomination * 100
    if user_data.get("coins_balance", 0) < coin_cost:
        raise HTTPException(400, f"Need {coin_cost} Free Coins. You have {user_data.get('coins_balance', 0)}.")
    await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": -coin_cost}})
    await db.coin_transactions.insert_one({
        "user_id": user.id, "amount": -coin_cost, "type": "voucher_redeem",
        "description": f"Redeemed ₹{req.denomination} voucher ({req.product_id})",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    email = user_data.get("email", "")
    mobile = req.mobile or user_data.get("mobile", "")
    result = await xoxoday.place_order(user.id, req.product_id, req.denomination, email, mobile)
    if result.get("status") == "failed":
        await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": coin_cost}})
        await db.coin_transactions.insert_one({
            "user_id": user.id, "amount": coin_cost, "type": "voucher_refund",
            "description": "Refund: voucher order failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        raise HTTPException(500, "Voucher order failed. Coins refunded.")
    return {
        "status": result["status"], "voucher_code": result.get("voucher_code", ""),
        "delivery": result.get("delivery", ""), "coins_spent": coin_cost,
        "new_balance": user_data.get("coins_balance", 0) - coin_cost,
    }

# ── FreeBucks & Payments ───────────────────────────────────────────────────────

@router.get("/freebucks/balance")
async def get_freebucks_balance(user: User = Depends(get_current_user)):
    u = await db.users.find_one({"id": user.id}, {"_id": 0, "free_bucks": 1})
    return {"free_bucks": (u or {}).get("free_bucks", 0), "user_id": user.id}

@router.get("/freebucks/history")
async def get_freebucks_history(user: User = Depends(get_current_user)):
    txns = await db.freebucks_purchases.find(
        {"user_id": user.id, "payment_status": "paid"}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"transactions": txns}

@router.get("/freebucks/packages")
async def get_freebucks_packages():
    return {"packages": [
        {"id": "starter",  "label": "Starter Pack",  "price_inr": 49,   "free_bucks": 50,   "bonus": 0},
        {"id": "popular",  "label": "Popular Pack",   "price_inr": 149,  "free_bucks": 160,  "bonus": 10},
        {"id": "value",    "label": "Value Pack",     "price_inr": 499,  "free_bucks": 550,  "bonus": 50},
        {"id": "mega",     "label": "Mega Pack",      "price_inr": 999,  "free_bucks": 1200, "bonus": 200},
    ]}

@router.get("/payments/history")
async def get_payment_history(user: User = Depends(get_current_user)):
    txns = await db.freebucks_purchases.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"transactions": txns}

# ── Wishlist ───────────────────────────────────────────────────────────────────

@router.post("/wishlist/pin")
async def pin_wishlist(req: PinWishlistReq, user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": req.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(404, "Product not found")
    await db.user_wishlist.update_one(
        {"user_id": user.id},
        {"$set": {"user_id": user.id, "product_id": req.product_id, "pinned_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"pinned": True, "product_id": req.product_id}

@router.delete("/wishlist/unpin")
async def unpin_wishlist(user: User = Depends(get_current_user)):
    await db.user_wishlist.delete_one({"user_id": user.id})
    return {"unpinned": True}

@router.get("/wishlist")
async def get_wishlist(user: User = Depends(get_current_user)):
    doc = await db.user_wishlist.find_one({"user_id": user.id}, {"_id": 0})
    if not doc:
        return {"pinned": False, "product": None}
    product = await db.products.find_one({"id": doc["product_id"]}, {"_id": 0})
    if not product:
        await db.user_wishlist.delete_one({"user_id": user.id})
        return {"pinned": False, "product": None}
    u_data = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
    coins_balance = (u_data or {}).get("coins_balance", 0)
    coin_price = product.get("coin_price", 0)
    progress = round(min(100, (coins_balance / coin_price) * 100), 1) if coin_price > 0 else 100
    return {
        "pinned": True, "product": product, "progress": progress,
        "coins_needed": max(0, coin_price - coins_balance),
        "coins_balance": coins_balance, "pinned_at": doc["pinned_at"],
    }

# ── Push Notifications ─────────────────────────────────────────────────────────

def _get_fcm():
    from server import fcm as _fcm
    return _fcm

@router.post("/push/register")
async def register_device_v2(req: PushRegisterReq, user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    await db.user_devices.update_one(
        {"user_id": user.id, "device_type": req.device_type},
        {"$set": {"device_token": req.device_token, "device_type": req.device_type,
                  "updated_at": now, "active": True},
         "$setOnInsert": {"user_id": user.id, "created_at": now}},
        upsert=True,
    )
    await _get_fcm().register_token(user.id, req.device_token, req.device_type)
    return {"registered": True, "device_type": req.device_type}

@router.post("/push/send")
async def send_push_notification(req: PushSendReq, user: User = Depends(get_current_user)):
    target = req.user_id or user.id
    data = {"deep_link": req.deep_link} if req.deep_link else {}
    sent = await _get_fcm().send_push(target, req.title, req.body, data)
    return {"sent": sent, "target_user_id": target}

# ── Smart Commerce Router ──────────────────────────────────────────────────────

@router.get("/router/skus")
async def router_skus(geo_state: str = "", category: str = ""):
    from router_service import get_aggregated_skus
    skus = get_aggregated_skus(geo_state=geo_state, category=category)
    return {"skus": skus, "count": len(skus)}

@router.get("/router/tease")
async def router_tease(sku: str, geo_state: str = ""):
    from router_service import get_router_tease
    result = get_router_tease(sku, geo_state)
    if not result:
        raise HTTPException(404, f"SKU '{sku}' not found.")
    return result

@router.post("/router/settle")
async def router_settle(req: RouterSettleReq, user: User = Depends(get_current_user)):
    from redis_cache import get_redis
    from router_service import get_best_provider

    # Per-user rate limit (5 settles/min)
    r = get_redis()
    if r:
        rl_key = f"rl:router_settle:{user.id}:{int(time.time() // 60)}"
        count = r.incr(rl_key)
        if count == 1:
            r.expire(rl_key, 60)
        if count > ROUTER_SETTLE_LIMIT:
            raise HTTPException(429, "Too many redemptions — try again in a minute.")

    best = get_best_provider(req.sku, req.geo_state)
    if not best:
        raise HTTPException(404, f"SKU '{req.sku}' not available from any provider.")

    provider, _ = best
    authoritative_price = provider.get_price(req.sku)
    if authoritative_price <= 0:
        raise HTTPException(400, "Invalid coin price for SKU.")

    # Atomic coin deduction
    updated = await db.users.find_one_and_update(
        {"id": user.id, "coins_balance": {"$gte": authoritative_price}},
        {"$inc": {"coins_balance": -authoritative_price, "total_redeemed": authoritative_price}},
        return_document=True,
        projection={"_id": 0, "coins_balance": 1},
    )
    if not updated:
        doc = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
        have = doc.get("coins_balance", 0) if doc else 0
        raise HTTPException(402, f"Insufficient coins. Need {authoritative_price}, have {have}.")

    new_balance = updated["coins_balance"]

    # Ledger + order log
    try:
        import uuid as _uuid
        from datetime import datetime as _dt, timezone as _tz
        now = _dt.now(_tz.utc).isoformat()
        await db.ledger.insert_one({
            "id": str(_uuid.uuid4()), "user_id": user.id, "type": "router_redemption",
            "reference_id": req.sku, "credit": 0, "debit": authoritative_price,
            "description": f"Smart Router: {req.sku} via {provider.name}",
            "balance_after": new_balance, "timestamp": now,
        })
        from router_service import settle_router_order
        order = await settle_router_order(user.id, req.sku, provider, req.delivery_address or "")
        await db.router_orders.insert_one({
            "id": str(_uuid.uuid4()), "user_id": user.id, "sku": req.sku,
            "provider": provider.name, "coins_spent": authoritative_price,
            "status": order.get("status", "processing"),
            "partner_label": order.get("partner_label", ""),
            "created_at": now,
        })
    except Exception:
        pass

    return {
        "status": "processing", "sku": req.sku, "provider": provider.name,
        "coins_spent": authoritative_price, "new_balance": new_balance,
        "message": "Order placed! Your reward is on its way.",
    }
