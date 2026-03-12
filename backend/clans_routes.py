"""
Clans Routes for FREE11
Clan creation, membership, challenges, and leaderboards
Focus: Learning, belonging, streak challenges
No: Coin pooling, P2P transfers, coin multipliers
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

# Import from server.py
from server import db, get_current_user, User

clans_router = APIRouter(prefix="/clans", tags=["Clans"])

# ==================== MODELS ====================

class Clan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    tag: str  # Short 3-5 char tag like [CSK], [BLEED]
    created_by: str  # User ID
    leader_id: str  # Current leader
    logo_emoji: str = "🏏"  # Emoji as logo
    member_count: int = 1
    max_members: int = 50
    # Skill-based stats (NOT coins)
    total_predictions: int = 0
    total_correct: int = 0
    clan_accuracy: float = 0.0
    clan_streak: int = 0  # Consecutive days with predictions
    best_streak: int = 0
    # Challenge tracking
    active_challenge: Optional[str] = None
    challenges_won: int = 0
    challenges_played: int = 0
    # Metadata
    is_public: bool = True
    join_requirement: str = "open"  # open, approval, invite_only
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ClanMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    clan_id: str
    user_id: str
    role: str = "member"  # leader, co-leader, elder, member
    predictions_in_clan: int = 0
    correct_in_clan: int = 0
    personal_streak: int = 0  # Personal streak while in clan
    joined_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ClanChallenge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    challenge_type: str  # accuracy_race, streak_challenge, prediction_count
    clan1_id: str
    clan2_id: Optional[str] = None  # None for solo clan challenges
    target_value: int  # Target to reach
    clan1_progress: int = 0
    clan2_progress: Optional[int] = None
    start_time: str
    end_time: str
    status: str = "active"  # active, completed, expired
    winner_clan_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ==================== REQUEST MODELS ====================

class ClanCreate(BaseModel):
    name: str
    description: str
    tag: str
    logo_emoji: str = "🏏"
    is_public: bool = True

class ClanJoinRequest(BaseModel):
    clan_id: str

# ==================== CLAN CRUD ====================

@clans_router.post("/create")
async def create_clan(
    clan_data: ClanCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new clan - Requires Level 2+ (Amateur)"""
    # Level requirement for clan creation
    if current_user.level < 2:
        raise HTTPException(
            status_code=403, 
            detail="You need to be Level 2 (Amateur) or higher to create a clan. Keep predicting to level up!"
        )
    
    # Validate tag
    if len(clan_data.tag) < 2 or len(clan_data.tag) > 5:
        raise HTTPException(status_code=400, detail="Tag must be 2-5 characters")
    
    # Check if user already in a clan
    existing_membership = await db.clan_members.find_one({"user_id": current_user.id})
    if existing_membership:
        raise HTTPException(status_code=400, detail="You are already in a clan. Leave your current clan first.")
    
    # Check if tag exists
    existing_tag = await db.clans.find_one({"tag": clan_data.tag.upper()})
    if existing_tag:
        raise HTTPException(status_code=400, detail="Clan tag already taken")
    
    # Create clan
    clan = Clan(
        name=clan_data.name,
        description=clan_data.description,
        tag=clan_data.tag.upper(),
        logo_emoji=clan_data.logo_emoji,
        created_by=current_user.id,
        leader_id=current_user.id,
        is_public=clan_data.is_public
    )
    await db.clans.insert_one(clan.model_dump())
    
    # Add creator as leader
    membership = ClanMember(
        clan_id=clan.id,
        user_id=current_user.id,
        role="leader"
    )
    await db.clan_members.insert_one(membership.model_dump())
    
    return {"message": f"Clan [{clan.tag}] {clan.name} created!", "clan": clan.model_dump()}

@clans_router.get("/list")
async def list_clans(
    sort_by: str = "accuracy",  # accuracy, members, streak
    limit: int = 20
):
    """List clans sorted by skill metrics"""
    sort_field = "clan_accuracy"
    if sort_by == "members":
        sort_field = "member_count"
    elif sort_by == "streak":
        sort_field = "best_streak"
    
    clans = await db.clans.find(
        {"is_public": True},
        {"_id": 0}
    ).sort(sort_field, -1).limit(limit).to_list(limit)
    
    return clans

