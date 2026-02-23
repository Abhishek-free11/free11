"""
Beta Invite System for FREE11
==============================
Controlled beta onboarding with invite codes.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import random
import string

# Import db from server
from server import db, get_current_user

beta_router = APIRouter(prefix="/api/beta", tags=["beta"])

# Configuration
DEFAULT_INVITE_CAP = 200
INVITE_CODE_PREFIX = "FREE11"


class InviteCode(BaseModel):
    """Beta invite code model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    source: str  # Where/who the invite came from
    created_by: Optional[str] = None  # Admin who created it
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    used_at: Optional[str] = None
    used_by_user_id: Optional[str] = None
    used_by_email: Optional[str] = None
    is_active: bool = True
    is_revoked: bool = False
    revoked_at: Optional[str] = None
    revoked_reason: Optional[str] = None
    max_uses: int = 1  # Single use by default
    current_uses: int = 0
    expires_at: Optional[str] = None


class CreateInviteRequest(BaseModel):
    source: str = Field(..., description="Invite source (e.g., 'twitter_campaign', 'founder_direct')")
    count: int = Field(default=1, ge=1, le=100, description="Number of codes to generate")
    max_uses_per_code: int = Field(default=1, ge=1, le=100)
    expires_in_days: Optional[int] = Field(default=30, ge=1, le=365)


class ValidateInviteRequest(BaseModel):
    code: str


class RevokeInviteRequest(BaseModel):
    reason: Optional[str] = None


class BetaSettings(BaseModel):
    invite_cap: int = DEFAULT_INVITE_CAP
    is_beta_open: bool = True
    allow_new_registrations: bool = True
    require_invite_code: bool = True


