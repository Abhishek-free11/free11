"""
Fantasy Team Contests for FREE11
Dream11-style player selection and scoring
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import uuid
import random

# Import from server.py
from server import db, get_current_user, add_coins, User

fantasy_router = APIRouter(prefix="/fantasy", tags=["Fantasy"])

# ==================== CONSTANTS ====================

# Fantasy Points System (Dream11-style)
FANTASY_POINTS = {
    "batting": {
        "run": 1,
        "boundary_4": 1,  # Bonus for 4
        "boundary_6": 2,  # Bonus for 6
        "half_century": 8,
        "century": 16,
        "duck": -2,  # For batsman only
        "strike_rate_bonus": {  # Min 10 balls
            "170+": 6,
            "150-170": 4,
            "130-150": 2,
            "60-70": -2,
            "50-60": -4,
            "<50": -6
        }
    },
    "bowling": {
        "wicket": 25,
        "bonus_3w": 4,  # 3 wicket bonus
        "bonus_4w": 8,  # 4 wicket bonus
        "bonus_5w": 16,  # 5 wicket bonus
        "maiden": 12,
        "economy_bonus": {  # Min 2 overs
            "<5": 6,
            "5-6": 4,
            "6-7": 2,
            "10-11": -2,
            "11-12": -4,
            ">12": -6
        }
    },
    "fielding": {
        "catch": 8,
        "stumping": 12,
        "run_out_direct": 12,
        "run_out_indirect": 6
    },
    "captain_multiplier": 2,
    "vice_captain_multiplier": 1.5
}

# Max team constraints
MAX_PLAYERS_PER_TEAM = 11
MAX_FROM_ONE_TEAM = 7
MIN_FROM_ONE_TEAM = 4
CREDIT_LIMIT = 100

# ==================== MODELS ====================

class Player(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    team: str
    team_short: str
    role: str  # BAT, BOWL, ALL, WK
    credits: float  # 7.0 - 11.0
    image_url: Optional[str] = None
    is_playing: bool = True
    stats: Dict = Field(default_factory=dict)

class FantasyTeam(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    match_id: str
    contest_id: str
    players: List[str]  # List of player IDs
    captain_id: str
    vice_captain_id: str
    total_credits: float
    points: float = 0
    rank: Optional[int] = None
    coins_won: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Contest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    name: str
    contest_type: str  # mega, head_to_head, practice, private_league
    entry_coins: int = 0  # Always 0 for FREE11 (no buy-ins)
    prize_pool_coins: int
    max_entries: int
    current_entries: int = 0
    prize_distribution: List[Dict]  # [{rank: 1, coins: 500}, ...]
    status: str = "upcoming"  # upcoming, live, completed
    is_private: bool = False
    private_code: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Request Models
class CreateTeamRequest(BaseModel):
    match_id: str
    contest_id: str
    player_ids: List[str]
    captain_id: str
    vice_captain_id: str

class CreateContestRequest(BaseModel):
    match_id: str
    name: str
    max_entries: int = 10
    is_private: bool = True

class JoinContestRequest(BaseModel):
    contest_id: str
    team_id: str

# ==================== MOCK PLAYERS DATA ====================

def generate_mock_players(team1_short: str, team2_short: str):
    """Generate mock players for a match"""
    
    team_players = {
        "CSK": [
            {"name": "MS Dhoni", "role": "WK", "credits": 9.5},
            {"name": "Ruturaj Gaikwad", "role": "BAT", "credits": 9.0},
            {"name": "Devon Conway", "role": "BAT", "credits": 8.5},
            {"name": "Shivam Dube", "role": "ALL", "credits": 8.5},
            {"name": "Ravindra Jadeja", "role": "ALL", "credits": 9.0},
            {"name": "Moeen Ali", "role": "ALL", "credits": 8.0},
            {"name": "Deepak Chahar", "role": "BOWL", "credits": 8.0},
            {"name": "Tushar Deshpande", "role": "BOWL", "credits": 7.5},
            {"name": "Matheesha Pathirana", "role": "BOWL", "credits": 8.0},
            {"name": "Maheesh Theekshana", "role": "BOWL", "credits": 7.5},
            {"name": "Ajinkya Rahane", "role": "BAT", "credits": 7.0},
        ],
        "MI": [
            {"name": "Rohit Sharma", "role": "BAT", "credits": 10.0},
            {"name": "Ishan Kishan", "role": "WK", "credits": 9.0},
            {"name": "Suryakumar Yadav", "role": "BAT", "credits": 9.5},
            {"name": "Tilak Varma", "role": "BAT", "credits": 8.5},
            {"name": "Hardik Pandya", "role": "ALL", "credits": 9.5},
            {"name": "Tim David", "role": "BAT", "credits": 8.0},
            {"name": "Jasprit Bumrah", "role": "BOWL", "credits": 9.5},
            {"name": "Piyush Chawla", "role": "BOWL", "credits": 7.5},
            {"name": "Akash Madhwal", "role": "BOWL", "credits": 7.0},
            {"name": "Gerald Coetzee", "role": "BOWL", "credits": 8.0},
            {"name": "Naman Dhir", "role": "ALL", "credits": 7.0},
        ],
        "RCB": [
            {"name": "Virat Kohli", "role": "BAT", "credits": 10.5},
            {"name": "Faf du Plessis", "role": "BAT", "credits": 9.5},
            {"name": "Glenn Maxwell", "role": "ALL", "credits": 9.0},
            {"name": "Dinesh Karthik", "role": "WK", "credits": 8.0},
            {"name": "Cameron Green", "role": "ALL", "credits": 9.0},
            {"name": "Rajat Patidar", "role": "BAT", "credits": 8.0},
            {"name": "Wanindu Hasaranga", "role": "ALL", "credits": 8.5},
            {"name": "Mohammed Siraj", "role": "BOWL", "credits": 8.5},
            {"name": "Harshal Patel", "role": "BOWL", "credits": 8.0},
            {"name": "Josh Hazlewood", "role": "BOWL", "credits": 8.5},
            {"name": "Reece Topley", "role": "BOWL", "credits": 7.5},
        ],
        "KKR": [
            {"name": "Shreyas Iyer", "role": "BAT", "credits": 9.5},
            {"name": "Venkatesh Iyer", "role": "ALL", "credits": 8.5},
            {"name": "Andre Russell", "role": "ALL", "credits": 9.5},
            {"name": "Sunil Narine", "role": "ALL", "credits": 9.0},
            {"name": "Rinku Singh", "role": "BAT", "credits": 8.5},
            {"name": "Phil Salt", "role": "WK", "credits": 9.0},
            {"name": "Nitish Rana", "role": "BAT", "credits": 8.0},
            {"name": "Mitchell Starc", "role": "BOWL", "credits": 9.0},
            {"name": "Varun Chakravarthy", "role": "BOWL", "credits": 8.0},
            {"name": "Harshit Rana", "role": "BOWL", "credits": 7.5},
            {"name": "Ramandeep Singh", "role": "ALL", "credits": 7.0},
        ]
    }
    
    # Get players for both teams or use CSK/MI as default
    team1_players = team_players.get(team1_short, team_players["CSK"])
    team2_players = team_players.get(team2_short, team_players["MI"])
    
    players = []
    for p in team1_players:
        players.append(Player(
            name=p["name"],
            team=team1_short,
            team_short=team1_short,
            role=p["role"],
            credits=p["credits"]
        ))
    for p in team2_players:
        players.append(Player(
            name=p["name"],
            team=team2_short,
            team_short=team2_short,
            role=p["role"],
            credits=p["credits"]
        ))
    
    return players

# ==================== ROUTES ====================

@fantasy_router.get("/matches/{match_id}/players")
async def get_match_players(match_id: str):
    """Get all players available for a match"""
    
    # Check if players exist in DB
    players = await db.fantasy_players.find({"match_id": match_id}, {"_id": 0}).to_list(30)
    
    if not players:
        # Get match details to determine teams
        match = await db.cricket_matches.find_one({"match_id": match_id}, {"_id": 0})
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Generate mock players
        team1_short = match.get("team1_short", "CSK")
        team2_short = match.get("team2_short", "MI")
        mock_players = generate_mock_players(team1_short, team2_short)
        
        # Store in DB
        for player in mock_players:
            player_dict = player.model_dump()
            player_dict["match_id"] = match_id
            await db.fantasy_players.insert_one(player_dict)
        
        players = await db.fantasy_players.find({"match_id": match_id}, {"_id": 0}).to_list(30)
    
    # Group by role
    by_role = {"WK": [], "BAT": [], "ALL": [], "BOWL": []}
    for p in players:
        role = p.get("role", "BAT")
        if role in by_role:
            by_role[role].append(p)
    
    return {
        "match_id": match_id,
        "players": players,
        "by_role": by_role,
        "constraints": {
            "max_players": MAX_PLAYERS_PER_TEAM,
            "max_from_one_team": MAX_FROM_ONE_TEAM,
            "min_from_one_team": MIN_FROM_ONE_TEAM,
            "credit_limit": CREDIT_LIMIT,
            "min_wk": 1, "max_wk": 4,
            "min_bat": 3, "max_bat": 6,
            "min_all": 1, "max_all": 4,
            "min_bowl": 3, "max_bowl": 6
        }
    }

@fantasy_router.get("/matches/{match_id}/contests")
async def get_match_contests(match_id: str):
    """Get all contests for a match"""
    
    contests = await db.fantasy_contests.find(
        {"match_id": match_id, "is_private": False},
        {"_id": 0}
    ).to_list(50)
    
    # Seed default contests if none exist
    if not contests:
        default_contests = [
            {
                "match_id": match_id,
                "name": "Mega Contest",
                "contest_type": "mega",
                "entry_coins": 0,
                "prize_pool_coins": 1000,
                "max_entries": 100,
                "current_entries": 0,
                "prize_distribution": [
                    {"rank": 1, "coins": 300},
                    {"rank": 2, "coins": 200},
                    {"rank": 3, "coins": 150},
                    {"rank_start": 4, "rank_end": 10, "coins": 50}
                ],
                "status": "upcoming",
                "is_private": False
            },
            {
                "match_id": match_id,
                "name": "Head to Head",
                "contest_type": "head_to_head",
                "entry_coins": 0,
                "prize_pool_coins": 100,
                "max_entries": 2,
                "current_entries": 0,
                "prize_distribution": [
                    {"rank": 1, "coins": 100}
                ],
                "status": "upcoming",
                "is_private": False
            },
            {
                "match_id": match_id,
                "name": "Practice Contest",
                "contest_type": "practice",
                "entry_coins": 0,
                "prize_pool_coins": 50,
                "max_entries": 1000,
                "current_entries": 0,
                "prize_distribution": [
                    {"rank_start": 1, "rank_end": 100, "coins": 0}  # No prizes, just practice
                ],
                "status": "upcoming",
                "is_private": False
            }
        ]
        
        for contest_data in default_contests:
            contest = Contest(**contest_data)
            await db.fantasy_contests.insert_one(contest.model_dump())
        
        contests = await db.fantasy_contests.find(
            {"match_id": match_id, "is_private": False},
            {"_id": 0}
        ).to_list(50)
    
    return {
        "match_id": match_id,
        "contests": contests,
        "total": len(contests)
    }

@fantasy_router.post("/teams/create")
async def create_fantasy_team(
    request: CreateTeamRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a fantasy team for a contest"""
    
    # Validate player count
    if len(request.player_ids) != MAX_PLAYERS_PER_TEAM:
        raise HTTPException(
            status_code=400, 
            detail=f"Team must have exactly {MAX_PLAYERS_PER_TEAM} players"
        )
    
    # Validate captain and vice-captain
    if request.captain_id not in request.player_ids:
        raise HTTPException(status_code=400, detail="Captain must be in the team")
    if request.vice_captain_id not in request.player_ids:
        raise HTTPException(status_code=400, detail="Vice-captain must be in the team")
    if request.captain_id == request.vice_captain_id:
        raise HTTPException(status_code=400, detail="Captain and vice-captain must be different")
    
    # Get players and validate
    players = await db.fantasy_players.find(
        {"id": {"$in": request.player_ids}, "match_id": request.match_id},
        {"_id": 0}
    ).to_list(15)
    
    if len(players) != MAX_PLAYERS_PER_TEAM:
        raise HTTPException(status_code=400, detail="Some players not found or invalid")
    
    # Validate credits
    total_credits = sum(p["credits"] for p in players)
    if total_credits > CREDIT_LIMIT:
        raise HTTPException(
            status_code=400, 
            detail=f"Team exceeds credit limit. Total: {total_credits}, Limit: {CREDIT_LIMIT}"
        )
    
    # Validate team composition
    team_counts = {}
    role_counts = {"WK": 0, "BAT": 0, "ALL": 0, "BOWL": 0}
    
    for p in players:
        team = p["team_short"]
        team_counts[team] = team_counts.get(team, 0) + 1
        role_counts[p["role"]] = role_counts.get(p["role"], 0) + 1
    
    # Check max from one team
    for team, count in team_counts.items():
        if count > MAX_FROM_ONE_TEAM:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum {MAX_FROM_ONE_TEAM} players allowed from one team"
            )
    
    # Check role constraints
    if role_counts["WK"] < 1 or role_counts["WK"] > 4:
        raise HTTPException(status_code=400, detail="Team must have 1-4 wicket-keepers")
    if role_counts["BAT"] < 3 or role_counts["BAT"] > 6:
        raise HTTPException(status_code=400, detail="Team must have 3-6 batsmen")
    if role_counts["ALL"] < 1 or role_counts["ALL"] > 4:
        raise HTTPException(status_code=400, detail="Team must have 1-4 all-rounders")
    if role_counts["BOWL"] < 3 or role_counts["BOWL"] > 6:
        raise HTTPException(status_code=400, detail="Team must have 3-6 bowlers")
    
    # Check contest exists
    contest = await db.fantasy_contests.find_one({"id": request.contest_id}, {"_id": 0})
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    
    if contest["current_entries"] >= contest["max_entries"]:
        raise HTTPException(status_code=400, detail="Contest is full")
    
    # Check if user already has a team in this contest
    existing_team = await db.fantasy_teams.find_one({
        "user_id": current_user.id,
        "contest_id": request.contest_id
    })
    if existing_team:
        raise HTTPException(status_code=400, detail="You already have a team in this contest")
    
    # Create team
    team = FantasyTeam(
        user_id=current_user.id,
        match_id=request.match_id,
        contest_id=request.contest_id,
        players=request.player_ids,
        captain_id=request.captain_id,
        vice_captain_id=request.vice_captain_id,
        total_credits=total_credits
    )
    
    await db.fantasy_teams.insert_one(team.model_dump())
    
    # Update contest entry count
    await db.fantasy_contests.update_one(
        {"id": request.contest_id},
        {"$inc": {"current_entries": 1}}
    )
    
    return {
        "message": "Team created successfully!",
        "team": team.model_dump(),
        "total_credits": total_credits
    }

