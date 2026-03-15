"""
FREE11 — Admin Analytics 360° Dashboard Backend
Comprehensive analytics endpoint for all real user data.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from datetime import datetime, timezone, timedelta
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

analytics_360_router = APIRouter(prefix="/api/admin/analytics-360", tags=["Analytics 360"])

# ── Injected at startup from server.py ─────────────────────────────────────
_db = None

def init_analytics_360(db):
    global _db
    _db = db

# ── Real-user filter — excludes all test/seed/admin accounts ───────────────
EXCLUDED_EMAIL_PATTERN = re.compile(
    r"test\.com$|free11test\.com$|^flood_|^lb_seed_|^otp_fix_test_|^prodtest|^adult_test|^test_",
    re.IGNORECASE,
)

REAL_USER_MONGO_FILTER = {
    "is_admin": {"$ne": True},
    "is_seed": {"$ne": True},
    "email": {
        "$not": re.compile(
            r"test\.com$|free11test\.com$|^flood_|^lb_seed_|^otp_fix_test_|^prodtest|^adult_test|^test_",
            re.IGNORECASE,
        )
    },
}


def _is_real_user(email: str) -> bool:
    if not email:
        return False
    return not EXCLUDED_EMAIL_PATTERN.search(email)


async def _require_admin(token: str, db):
    """Validate admin token."""
    from jose import jwt, JWTError
    import os
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "is_admin": 1})
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


# ── Helpers ─────────────────────────────────────────────────────────────────

def _safe_pct(num, denom) -> float:
    return round(num / denom * 100, 1) if denom else 0.0


def _days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


@analytics_360_router.get("")
async def get_analytics_360(authorization: Optional[str] = Header(None)):
    """
    Full 360° analytics dashboard.
    Requires admin JWT via Authorization header.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.replace("Bearer ", "").replace("bearer ", "").strip()
    await _require_admin(token, _db)
    if _db is None:
        raise HTTPException(500, "Analytics DB not initialized")

    # ── Gather all real users ────────────────────────────────────────────────
    all_users = await _db.users.find({}, {"_id": 0}).to_list(10000)
    real_users = [u for u in all_users if not u.get("is_admin") and not u.get("is_seed")
                  and _is_real_user(u.get("email", ""))]
    test_count = len(all_users) - len(real_users)
    real_ids = [u["id"] for u in real_users if u.get("id")]

    now = datetime.now(timezone.utc)

    # ── Parallel bulk queries ────────────────────────────────────────────────
    # Predictions
    all_preds = await _db.predictions.find(
        {"user_id": {"$in": real_ids}}, {"_id": 0}
    ).to_list(100000)
    # Coin transactions
    all_txns = await _db.coin_transactions.find(
        {"user_id": {"$in": real_ids}}, {"_id": 0}
    ).to_list(100000)
    # Redemptions
    all_redemptions = await _db.redemptions.find(
        {"user_id": {"$in": real_ids}}, {"_id": 0}
    ).to_list(10000)
    # Payments
    all_payments = await _db.freebucks_purchases.find(
        {"user_id": {"$in": real_ids}}, {"_id": 0}
    ).to_list(10000)
    # Login events
    all_logins = await _db.login_events.find(
        {"user_id": {"$in": real_ids}}, {"_id": 0}
    ).to_list(100000)
    # Analytics events
    all_events = await _db.analytics_events.find(
        {"user_id": {"$in": real_ids + ["anon"]}}, {"_id": 0}
    ).sort("timestamp", -1).to_list(50000)
    # Quest sessions
    all_quests = await _db.quest_sessions.find(
        {"user_id": {"$in": real_ids}}, {"_id": 0}
    ).to_list(10000)
    # Router orders
    all_router = await _db.router_orders.find(
        {"user_id": {"$in": real_ids}}, {"_id": 0}
    ).to_list(10000)
    # Referral bindings
    all_referrals = await _db.referral_bindings.find({}, {"_id": 0}).to_list(10000)

    # ── Index by user_id for fast lookup ────────────────────────────────────
    preds_by_user: dict = {}
    for p in all_preds:
        uid = p.get("user_id", "")
        preds_by_user.setdefault(uid, []).append(p)

    txns_by_user: dict = {}
    for t in all_txns:
        uid = t.get("user_id", "")
        txns_by_user.setdefault(uid, []).append(t)

    redemp_by_user: dict = {}
    for r in all_redemptions:
        uid = r.get("user_id", "")
        redemp_by_user.setdefault(uid, []).append(r)

    payments_by_user: dict = {}
    for p in all_payments:
        uid = p.get("user_id", "")
        payments_by_user.setdefault(uid, []).append(p)

    logins_by_user: dict = {}
    for l in all_logins:
        uid = l.get("user_id", "")
        logins_by_user.setdefault(uid, []).append(l)

    events_by_user: dict = {}
    for e in all_events:
        uid = e.get("user_id", "")
        events_by_user.setdefault(uid, []).append(e)

    quests_by_user: dict = {}
    for q in all_quests:
        uid = q.get("user_id", "")
        quests_by_user.setdefault(uid, []).append(q)

    router_by_user: dict = {}
    for ro in all_router:
        uid = ro.get("user_id", "")
        router_by_user.setdefault(uid, []).append(ro)

    # ── High-level summary ───────────────────────────────────────────────────
    total_coins = sum(u.get("coins_balance", 0) for u in all_users)
    real_coins = sum(u.get("coins_balance", 0) for u in real_users)
    admin_coins = total_coins - real_coins

    total_revenue = sum(
        p.get("amount", 0) for p in all_payments if p.get("payment_status") == "paid"
    )

    activated_users = sum(
        1 for uid in real_ids
        if preds_by_user.get(uid) or redemp_by_user.get(uid) or payments_by_user.get(uid)
    )

    seven_days_ago = _days_ago(7)
    active_7d = sum(
        1 for u in real_users
        if (u.get("last_activity") or u.get("last_checkin") or "") >= seven_days_ago
    )

    high_level = {
        "total_registered": len(all_users),
        "real_users_count": len(real_users),
        "test_seed_admin_count": test_count,
        "active_7d": active_7d,
        "activation_rate_pct": _safe_pct(activated_users, len(real_users)),
        "total_predictions": len(all_preds),
        "total_redemptions": len(all_redemptions),
        "total_revenue_inr": total_revenue,
        "coins_in_circulation": total_coins,
        "real_user_coins": real_coins,
        "admin_seed_coins": admin_coins,
        "real_coins_pct": _safe_pct(real_coins, total_coins),
        "paying_users": len(set(
            p["user_id"] for p in all_payments if p.get("payment_status") == "paid"
        )),
        "users_with_predictions": len(preds_by_user),
        "users_with_redemptions": len(redemp_by_user),
    }

    # ── Per-user 360° profiles ───────────────────────────────────────────────
    user_profiles = []
    for u in real_users:
        uid = u.get("id", "")
        user_preds = preds_by_user.get(uid, [])
        user_txns = txns_by_user.get(uid, [])
        user_redemps = redemp_by_user.get(uid, [])
        user_pays = payments_by_user.get(uid, [])
        user_logins = logins_by_user.get(uid, [])
        user_evts = events_by_user.get(uid, [])
        user_quests = quests_by_user.get(uid, [])
        user_routers = router_by_user.get(uid, [])

        coins_earned = sum(t["amount"] for t in user_txns if t.get("amount", 0) > 0)
        coins_spent = abs(sum(t["amount"] for t in user_txns if t.get("amount", 0) < 0))
        revenue = sum(p.get("amount", 0) for p in user_pays if p.get("payment_status") == "paid")

        # Detect first action after registration
        first_action = None
        first_action_time = None
        reg_time = u.get("created_at", "")
        all_uid_actions = sorted(
            [{"ts": e.get("timestamp", ""), "type": e.get("event", "")} for e in user_evts
             if e.get("timestamp", "") > reg_time],
            key=lambda x: x["ts"]
        )
        if all_uid_actions:
            first_action = all_uid_actions[0]["type"]
            first_action_time = all_uid_actions[0]["ts"]

        # Device / platform from most recent login
        last_login_ua = ""
        if user_logins:
            sorted_logins = sorted(user_logins, key=lambda x: x.get("timestamp", ""), reverse=True)
            last_login_ua = sorted_logins[0].get("user_agent", "") or sorted_logins[0].get("ua", "")

        correct_preds = sum(1 for p in user_preds if p.get("is_correct"))
        accuracy = _safe_pct(correct_preds, len(user_preds)) if user_preds else 0

        # Session estimation from login events
        login_timestamps = sorted(
            [l.get("timestamp", "") for l in user_logins if l.get("timestamp")],
            reverse=True
        )

        quests_offered = len(user_quests)
        quests_completed = sum(1 for q in user_quests if q.get("status") == "completed")

        profile = {
            "user_id": uid,
            "email": u.get("email", ""),
            "phone": u.get("phone", ""),
            "name": u.get("name", ""),
            "registration_timestamp": u.get("created_at", ""),
            "last_active": u.get("last_activity", u.get("last_checkin", "")),
            "last_login_timestamps": login_timestamps[:5],
            "login_count": len(user_logins),
            "platform_ua": last_login_ua[:200] if last_login_ua else "Data not available",
            "referral_code": u.get("referral_code", ""),
            "referred_by": u.get("referred_by", ""),
            "predictions_count": len(user_preds),
            "predictions_correct": correct_preds,
            "prediction_accuracy_pct": accuracy,
            "prediction_list": [
                {"match_id": p.get("match_id"), "choice": p.get("choice"),
                 "is_correct": p.get("is_correct"), "ts": p.get("created_at", p.get("timestamp", ""))}
                for p in sorted(user_preds, key=lambda x: x.get("created_at", x.get("timestamp", "")), reverse=True)[:10]
            ],
            "coins_balance": u.get("coins_balance", 0),
            "coins_earned_total": coins_earned,
            "coins_spent_total": coins_spent,
            "coins_history": [
                {"amount": t.get("amount"), "type": t.get("type"), "desc": t.get("description", ""),
                 "ts": t.get("timestamp", "")}
                for t in sorted(user_txns, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
            ],
            "redemptions_count": len(user_redemps),
            "redemptions_list": [
                {"product": r.get("product_name"), "coins": r.get("coins_spent"),
                 "status": r.get("status"), "ts": r.get("order_date", "")}
                for r in sorted(user_redemps, key=lambda x: x.get("order_date", ""), reverse=True)[:10]
            ],
            "payments_count": len(user_pays),
            "revenue_contributed_inr": revenue,
            "payment_list": [
                {"package": p.get("package_id"), "amount": p.get("amount"),
                 "bucks": p.get("bucks"), "status": p.get("payment_status"),
                 "ts": p.get("created_at", "")}
                for p in sorted(user_pays, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
            ],
            "quests_offered": quests_offered,
            "quests_completed": quests_completed,
            "router_orders_count": len(user_routers),
            "router_orders_list": [
                {"sku": ro.get("sku"), "coins": ro.get("coins_used"),
                 "status": ro.get("status"), "ts": ro.get("created_at", "")}
                for ro in sorted(user_routers, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
            ],
            "streak_days": u.get("streak_days", 0),
            "level": u.get("level", 1),
            "xp": u.get("xp", 0),
            "total_events": len(user_evts),
            "first_action_after_reg": first_action,
            "first_action_time": first_action_time,
            "event_types": list(set(e.get("event", "") for e in user_evts)),
            "free_bucks": u.get("free_bucks", 0),
        }
        user_profiles.append(profile)

    # Sort by last_active descending
    user_profiles.sort(key=lambda x: x.get("last_active") or "", reverse=True)

    # ── Funnel analysis ──────────────────────────────────────────────────────
    n_real = len(real_users)
    n_verified = sum(1 for u in real_users if u.get("email_verified"))
    n_first_action = len([u for u in real_users if (u.get("id") or "") in events_by_user])
    n_first_pred = len([uid for uid in real_ids if preds_by_user.get(uid)])
    n_first_redemp = len([uid for uid in real_ids if redemp_by_user.get(uid)])
    n_paying = len([uid for uid in real_ids if payments_by_user.get(uid)])

    funnel = [
        {"stage": "Registered", "count": n_real, "pct": 100.0, "drop_pct": 0},
        {"stage": "Email Verified", "count": n_verified, "pct": _safe_pct(n_verified, n_real),
         "drop_pct": _safe_pct(n_real - n_verified, n_real)},
        {"stage": "First Action (any event)", "count": n_first_action, "pct": _safe_pct(n_first_action, n_real),
         "drop_pct": _safe_pct(n_verified - n_first_action, n_real)},
        {"stage": "First Prediction", "count": n_first_pred, "pct": _safe_pct(n_first_pred, n_real),
         "drop_pct": _safe_pct(n_first_action - n_first_pred, n_real)},
        {"stage": "First Redemption", "count": n_first_redemp, "pct": _safe_pct(n_first_redemp, n_real),
         "drop_pct": _safe_pct(n_first_pred - n_first_redemp, n_real)},
        {"stage": "Paying User", "count": n_paying, "pct": _safe_pct(n_paying, n_real),
         "drop_pct": _safe_pct(n_first_redemp - n_paying, n_real)},
    ]

    # ── Top events / actions ─────────────────────────────────────────────────
    event_counts: dict = {}
    for e in all_events:
        ename = e.get("event", "unknown")
        event_counts[ename] = event_counts.get(ename, 0) + 1
    top_actions = sorted(
        [{"event": k, "count": v} for k, v in event_counts.items()],
        key=lambda x: x["count"], reverse=True
    )[:20]

    # ── DAU (7-day) ──────────────────────────────────────────────────────────
    dau_7d = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        count = sum(
            1 for e in all_events
            if e.get("event") == "login" and e.get("timestamp", "").startswith(day)
            and e.get("user_id") in set(real_ids)
        )
        dau_7d.append({"date": day, "dau": count})

    # ── Monetization ────────────────────────────────────────────────────────
    rev_by_user = sorted(
        [{"user_id": uid, "email": next((u["email"] for u in real_users if u["id"] == uid), uid),
          "revenue_inr": sum(p.get("amount", 0) for p in pays if p.get("payment_status") == "paid"),
          "purchases": len(pays)}
         for uid, pays in payments_by_user.items() if uid in set(real_ids)],
        key=lambda x: x["revenue_inr"], reverse=True
    )

    # Coins economy breakdown
    earn_by_source: dict = {}
    for t in all_txns:
        if t.get("amount", 0) > 0:
            src = t.get("source", t.get("type", "unknown"))
            earn_by_source[src] = earn_by_source.get(src, 0) + t.get("amount", 0)

    # ── Referral funnel ──────────────────────────────────────────────────────
    referrers = {}
    for rb in all_referrals:
        referrer = rb.get("referrer_id", "")
        referrers[referrer] = referrers.get(referrer, 0) + 1
    top_referrers = sorted(
        [{"user_id": k, "referrals": v} for k, v in referrers.items()],
        key=lambda x: x["referrals"], reverse=True
    )[:10]

    return {
        "generated_at": now.isoformat(),
        "high_level": high_level,
        "real_users_360": user_profiles,
        "funnel": funnel,
        "dau_7d": dau_7d,
        "top_actions": top_actions,
        "monetization": {
            "revenue_by_user": rev_by_user[:20],
            "total_revenue_inr": total_revenue,
            "coins_earned_by_source": earn_by_source,
            "top_referrers": top_referrers,
        },
        "tracking_gaps": {
            "users_with_no_events": len(real_users) - len([u for u in real_users if u.get("id") in events_by_user]),
            "users_with_no_logins_tracked": len(real_users) - len([u for u in real_users if u.get("id") in logins_by_user]),
            "note": "Tracking gaps indicate pre-tracking registrations or users who haven't returned since tracking was enabled.",
        },
    }


@analytics_360_router.get("/export/csv")
async def export_users_csv(authorization: Optional[str] = Header(None)):
    """Export real users 360° data as CSV. Requires admin JWT."""
    from fastapi.responses import StreamingResponse
    import csv, io

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.replace("Bearer ", "").replace("bearer ", "").strip()
    await _require_admin(token, _db)

    if _db is None:
        raise HTTPException(500, "Analytics DB not initialized")

    all_users = await _db.users.find({}, {"_id": 0}).to_list(10000)
    real_users = [u for u in all_users if not u.get("is_admin") and not u.get("is_seed")
                  and _is_real_user(u.get("email", ""))]
    real_ids = [u["id"] for u in real_users if u.get("id")]

    preds = await _db.predictions.find({"user_id": {"$in": real_ids}}, {"_id": 0}).to_list(100000)
    redemps = await _db.redemptions.find({"user_id": {"$in": real_ids}}, {"_id": 0}).to_list(10000)
    pays = await _db.freebucks_purchases.find({"user_id": {"$in": real_ids}}, {"_id": 0}).to_list(10000)

    preds_count = {}
    for p in preds:
        preds_count[p.get("user_id", "")] = preds_count.get(p.get("user_id", ""), 0) + 1
    redemps_count = {}
    for r in redemps:
        redemps_count[r.get("user_id", "")] = redemps_count.get(r.get("user_id", ""), 0) + 1
    revenue_map = {}
    for p in pays:
        if p.get("payment_status") == "paid":
            uid = p.get("user_id", "")
            revenue_map[uid] = revenue_map.get(uid, 0) + p.get("amount", 0)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "user_id", "email", "phone", "name", "registration_timestamp",
        "last_active", "streak_days", "level", "xp", "coins_balance",
        "predictions_count", "redemptions_count", "revenue_inr",
        "referred_by", "referral_code",
    ])
    writer.writeheader()
    for u in real_users:
        uid = u.get("id", "")
        writer.writerow({
            "user_id": uid,
            "email": u.get("email", ""),
            "phone": u.get("phone", ""),
            "name": u.get("name", ""),
            "registration_timestamp": u.get("created_at", ""),
            "last_active": u.get("last_activity", ""),
            "streak_days": u.get("streak_days", 0),
            "level": u.get("level", 1),
            "xp": u.get("xp", 0),
            "coins_balance": u.get("coins_balance", 0),
            "predictions_count": preds_count.get(uid, 0),
            "redemptions_count": redemps_count.get(uid, 0),
            "revenue_inr": revenue_map.get(uid, 0),
            "referred_by": u.get("referred_by", ""),
            "referral_code": u.get("referral_code", ""),
        })

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=free11_users_360.csv"},
    )
