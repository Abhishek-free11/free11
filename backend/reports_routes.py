"""
Beta Reporting & Analytics for FREE11
======================================
Weekly beta metrics and reporting endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
import os

# Import db from server
from server import db, get_current_user

reports_router = APIRouter(prefix="/api/admin/reports", tags=["reports"])


class BetaReport(BaseModel):
    """Weekly beta report model"""
    report_date: str
    period_start: str
    period_end: str
    
    # User Metrics
    total_users: int
    new_users_this_period: int
    dau: int  # Daily Active Users (today)
    wau: int  # Weekly Active Users
    
    # Engagement Metrics
    total_predictions: int
    predictions_this_period: int
    prediction_accuracy_avg: float
    
    # Redemption Metrics
    total_redemptions: int
    redemptions_this_period: int
    voucher_failure_rate: float
    avg_delivery_time_minutes: Optional[float]
    
    # Brand Metrics
    brand_funded_redemptions: int
    total_consumption_value: float
    active_campaigns: int
    
    # Support Metrics
    open_tickets: int
    tickets_this_period: int
    top_issues: List[Dict]
    
    # Invite Metrics
    invites_generated: int
    invites_used: int
    remaining_invite_cap: int


async def calculate_dau() -> int:
    """Calculate Daily Active Users (users active in last 24h)"""
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    
    # Users who made predictions, redeemed, or logged in today
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"last_activity": {"$gte": yesterday}},
                    {"last_checkin": {"$gte": yesterday}}
                ]
            }
        },
        {"$count": "count"}
    ]
    
    result = await db.users.aggregate(pipeline).to_list(1)
    return result[0]["count"] if result else 0


async def calculate_wau() -> int:
    """Calculate Weekly Active Users (users active in last 7 days)"""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"last_activity": {"$gte": week_ago}},
                    {"last_checkin": {"$gte": week_ago}}
                ]
            }
        },
        {"$count": "count"}
    ]
    
    result = await db.users.aggregate(pipeline).to_list(1)
    return result[0]["count"] if result else 0


async def calculate_voucher_failure_rate(days: int = 7) -> float:
    """Calculate voucher failure rate over period"""
    period_start = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    total = await db.fulfillments.count_documents({"created_at": {"$gte": period_start}})
    failed = await db.fulfillments.count_documents({
        "created_at": {"$gte": period_start},
        "status": "failed"
    })
    
    if total == 0:
        return 0.0
    
    return round((failed / total) * 100, 2)


async def calculate_avg_delivery_time(days: int = 7) -> Optional[float]:
    """Calculate average delivery time in minutes"""
    period_start = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    pipeline = [
        {
            "$match": {
                "created_at": {"$gte": period_start},
                "status": "delivered",
                "delivered_at": {"$exists": True}
            }
        },
        {
            "$project": {
                "delivery_time": {
                    "$subtract": [
                        {"$dateFromString": {"dateString": "$delivered_at"}},
                        {"$dateFromString": {"dateString": "$created_at"}}
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "avg_time_ms": {"$avg": "$delivery_time"}
            }
        }
    ]
    
    result = await db.fulfillments.aggregate(pipeline).to_list(1)
    
    if result and result[0].get("avg_time_ms"):
        # Convert ms to minutes
        return round(result[0]["avg_time_ms"] / 60000, 2)
    return None


async def get_top_support_issues(days: int = 7, limit: int = 3) -> List[Dict]:
    """Get top support issues by category"""
    period_start = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    pipeline = [
        {"$match": {"created_at": {"$gte": period_start}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"category": "$_id", "count": 1, "_id": 0}}
    ]
    
    result = await db.support_tickets.aggregate(pipeline).to_list(limit)
    return result


@reports_router.get("/beta-report")
async def get_beta_report(days: int = 7, user: dict = Depends(get_current_user)):
    """
    Generate weekly beta report with all key metrics.
    
    Includes:
    - DAU/WAU
    - Redemptions
    - Voucher failure rate
    - Avg delivery time
    - Top support issues
    - Brand-funded redemptions
    """
    now = datetime.now(timezone.utc)
    period_start = (now - timedelta(days=days)).isoformat()
    
    # User metrics
    total_users = await db.users.count_documents({})
    new_users = await db.users.count_documents({"created_at": {"$gte": period_start}})
    dau = await calculate_dau()
    wau = await calculate_wau()
    
    # Prediction metrics
    total_predictions = await db.predictions.count_documents({})
    predictions_period = await db.predictions.count_documents({"created_at": {"$gte": period_start}})
    
    # Calculate avg accuracy
    accuracy_pipeline = [
        {"$match": {"is_correct": {"$exists": True}}},
        {"$group": {"_id": None, "avg": {"$avg": {"$cond": ["$is_correct", 1, 0]}}}}
    ]
    accuracy_result = await db.predictions.aggregate(accuracy_pipeline).to_list(1)
    avg_accuracy = round(accuracy_result[0]["avg"] * 100, 2) if accuracy_result else 0
    
    # Redemption metrics
    total_redemptions = await db.fulfillments.count_documents({})
    redemptions_period = await db.fulfillments.count_documents({"created_at": {"$gte": period_start}})
    failure_rate = await calculate_voucher_failure_rate(days)
    avg_delivery_time = await calculate_avg_delivery_time(days)
    
    # Brand metrics
    brand_funded = await db.fulfillments.count_documents({
        "brand_id": {"$exists": True, "$ne": None},
        "status": "delivered"
    })
    
    # Calculate total consumption value
    consumption_pipeline = [
        {"$match": {"status": "delivered"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    consumption_result = await db.fulfillments.aggregate(consumption_pipeline).to_list(1)
    total_consumption = consumption_result[0]["total"] if consumption_result else 0
    
    active_campaigns = await db.brand_campaigns.count_documents({"is_active": True})
    
    # Support metrics
    open_tickets = await db.support_tickets.count_documents({"status": {"$in": ["open", "in_progress"]}})
    tickets_period = await db.support_tickets.count_documents({"created_at": {"$gte": period_start}})
    top_issues = await get_top_support_issues(days)
    
    # Invite metrics
    invites_generated = await db.beta_invites.count_documents({})
    invites_used = await db.beta_invites.count_documents({"current_uses": {"$gt": 0}})
    
    # Get invite cap from settings
    settings = await db.beta_settings.find_one({}, {"_id": 0})
    invite_cap = settings.get("invite_cap", 200) if settings else 200
    
    report = BetaReport(
        report_date=now.isoformat(),
        period_start=period_start,
        period_end=now.isoformat(),
        
        total_users=total_users,
        new_users_this_period=new_users,
        dau=dau,
        wau=wau,
        
        total_predictions=total_predictions,
        predictions_this_period=predictions_period,
        prediction_accuracy_avg=avg_accuracy,
        
        total_redemptions=total_redemptions,
        redemptions_this_period=redemptions_period,
        voucher_failure_rate=failure_rate,
        avg_delivery_time_minutes=avg_delivery_time,
        
        brand_funded_redemptions=brand_funded,
        total_consumption_value=total_consumption,
        active_campaigns=active_campaigns,
        
        open_tickets=open_tickets,
        tickets_this_period=tickets_period,
        top_issues=top_issues,
        
        invites_generated=invites_generated,
        invites_used=invites_used,
        remaining_invite_cap=invite_cap - invites_generated
    )
    
    return report.dict()


@reports_router.get("/beta-summary")
async def get_beta_summary(user: dict = Depends(get_current_user)):
    """Quick summary for dashboard display"""
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    
    return {
        "timestamp": now.isoformat(),
        "users": {
            "total": await db.users.count_documents({}),
            "dau": await calculate_dau(),
            "wau": await calculate_wau()
        },
        "redemptions": {
            "total": await db.fulfillments.count_documents({}),
            "this_week": await db.fulfillments.count_documents({"created_at": {"$gte": week_ago}}),
            "failure_rate": await calculate_voucher_failure_rate(7)
        },
        "health": {
            "voucher_system": "healthy" if await calculate_voucher_failure_rate(1) < 5 else "degraded",
            "open_tickets": await db.support_tickets.count_documents({"status": "open"})
        }
    }


@reports_router.get("/funnel-metrics")
async def get_funnel_metrics(days: int = 7, user: dict = Depends(get_current_user)):
    """
    UX Funnel tracking: Predict → Earn → Redeem → Receive
    No gambling-like analytics - focus on conversion health.
    """
    period_start = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Users who made predictions
    predictors = await db.predictions.distinct("user_id", {"created_at": {"$gte": period_start}})
    
    # Users who earned coins
    earners = await db.users.count_documents({
        "total_earned": {"$gt": 0},
        "last_activity": {"$gte": period_start}
    })
    
    # Users who redeemed
    redeemers = await db.fulfillments.distinct("user_id", {"created_at": {"$gte": period_start}})
    
    # Users who received voucher
    receivers = await db.fulfillments.distinct("user_id", {
        "created_at": {"$gte": period_start},
        "status": "delivered"
    })
    
    total_users = await db.users.count_documents({})
    
    funnel = {
        "period_days": days,
        "total_users": total_users,
        "stages": {
            "predict": {
                "count": len(predictors),
                "rate": round(len(predictors) / total_users * 100, 1) if total_users else 0
            },
            "earn": {
                "count": earners,
                "rate": round(earners / total_users * 100, 1) if total_users else 0
            },
            "redeem": {
                "count": len(redeemers),
                "rate": round(len(redeemers) / total_users * 100, 1) if total_users else 0
            },
            "receive": {
                "count": len(receivers),
                "rate": round(len(receivers) / total_users * 100, 1) if total_users else 0
            }
        },
        "drop_offs": {
            "predict_to_earn": round((1 - earners / len(predictors)) * 100, 1) if predictors else 0,
            "earn_to_redeem": round((1 - len(redeemers) / earners) * 100, 1) if earners else 0,
            "redeem_to_receive": round((1 - len(receivers) / len(redeemers)) * 100, 1) if redeemers else 0
        }
    }
    
    return funnel