@clans_router.get("/my")
async def get_my_clan(current_user: User = Depends(get_current_user)):
    """Get current user's clan"""
    membership = await db.clan_members.find_one(
        {"user_id": current_user.id},
        {"_id": 0}
    )
    
    if not membership:
        return {"in_clan": False, "clan": None, "membership": None}
    
    clan = await db.clans.find_one(
        {"id": membership["clan_id"]},
        {"_id": 0}
    )
    
    # Get clan members
    members = await db.clan_members.find(
        {"clan_id": membership["clan_id"]},
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with user data
    enriched_members = []
    for member in members:
        user = await db.users.find_one(
            {"id": member["user_id"]},
            {"_id": 0, "name": 1, "level": 1}
        )
        if user:
            enriched_members.append({
                **member,
                "name": user.get("name", "Unknown"),
                "level": user.get("level", 1),
                "accuracy": round((member["correct_in_clan"] / member["predictions_in_clan"] * 100), 1) if member["predictions_in_clan"] > 0 else 0
            })
    
    # Sort members by accuracy
    enriched_members.sort(key=lambda x: x.get("accuracy", 0), reverse=True)
    
    return {
        "in_clan": True,
        "clan": clan,
        "membership": membership,
        "members": enriched_members
    }

@clans_router.get("/{clan_id}")
async def get_clan(clan_id: str):
    """Get clan details"""
    clan = await db.clans.find_one({"id": clan_id}, {"_id": 0})
    if not clan:
        raise HTTPException(status_code=404, detail="Clan not found")
    
    # Get top members by accuracy
    members = await db.clan_members.find(
        {"clan_id": clan_id},
        {"_id": 0}
    ).to_list(50)
    
    enriched_members = []
    for member in members:
        user = await db.users.find_one(
            {"id": member["user_id"]},
            {"_id": 0, "name": 1, "level": 1}
        )
        if user:
            enriched_members.append({
                **member,
                "name": user.get("name", "Unknown"),
                "level": user.get("level", 1),
                "accuracy": round((member["correct_in_clan"] / member["predictions_in_clan"] * 100), 1) if member["predictions_in_clan"] > 0 else 0
            })
    
    enriched_members.sort(key=lambda x: x.get("accuracy", 0), reverse=True)
    
    return {
        "clan": clan,
        "members": enriched_members
    }

@clans_router.post("/join")
async def join_clan(
    join_request: ClanJoinRequest,
    current_user: User = Depends(get_current_user)
):
    """Join a public clan"""
    # Check if already in clan
    existing = await db.clan_members.find_one({"user_id": current_user.id})
    if existing:
        raise HTTPException(status_code=400, detail="Already in a clan")
    
    # Get clan
    clan = await db.clans.find_one({"id": join_request.clan_id})
    if not clan:
        raise HTTPException(status_code=404, detail="Clan not found")
    
    if not clan.get("is_public"):
        raise HTTPException(status_code=403, detail="This clan is private")
    
    if clan.get("member_count", 0) >= clan.get("max_members", 50):
        raise HTTPException(status_code=400, detail="Clan is full")
    
    # Add member
    membership = ClanMember(
        clan_id=clan["id"],
        user_id=current_user.id,
        role="member"
    )
    await db.clan_members.insert_one(membership.model_dump())
    
    # Update clan member count
    await db.clans.update_one(
        {"id": clan["id"]},
        {"$inc": {"member_count": 1}}
    )
    
    return {"message": f"Joined [{clan['tag']}] {clan['name']}!"}

@clans_router.post("/leave")
async def leave_clan(current_user: User = Depends(get_current_user)):
    """Leave current clan"""
    membership = await db.clan_members.find_one({"user_id": current_user.id})
    if not membership:
        raise HTTPException(status_code=400, detail="Not in a clan")
    
    # Leaders can't leave (must transfer leadership first)
    if membership.get("role") == "leader":
        raise HTTPException(status_code=400, detail="Leaders must transfer leadership before leaving")
    
    # Remove membership
    await db.clan_members.delete_one({"id": membership["id"]})
    
    # Update clan count
    await db.clans.update_one(
        {"id": membership["clan_id"]},
        {"$inc": {"member_count": -1}}
    )
    
    return {"message": "Left the clan"}

# ==================== LEADERBOARDS (SKILL-BASED) ====================

@clans_router.get("/leaderboard/clans")
async def get_clan_leaderboard():
    """
    Get clan leaderboard ranked by SKILL metrics
    Primary: Accuracy | Secondary: Best Streak
    NOT ranked by coins
    """
    clans = await db.clans.find(
        {"member_count": {"$gt": 0}},
        {"_id": 0}
    ).to_list(100)
    
    # Sort by accuracy (primary), then streak (secondary)
    clans.sort(key=lambda x: (x.get("clan_accuracy", 0), x.get("best_streak", 0)), reverse=True)
    
    result = []
    for i, clan in enumerate(clans[:20]):
        result.append({
            "rank": i + 1,
            "id": clan["id"],
            "name": clan["name"],
            "tag": clan["tag"],
            "logo_emoji": clan.get("logo_emoji", "🏏"),
            "accuracy": round(clan.get("clan_accuracy", 0), 1),
            "best_streak": clan.get("best_streak", 0),
            "member_count": clan.get("member_count", 0),
            "total_predictions": clan.get("total_predictions", 0)
        })
    
    return result

@clans_router.get("/leaderboard/members/{clan_id}")
async def get_clan_member_leaderboard(clan_id: str):
    """
    Get members within a clan ranked by SKILL
    Primary: Accuracy | Secondary: Personal Streak
    """
    members = await db.clan_members.find(
        {"clan_id": clan_id},
        {"_id": 0}
    ).to_list(50)
    
    result = []
    for member in members:
        user = await db.users.find_one(
            {"id": member["user_id"]},
            {"_id": 0, "name": 1, "level": 1}
        )
        if user:
            accuracy = round((member["correct_in_clan"] / member["predictions_in_clan"] * 100), 1) if member["predictions_in_clan"] > 0 else 0
            result.append({
                "user_id": member["user_id"],
                "name": user.get("name", "Unknown"),
                "level": user.get("level", 1),
                "role": member.get("role", "member"),
                "accuracy": accuracy,
                "predictions": member.get("predictions_in_clan", 0),
                "correct": member.get("correct_in_clan", 0),
                "streak": member.get("personal_streak", 0)
            })
    
    # Sort by accuracy
    result.sort(key=lambda x: (x["accuracy"], x["streak"]), reverse=True)
    
    for i, member in enumerate(result):
        member["rank"] = i + 1
    
    return result

# ==================== CHALLENGES ====================

@clans_router.get("/challenges/available")
async def get_available_challenges(current_user: User = Depends(get_current_user)):
    """Get available clan challenges"""
    membership = await db.clan_members.find_one({"user_id": current_user.id})
    if not membership:
        return {"challenges": [], "message": "Join a clan to participate in challenges"}
    
    # Daily challenges for all clans
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    challenges = [
        {
            "id": f"daily_accuracy_{today}",
            "name": "Accuracy Challenge",
            "description": "Get the highest prediction accuracy today",
            "type": "accuracy_race",
            "target": "Highest % wins",
            "duration": "24 hours",
            "reward": "Clan badge + bragging rights"
        },
        {
            "id": f"streak_challenge_{today}",
            "name": "Streak Builder",
            "description": "Maintain your clan's prediction streak",
            "type": "streak_challenge",
            "target": "Keep the streak alive",
            "duration": "Daily",
            "reward": "Streak multiplier badge"
        },
        {
            "id": f"prediction_count_{today}",
            "name": "Prediction Rush",
            "description": "Make the most predictions as a clan",
            "type": "prediction_count",
            "target": "100 predictions",
            "duration": "24 hours",
            "reward": "Active clan badge"
        }
    ]
    
    return {"challenges": challenges}

@clans_router.post("/challenges/participate/{challenge_id}")
async def participate_in_challenge(
    challenge_id: str,
    current_user: User = Depends(get_current_user)
):
    """Join a clan challenge"""
    membership = await db.clan_members.find_one({"user_id": current_user.id})
    if not membership:
        raise HTTPException(status_code=400, detail="Must be in a clan")
    
    return {
        "message": f"Your clan is participating in the challenge!",
        "note": "Make predictions to contribute to your clan's score"
    }

# ==================== HELPER: Update Clan Stats ====================

async def update_clan_stats_on_prediction(user_id: str, is_correct: bool):
    """
    Called after a prediction to update clan stats
    This should be called from cricket_routes.py
    """
    membership = await db.clan_members.find_one({"user_id": user_id})
    if not membership:
        return
    
    # Update member stats
    update_member = {
        "$inc": {
            "predictions_in_clan": 1,
            "correct_in_clan": 1 if is_correct else 0
        }
    }
    if is_correct:
        update_member["$inc"]["personal_streak"] = 1
    else:
        update_member["$set"] = {"personal_streak": 0}
    
    await db.clan_members.update_one({"id": membership["id"]}, update_member)
    
    # Update clan stats
    clan = await db.clans.find_one({"id": membership["clan_id"]})
    if clan:
        new_total = clan.get("total_predictions", 0) + 1
        new_correct = clan.get("total_correct", 0) + (1 if is_correct else 0)
        new_accuracy = (new_correct / new_total * 100) if new_total > 0 else 0
        
        update_clan = {
            "$set": {
                "total_predictions": new_total,
                "total_correct": new_correct,
                "clan_accuracy": round(new_accuracy, 1)
            }
        }
        
        await db.clans.update_one({"id": clan["id"]}, update_clan)
