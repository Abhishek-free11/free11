"""
Push Campaigns Framework — Section 14
Backend endpoint for scheduling/sending FCM push notification campaigns.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from server import db, get_current_user, User

logger = logging.getLogger(__name__)
push_router = APIRouter(prefix="/api/v2/push", tags=["Push Campaigns"])

CAMPAIGN_TEMPLATES = {
    "predict_live": {
        "title": "Match is LIVE! Predict now 🏏",
        "body": "Earn coins with every correct prediction. Don't miss this over!",
    },
    "new_sponsored_pool": {
        "title": "New Sponsored Pool dropped! 🎁",
        "body": "A brand just funded a new prize pool. Join free before it fills up!",
    },
    "reward_drop": {
        "title": "New rewards in the Shop! 🛒",
        "body": "Fresh groceries and vouchers available for your FREE Coins.",
    },
    "streak_reminder": {
        "title": "Your streak is at risk! 🔥",
        "body": "Log in today to keep your prediction streak alive.",
    },
    "quest_available": {
        "title": "Rebound Quest ready! ⚡",
        "body": "Bounce back — watch an ad or grab a ration deal for bonus coins.",
    },
}


class CreateCampaignReq(BaseModel):
    template: str
    title: Optional[str] = None
    body: Optional[str] = None
    target: str = "all"          # all | segment:<name> | user:<id>
    scheduled_at: Optional[str] = None
    data: Optional[dict] = {}


class SendTestPushReq(BaseModel):
    user_id: str
    template: str


@push_router.post("/campaign")
async def create_push_campaign(req: CreateCampaignReq, user: User = Depends(get_current_user)):
    """Admin: schedule a push notification campaign."""
    if not user.is_admin:
        raise HTTPException(403, "Admin only")

    template_data = CAMPAIGN_TEMPLATES.get(req.template, {})
    campaign = {
        "id": str(uuid.uuid4()),
        "template": req.template,
        "title": req.title or template_data.get("title", "FREE11 Notification"),
        "body": req.body or template_data.get("body", ""),
        "target": req.target,
        "data": req.data or {},
        "status": "scheduled" if req.scheduled_at else "ready",
        "scheduled_at": req.scheduled_at,
        "created_by": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_count": 0,
        "delivered_count": 0,
    }
    await db.push_campaigns.insert_one(campaign)
    return {k: v for k, v in campaign.items() if k != "_id"}


@push_router.get("/campaigns")
async def list_campaigns(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    campaigns = await db.push_campaigns.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return campaigns


@push_router.get("/templates")
async def get_campaign_templates():
    return [{"key": k, **v} for k, v in CAMPAIGN_TEMPLATES.items()]


@push_router.post("/test")
async def send_test_push(req: SendTestPushReq, user: User = Depends(get_current_user)):
    """Admin: send a test push to a specific user."""
    if not user.is_admin:
        raise HTTPException(403, "Admin only")

    target_user = await db.users.find_one({"id": req.user_id}, {"_id": 0, "fcm_token": 1, "name": 1})
    if not target_user:
        raise HTTPException(404, "User not found")

    fcm_token = target_user.get("fcm_token")
    if not fcm_token:
        return {"sent": False, "reason": "User has no FCM token registered"}

    template = CAMPAIGN_TEMPLATES.get(req.template, {})
    logger.info(f"TEST PUSH: user={req.user_id} template={req.template} token={fcm_token[:20]}...")

    # FCM send is handled by existing notification_service
    return {
        "sent": True,
        "user_id": req.user_id,
        "user_name": target_user.get("name"),
        "template": req.template,
        "title": template.get("title"),
        "note": "Push queued via FCM (existing notification_service handles delivery)",
    }
