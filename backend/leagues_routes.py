"""
Private Leagues for FREE11
User-created P2P leagues (no money)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import uuid
import random
import string

from server import db, get_current_user, User

leagues_router = APIRouter(prefix="/leagues", tags=["Private Leagues"])

# ==================== CONSTANTS ====================

MAX_LEAGUE_MEMBERS = 100
MAX_LEAGUES_PER_USER = 5

# ==================== MODELS ====================

class League(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    code: str  # Unique join code
    created_by: str  # User ID
    admin_ids: List[str] = Field(default_factory=list)  # User IDs with admin rights
    member_ids: List[str] = Field(default_factory=list)
    max_members: int = MAX_LEAGUE_MEMBERS
    is_active: bool = True
    season: str = "IPL 2026"
    # Scoring
    total_matches_played: int = 0
    # Settings
    scoring_type: str = "accuracy"  # accuracy, total_predictions, streak
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class LeagueMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    league_id: str
    user_id: str
    joined_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Stats within this league
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy: float = 0
    points: int = 0
    rank: int = 0
    streak: int = 0
    best_streak: int = 0

class LeagueInvite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    league_id: str
    invited_by: str
    invited_email: Optional[str] = None
    code: str
    is_used: bool = False
    expires_at: str

# Request Models
class CreateLeagueRequest(BaseModel):
    name: str
    description: Optional[str] = None
    max_members: int = 20
    scoring_type: str = "accuracy"

class JoinLeagueRequest(BaseModel):
    code: str

# ==================== HELPER FUNCTIONS ====================

def generate_league_code() -> str:
    """Generate a unique 8-character league code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ==================== ROUTES ====================

