"""
routes/v2_engagement.py — Notifications, Analytics, Features, Health, Cache routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from server import db, get_current_user, User
from v2_engines import _analytics
from redis_cache import get_cache_stats

router = APIRouter()

# ── Notifications ──────────────────────────────────────────────────────────────

@router.get("/notifications")
async def get_notifications(user: User = Depends(get_current_user)):
    notifs = await db.notifications.find(
        {"user_id": user.id}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"notifications": notifs, "unread": sum(1 for n in notifs if not n.get("read"))}

@router.post("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, user: User = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notif_id, "user_id": user.id},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"ok": True}

@router.post("/notifications/read-all")
async def mark_all_notifications_read(user: User = Depends(get_current_user)):
    result = await db.notifications.update_many(
        {"user_id": user.id, "read": {"$ne": True}},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"ok": True, "updated": result.modified_count}


@router.post("/notifications/trigger-test")
async def trigger_test_notification(user: User = Depends(get_current_user)):
    """Admin-only: immediately fire a test notification to yourself for both campaign types."""
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    now = datetime.now(timezone.utc).isoformat()
    notifs = [
        {
            "id": str(__import__("uuid").uuid4()),
            "user_id": user.id,
            "type": "activation_trigger",
            "title": "Test: Make your first prediction",
            "body": "You're 1 tap away from winning 50 FREE coins. Pick a match — it's FREE!",
            "deep_link": "/match-centre",
            "read": False,
            "created_at": now,
        },
        {
            "id": str(__import__("uuid").uuid4()),
            "user_id": user.id,
            "type": "streak_reminder",
            "title": "🔥 Test: Your 7-day streak breaks in 4h!",
            "body": "Log in and make a prediction to keep your streak alive!",
            "deep_link": "/dashboard",
            "read": False,
            "created_at": now,
        },
    ]
    await db.notifications.insert_many(notifs)
    return {"ok": True, "inserted": len(notifs), "note": "Test notifications injected — open the bell icon to see them"}

# ── Analytics Events ───────────────────────────────────────────────────────────

@router.post("/analytics/event")
async def track_ui_event(request: Request, current_user: User = Depends(get_current_user)):
    try:
        body = await request.json()
    except Exception:
        body = {}
    await _analytics.track(body.get("event", "unknown"), str(current_user.id), body.get("properties", {}))
    return {"ok": True}

@router.post("/analytics/event/anon")
async def track_anon_event(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    await _analytics.track(body.get("event", "unknown"), "anon", body.get("properties", {}))
    return {"ok": True}

@router.get("/analytics/dashboard")
async def analytics_dashboard(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return await _analytics.get_dashboard()

# ── Feature Gates ──────────────────────────────────────────────────────────────

@router.get("/features/gated")
async def get_gated_features(user: User = Depends(get_current_user)):
    return {
        "features": {
            "card_games": True,
            "fantasy_builder": True,
            "sponsored_pools": True,
            "free_bucks_purchase": True,
        }
    }

@router.get("/features/check/{feature}")
async def check_feature_access(feature: str, user: User = Depends(get_current_user)):
    return {"feature": feature, "has_access": True, "user_id": user.id}

@router.post("/features/use")
async def use_feature(request: Request, user: User = Depends(get_current_user)):
    try:
        body = await request.json()
    except Exception:
        body = {}
    feature = body.get("feature", "unknown")
    return {"feature": feature, "used": True, "user_id": user.id}

# ── Cache Stats & Health ───────────────────────────────────────────────────────

@router.get("/cache/stats")
async def cache_stats(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return get_cache_stats()

@router.get("/health")
async def health_check():
    from redis_cache import get_redis
    redis_ok = False
    try:
        r = get_redis()
        if r:
            redis_ok = r.ping()
    except Exception:
        pass
    return {
        "status": "ok", "redis": redis_ok, "version": "2.0.0",
        "env": __import__("os").environ.get("FREE11_ENV", "unknown"),
    }
