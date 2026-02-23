"""
Leaderboards Routes for FREE11
Global, Weekly, and Clan leaderboards - all SKILL-BASED
NO coin totals displayed - only accuracy, streaks, predictions
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

# Import from server.py
from server import db, get_current_user, User, USER_RANKS

leaderboards_router = APIRouter(prefix="/leaderboards", tags=["Leaderboards"])

# ==================== MODELS ====================

class Duel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    challenger_id: str
    challenged_id: str
    challenger_name: str
    challenged_name: str
    match_id: Optional[str] = None  # Specific match or general
    status: str = "pending"  # pending, accepted, active, completed, declined, expired
    # Skill tracking - NO coins
    challenger_predictions: int = 0
    challenged_predictions: int = 0
    challenger_correct: int = 0
    challenged_correct: int = 0
    winner_id: Optional[str] = None
    # Rewards - badges/recognition only, NO coins
    winner_badge: str = "duel_winner"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DuelCreate(BaseModel):
    challenged_id: str
    match_id: Optional[str] = None

# ==================== GLOBAL LEADERBOARD ====================

@leaderboards_router.get("/global")
async def get_global_leaderboard(limit: int = 50):
    """
    Global leaderboard ranked by SKILL (accuracy + streak)
    NO coin totals displayed
    """
    # Get users with prediction data
    pipeline = [
        {"$match": {"total_predictions": {"$gte": 5}}},  # Min 5 predictions to qualify
        {"$addFields": {
            "accuracy": {
                "$cond": {
                    "if": {"$gt": ["$total_predictions", 0]},
                    "then": {"$multiply": [{"$divide": ["$correct_predictions", "$total_predictions"]}, 100]},
                    "else": 0
                }
            }
        }},
        {"$sort": {"accuracy": -1, "prediction_streak": -1, "correct_predictions": -1}},
        {"$limit": limit},
        {"$project": {
            "_id": 0,
            "id": 1,
            "name": 1,
            "level": 1,
            "accuracy": 1,
            "total_predictions": 1,
            "correct_predictions": 1,
            "prediction_streak": 1
            # NO coins_balance exposed
        }}
    ]
    
    users = await db.users.aggregate(pipeline).to_list(limit)
    
    result = []
    for i, user in enumerate(users):
        level = user.get("level", 1)
        rank_info = USER_RANKS.get(level, USER_RANKS[1])
        result.append({
            "rank": i + 1,
            "id": user["id"],
            "name": user.get("name", "Anonymous"),
            "level": level,
            "rank_name": rank_info["name"],
            "rank_color": rank_info["color"],
            "accuracy": round(user.get("accuracy", 0), 1),
            "total_predictions": user.get("total_predictions", 0),
            "correct_predictions": user.get("correct_predictions", 0),
            "streak": user.get("prediction_streak", 0)
        })
    
    return {
        "leaderboard": result,
        "metric": "Skill (Accuracy + Streak)",
        "min_predictions": 5
    }

@leaderboards_router.get("/weekly")
async def get_weekly_leaderboard(limit: int = 50):
    """
    Weekly leaderboard - resets every Monday
    Tracks predictions made in the current week only
    """
    # Calculate start of current week (Monday)
    now = datetime.now(timezone.utc)
    days_since_monday = now.weekday()
    week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    week_start_iso = week_start.isoformat()
    
    # Aggregate ball predictions from this week
    pipeline = [
        {"$match": {"predicted_at": {"$gte": week_start_iso}}},
        {"$group": {
            "_id": "$user_id",
            "total_predictions": {"$sum": 1},
            "correct_predictions": {"$sum": {"$cond": ["$is_correct", 1, 0]}}
        }},
        {"$match": {"total_predictions": {"$gte": 3}}},  # Min 3 predictions this week
        {"$addFields": {
            "accuracy": {"$multiply": [{"$divide": ["$correct_predictions", "$total_predictions"]}, 100]}
        }},
        {"$sort": {"accuracy": -1, "correct_predictions": -1}},
        {"$limit": limit}
    ]
    
    weekly_data = await db.ball_predictions.aggregate(pipeline).to_list(limit)
    
    result = []
    for i, entry in enumerate(weekly_data):
        user = await db.users.find_one(
            {"id": entry["_id"]},
            {"_id": 0, "name": 1, "level": 1}
        )
        if user:
            level = user.get("level", 1)
            rank_info = USER_RANKS.get(level, USER_RANKS[1])
            result.append({
                "rank": i + 1,
                "id": entry["_id"],
                "name": user.get("name", "Anonymous"),
                "level": level,
                "rank_name": rank_info["name"],
                "accuracy": round(entry.get("accuracy", 0), 1),
                "predictions_this_week": entry.get("total_predictions", 0),
                "correct_this_week": entry.get("correct_predictions", 0)
            })
    
    return {
        "leaderboard": result,
        "week_start": week_start_iso,
        "metric": "Weekly Accuracy",
        "min_predictions": 3
    }

@leaderboards_router.get("/streak")
async def get_streak_leaderboard(limit: int = 50):
    """
    Streak leaderboard - who has the longest prediction streak
    """
    users = await db.users.find(
        {"prediction_streak": {"$gt": 0}},
        {"_id": 0, "id": 1, "name": 1, "level": 1, "prediction_streak": 1}
    ).sort("prediction_streak", -1).limit(limit).to_list(limit)
    
    result = []
    for i, user in enumerate(users):
        level = user.get("level", 1)
        rank_info = USER_RANKS.get(level, USER_RANKS[1])
        result.append({
            "rank": i + 1,
            "id": user["id"],
            "name": user.get("name", "Anonymous"),
            "level": level,
            "rank_name": rank_info["name"],
            "streak": user.get("prediction_streak", 0)
        })
    
    return {
        "leaderboard": result,
        "metric": "Prediction Streak"
    }

# ==================== USER PUBLIC PROFILE ====================

@leaderboards_router.get("/profile/{user_id}")
async def get_public_profile(user_id: str):
    """
    Get public profile of a user - SKILL stats only
    NO coin balance exposed
    """
    user = await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "password_hash": 0, "email": 0, "coins_balance": 0, "total_earned": 0, "total_redeemed": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get clan membership
    membership = await db.clan_members.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    clan = None
    if membership:
        clan = await db.clans.find_one(
            {"id": membership["clan_id"]},
            {"_id": 0, "name": 1, "tag": 1, "logo_emoji": 1}
        )
    
    # Calculate accuracy
    total_predictions = user.get("total_predictions", 0)
    correct_predictions = user.get("correct_predictions", 0)
    accuracy = round((correct_predictions / total_predictions * 100), 1) if total_predictions > 0 else 0
    
    level = user.get("level", 1)
    rank_info = USER_RANKS.get(level, USER_RANKS[1])
    
    # Get badges
    badges = user.get("badges", [])
    
    # Get duel stats
    duels_won = await db.duels.count_documents({"winner_id": user_id})
    duels_played = await db.duels.count_documents({
        "$or": [{"challenger_id": user_id}, {"challenged_id": user_id}],
        "status": "completed"
    })
    
    return {
        "id": user["id"],
        "name": user.get("name", "Anonymous"),
        "level": level,
        "rank": {
            "name": rank_info["name"],
            "color": rank_info["color"]
        },
        "skill_stats": {
            "accuracy": accuracy,
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions,
            "current_streak": user.get("prediction_streak", 0)
        },
        "badges": badges,
        "clan": {
            "name": clan["name"],
            "tag": clan["tag"],
            "logo": clan.get("logo_emoji", "🏏")
        } if clan else None,
        "duel_stats": {
            "won": duels_won,
            "played": duels_played,
            "win_rate": round((duels_won / duels_played * 100), 1) if duels_played > 0 else 0
        },
        "member_since": user.get("created_at", "")
    }

# ==================== DUELS (SKILL-BASED, NO COINS) ====================

@leaderboards_router.get("/duels/my")
async def get_my_duels(current_user: User = Depends(get_current_user)):
    """Get user's duels - pending, active, and recent completed"""
    duels = await db.duels.find(
        {"$or": [
            {"challenger_id": current_user.id},
            {"challenged_id": current_user.id}
        ]},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    # Categorize
    pending = [d for d in duels if d["status"] == "pending"]
    active = [d for d in duels if d["status"] == "active"]
    completed = [d for d in duels if d["status"] == "completed"]
    
    # Stats
    total_won = await db.duels.count_documents({"winner_id": current_user.id})
    total_played = await db.duels.count_documents({
        "$or": [{"challenger_id": current_user.id}, {"challenged_id": current_user.id}],
        "status": "completed"
    })
    
    return {
        "pending": pending,
        "active": active,
        "completed": completed[:5],
        "stats": {
            "won": total_won,
            "played": total_played,
            "win_rate": round((total_won / total_played * 100), 1) if total_played > 0 else 0
        }
    }

@leaderboards_router.post("/duels/challenge")
async def create_duel(
    duel_data: DuelCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Challenge another user to a prediction duel
    Winner gets badge/recognition - NO coins involved
    """
    # Can't duel yourself
    if duel_data.challenged_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't challenge yourself!")
    
    # Check challenged user exists
    challenged_user = await db.users.find_one(
        {"id": duel_data.challenged_id},
        {"_id": 0, "name": 1}
    )
    if not challenged_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for existing pending/active duel between these users
    existing = await db.duels.find_one({
        "$or": [
            {"challenger_id": current_user.id, "challenged_id": duel_data.challenged_id},
            {"challenger_id": duel_data.challenged_id, "challenged_id": current_user.id}
        ],
        "status": {"$in": ["pending", "active"]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active duel with this user")
    
    # Create duel
    duel = Duel(
        challenger_id=current_user.id,
        challenged_id=duel_data.challenged_id,
        challenger_name=current_user.name,
        challenged_name=challenged_user.get("name", "Unknown"),
        match_id=duel_data.match_id
    )
    await db.duels.insert_one(duel.model_dump())
    
    return {
        "message": f"Duel challenge sent to {challenged_user.get('name')}!",
        "duel_id": duel.id,
        "note": "Winner earns the Duel Winner badge - no coins at stake!"
    }

@leaderboards_router.post("/duels/{duel_id}/accept")
async def accept_duel(
    duel_id: str,
    current_user: User = Depends(get_current_user)
):
    """Accept a duel challenge"""
    duel = await db.duels.find_one({"id": duel_id})
    if not duel:
        raise HTTPException(status_code=404, detail="Duel not found")
    
    if duel["challenged_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="This duel wasn't sent to you")
    
    if duel["status"] != "pending":
        raise HTTPException(status_code=400, detail="Duel is no longer pending")
    
    # Activate duel
    now = datetime.now(timezone.utc)
    await db.duels.update_one(
        {"id": duel_id},
        {"$set": {
            "status": "active",
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(hours=24)).isoformat()  # 24 hour duel
        }}
    )
    
    return {
        "message": "Duel accepted! You have 24 hours to out-predict your opponent.",
        "note": "Make predictions on any match - highest accuracy wins!"
    }

@leaderboards_router.post("/duels/{duel_id}/decline")
async def decline_duel(
    duel_id: str,
    current_user: User = Depends(get_current_user)
):
    """Decline a duel challenge"""
    duel = await db.duels.find_one({"id": duel_id})
    if not duel:
        raise HTTPException(status_code=404, detail="Duel not found")
    
    if duel["challenged_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="This duel wasn't sent to you")
    
    if duel["status"] != "pending":
        raise HTTPException(status_code=400, detail="Duel is no longer pending")
    
    await db.duels.update_one(
        {"id": duel_id},
        {"$set": {"status": "declined"}}
    )
    
    return {"message": "Duel declined"}

# ==================== ACTIVITY FEED ====================

@leaderboards_router.get("/activity-feed")
async def get_activity_feed(current_user: User = Depends(get_current_user), limit: int = 20):
    """
    Get activity feed - clan achievements, duel results, badge unlocks
    NO coin-related activities
    """
    # Get user's clan for clan-specific feed
    membership = await db.clan_members.find_one({"user_id": current_user.id})
    
    activities = []
    
    # Recent duel completions
    recent_duels = await db.duels.find(
        {"status": "completed"},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    for duel in recent_duels:
        activities.append({
            "type": "duel_completed",
            "title": f"{duel['challenger_name']} vs {duel['challenged_name']}",
            "description": f"Winner: {duel['challenger_name'] if duel['winner_id'] == duel['challenger_id'] else duel['challenged_name']}",
            "timestamp": duel.get("created_at", "")
        })
    
    # Clan achievements if user is in a clan
    if membership:
        clan = await db.clans.find_one({"id": membership["clan_id"]}, {"_id": 0})
        if clan:
            activities.append({
                "type": "clan_stats",
                "title": f"[{clan['tag']}] Clan Update",
                "description": f"Accuracy: {clan.get('clan_accuracy', 0)}% | Streak: {clan.get('clan_streak', 0)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {"activities": activities[:limit]}

# ==================== HELPER FUNCTION ====================

async def update_duel_on_prediction(user_id: str, is_correct: bool):
    """
    Called after a prediction to update active duels
    Should be called from cricket_routes.py
    """
    # Find active duels for this user
    active_duels = await db.duels.find({
        "$or": [
            {"challenger_id": user_id},
            {"challenged_id": user_id}
        ],
        "status": "active"
    }).to_list(10)
    
    for duel in active_duels:
        update_field = "challenger_predictions" if duel["challenger_id"] == user_id else "challenged_predictions"
        correct_field = "challenger_correct" if duel["challenger_id"] == user_id else "challenged_correct"
        
        update = {"$inc": {update_field: 1}}
        if is_correct:
            update["$inc"][correct_field] = 1
        
        await db.duels.update_one({"id": duel["id"]}, update)
        
        # Check if duel ended (time-based)
        if duel.get("end_time"):
            end_time = datetime.fromisoformat(duel["end_time"])
            if datetime.now(timezone.utc) > end_time:
                await complete_duel(duel["id"])

async def complete_duel(duel_id: str):
    """Complete a duel and determine winner based on accuracy"""
    duel = await db.duels.find_one({"id": duel_id})
    if not duel or duel["status"] != "active":
        return
    
    # Calculate accuracies
    c1_acc = (duel["challenger_correct"] / duel["challenger_predictions"] * 100) if duel["challenger_predictions"] > 0 else 0
    c2_acc = (duel["challenged_correct"] / duel["challenged_predictions"] * 100) if duel["challenged_predictions"] > 0 else 0
    
    # Determine winner (higher accuracy wins, tie goes to more predictions)
    if c1_acc > c2_acc:
        winner_id = duel["challenger_id"]
    elif c2_acc > c1_acc:
        winner_id = duel["challenged_id"]
    elif duel["challenger_predictions"] > duel["challenged_predictions"]:
        winner_id = duel["challenger_id"]
    else:
        winner_id = duel["challenged_id"]
    
    await db.duels.update_one(
        {"id": duel_id},
        {"$set": {"status": "completed", "winner_id": winner_id}}
    )
    
    # Award badge to winner (check if not already earned)
    user = await db.users.find_one({"id": winner_id})
    if user and "duel_winner" not in user.get("badges", []):
        await db.users.update_one(
            {"id": winner_id},
            {"$push": {"badges": "duel_winner"}}
        )