@leagues_router.post("/create")
async def create_league(
    request: CreateLeagueRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new private league"""
    
    # Check user's league limit
    user_leagues = await db.private_leagues.count_documents({
        "created_by": current_user.id,
        "is_active": True
    })
    
    if user_leagues >= MAX_LEAGUES_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"You can only create {MAX_LEAGUES_PER_USER} leagues"
        )
    
    # Generate unique code
    code = generate_league_code()
    while await db.private_leagues.find_one({"code": code}):
        code = generate_league_code()
    
    # Validate scoring type
    valid_scoring = ["accuracy", "total_predictions", "streak"]
    if request.scoring_type not in valid_scoring:
        request.scoring_type = "accuracy"
    
    # Create league
    league = League(
        name=request.name,
        description=request.description,
        code=code,
        created_by=current_user.id,
        admin_ids=[current_user.id],
        member_ids=[current_user.id],
        max_members=min(request.max_members, MAX_LEAGUE_MEMBERS),
        scoring_type=request.scoring_type
    )
    
    await db.private_leagues.insert_one(league.model_dump())
    
    # Add creator as first member
    member = LeagueMember(
        league_id=league.id,
        user_id=current_user.id
    )
    await db.league_members.insert_one(member.model_dump())
    
    return {
        "message": "League created successfully!",
        "league": league.model_dump(),
        "join_code": code,
        "share_message": f"Join my FREE11 league '{request.name}'! Use code: {code}"
    }

@leagues_router.post("/join")
async def join_league(
    request: JoinLeagueRequest,
    current_user: User = Depends(get_current_user)
):
    """Join a private league using code"""
    
    code = request.code.upper().strip()
    
    league = await db.private_leagues.find_one(
        {"code": code, "is_active": True},
        {"_id": 0}
    )
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found. Check the code.")
    
    # Check if already a member
    if current_user.id in league.get("member_ids", []):
        raise HTTPException(status_code=400, detail="You're already a member of this league")
    
    # Check capacity
    if len(league.get("member_ids", [])) >= league.get("max_members", MAX_LEAGUE_MEMBERS):
        raise HTTPException(status_code=400, detail="League is full")
    
    # Add member
    await db.private_leagues.update_one(
        {"id": league["id"]},
        {"$push": {"member_ids": current_user.id}}
    )
    
    # Create member record
    member = LeagueMember(
        league_id=league["id"],
        user_id=current_user.id
    )
    await db.league_members.insert_one(member.model_dump())
    
    return {
        "message": f"Welcome to {league['name']}!",
        "league": league
    }

@leagues_router.get("/my")
async def get_my_leagues(current_user: User = Depends(get_current_user)):
    """Get all leagues user is a member of"""
    
    leagues = await db.private_leagues.find(
        {"member_ids": current_user.id, "is_active": True},
        {"_id": 0}
    ).to_list(50)
    
    # Add member stats for each league
    for league in leagues:
        member = await db.league_members.find_one(
            {"league_id": league["id"], "user_id": current_user.id},
            {"_id": 0}
        )
        league["my_stats"] = member
        league["member_count"] = len(league.get("member_ids", []))
        league["is_admin"] = current_user.id in league.get("admin_ids", [])
    
    return {
        "leagues": leagues,
        "total": len(leagues)
    }

@leagues_router.get("/{league_id}")
async def get_league_details(
    league_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific league"""
    
    league = await db.private_leagues.find_one(
        {"id": league_id, "is_active": True},
        {"_id": 0}
    )
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check if user is a member
    if current_user.id not in league.get("member_ids", []):
        raise HTTPException(status_code=403, detail="You're not a member of this league")
    
    return {
        "league": league,
        "member_count": len(league.get("member_ids", [])),
        "is_admin": current_user.id in league.get("admin_ids", [])
    }

@leagues_router.get("/{league_id}/leaderboard")
async def get_league_leaderboard(
    league_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get leaderboard for a private league"""
    
    league = await db.private_leagues.find_one(
        {"id": league_id, "is_active": True},
        {"_id": 0}
    )
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get all members with stats
    members = await db.league_members.find(
        {"league_id": league_id},
        {"_id": 0}
    ).to_list(MAX_LEAGUE_MEMBERS)
    
    # Enrich with user data
    leaderboard = []
    for member in members:
        user = await db.users.find_one(
            {"id": member["user_id"]},
            {"_id": 0, "name": 1, "level": 1}
        )
        if user:
            leaderboard.append({
                "user_id": member["user_id"],
                "name": user.get("name", "Anonymous"),
                "level": user.get("level", 1),
                "points": member.get("points", 0),
                "accuracy": member.get("accuracy", 0),
                "total_predictions": member.get("total_predictions", 0),
                "correct_predictions": member.get("correct_predictions", 0),
                "streak": member.get("streak", 0),
                "best_streak": member.get("best_streak", 0)
            })
    
    # Sort by scoring type
    scoring_type = league.get("scoring_type", "accuracy")
    if scoring_type == "accuracy":
        leaderboard.sort(key=lambda x: (-x["accuracy"], -x["total_predictions"]))
    elif scoring_type == "total_predictions":
        leaderboard.sort(key=lambda x: -x["total_predictions"])
    elif scoring_type == "streak":
        leaderboard.sort(key=lambda x: (-x["best_streak"], -x["accuracy"]))
    
    # Add ranks
    for i, entry in enumerate(leaderboard, 1):
        entry["rank"] = i
    
    return {
        "league": league,
        "leaderboard": leaderboard,
        "scoring_type": scoring_type,
        "my_rank": next(
            (e["rank"] for e in leaderboard if e["user_id"] == current_user.id),
            None
        )
    }

@leagues_router.get("/{league_id}/members")
async def get_league_members(
    league_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all members of a league"""
    
    league = await db.private_leagues.find_one(
        {"id": league_id, "is_active": True},
        {"_id": 0}
    )
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    if current_user.id not in league.get("member_ids", []):
        raise HTTPException(status_code=403, detail="You're not a member of this league")
    
    # Get member details
    members = []
    for user_id in league.get("member_ids", []):
        user = await db.users.find_one(
            {"id": user_id},
            {"_id": 0, "id": 1, "name": 1, "level": 1}
        )
        if user:
            members.append({
                "user_id": user["id"],
                "name": user.get("name", "Anonymous"),
                "level": user.get("level", 1),
                "is_admin": user_id in league.get("admin_ids", []),
                "is_creator": user_id == league.get("created_by")
            })
    
    return {
        "league_id": league_id,
        "members": members,
        "total": len(members)
    }

@leagues_router.post("/{league_id}/leave")
async def leave_league(
    league_id: str,
    current_user: User = Depends(get_current_user)
):
    """Leave a private league"""
    
    league = await db.private_leagues.find_one(
        {"id": league_id, "is_active": True},
        {"_id": 0}
    )
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    if current_user.id not in league.get("member_ids", []):
        raise HTTPException(status_code=400, detail="You're not a member of this league")
    
    # Creator cannot leave
    if current_user.id == league.get("created_by"):
        raise HTTPException(
            status_code=400,
            detail="League creator cannot leave. Transfer ownership or delete the league."
        )
    
    # Remove from members
    await db.private_leagues.update_one(
        {"id": league_id},
        {
            "$pull": {
                "member_ids": current_user.id,
                "admin_ids": current_user.id
            }
        }
    )
    
    # Remove member record
    await db.league_members.delete_one({
        "league_id": league_id,
        "user_id": current_user.id
    })
    
    return {"message": f"Left {league['name']}"}

@leagues_router.delete("/{league_id}")
async def delete_league(
    league_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a league (creator only)"""
    
    league = await db.private_leagues.find_one(
        {"id": league_id, "is_active": True},
        {"_id": 0}
    )
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    if league.get("created_by") != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can delete the league")
    
    # Soft delete
    await db.private_leagues.update_one(
        {"id": league_id},
        {"$set": {"is_active": False}}
    )
    
    return {"message": f"League '{league['name']}' deleted"}

@leagues_router.post("/{league_id}/admin/{user_id}")
async def add_admin(
    league_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Add an admin to the league"""
    
    league = await db.private_leagues.find_one(
        {"id": league_id, "is_active": True},
        {"_id": 0}
    )
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Only creator can add admins
    if league.get("created_by") != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can add admins")
    
    if user_id not in league.get("member_ids", []):
        raise HTTPException(status_code=400, detail="User must be a member first")
    
    if user_id in league.get("admin_ids", []):
        raise HTTPException(status_code=400, detail="User is already an admin")
    
    await db.private_leagues.update_one(
        {"id": league_id},
        {"$push": {"admin_ids": user_id}}
    )
    
    return {"message": "Admin added successfully"}

# ==================== STATS UPDATE (called by prediction routes) ====================

async def update_league_member_stats(user_id: str, is_correct: bool):
    """Update stats for a user across all their leagues"""
    
    # Find all leagues user is in
    leagues = await db.private_leagues.find(
        {"member_ids": user_id, "is_active": True},
        {"_id": 0, "id": 1}
    ).to_list(50)
    
    for league in leagues:
        # Update member stats
        inc_fields = {"total_predictions": 1}
        if is_correct:
            inc_fields["correct_predictions"] = 1
            inc_fields["streak"] = 1
        
        member = await db.league_members.find_one({
            "league_id": league["id"],
            "user_id": user_id
        })
        
        if member:
            new_total = member.get("total_predictions", 0) + 1
            new_correct = member.get("correct_predictions", 0) + (1 if is_correct else 0)
            new_accuracy = round((new_correct / new_total) * 100, 1) if new_total > 0 else 0
            
            new_streak = member.get("streak", 0) + 1 if is_correct else 0
            best_streak = max(member.get("best_streak", 0), new_streak)
            
            await db.league_members.update_one(
                {"league_id": league["id"], "user_id": user_id},
                {
                    "$inc": {"total_predictions": 1, "correct_predictions": 1 if is_correct else 0},
                    "$set": {
                        "accuracy": new_accuracy,
                        "streak": new_streak,
                        "best_streak": best_streak
                    }
                }
            )
