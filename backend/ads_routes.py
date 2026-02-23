"""
Ad Reward Routes for FREE11
Watch ads to earn coins (AdMob integration backend)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid

# Import from server.py
from server import db, get_current_user, add_coins, User, Activity

ads_router = APIRouter(prefix="/ads", tags=["Ads"])

# ==================== CONFIG ====================

# Ad reward configuration
AD_REWARD_COINS = 50  # Coins per ad watched
MAX_ADS_PER_DAY = 5   # Maximum ads user can watch per day

# ==================== MODELS ====================

class AdWatch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    ad_type: str = "rewarded"  # rewarded, interstitial
    ad_unit_id: Optional[str] = None
    coins_earned: int = AD_REWARD_COINS
    watched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AdWatchRequest(BaseModel):
    ad_type: str = "rewarded"
    ad_unit_id: Optional[str] = None  # For tracking which ad was shown

# ==================== ROUTES ====================

@ads_router.get("/config")
async def get_ad_config():
    """Get ad configuration for the frontend"""
    return {
        "enabled": True,
        "reward_coins": AD_REWARD_COINS,
        "max_per_day": MAX_ADS_PER_DAY,
        "ad_units": {
            "rewarded": {
                # Test Ad Unit IDs - Replace with real ones before production
                "android": "ca-app-pub-3940256099942544/5224354917",  # Google test
                "ios": "ca-app-pub-3940256099942544/1712485313",       # Google test
                "web": "test-rewarded-ad"  # For web preview
            }
        }
    }

@ads_router.get("/status")
async def get_ad_status(current_user: User = Depends(get_current_user)):
    """Check how many ads user can still watch today"""
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Count today's ad watches
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    ads_watched_today = await db.ad_watches.count_documents({
        "user_id": current_user.id,
        "watched_at": {"$gte": today_start.isoformat()}
    })
    
    # Get last watch time
    last_watch = await db.ad_watches.find_one(
        {"user_id": current_user.id},
        {"_id": 0},
        sort=[("watched_at", -1)]
    )
    
    return {
        "ads_watched_today": ads_watched_today,
        "ads_remaining": max(0, MAX_ADS_PER_DAY - ads_watched_today),
        "max_per_day": MAX_ADS_PER_DAY,
        "reward_per_ad": AD_REWARD_COINS,
        "can_watch": ads_watched_today < MAX_ADS_PER_DAY,
        "last_watch": last_watch.get("watched_at") if last_watch else None,
        "potential_earnings": max(0, MAX_ADS_PER_DAY - ads_watched_today) * AD_REWARD_COINS
    }

@ads_router.post("/reward")
async def record_ad_reward(
    ad_data: AdWatchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Record that user watched an ad and reward them
    Called by frontend after ad completion verification
    """
    # Check daily limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    ads_watched_today = await db.ad_watches.count_documents({
        "user_id": current_user.id,
        "watched_at": {"$gte": today_start.isoformat()}
    })
    
    if ads_watched_today >= MAX_ADS_PER_DAY:
        raise HTTPException(
            status_code=400,
            detail=f"Daily ad limit reached ({MAX_ADS_PER_DAY}/day). Come back tomorrow!"
        )
    
    # Cooldown check (prevent rapid-fire abuse) - 30 second minimum between ads
    last_watch = await db.ad_watches.find_one(
        {"user_id": current_user.id},
        {"_id": 0},
        sort=[("watched_at", -1)]
    )
    
    if last_watch:
        last_time = datetime.fromisoformat(last_watch["watched_at"].replace('Z', '+00:00'))
        cooldown = timedelta(seconds=30)
        if datetime.now(timezone.utc) - last_time < cooldown:
            remaining = (last_time + cooldown - datetime.now(timezone.utc)).seconds
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {remaining} seconds before watching another ad"
            )
    
    # Record ad watch
    ad_watch = AdWatch(
        user_id=current_user.id,
        ad_type=ad_data.ad_type,
        ad_unit_id=ad_data.ad_unit_id
    )
    await db.ad_watches.insert_one(ad_watch.model_dump())
    
    # Award coins
    await add_coins(
        current_user.id,
        AD_REWARD_COINS,
        "earned",
        f"Watched ad ({ads_watched_today + 1}/{MAX_ADS_PER_DAY} today)"
    )
    
    # Record activity
    activity = Activity(
        user_id=current_user.id,
        activity_type="watch_ad",
        coins_earned=AD_REWARD_COINS,
        details={
            "ad_type": ad_data.ad_type,
            "daily_count": ads_watched_today + 1
        }
    )
    await db.activities.insert_one(activity.model_dump())
    
    return {
        "message": f"Reward claimed! +{AD_REWARD_COINS} coins",
        "coins_earned": AD_REWARD_COINS,
        "new_balance": current_user.coins_balance + AD_REWARD_COINS,
        "ads_watched_today": ads_watched_today + 1,
        "ads_remaining": MAX_ADS_PER_DAY - ads_watched_today - 1
    }

@ads_router.get("/history")
async def get_ad_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get user's ad watch history"""
    history = await db.ad_watches.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("watched_at", -1).limit(limit).to_list(limit)
    
    # Calculate totals
    total_ads = await db.ad_watches.count_documents({"user_id": current_user.id})
    total_earned = total_ads * AD_REWARD_COINS
    
    return {
        "history": history,
        "total_ads_watched": total_ads,
        "total_coins_earned": total_earned
    }

@ads_router.get("/stats")
async def get_ad_stats():
    """Get overall ad stats (public/admin)"""
    total_ads_watched = await db.ad_watches.count_documents({})
    total_coins_awarded = total_ads_watched * AD_REWARD_COINS
    
    # Unique users who watched ads
    unique_users = len(await db.ad_watches.distinct("user_id"))
    
    # Today's stats
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_ads = await db.ad_watches.count_documents({
        "watched_at": {"$gte": today_start.isoformat()}
    })
    
    return {
        "total_ads_watched": total_ads_watched,
        "total_coins_awarded": total_coins_awarded,
        "unique_users": unique_users,
        "today_ads": today_ads,
        "reward_per_ad": AD_REWARD_COINS,
        "max_per_day": MAX_ADS_PER_DAY
    }
