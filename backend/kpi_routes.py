"""
KPI Routes — Platform Analytics & Cohort Data
Provides: opt-in rate, repeat redemptions, pool_lift, household estimates.
Admin-only endpoints.
"""
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from server import db, get_current_user, User

logger = logging.getLogger(__name__)
kpi_router = APIRouter(prefix="/api/v2/kpis", tags=["KPIs"])


@kpi_router.get("")
async def get_platform_kpis(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")

    now = datetime.now(timezone.utc)
    day_30_ago = (now - timedelta(days=30)).isoformat()
    day_7_ago = (now - timedelta(days=7)).isoformat()

    # === USER COUNTS ===
    total_users = await db.users.count_documents({"is_admin": {"$ne": True}})

    # === QUEST OPT-IN ===
    total_quests_offered = await db.quest_sessions.count_documents({})
    quests_engaged = await db.quest_sessions.count_documents(
        {"status": {"$in": ["ad_claimed", "ration_viewed"]}}
    )
    quest_opt_in_rate = round((quests_engaged / total_quests_offered * 100), 1) if total_quests_offered > 0 else 0

    # === REPEAT REDEMPTIONS (30d) ===
    redemption_pipeline = [
        {"$match": {"order_date": {"$gte": day_30_ago}}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 2}}},
        {"$count": "repeat_users"}
    ]
    repeat_result = await db.redemptions.aggregate(redemption_pipeline).to_list(1)
    repeat_users_30d = repeat_result[0]["repeat_users"] if repeat_result else 0
    redeeming_users = await db.redemptions.distinct("user_id", {"order_date": {"$gte": day_30_ago}})
    repeat_rate_30d = round((repeat_users_30d / len(redeeming_users) * 100), 1) if redeeming_users else 0

    # === SPONSORED POOL LIFT ===
    sponsored_joined = await db.sponsored_pools.count_documents({"current_participants": {"$gt": 0}})
    total_sponsored_participants = 0
    pools = await db.sponsored_pools.find({}, {"_id": 0, "current_participants": 1}).to_list(100)
    for p in pools:
        total_sponsored_participants += p.get("current_participants", 0)
    pool_lift_pct = round((total_sponsored_participants / total_users * 100), 1) if total_users > 0 else 0

    # === HOUSEHOLD ESTIMATE (unique redemptions = proxy for households reached) ===
    unique_redeemers = await db.redemptions.distinct("user_id")
    household_estimate = len(unique_redeemers)

    # === GROCERY REDEMPTIONS ===
    grocery_categories = ["groceries", "recharge", "food"]
    grocery_redemptions = await db.redemptions.count_documents({})  # Simplified for now

    # === REVENUE ESTIMATE (AdMob + commission) ===
    total_ad_rewards = await db.ad_events.count_documents({"status": "completed"})
    estimated_admob_revenue_inr = round(total_ad_rewards * 0.35, 2)  # ~₹0.35/ad watch
    total_voucher_coins = 0
    voucher_agg = await db.coin_transactions.aggregate([
        {"$match": {"type": {"$in": ["redemption", "voucher_redeem", "sponsored_prize"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    if voucher_agg:
        total_voucher_coins = abs(voucher_agg[0].get("total", 0))

    # Estimated 8% commission on ₹1/100coins value
    estimated_commission_inr = round(abs(total_voucher_coins) / 100 * 0.08, 2)

    # === 7d ACTIVE ===
    active_7d = await db.users.count_documents({"last_activity": {"$gte": day_7_ago}})

    return {
        "generated_at": now.isoformat(),
        "users": {
            "total": total_users,
            "active_7d": active_7d,
        },
        "quests": {
            "total_offered": total_quests_offered,
            "engaged": quests_engaged,
            "opt_in_rate_pct": quest_opt_in_rate,
        },
        "redemptions": {
            "unique_redeemers": household_estimate,
            "repeat_users_30d": repeat_users_30d,
            "repeat_rate_30d_pct": repeat_rate_30d,
            "household_estimate": household_estimate,
        },
        "sponsored_pools": {
            "active_pools": sponsored_joined,
            "total_participants": total_sponsored_participants,
            "pool_lift_pct": pool_lift_pct,
        },
        "revenue_estimates": {
            "admob_inr": estimated_admob_revenue_inr,
            "commission_inr": estimated_commission_inr,
            "total_inr": round(estimated_admob_revenue_inr + estimated_commission_inr, 2),
            "note": "Estimates based on mock data. Live figures available after payment integration.",
        },
        "disclaimer": "All KPI data based on platform activity. Revenue estimates are indicative.",
    }


@kpi_router.get("/breakage")
async def get_breakage_metrics(user: User = Depends(get_current_user)):
    """Section 3.4 — Coin Liability / Breakage Tracking"""
    if not user.is_admin:
        raise HTTPException(403, "Admin only")

    # Total coins ever issued
    issued_agg = await db.coin_transactions.aggregate([
        {"$match": {"amount": {"$gt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    total_issued = issued_agg[0]["total"] if issued_agg else 0

    # Total coins ever spent (redemptions)
    spent_agg = await db.coin_transactions.aggregate([
        {"$match": {"amount": {"$lt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    total_spent = abs(spent_agg[0]["total"]) if spent_agg else 0

    # Currently live coins in all wallets
    wallet_agg = await db.users.aggregate([
        {"$match": {"is_admin": {"$ne": True}}},
        {"$group": {"_id": None, "total": {"$sum": "$coins_balance"}}}
    ]).to_list(1)
    live_balance = wallet_agg[0]["total"] if wallet_agg else 0

    unredeemed = total_issued - total_spent
    breakage_rate = round((unredeemed / total_issued * 100), 1) if total_issued > 0 else 0

    return {
        "total_coins_issued": total_issued,
        "total_coins_spent": total_spent,
        "live_wallet_balance": live_balance,
        "unredeemed_coins": unredeemed,
        "unredeemed_coin_ratio_pct": breakage_rate,
        "target_breakage_pct": 10.0,
        "status": "healthy" if breakage_rate >= 10 else "low_breakage",
        "note": "Target: >10% breakage (standard loyalty economics). Higher breakage = lower liability.",
    }


@kpi_router.get("/cohort-csv")
async def get_cohort_csv(user: User = Depends(get_current_user)):
    """Returns a simple CSV-friendly cohort summary."""
    if not user.is_admin:
        raise HTTPException(403, "Admin only")

    now = datetime.now(timezone.utc)
    rows = []

    # Last 7 days cohort
    for days_ago in range(7, -1, -1):
        d = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        registrations = await db.users.count_documents({
            "created_at": {"$gte": d, "$lt": (now - timedelta(days=days_ago - 1)).strftime("%Y-%m-%d")}
        })
        redemptions = await db.redemptions.count_documents({
            "order_date": {"$gte": d, "$lt": (now - timedelta(days=days_ago - 1)).strftime("%Y-%m-%d")}
        })
        rows.append({
            "date": d,
            "registrations": registrations,
            "redemptions": redemptions,
            "repeat_pct": 20.0,  # Placeholder sample stat
        })

    return {
        "columns": ["date", "registrations", "redemptions", "repeat_pct"],
        "rows": rows,
        "note": "repeat_pct is sample (20%) per spec. Live cohort requires 30d of production data.",
    }


@kpi_router.get("/router")
async def get_router_kpis(user: User = Depends(get_current_user)):
    """
    Smart Commerce Router KPIs — admin only.
    Returns: order count, provider distribution, avg coin price,
             avg value score, redemption conversion rate.
    """
    if not user.is_admin:
        raise HTTPException(403, "Admin only")

    now = datetime.now(timezone.utc)
    day_30_ago = (now - timedelta(days=30)).isoformat()

    # Total router orders
    total_orders = await db.router_orders.count_documents({})
    orders_30d   = await db.router_orders.count_documents({"created_at": {"$gte": day_30_ago}})

    # Provider distribution
    provider_pipeline = [
        {"$group": {"_id": "$provider", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    prov_raw = await db.router_orders.aggregate(provider_pipeline).to_list(20)
    provider_distribution = []
    for p in prov_raw:
        pct = round(p["count"] / total_orders * 100, 1) if total_orders > 0 else 0
        provider_distribution.append({
            "provider": p["_id"] or "unknown",
            "count": p["count"],
            "pct": pct,
        })

    # Average coin price
    coin_agg = await db.router_orders.aggregate([
        {"$group": {"_id": None, "avg": {"$avg": "$coins_used"}}}
    ]).to_list(1)
    avg_coin_price = round(coin_agg[0]["avg"], 1) if coin_agg else 0

    # Average value score
    vs_agg = await db.router_orders.aggregate([
        {"$match": {"value_score_used": {"$exists": True}}},
        {"$group": {"_id": None, "avg": {"$avg": "$value_score_used"}}}
    ]).to_list(1)
    avg_value_score = round(vs_agg[0]["avg"], 3) if vs_agg else 0

    # Redemption conversion rate: settles / tease views
    tease_views = 0
    try:
        from redis_cache import get_redis
        r = get_redis()
        if r:
            raw = r.get("router:tease:total_views")
            tease_views = int(raw) if raw else 0
        if tease_views == 0:
            # MongoDB fallback
            doc = await db.router_metrics.find_one({"_id": "tease_views"})
            tease_views = doc.get("count", 0) if doc else 0
    except Exception:
        pass

    conversion_rate = round(total_orders / tease_views * 100, 1) if tease_views > 0 else 0

    # Top SKUs
    sku_pipeline = [
        {"$group": {"_id": "$sku", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    top_skus = await db.router_orders.aggregate(sku_pipeline).to_list(5)

    return {
        "generated_at": now.isoformat(),
        "orders": {
            "total": total_orders,
            "last_30d": orders_30d,
        },
        "provider_distribution": provider_distribution,
        "avg_coin_price": avg_coin_price,
        "avg_value_score": avg_value_score,
        "tease_views": tease_views,
        "conversion_rate_pct": conversion_rate,
        "top_skus": [{"sku": s["_id"], "count": s["count"]} for s in top_skus],
        "note": "MOCK data — live values after real provider API integration.",
    }
