"""
Feature Flags & Compliance System for FREE11
Age Gate, Geo-blocking, and Feature Toggles
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os

feature_router = APIRouter(prefix="/features", tags=["Features"])

# ==================== BLOCKED STATES ====================
# States where fantasy sports are restricted/banned in India
BLOCKED_STATES = {
    "AP": "Andhra Pradesh",
    "TG": "Telangana",
    "AS": "Assam",
    "OD": "Odisha",
    "SK": "Sikkim",
    "NL": "Nagaland"
}

BLOCKED_STATE_NAMES = list(BLOCKED_STATES.values())

# ==================== FEATURE FLAGS ====================
# Default feature flag configuration
DEFAULT_FEATURE_FLAGS = {
    "fantasy_contests": True,
    "over_predictions": True,
    "match_predictions": True,
    "ball_by_ball": True,
    "ball_by_ball_limit": 20,  # Max ball predictions per match per user
    "private_leagues": True,
    "clans": True,
    "leaderboards": True,
    "catalog_redemption": True,
    "mini_games": True,  # Quiz, Spin, Scratch
    "daily_checkin": True,
    "referral_system": False,  # Not in Beta
    "push_notifications": False,  # Not in Beta
}

# In-memory feature flags (in production, use Redis/DB)
_feature_flags = DEFAULT_FEATURE_FLAGS.copy()

# ==================== MODELS ====================

class AgeVerification(BaseModel):
    date_of_birth: str  # YYYY-MM-DD format
    
class GeoCheckRequest(BaseModel):
    state: str
    state_code: Optional[str] = None

class GeoCheckResponse(BaseModel):
    allowed: bool
    state: str
    message: str

class FeatureFlagResponse(BaseModel):
    flags: Dict[str, Any]
    environment: str

# ==================== HELPER FUNCTIONS ====================

def calculate_age(dob_str: str) -> int:
    """Calculate age from date of birth string (YYYY-MM-DD)"""
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

def is_state_blocked(state: str) -> bool:
    """Check if a state is blocked for fantasy sports"""
    state_upper = state.upper().strip()
    # Check against state codes
    if state_upper in BLOCKED_STATES:
        return True
    # Check against full state names
    if state.strip().title() in BLOCKED_STATE_NAMES:
        return True
    return False

def get_feature_flag(flag_name: str) -> any:
    """Get a feature flag value"""
    return _feature_flags.get(flag_name, False)

def set_feature_flag(flag_name: str, value: any) -> None:
    """Set a feature flag value (admin only)"""
    _feature_flags[flag_name] = value

# ==================== ROUTES ====================

@feature_router.post("/verify-age")
async def verify_age(data: AgeVerification):
    """
    Verify if user meets minimum age requirement (18+)
    """
    age = calculate_age(data.date_of_birth)
    
    if age < 18:
        return {
            "allowed": False,
            "age": age,
            "message": "You must be 18 years or older to use FREE11",
            "min_age": 18
        }
    
    return {
        "allowed": True,
        "age": age,
        "message": "Age verification successful",
        "min_age": 18
    }

@feature_router.post("/check-geo", response_model=GeoCheckResponse)
async def check_geo(data: GeoCheckRequest):
    """
    Check if user's state allows fantasy sports
    """
    state = data.state.strip()
    state_code = data.state_code.strip().upper() if data.state_code else None
    
    # Check state code first if provided
    if state_code and state_code in BLOCKED_STATES:
        return GeoCheckResponse(
            allowed=False,
            state=BLOCKED_STATES[state_code],
            message=f"Fantasy sports are not available in {BLOCKED_STATES[state_code]} due to local regulations"
        )
    
    # Check full state name
    if is_state_blocked(state):
        return GeoCheckResponse(
            allowed=False,
            state=state,
            message=f"Fantasy sports are not available in {state} due to local regulations"
        )
    
    return GeoCheckResponse(
        allowed=True,
        state=state,
        message="Your location is eligible for FREE11"
    )

@feature_router.get("/blocked-states")
async def get_blocked_states():
    """
    Get list of blocked states for client-side validation
    """
    return {
        "blocked_states": BLOCKED_STATES,
        "blocked_state_names": BLOCKED_STATE_NAMES,
        "reason": "Fantasy sports are restricted in these states due to local regulations"
    }

@feature_router.get("/flags", response_model=FeatureFlagResponse)
async def get_feature_flags():
    """
    Get current feature flags for the app
    """
    env = os.environ.get("FREE11_ENV", "sandbox")
    return FeatureFlagResponse(
        flags=_feature_flags,
        environment=env
    )

@feature_router.get("/flags/{flag_name}")
async def get_single_flag(flag_name: str):
    """
    Get a specific feature flag value
    """
    if flag_name not in _feature_flags:
        raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")
    
    return {
        "flag": flag_name,
        "value": _feature_flags[flag_name],
        "environment": os.environ.get("FREE11_ENV", "sandbox")
    }

@feature_router.put("/flags/{flag_name}")
async def update_feature_flag(flag_name: str, value: bool):
    """
    Update a feature flag (admin only)
    In production, this should be protected with admin authentication
    """
    if flag_name not in DEFAULT_FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")
    
    old_value = _feature_flags.get(flag_name)
    _feature_flags[flag_name] = value
    
    return {
        "flag": flag_name,
        "old_value": old_value,
        "new_value": value,
        "message": f"Feature flag '{flag_name}' updated successfully"
    }

@feature_router.post("/flags/reset")
async def reset_feature_flags():
    """
    Reset all feature flags to defaults (admin only)
    """
    global _feature_flags
    _feature_flags = DEFAULT_FEATURE_FLAGS.copy()
    
    return {
        "message": "All feature flags reset to defaults",
        "flags": _feature_flags
    }

# ==================== COMPLIANCE CHECK ====================

@feature_router.post("/compliance-check")
async def full_compliance_check(
    date_of_birth: str,
    state: str,
    state_code: Optional[str] = None
):
    """
    Full compliance check for registration:
    1. Age verification (18+)
    2. Geo-blocking (state check)
    """
    errors = []
    
    # Age check
    try:
        age = calculate_age(date_of_birth)
        if age < 18:
            errors.append({
                "type": "age",
                "message": "You must be 18 years or older to use FREE11",
                "details": {"age": age, "min_age": 18}
            })
    except HTTPException as e:
        errors.append({
            "type": "age",
            "message": str(e.detail),
            "details": {}
        })
    
    # Geo check
    if state_code and state_code.upper() in BLOCKED_STATES:
        errors.append({
            "type": "geo",
            "message": f"Fantasy sports are not available in {BLOCKED_STATES[state_code.upper()]}",
            "details": {"state": state, "state_code": state_code}
        })
    elif is_state_blocked(state):
        errors.append({
            "type": "geo",
            "message": f"Fantasy sports are not available in {state}",
            "details": {"state": state}
        })
    
    if errors:
        return {
            "allowed": False,
            "errors": errors,
            "message": "Registration not allowed due to compliance requirements"
        }
    
    return {
        "allowed": True,
        "errors": [],
        "message": "All compliance checks passed"
    }