def generate_invite_code() -> str:
    """Generate a unique invite code like FREE11-ABCD1234"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{INVITE_CODE_PREFIX}-{suffix}"


# ==================== Admin Endpoints ====================

@beta_router.post("/admin/invites/generate")
async def generate_invites(request: CreateInviteRequest, user = Depends(get_current_user)):
    """Generate new invite codes (admin only)"""
    # Check beta cap
    total_invites = await db.beta_invites.count_documents({"is_revoked": False})
    settings = await get_beta_settings()
    
    if total_invites + request.count > settings.invite_cap:
        remaining = settings.invite_cap - total_invites
        raise HTTPException(
            status_code=400,
            detail=f"Would exceed invite cap. Remaining slots: {remaining}"
        )
    
    # Calculate expiry
    expires_at = None
    if request.expires_in_days:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)).isoformat()
    
    # Get user ID (handle both dict and Pydantic model)
    user_id = user.id if hasattr(user, 'id') else user.get("id")
    
    # Generate codes
    codes = []
    for _ in range(request.count):
        code = generate_invite_code()
        
        # Ensure uniqueness
        while await db.beta_invites.find_one({"code": code}):
            code = generate_invite_code()
        
        invite = InviteCode(
            code=code,
            source=request.source,
            created_by=user_id,
            max_uses=request.max_uses_per_code,
            expires_at=expires_at
        )
        
        await db.beta_invites.insert_one(invite.dict())
        codes.append({
            "code": code,
            "expires_at": expires_at,
            "max_uses": request.max_uses_per_code
        })
    
    return {
        "generated": len(codes),
        "source": request.source,
        "codes": codes
    }


@beta_router.get("/admin/invites")
async def list_invites(
    status: Optional[str] = None,  # active, used, revoked, expired
    source: Optional[str] = None,
    limit: int = 50,
    user = Depends(get_current_user)
):
    """List all invite codes with filters"""
    query = {}
    
    now = datetime.now(timezone.utc).isoformat()
    
    if status == "active":
        query["is_active"] = True
        query["is_revoked"] = False
        query["$or"] = [
            {"expires_at": None},
            {"expires_at": {"$gt": now}}
        ]
    elif status == "used":
        query["current_uses"] = {"$gt": 0}
    elif status == "revoked":
        query["is_revoked"] = True
    elif status == "expired":
        query["expires_at"] = {"$lt": now, "$ne": None}
    
    if source:
        query["source"] = source
    
    invites = await db.beta_invites.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Get summary stats
    total = await db.beta_invites.count_documents({})
    active = await db.beta_invites.count_documents({"is_active": True, "is_revoked": False})
    used = await db.beta_invites.count_documents({"current_uses": {"$gt": 0}})
    revoked = await db.beta_invites.count_documents({"is_revoked": True})
    
    return {
        "invites": invites,
        "summary": {
            "total": total,
            "active": active,
            "used": used,
            "revoked": revoked
        }
    }


@beta_router.post("/admin/invites/{code}/revoke")
async def revoke_invite(code: str, request: RevokeInviteRequest, user = Depends(get_current_user)):
    """Revoke an invite code"""
    invite = await db.beta_invites.find_one({"code": code})
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invite code not found")
    
    if invite.get("is_revoked"):
        raise HTTPException(status_code=400, detail="Invite already revoked")
    
    await db.beta_invites.update_one(
        {"code": code},
        {
            "$set": {
                "is_revoked": True,
                "is_active": False,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "revoked_reason": request.reason
            }
        }
    )
    
    return {"success": True, "message": f"Invite {code} revoked"}


@beta_router.post("/admin/invites/pause")
async def pause_all_invites(user = Depends(get_current_user)):
    """Pause all active invites (emergency brake)"""
    result = await db.beta_invites.update_many(
        {"is_active": True, "is_revoked": False},
        {"$set": {"is_active": False}}
    )
    
    return {
        "success": True,
        "paused_count": result.modified_count,
        "message": "All active invites paused"
    }


@beta_router.post("/admin/invites/resume")
async def resume_invites(user = Depends(get_current_user)):
    """Resume paused invites"""
    result = await db.beta_invites.update_many(
        {"is_active": False, "is_revoked": False},
        {"$set": {"is_active": True}}
    )
    
    return {
        "success": True,
        "resumed_count": result.modified_count,
        "message": "Paused invites resumed"
    }


@beta_router.get("/admin/settings")
async def get_beta_settings_endpoint(user: dict = Depends(get_current_user)):
    """Get current beta settings"""
    settings = await get_beta_settings()
    
    # Get current counts
    total_invites = await db.beta_invites.count_documents({"is_revoked": False})
    used_invites = await db.beta_invites.count_documents({"current_uses": {"$gt": 0}})
    beta_users = await db.users.count_documents({"beta_invite_code": {"$exists": True}})
    
    return {
        "settings": settings.dict(),
        "usage": {
            "total_invites_generated": total_invites,
            "invites_used": used_invites,
            "beta_users_onboarded": beta_users,
            "remaining_cap": settings.invite_cap - total_invites
        }
    }


@beta_router.put("/admin/settings")
async def update_beta_settings(settings: BetaSettings, user: dict = Depends(get_current_user)):
    """Update beta settings"""
    await db.beta_settings.update_one(
        {},
        {"$set": settings.dict()},
        upsert=True
    )
    
    return {"success": True, "settings": settings.dict()}


# ==================== Public Endpoints ====================

@beta_router.post("/validate-invite")
async def validate_invite(request: ValidateInviteRequest):
    """Validate an invite code (public - used during registration)"""
    code = request.code.upper().strip()
    
    invite = await db.beta_invites.find_one({"code": code})
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if invite.get("is_revoked"):
        raise HTTPException(status_code=400, detail="This invite code has been revoked")
    
    if not invite.get("is_active"):
        raise HTTPException(status_code=400, detail="This invite code is not active")
    
    # Check expiry
    if invite.get("expires_at"):
        expires = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=400, detail="This invite code has expired")
    
    # Check usage
    if invite.get("current_uses", 0) >= invite.get("max_uses", 1):
        raise HTTPException(status_code=400, detail="This invite code has reached its usage limit")
    
    return {
        "valid": True,
        "source": invite.get("source"),
        "remaining_uses": invite.get("max_uses", 1) - invite.get("current_uses", 0)
    }


@beta_router.get("/status")
async def get_beta_status():
    """Get public beta status"""
    settings = await get_beta_settings()
    
    return {
        "is_beta_open": settings.is_beta_open,
        "require_invite_code": settings.require_invite_code,
        "allow_new_registrations": settings.allow_new_registrations
    }


# ==================== Helper Functions ====================

async def get_beta_settings() -> BetaSettings:
    """Get current beta settings from DB"""
    settings = await db.beta_settings.find_one({}, {"_id": 0})
    if settings:
        return BetaSettings(**settings)
    return BetaSettings()


async def use_invite_code(code: str, user_id: str, user_email: str) -> bool:
    """Mark an invite code as used (called during registration)"""
    code = code.upper().strip()
    
    result = await db.beta_invites.update_one(
        {
            "code": code,
            "is_active": True,
            "is_revoked": False,
            "$expr": {"$lt": ["$current_uses", "$max_uses"]}
        },
        {
            "$inc": {"current_uses": 1},
            "$set": {
                "used_at": datetime.now(timezone.utc).isoformat(),
                "used_by_user_id": user_id,
                "used_by_email": user_email
            }
        }
    )
    
    return result.modified_count > 0


async def check_beta_registration_allowed(invite_code: Optional[str] = None) -> tuple[bool, str]:
    """Check if registration is allowed (with or without invite)"""
    settings = await get_beta_settings()
    
    if not settings.is_beta_open:
        return False, "Beta registration is currently closed"
    
    if not settings.allow_new_registrations:
        return False, "New registrations are paused"
    
    if settings.require_invite_code:
        if not invite_code:
            return False, "Invite code required for beta registration"
        
        # Validate the code
        code = invite_code.upper().strip()
        invite = await db.beta_invites.find_one({"code": code})
        
        if not invite:
            return False, "Invalid invite code"
        
        if invite.get("is_revoked") or not invite.get("is_active"):
            return False, "Invite code is not valid"
        
        if invite.get("current_uses", 0) >= invite.get("max_uses", 1):
            return False, "Invite code has reached its usage limit"
    
    return True, "OK"