@fantasy_router.get("/teams/my")
async def get_my_teams(
    match_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get current user's fantasy teams"""
    
    query = {"user_id": current_user.id}
    if match_id:
        query["match_id"] = match_id
    
    teams = await db.fantasy_teams.find(query, {"_id": 0}).to_list(50)
    
    # Enrich with player details
    for team in teams:
        players = await db.fantasy_players.find(
            {"id": {"$in": team["players"]}},
            {"_id": 0}
        ).to_list(15)
        team["player_details"] = players
        
        # Get contest details
        contest = await db.fantasy_contests.find_one(
            {"id": team["contest_id"]},
            {"_id": 0}
        )
        team["contest"] = contest
    
    return {
        "teams": teams,
        "total": len(teams)
    }

@fantasy_router.get("/teams/{team_id}")
async def get_team_details(
    team_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific team"""
    
    team = await db.fantasy_teams.find_one(
        {"id": team_id, "user_id": current_user.id},
        {"_id": 0}
    )
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get player details
    players = await db.fantasy_players.find(
        {"id": {"$in": team["players"]}},
        {"_id": 0}
    ).to_list(15)
    
    # Get contest details
    contest = await db.fantasy_contests.find_one(
        {"id": team["contest_id"]},
        {"_id": 0}
    )
    
    return {
        "team": team,
        "players": players,
        "contest": contest,
        "captain": next((p for p in players if p["id"] == team["captain_id"]), None),
        "vice_captain": next((p for p in players if p["id"] == team["vice_captain_id"]), None)
    }

@fantasy_router.post("/contests/create")
async def create_private_contest(
    request: CreateContestRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a private league contest"""
    
    # Generate unique code
    import string
    private_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Calculate prize pool based on entries
    prize_pool = request.max_entries * 10  # 10 coins per entry slot
    
    contest = Contest(
        match_id=request.match_id,
        name=request.name,
        contest_type="private_league",
        entry_coins=0,
        prize_pool_coins=prize_pool,
        max_entries=min(request.max_entries, 100),  # Cap at 100
        prize_distribution=[
            {"rank": 1, "coins": int(prize_pool * 0.5)},
            {"rank": 2, "coins": int(prize_pool * 0.3)},
            {"rank": 3, "coins": int(prize_pool * 0.2)}
        ],
        is_private=True,
        private_code=private_code,
        created_by=current_user.id
    )
    
    await db.fantasy_contests.insert_one(contest.model_dump())
    
    return {
        "message": "Private contest created!",
        "contest": contest.model_dump(),
        "share_code": private_code,
        "share_message": f"Join my FREE11 contest! Use code: {private_code}"
    }

@fantasy_router.post("/contests/join")
async def join_contest_with_code(
    code: str,
    team_id: str,
    current_user: User = Depends(get_current_user)
):
    """Join a private contest using share code"""
    
    contest = await db.fantasy_contests.find_one(
        {"private_code": code.upper(), "is_private": True},
        {"_id": 0}
    )
    
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found. Check the code.")
    
    if contest["current_entries"] >= contest["max_entries"]:
        raise HTTPException(status_code=400, detail="Contest is full")
    
    # Check if user already joined
    existing = await db.fantasy_teams.find_one({
        "user_id": current_user.id,
        "contest_id": contest["id"]
    })
    if existing:
        raise HTTPException(status_code=400, detail="You're already in this contest")
    
    # Verify team belongs to user
    team = await db.fantasy_teams.find_one({
        "id": team_id,
        "user_id": current_user.id
    })
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Update team to this contest
    await db.fantasy_teams.update_one(
        {"id": team_id},
        {"$set": {"contest_id": contest["id"]}}
    )
    
    # Increment entries
    await db.fantasy_contests.update_one(
        {"id": contest["id"]},
        {"$inc": {"current_entries": 1}}
    )
    
    return {
        "message": f"Joined {contest['name']}!",
        "contest": contest
    }

@fantasy_router.get("/contests/{contest_id}/leaderboard")
async def get_contest_leaderboard(contest_id: str):
    """Get leaderboard for a contest"""
    
    contest = await db.fantasy_contests.find_one({"id": contest_id}, {"_id": 0})
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    
    # Get all teams in contest sorted by points
    teams = await db.fantasy_teams.find(
        {"contest_id": contest_id},
        {"_id": 0}
    ).sort("points", -1).to_list(100)
    
    # Enrich with user names
    leaderboard = []
    for rank, team in enumerate(teams, 1):
        user = await db.users.find_one({"id": team["user_id"]}, {"_id": 0, "name": 1})
        leaderboard.append({
            "rank": rank,
            "user_name": user.get("name", "Anonymous") if user else "Anonymous",
            "team_id": team["id"],
            "points": team["points"],
            "coins_won": team.get("coins_won", 0)
        })
    
    return {
        "contest": contest,
        "leaderboard": leaderboard,
        "total_entries": len(teams)
    }

@fantasy_router.get("/points-system")
async def get_points_system():
    """Get fantasy points system breakdown"""
    return FANTASY_POINTS
