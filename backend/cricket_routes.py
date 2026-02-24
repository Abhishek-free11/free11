"""
Cricket Routes for FREE11
Ball-by-ball predictions, Over predictions, Match predictions, and rewards
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import uuid
import random

# Import from server.py (will be connected via include_router)
from server import db, get_current_user, add_coins, User, Activity

cricket_router = APIRouter(prefix="/cricket", tags=["Cricket"])

# ==================== CONSTANTS ====================

# Ball-by-ball limit per match per user
BALL_PREDICTION_LIMIT_PER_MATCH = 20

# Over outcome options
OVER_OUTCOMES = ["0-5", "6-10", "11-15", "16+", "wicket_fall"]

# Coin rewards
REWARDS = {
    "ball_correct": 5,
    "ball_boundary": 10,  # 4 or 6
    "ball_wicket": 15,
    "over_correct": 25,
    "match_winner_correct": 50
}

# ==================== MODELS ====================

class Match(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str  # External API match ID
    team1: str
    team2: str
    team1_short: str
    team2_short: str
    team1_logo: str = ""
    team2_logo: str = ""
    venue: str
    match_type: str  # T20, ODI, Test
    series: str
    status: str  # upcoming, live, completed
    match_date: str
    team1_score: Optional[str] = None
    team2_score: Optional[str] = None
    current_ball: Optional[str] = None  # e.g., "14.3"
    current_over_balls: Optional[List[str]] = None  # ["1", "4", "0", "W", "2"]
    batting_team: Optional[str] = None
    toss_winner: Optional[str] = None
    toss_decision: Optional[str] = None
    winner: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BallPrediction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    match_id: str
    ball_number: str  # e.g., "14.3"
    prediction: str  # 0, 1, 2, 3, 4, 6, wicket, wide, no_ball, dot
    actual_result: Optional[str] = None
    is_correct: Optional[bool] = None
    coins_earned: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MatchPrediction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    match_id: str
    prediction_type: str  # winner, over_outcome, score_6_overs, score_10_overs, final_score, top_scorer, mom
    prediction_value: str
    over_number: Optional[int] = None  # For over outcome predictions
    actual_value: Optional[str] = None
    is_correct: Optional[bool] = None
    coins_earned: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Request models
class BallPredictionCreate(BaseModel):
    match_id: str
    ball_number: str
    prediction: str  # 0, 1, 2, 3, 4, 6, wicket, wide, no_ball, dot

class MatchPredictionCreate(BaseModel):
    match_id: str
    prediction_type: str
    prediction_value: str

class OverPredictionCreate(BaseModel):
    match_id: str
    over_number: int
    prediction: str  # 0-5, 6-10, 11-15, 16+, wicket_fall

class MatchWinnerPredictionCreate(BaseModel):
    match_id: str
    winner: str  # Team short code (CSK, MI, etc.)

# ==================== MOCK DATA ====================
# IPL 2026 Mock Matches for development

IPL_TEAMS = {
    "CSK": {"name": "Chennai Super Kings", "short": "CSK", "logo": "https://upload.wikimedia.org/wikipedia/en/2/2b/Chennai_Super_Kings_Logo.svg"},
    "MI": {"name": "Mumbai Indians", "short": "MI", "logo": "https://upload.wikimedia.org/wikipedia/en/c/cd/Mumbai_Indians_Logo.svg"},
    "RCB": {"name": "Royal Challengers Bangalore", "short": "RCB", "logo": "https://upload.wikimedia.org/wikipedia/en/2/2a/Royal_Challengers_Bangalore_2020.svg"},
    "KKR": {"name": "Kolkata Knight Riders", "short": "KKR", "logo": "https://upload.wikimedia.org/wikipedia/en/4/4c/Kolkata_Knight_Riders_Logo.svg"},
    "DC": {"name": "Delhi Capitals", "short": "DC", "logo": "https://upload.wikimedia.org/wikipedia/en/2/2f/Delhi_Capitals.svg"},
    "PBKS": {"name": "Punjab Kings", "short": "PBKS", "logo": "https://upload.wikimedia.org/wikipedia/en/d/d4/Punjab_Kings_Logo.svg"},
    "RR": {"name": "Rajasthan Royals", "short": "RR", "logo": "https://upload.wikimedia.org/wikipedia/en/6/60/Rajasthan_Royals_Logo.svg"},
    "SRH": {"name": "Sunrisers Hyderabad", "short": "SRH", "logo": "https://upload.wikimedia.org/wikipedia/en/8/81/Sunrisers_Hyderabad.svg"},
    "GT": {"name": "Gujarat Titans", "short": "GT", "logo": "https://upload.wikimedia.org/wikipedia/en/0/09/Gujarat_Titans_Logo.svg"},
    "LSG": {"name": "Lucknow Super Giants", "short": "LSG", "logo": "https://upload.wikimedia.org/wikipedia/en/0/0b/Lucknow_Super_Giants_Logo.svg"},
}

def generate_mock_matches():
    """Generate mock IPL 2026 matches for development"""
    matches = []
    base_date = datetime(2026, 3, 26, tzinfo=timezone.utc)  # IPL 2026 start
    
    # Match pairs for IPL 2026 opening week
    match_pairs = [
        ("CSK", "MI"),  # Opening match
        ("RCB", "KKR"),
        ("DC", "PBKS"),
        ("RR", "SRH"),
        ("GT", "LSG"),
        ("CSK", "RCB"),
        ("MI", "KKR"),
    ]
    
    venues = [
        "M.A. Chidambaram Stadium, Chennai",
        "Wankhede Stadium, Mumbai",
        "M. Chinnaswamy Stadium, Bangalore",
        "Eden Gardens, Kolkata",
        "Arun Jaitley Stadium, Delhi",
        "Narendra Modi Stadium, Ahmedabad",
    ]
    
    for i, (team1_key, team2_key) in enumerate(match_pairs):
        team1 = IPL_TEAMS[team1_key]
        team2 = IPL_TEAMS[team2_key]
        match_date = base_date + timedelta(days=i)
        
        # First match is "live" for demo, others upcoming
        status = "live" if i == 0 else "upcoming"
        
        match = {
            "id": f"ipl2026_{i+1:03d}",
            "match_id": f"ipl2026_{i+1:03d}",
            "team1": team1["name"],
            "team2": team2["name"],
            "team1_short": team1["short"],
            "team2_short": team2["short"],
            "team1_logo": team1["logo"],
            "team2_logo": team2["logo"],
            "venue": venues[i % len(venues)],
            "match_type": "T20",
            "series": "IPL 2026",
            "status": status,
            "match_date": match_date.isoformat(),
        }
        
        # Add live match details for the first match
        if status == "live":
            match.update({
                "team1_score": "156/4 (18.2)",
                "team2_score": None,
                "current_ball": "18.3",
                "current_over_balls": ["1", "4", ".", "W", "6", "2"],
                "batting_team": team1_key,
                "toss_winner": team1_key,
                "toss_decision": "bat",
            })
        
        matches.append(match)
    
    return matches

MOCK_MATCHES = generate_mock_matches()

# ==================== ROUTES ====================

@cricket_router.get("/matches")
async def get_matches(status: Optional[str] = None):
    """Get all matches, optionally filtered by status (live, upcoming, completed)"""
    # First check DB for matches
    query = {}
    if status:
        query["status"] = status
    
    matches = await db.cricket_matches.find(query, {"_id": 0}).to_list(100)
    
    # If no matches in DB, seed with mock data
    if not matches:
        for match_data in MOCK_MATCHES:
            match = Match(**match_data)
            existing = await db.cricket_matches.find_one({"match_id": match.match_id})
            if not existing:
                await db.cricket_matches.insert_one(match.model_dump())
        
        matches = await db.cricket_matches.find(query, {"_id": 0}).to_list(100)
    
    return matches

@cricket_router.get("/matches/live")
async def get_live_matches():
    """Get currently live matches"""
    matches = await db.cricket_matches.find({"status": "live"}, {"_id": 0}).to_list(20)
    return matches

@cricket_router.get("/matches/{match_id}")
async def get_match(match_id: str):
    """Get details of a specific match"""
    match = await db.cricket_matches.find_one({"match_id": match_id}, {"_id": 0})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

@cricket_router.post("/predict/ball")
async def predict_ball(
    prediction_data: BallPredictionCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Make a ball-by-ball prediction (LIMITED to 20 per match)
    Valid predictions: 0, 1, 2, 3, 4, 6, wicket, wide, no_ball, dot
    """
    valid_predictions = ['0', '1', '2', '3', '4', '6', 'wicket', 'wide', 'no_ball', 'dot']
    if prediction_data.prediction not in valid_predictions:
        raise HTTPException(status_code=400, detail=f"Invalid prediction. Must be one of: {valid_predictions}")
    
    # Check if match exists and is live
    match = await db.cricket_matches.find_one({"match_id": prediction_data.match_id}, {"_id": 0})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.get("status") != "live":
        raise HTTPException(status_code=400, detail="Can only predict on live matches")
    
    # Check ball prediction limit per match
    user_ball_count = await db.ball_predictions.count_documents({
        "user_id": current_user.id,
        "match_id": prediction_data.match_id
    })
    
    if user_ball_count >= BALL_PREDICTION_LIMIT_PER_MATCH:
        raise HTTPException(
            status_code=400, 
            detail=f"Ball prediction limit reached ({BALL_PREDICTION_LIMIT_PER_MATCH} per match). Try Over Outcome or Match Winner predictions!"
        )
    
    # Check if already predicted for this ball
    existing = await db.ball_predictions.find_one({
        "user_id": current_user.id,
        "match_id": prediction_data.match_id,
        "ball_number": prediction_data.ball_number
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already predicted for this ball")
    
    # Create prediction
    prediction = BallPrediction(
        user_id=current_user.id,
        match_id=prediction_data.match_id,
        ball_number=prediction_data.ball_number,
        prediction=prediction_data.prediction
    )
    await db.ball_predictions.insert_one(prediction.model_dump())
    
    # For demo: Simulate instant result (in production, this would be updated by live data feed)
    actual_outcomes = ['0', '1', '1', '2', '4', '6', '0', '1', 'wicket', '1', '2', '4']
    actual_result = random.choice(actual_outcomes)
    is_correct = prediction_data.prediction == actual_result
    
    coins_earned = 0
    if is_correct:
        # Base reward for correct prediction
        coins_earned = 5
        # Bonus for harder predictions
        if actual_result in ['6', 'wicket']:
            coins_earned = 15
        elif actual_result in ['4']:
            coins_earned = 10
        
        await add_coins(current_user.id, coins_earned, "earned", f"Correct ball prediction: {actual_result}")
    
    # Update prediction with result
    await db.ball_predictions.update_one(
        {"id": prediction.id},
        {"$set": {
            "actual_result": actual_result,
            "is_correct": is_correct,
            "coins_earned": coins_earned
        }}
    )
    
    # Record activity
    activity = Activity(
        user_id=current_user.id,
        activity_type="ball_prediction",
        coins_earned=coins_earned,
        details={
            "match_id": prediction_data.match_id,
            "ball": prediction_data.ball_number,
            "prediction": prediction_data.prediction,
            "actual": actual_result,
            "correct": is_correct
        }
    )
    await db.activities.insert_one(activity.model_dump())
    
    return {
        "prediction": prediction_data.prediction,
        "actual_result": actual_result,
        "is_correct": is_correct,
        "coins_earned": coins_earned,
        "new_balance": current_user.coins_balance + coins_earned,
        "message": f"Correct! +{coins_earned} coins!" if is_correct else f"Wrong! It was a {actual_result}"
    }

@cricket_router.post("/predict/match")
async def predict_match(
    prediction_data: MatchPredictionCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Make a match prediction (winner, scores, top scorer, MoM)
    """
    valid_types = ['winner', 'score_6_overs', 'score_10_overs', 'final_score', 'top_scorer', 'mom']
    if prediction_data.prediction_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid prediction type. Must be one of: {valid_types}")
    
    # Check if match exists
    match = await db.cricket_matches.find_one({"match_id": prediction_data.match_id}, {"_id": 0})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Check if already predicted this type for this match
    existing = await db.match_predictions.find_one({
        "user_id": current_user.id,
        "match_id": prediction_data.match_id,
        "prediction_type": prediction_data.prediction_type
    })
    if existing:
        raise HTTPException(status_code=400, detail=f"Already made a {prediction_data.prediction_type} prediction for this match")
    
    # Create prediction
    prediction = MatchPrediction(
        user_id=current_user.id,
        match_id=prediction_data.match_id,
        prediction_type=prediction_data.prediction_type,
        prediction_value=prediction_data.prediction_value
    )
    await db.match_predictions.insert_one(prediction.model_dump())
    
    return {
        "message": f"{prediction_data.prediction_type} prediction recorded",
        "prediction_type": prediction_data.prediction_type,
        "prediction_value": prediction_data.prediction_value,
        "match_id": prediction_data.match_id
    }

@cricket_router.get("/predictions/my")
async def get_my_predictions(
    match_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get current user's predictions"""
    query = {"user_id": current_user.id}
    if match_id:
        query["match_id"] = match_id
    
    ball_predictions = await db.ball_predictions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    match_predictions = await db.match_predictions.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    # Calculate stats
    total_ball_predictions = len(ball_predictions)
    correct_predictions = sum(1 for p in ball_predictions if p.get("is_correct"))
    total_coins_from_predictions = sum(p.get("coins_earned", 0) for p in ball_predictions)
    
    return {
        "ball_predictions": ball_predictions,
        "match_predictions": match_predictions,
        "stats": {
            "total_predictions": total_ball_predictions,
            "correct_predictions": correct_predictions,
            "accuracy": round((correct_predictions / total_ball_predictions * 100), 1) if total_ball_predictions > 0 else 0,
            "total_coins_earned": total_coins_from_predictions
        }
    }

@cricket_router.get("/leaderboard")
async def get_cricket_leaderboard():
    """Get cricket prediction leaderboard"""
    # Aggregate user stats from ball predictions
    pipeline = [
        {"$match": {"is_correct": True}},
        {"$group": {
            "_id": "$user_id",
            "correct_predictions": {"$sum": 1},
            "coins_earned": {"$sum": "$coins_earned"}
        }},
        {"$sort": {"correct_predictions": -1}},
        {"$limit": 20}
    ]
    
    leaderboard_data = await db.ball_predictions.aggregate(pipeline).to_list(20)
    
    # Enrich with user names
    result = []
    for i, entry in enumerate(leaderboard_data):
        user = await db.users.find_one({"id": entry["_id"]}, {"_id": 0, "name": 1})
        result.append({
            "rank": i + 1,
            "user_id": entry["_id"],
            "name": user.get("name", "Anonymous") if user else "Anonymous",
            "correct_predictions": entry["correct_predictions"],
            "coins_earned": entry["coins_earned"]
        })
    
    return result
