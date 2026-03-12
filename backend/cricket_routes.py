"""
Cricket Routes for FREE11
Ball-by-ball predictions with EntitySport integration and prediction lock
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import uuid
import time

# Import from server.py (will be connected via include_router)
from server import db, get_current_user, add_coins, User, Activity
from cricket_data_service import cricket_service

# EntitySport integration
try:
    from entitysport_service import (
        get_entitysport_service, 
        get_prediction_validator,
        EntitySportService,
        PredictionLockValidator
    )
    ENTITYSPORT_ENABLED = True
except ImportError:
    ENTITYSPORT_ENABLED = False

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
            "series": "T20 Season 2026",
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

@cricket_router.get("/live")
async def get_live_cricket_matches():
    """Get live matches from licensed Cricket APIs with HOT FAILOVER (NO MOCK DATA)"""
    try:
        matches = await cricket_service.get_live_matches()
        
        if not matches:
            return {
                "source": "no_data",
                "count": 0,
                "matches": [],
                "is_mock": False,
                "notice": "No live matches available right now. Check back during T20 Season 2026 (starts March 26)!"
            }
        
        source = matches[0].get('source', 'unknown') if matches else 'unknown'
        is_mock = False  # No more mock data
        is_stale = matches[0].get('is_stale', False) if matches else False
        stale_age = matches[0].get('stale_age_minutes', 0) if matches else 0
        failover_source = matches[0].get('failover_source', 'unknown') if matches else 'unknown'
        
        # Set appropriate notice based on data source
        notice = None
        if source == 'cached_stale':
            notice = f"⏳ Using cached data ({stale_age} min old) - Live API temporarily unavailable"
        # Silent failover - user doesn't need to know which API is serving
        
        return {
            "source": source,
            "count": len(matches),
            "matches": matches,
            "is_mock": is_mock,
            "is_stale": is_stale,
            "notice": notice
        }
    except Exception as e:
        return {
            "source": "error",
            "error": str(e),
            "matches": [],
            "is_mock": False,
            "notice": "Failed to fetch live data - please try again"
        }

@cricket_router.get("/api-status")
async def get_api_failover_status():
    """Get current API failover status (admin monitoring)"""
    return {
        "status": "ok",
        "failover_config": cricket_service.get_failover_status(),
        "cache_status": {
            "primary_cache": "/tmp/cricket_api_cache.json",
            "fallback_cache": "/tmp/cricket_fallback_cache.json",
            "health_file": "/tmp/cricket_api_health.json"
        },
        "failover_logic": [
            "1. Primary API (CricketData.org - subscribed)",
            "2. Sportmonks FREE tier (180 req/hr failover)",
            "3. Stale Cache (< 1 hour)",
            "4. NO MOCK DATA - Shows 'No matches' message"
        ]
    }

@cricket_router.get("/live/{match_id}/players")
async def get_match_players(match_id: str):
    """Get REAL players for a specific live match from CricketData API"""
    import httpx
    import os
    
    try:
        # First get the match details
        matches = await cricket_service.get_live_matches()
        match = next((m for m in matches if m.get('id') == match_id), None)
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        team1 = match.get('team1', 'Team A')
        team2 = match.get('team2', 'Team B')
        team1_short = match.get('team1_short', 'T1')
        team2_short = match.get('team2_short', 'T2')
        
        # Try to fetch REAL squad from CricketData API
        api_key = os.environ.get('CRICKET_API_KEY')
        players = []
        
        if api_key:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"https://api.cricapi.com/v1/match_squad",
                        params={"apikey": api_key, "id": match_id}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'success' and data.get('data'):
                            for team_data in data.get('data', []):
                                team_name = team_data.get('teamName', '')
                                # Determine which team this is
                                if team1.lower() in team_name.lower() or team_name.lower() in team1.lower():
                                    current_team = team1
                                    current_short = team1_short
                                else:
                                    current_team = team2
                                    current_short = team2_short
                                
                                for p in team_data.get('players', []):
                                    player_name = p.get('name', 'Unknown')
                                    # Determine role based on position or default
                                    role = determine_player_role(player_name, p)
                                    credits = calculate_player_credits(player_name, role)
                                    
                                    players.append({
                                        'name': player_name,
                                        'team': current_team,
                                        'team_short': current_short,
                                        'role': role,
                                        'credits': credits,
                                        'is_real': True
                                    })
            except Exception as e:
                print(f"Error fetching real squad: {e}")
        
        # If no real players found, fall back to generated ones
        if not players:
            players = generate_match_players(team1, team1_short, team2, team2_short)
            for p in players:
                p['is_real'] = False
        
        return {
            "match_id": match_id,
            "match_name": match.get('name'),
            "team1": team1,
            "team2": team2,
            "players": players,
            "is_real_squad": len(players) > 0 and players[0].get('is_real', False)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def determine_player_role(name: str, player_data: dict) -> str:
    """Determine player role based on name patterns or data"""
    name_lower = name.lower()
    
    # Known wicket-keepers
    wk_names = ['pant', 'rahul', 'dhoni', 'samson', 'kishan', 'karthik', 'saha', 'chakabva', 'madande', 'gumbie']
    if any(wk in name_lower for wk in wk_names):
        return 'WK'
    
    # Known bowlers
    bowl_names = ['bumrah', 'shami', 'siraj', 'chahal', 'ashwin', 'jadeja', 'kuldeep', 'arshdeep', 'muzarabani', 'ngarava', 'chatara', 'chakaravarthy', 'varun']
    if any(b in name_lower for b in bowl_names):
        return 'BOWL'
    
    # Known all-rounders
    all_names = ['pandya', 'jadeja', 'axar', 'raza', 'sikandar', 'williams', 'burl', 'jongwe', 'tilak', 'sundar']
    if any(a in name_lower for a in all_names):
        return 'ALL'
    
    # Default to batsman
    return 'BAT'


def calculate_player_credits(name: str, role: str) -> float:
    """Calculate fantasy credits based on player reputation"""
    name_lower = name.lower()
    
    # Star players get higher credits
    star_players = {
        'kohli': 10.5, 'rohit': 10.0, 'bumrah': 9.5, 'pant': 9.5,
        'rahul': 9.0, 'jadeja': 9.0, 'hardik': 9.5, 'siraj': 8.5,
        'raza': 9.5, 'sikandar': 9.5, 'muzarabani': 8.5, 'williams': 9.0,
        'arshdeep': 8.5, 'axar': 8.5, 'chakaravarthy': 8.5, 'varun': 8.5,
        'tilak': 8.5, 'varma': 8.5
    }
    
    for player, credits in star_players.items():
        if player in name_lower:
            return credits
    
    # Default credits by role
    role_defaults = {'WK': 8.0, 'BAT': 8.0, 'ALL': 8.0, 'BOWL': 7.5}
    return role_defaults.get(role, 7.5)

def generate_match_players(team1: str, team1_short: str, team2: str, team2_short: str):
    """Generate realistic player names based on team names"""
    import hashlib
    
    # Player pools by region/team type
    SA_PLAYERS = {
        'WK': [('Quinton de Kock', 9.5), ('Kyle Verreynne', 8.0), ('Heinrich Klaasen', 9.0), ('Ryan Rickelton', 7.5)],
        'BAT': [('Aiden Markram', 9.0), ('Temba Bavuma', 8.5), ('Rassie van der Dussen', 8.5), ('David Miller', 9.0), ('Reeza Hendricks', 8.0), ('Tony de Zorzi', 7.5)],
        'ALL': [('Marco Jansen', 8.5), ('Wiaan Mulder', 7.5), ('Andile Phehlukwayo', 7.0), ('Aiden Markram', 8.5)],
        'BOWL': [('Kagiso Rabada', 9.5), ('Anrich Nortje', 9.0), ('Lungi Ngidi', 8.5), ('Keshav Maharaj', 8.0), ('Tabraiz Shamsi', 8.0), ('Gerald Coetzee', 7.5)]
    }
    
    INDIA_PLAYERS = {
        'WK': [('Rishabh Pant', 9.5), ('KL Rahul', 9.0), ('Ishan Kishan', 8.0), ('Sanju Samson', 8.5)],
        'BAT': [('Virat Kohli', 10.5), ('Rohit Sharma', 10.0), ('Shubman Gill', 9.0), ('Shreyas Iyer', 8.5), ('Suryakumar Yadav', 9.5), ('Yashasvi Jaiswal', 8.5)],
        'ALL': [('Hardik Pandya', 9.5), ('Ravindra Jadeja', 9.0), ('Axar Patel', 8.0), ('Washington Sundar', 7.5)],
        'BOWL': [('Jasprit Bumrah', 10.0), ('Mohammed Siraj', 8.5), ('Mohammed Shami', 9.0), ('Kuldeep Yadav', 8.5), ('Ravichandran Ashwin', 8.5), ('Arshdeep Singh', 8.0)]
    }
    
    SL_PLAYERS = {
        'WK': [('Kusal Mendis', 8.5), ('Kusal Perera', 8.0), ('Niroshan Dickwella', 7.5), ('Dinesh Chandimal', 8.0)],
        'BAT': [('Pathum Nissanka', 8.5), ('Charith Asalanka', 8.0), ('Dimuth Karunaratne', 8.0), ('Angelo Mathews', 8.5), ('Dhananjaya de Silva', 8.0), ('Kamindu Mendis', 7.5)],
        'ALL': [('Wanindu Hasaranga', 9.0), ('Dasun Shanaka', 8.0), ('Dhananjaya de Silva', 8.0), ('Chamika Karunaratne', 7.0)],
        'BOWL': [('Matheesha Pathirana', 8.5), ('Maheesh Theekshana', 8.0), ('Dilshan Madushanka', 7.5), ('Dushmantha Chameera', 7.5), ('Dunith Wellalage', 7.0), ('Lahiru Kumara', 7.0)]
    }
    
    NZ_PLAYERS = {
        'WK': [('Tom Latham', 8.5), ('Devon Conway', 9.0), ('Glenn Phillips', 8.5), ('Cam Fletcher', 7.0)],
        'BAT': [('Kane Williamson', 10.0), ('Devon Conway', 9.0), ('Rachin Ravindra', 8.5), ('Will Young', 8.0), ('Daryl Mitchell', 8.5), ('Mark Chapman', 7.5)],
        'ALL': [('Daryl Mitchell', 8.5), ('Glenn Phillips', 8.5), ('Mitchell Santner', 8.0), ('Michael Bracewell', 7.5)],
        'BOWL': [('Trent Boult', 9.5), ('Tim Southee', 9.0), ('Matt Henry', 8.5), ('Lockie Ferguson', 9.0), ('Ish Sodhi', 7.5), ('Kyle Jamieson', 8.0)]
    }
    
    WI_PLAYERS = {
        'WK': [('Nicholas Pooran', 9.0), ('Shai Hope', 8.5), ('Joshua Da Silva', 7.5), ('Devon Thomas', 7.0)],
        'BAT': [('Shai Hope', 8.5), ('Brandon King', 8.0), ('Shimron Hetmyer', 8.5), ('Roston Chase', 8.0), ('Kyle Mayers', 8.0), ('Sherfane Rutherford', 7.5)],
        'ALL': [('Andre Russell', 9.5), ('Jason Holder', 8.5), ('Roston Chase', 8.0), ('Romario Shepherd', 7.5)],
        'BOWL': [('Alzarri Joseph', 8.5), ('Akeal Hosein', 8.0), ('Gudakesh Motie', 8.0), ('Jayden Seales', 7.5), ('Obed McCoy', 7.5), ('Shamar Joseph', 7.5)]
    }
    
    ZIMBABWE_PLAYERS = {
        'WK': [('Clive Madande', 8.0), ('Joylord Gumbie', 7.5), ('Regis Chakabva', 8.0), ('Tadiwanashe Marumani', 7.5)],
        'BAT': [('Craig Ervine', 8.5), ('Wessly Madhevere', 8.0), ('Dion Myers', 7.5), ('Brian Bennett', 7.0), ('Innocent Kaia', 7.5), ('Takudzwanashe Kaitano', 7.0)],
        'ALL': [('Sean Williams', 9.0), ('Sikandar Raza', 9.5), ('Ryan Burl', 8.0), ('Luke Jongwe', 7.5), ('Wellington Masakadza', 7.0), ('Milton Shumba', 7.5)],
        'BOWL': [('Blessing Muzarabani', 8.5), ('Tendai Chatara', 7.5), ('Richard Ngarava', 7.5), ('Victor Nyauchi', 7.0), ('Tanaka Chivanga', 7.0), ('Brandon Mavuta', 7.0)]
    }
    
    GENERIC_PLAYERS = {
        'WK': [('Player WK1', 8.0), ('Player WK2', 7.5), ('Player WK3', 7.0), ('Player WK4', 7.0)],
        'BAT': [('Player BAT1', 8.5), ('Player BAT2', 8.0), ('Player BAT3', 7.5), ('Player BAT4', 7.5), ('Player BAT5', 7.0), ('Player BAT6', 7.0)],
        'ALL': [('Player ALL1', 8.0), ('Player ALL2', 7.5), ('Player ALL3', 7.0), ('Player ALL4', 7.0)],
        'BOWL': [('Player BOWL1', 8.5), ('Player BOWL2', 8.0), ('Player BOWL3', 7.5), ('Player BOWL4', 7.5), ('Player BOWL5', 7.0), ('Player BOWL6', 7.0)]
    }
    
    def get_player_pool(team):
        team_lower = team.lower()
        short_lower = team_lower[:3] if len(team_lower) >= 3 else team_lower
        
        # South African teams
        if any(x in team_lower for x in ['south africa', 'cape', 'lions', 'titans', 'dolphins', 'warriors', 'knights', 'cobras', 'storm', 'rhinos', 'limpopo', 'border', 'districts', 'emerging']):
            return SA_PLAYERS
        # Indian teams  
        elif any(x in team_lower for x in ['india', 'karnataka', 'mumbai', 'chennai', 'kolkata', 'delhi', 'punjab', 'rajasthan', 'hyderabad', 'bengal', 'tamil', 'maharashtra', 'jammu', 'kashmir']):
            return INDIA_PLAYERS
        # Zimbabwe teams
        elif any(x in team_lower for x in ['zimbabwe', 'zim']):
            return ZIMBABWE_PLAYERS
        # Sri Lankan teams
        elif any(x in team_lower for x in ['sri lanka', 'lanka', 'colombo']):
            return SL_PLAYERS
        # New Zealand teams
        elif any(x in team_lower for x in ['new zealand', 'zealand', 'auckland', 'wellington', 'canterbury', 'otago']):
            return NZ_PLAYERS
        # West Indies teams
        elif any(x in team_lower for x in ['west indies', 'windies', 'barbados', 'jamaica', 'trinidad', 'guyana']):
            return WI_PLAYERS
        
        return GENERIC_PLAYERS
    
    def select_players_deterministic(pool, team_name, role, count):
        """Select players deterministically based on team name hash"""
        available = pool.get(role, [])
        if not available:
            return []
        
        # Use team name as seed for consistent selection
        seed = int(hashlib.md5(f"{team_name}_{role}".encode()).hexdigest()[:8], 16)
        
        # Rotate through available players based on seed
        selected = []
        for i in range(min(count, len(available))):
            idx = (seed + i) % len(available)
            selected.append(available[idx])
        return selected
    
    players = []
    player_id = 1
    
    for team, team_short in [(team1, team1_short), (team2, team2_short)]:
        pool = get_player_pool(team)
        
        # Select players for each role
        role_counts = {'WK': 2, 'BAT': 3, 'ALL': 2, 'BOWL': 3}
        
        for role, count in role_counts.items():
            selected = select_players_deterministic(pool, team, role, count)
            
            for name, base_credits in selected:
                players.append({
                    'id': f'player_{player_id}',
                    'name': name,
                    'team': team,
                    'team_short': team_short,
                    'role': role,
                    'credits': base_credits,
                    'points': int(base_credits * 8),
                    'selected_by': f"{(player_id * 7) % 50 + 10}%"
                })
                player_id += 1
    
    return players

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


# =============================================================================
# ENTITYSPORT BBB ENDPOINTS
# =============================================================================

@cricket_router.get("/entitysport/live")
async def get_entitysport_live_matches():
    """
    Get live matches from EntitySport API.
    Cache TTL: 5 seconds
    """
    if not ENTITYSPORT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="EntitySport integration not configured"
        )
    
    service = get_entitysport_service()
    matches = await service.get_live_matches()
    
    return {
        "source": "entitysport",
        "count": len(matches),
        "matches": matches,
        "is_mock": False
    }


@cricket_router.get("/entitysport/match/{match_id}/bbb")
async def get_entitysport_bbb(match_id: str, innings: int = None):
    """
    Get ball-by-ball data from EntitySport.
    Cache TTL: 2 seconds (critical for prediction integrity)
    """
    if not ENTITYSPORT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="EntitySport integration not configured"
        )
    
    service = get_entitysport_service()
    bbb_data = await service.get_ball_by_ball(match_id, innings)
    
    if not bbb_data:
        raise HTTPException(
            status_code=404,
            detail="Ball-by-ball data not available for this match"
        )
    
    return bbb_data


@cricket_router.get("/entitysport/match/{match_id}/playing-xi")
async def get_entitysport_playing_xi(match_id: str):
    """
    Get confirmed playing XI from EntitySport.
    Only available after toss is completed.
    """
    if not ENTITYSPORT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="EntitySport integration not configured"
        )
    
    service = get_entitysport_service()
    playing_xi = await service.get_confirmed_playing_xi(match_id)
    
    if not playing_xi:
        raise HTTPException(
            status_code=404,
            detail="Playing XI data not available"
        )
    
    return playing_xi


@cricket_router.get("/entitysport/match/{match_id}/prediction-window")
async def get_prediction_window(match_id: str):
    """
    Get current prediction window status.
    Shows which ball is open for predictions.
    """
    if not ENTITYSPORT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="EntitySport integration not configured"
        )
    
    validator = get_prediction_validator()
    window = await validator.get_next_ball_prediction_window(match_id)
    
    return window


# =============================================================================
# BALL PREDICTION WITH TIMESTAMP LOCK
# =============================================================================

class BallPredictionWithLock(BaseModel):
    """Ball prediction with server timestamp validation."""
    match_id: str
    innings: int = Field(ge=1, le=4)
    over: int = Field(ge=0, le=99)  # 0-99 for Test, 0-49 for ODI, 0-19 for T20
    ball: int = Field(ge=1, le=8)   # 1-8 (allows for extras like wides/noballs in same over)
    prediction: str  # '0', '1', '2', '3', '4', '6', 'wicket', 'wide', 'noball', 'dot'


@cricket_router.post("/predict/ball")
async def predict_ball(
    prediction_data: BallPredictionWithLock,
    current_user: User = Depends(get_current_user)
):
    """
    Ball-by-ball prediction with EntitySport timestamp lock.
    
    PREDICTION LOCK RULE:
        prediction_valid = server_timestamp < ball_event_timestamp
    
    Predictions submitted AFTER ball is bowled are REJECTED.
    """
    # Capture server timestamp immediately
    server_timestamp = int(time.time())
    
    if not ENTITYSPORT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ENTITYSPORT_NOT_CONFIGURED",
                "message": "Ball predictions require EntitySport API token",
                "alternatives": ["Over Outcome predictions", "Match Winner predictions"]
            }
        )
    
    # Get EntitySport service
    service = get_entitysport_service()
    validator = get_prediction_validator()
    
    # Check if match is live
    match_info = await service.get_match_info(prediction_data.match_id)
    if not match_info:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match_info.get("status") != 3:  # 3 = live in EntitySport
        raise HTTPException(
            status_code=400, 
            detail="Can only predict on live matches"
        )
    
    # Validate prediction outcomes
    valid_predictions = ['0', '1', '2', '3', '4', '6', 'wicket', 'wide', 'noball', 'dot']
    if prediction_data.prediction not in valid_predictions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid prediction. Must be one of: {valid_predictions}"
        )
    
    # Check ball prediction limit per match
    user_ball_count = await db.ball_predictions.count_documents({
        "user_id": current_user.id,
        "match_id": prediction_data.match_id
    })
    
    if user_ball_count >= BALL_PREDICTION_LIMIT_PER_MATCH:
        raise HTTPException(
            status_code=400, 
            detail=f"Ball prediction limit reached ({BALL_PREDICTION_LIMIT_PER_MATCH} per match)"
        )
    
    # Check if already predicted for this ball
    ball_key = f"{prediction_data.innings}_{prediction_data.over}_{prediction_data.ball}"
    existing = await db.ball_predictions.find_one({
        "user_id": current_user.id,
        "match_id": prediction_data.match_id,
        "ball_key": ball_key
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already predicted for this ball")
    
    # VALIDATE PREDICTION LOCK (CRITICAL)
    lock_validation = await validator.validate_prediction(
        match_id=prediction_data.match_id,
        innings=prediction_data.innings,
        over=prediction_data.over,
        ball=prediction_data.ball,
        user_prediction_timestamp=server_timestamp
    )
    
    if not lock_validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PREDICTION_LOCKED",
                "reason": lock_validation["reason"],
                "message": lock_validation.get("message", "Prediction window closed"),
                "ball_timestamp": lock_validation.get("ball_timestamp"),
                "your_timestamp": server_timestamp,
                "time_diff_seconds": lock_validation.get("time_diff_seconds")
            }
        )
    
    # Store prediction (result will be updated when ball is bowled)
    prediction_doc = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "match_id": prediction_data.match_id,
        "innings": prediction_data.innings,
        "over": prediction_data.over,
        "ball": prediction_data.ball,
        "ball_key": ball_key,
        "prediction": prediction_data.prediction,
        "predicted_at": server_timestamp,
        "predicted_at_iso": datetime.now(timezone.utc).isoformat(),
        "lock_validated": True,
        "ball_delivered": lock_validation["ball_delivered"],
        "ball_timestamp": lock_validation.get("ball_timestamp"),
        "actual_result": None,
        "is_correct": None,
        "coins_earned": 0,
        "resolved": False
    }
    
    await db.ball_predictions.insert_one(prediction_doc)
    
    return {
        "success": True,
        "prediction_id": prediction_doc["id"],
        "ball": f"{prediction_data.over}.{prediction_data.ball}",
        "prediction": prediction_data.prediction,
        "predicted_at": server_timestamp,
        "lock_validation": {
            "valid": True,
            "reason": lock_validation["reason"]
        },
        "message": "Prediction submitted! Result will be resolved when ball is bowled."
    }


@cricket_router.post("/resolve/ball/{match_id}")
async def resolve_ball_predictions(match_id: str):
    """
    Resolve pending ball predictions with actual results from EntitySport.
    Called automatically when new ball event is detected.
    """
    if not ENTITYSPORT_ENABLED:
        raise HTTPException(status_code=503, detail="EntitySport not configured")
    
    service = get_entitysport_service()
    bbb_data = await service.get_ball_by_ball(match_id)
    
    if not bbb_data:
        return {"resolved": 0, "error": "No BBB data available"}
    
    resolved_count = 0
    coins_awarded = 0
    
    # Get all unresolved predictions for this match
    pending = await db.ball_predictions.find({
        "match_id": match_id,
        "resolved": False
    }).to_list(1000)
    
    # Create lookup for ball results
    ball_results = {}
    for ball in bbb_data.get("balls", []):
        key = f"{ball['innings']}_{ball['over']}_{ball['ball']}"
        
        # Determine result
        if ball.get("is_wicket"):
            result = "wicket"
        elif ball.get("is_six"):
            result = "6"
        elif ball.get("is_four"):
            result = "4"
        elif ball.get("is_wide"):
            result = "wide"
        elif ball.get("is_noball"):
            result = "noball"
        elif ball.get("runs", 0) == 0:
            result = "dot" if ball.get("bat_runs", 0) == 0 else "0"
        else:
            result = str(ball.get("runs", 0))
        
        ball_results[key] = {
            "result": result,
            "timestamp": ball.get("timestamp")
        }
    
    # Resolve each prediction
    for pred in pending:
        ball_key = pred.get("ball_key")
        if ball_key not in ball_results:
            continue
        
        actual = ball_results[ball_key]["result"]
        is_correct = pred["prediction"] == actual
        
        # Calculate coins
        coins = 0
        if is_correct:
            if actual in ['4', '6']:
                coins = REWARDS["ball_boundary"]
            elif actual == 'wicket':
                coins = REWARDS["ball_wicket"]
            else:
                coins = REWARDS["ball_correct"]
            
            # Award coins
            await add_coins(pred["user_id"], coins, "earned", f"Correct ball prediction: {actual}")
            coins_awarded += coins
        
        # Update prediction
        await db.ball_predictions.update_one(
            {"id": pred["id"]},
            {"$set": {
                "actual_result": actual,
                "is_correct": is_correct,
                "coins_earned": coins,
                "resolved": True,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "ball_timestamp": ball_results[ball_key]["timestamp"]
            }}
        )
        resolved_count += 1
    
    return {
        "resolved": resolved_count,
        "coins_awarded": coins_awarded,
        "match_id": match_id
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

# ==================== NEW: OVER OUTCOME PREDICTION ====================

@cricket_router.post("/predict/over")
async def predict_over_outcome(
    prediction_data: OverPredictionCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Predict the outcome of an over
    Options: 0-5, 6-10, 11-15, 16+, wicket_fall
    Rewards: 25 coins for correct prediction
    """
    if prediction_data.prediction not in OVER_OUTCOMES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid prediction. Must be one of: {OVER_OUTCOMES}"
        )
    
    # Check if match exists and is live
    match = await db.cricket_matches.find_one({"match_id": prediction_data.match_id}, {"_id": 0})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.get("status") != "live":
        raise HTTPException(status_code=400, detail="Can only predict on live matches")
    
    # Check if already predicted for this over
    existing = await db.match_predictions.find_one({
        "user_id": current_user.id,
        "match_id": prediction_data.match_id,
        "prediction_type": "over_outcome",
        "over_number": prediction_data.over_number
    })
    if existing:
        raise HTTPException(status_code=400, detail=f"Already predicted for over {prediction_data.over_number}")
    
    # Create prediction
    prediction = MatchPrediction(
        user_id=current_user.id,
        match_id=prediction_data.match_id,
        prediction_type="over_outcome",
        prediction_value=prediction_data.prediction,
        over_number=prediction_data.over_number
    )
    await db.match_predictions.insert_one(prediction.model_dump())
    
    # Simulate result for demo (in production, updated by live data feed)
    actual_outcomes = ["0-5", "6-10", "6-10", "11-15", "11-15", "16+", "wicket_fall"]
    actual_result = random.choice(actual_outcomes)
    is_correct = prediction_data.prediction == actual_result
    
    coins_earned = 0
    if is_correct:
        coins_earned = REWARDS["over_correct"]
        await add_coins(current_user.id, coins_earned, "earned", f"Correct over prediction: Over {prediction_data.over_number}")
    
    # Update prediction with result
    await db.match_predictions.update_one(
        {"id": prediction.id},
        {"$set": {
            "actual_value": actual_result,
            "is_correct": is_correct,
            "coins_earned": coins_earned
        }}
    )
    
    # Record activity
    activity = Activity(
        user_id=current_user.id,
        activity_type="over_prediction",
        coins_earned=coins_earned,
        details={
            "match_id": prediction_data.match_id,
            "over": prediction_data.over_number,
            "prediction": prediction_data.prediction,
            "actual": actual_result,
            "correct": is_correct
        }
    )
    await db.activities.insert_one(activity.model_dump())
    
    return {
        "prediction": prediction_data.prediction,
        "over_number": prediction_data.over_number,
        "actual_result": actual_result,
        "is_correct": is_correct,
        "coins_earned": coins_earned,
        "new_balance": current_user.coins_balance + coins_earned,
        "message": f"Correct! +{coins_earned} coins!" if is_correct else f"Wrong! Over yielded {actual_result} runs"
    }

# ==================== NEW: MATCH WINNER PREDICTION ====================

@cricket_router.post("/predict/winner")
async def predict_match_winner(
    prediction_data: MatchWinnerPredictionCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Predict the match winner
    Must be made before match starts or within first 6 overs
    Rewards: 50 coins for correct prediction
    """
    # Check if match exists
    match = await db.cricket_matches.find_one({"match_id": prediction_data.match_id}, {"_id": 0})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Validate winner is one of the teams
    valid_teams = [match.get("team1_short"), match.get("team2_short")]
    if prediction_data.winner not in valid_teams:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid team. Must be one of: {valid_teams}"
        )
    
    # Check if match is completed (can't predict after completion)
    if match.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Match has already ended")
    
    # Check if already predicted winner for this match
    existing = await db.match_predictions.find_one({
        "user_id": current_user.id,
        "match_id": prediction_data.match_id,
        "prediction_type": "winner"
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already predicted the winner for this match")
    
    # Create prediction
    prediction = MatchPrediction(
        user_id=current_user.id,
        match_id=prediction_data.match_id,
        prediction_type="winner",
        prediction_value=prediction_data.winner
    )
    await db.match_predictions.insert_one(prediction.model_dump())
    
    # For live matches, simulate result (in production, resolved when match ends)
    if match.get("status") == "live":
        # Simulate for demo
        actual_winner = random.choice(valid_teams)
        is_correct = prediction_data.winner == actual_winner
        
        coins_earned = 0
        if is_correct:
            coins_earned = REWARDS["match_winner_correct"]
            await add_coins(current_user.id, coins_earned, "earned", f"Correct match winner prediction!")
        
        # Update prediction with result
        await db.match_predictions.update_one(
            {"id": prediction.id},
            {"$set": {
                "actual_value": actual_winner,
                "is_correct": is_correct,
                "coins_earned": coins_earned
            }}
        )
        
        # Record activity
        activity = Activity(
            user_id=current_user.id,
            activity_type="winner_prediction",
            coins_earned=coins_earned,
            details={
                "match_id": prediction_data.match_id,
                "prediction": prediction_data.winner,
                "actual": actual_winner,
                "correct": is_correct
            }
        )
        await db.activities.insert_one(activity.model_dump())
        
        return {
            "prediction": prediction_data.winner,
            "actual_winner": actual_winner,
            "is_correct": is_correct,
            "coins_earned": coins_earned,
            "new_balance": current_user.coins_balance + coins_earned,
            "message": f"Correct! +{coins_earned} coins!" if is_correct else f"Wrong! {actual_winner} won the match"
        }
    
    # For upcoming matches
    return {
        "message": f"Winner prediction recorded: {prediction_data.winner}",
        "prediction": prediction_data.winner,
        "match_id": prediction_data.match_id,
        "note": "Result will be updated when match ends"
    }

# ==================== PREDICTION LIMITS INFO ====================

@cricket_router.get("/matches/{match_id}/prediction-status")
async def get_prediction_status(
    match_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get user's prediction status for a match (limits, counts)"""
    
    # Ball predictions count
    ball_count = await db.ball_predictions.count_documents({
        "user_id": current_user.id,
        "match_id": match_id
    })
    
    # Over predictions count
    over_count = await db.match_predictions.count_documents({
        "user_id": current_user.id,
        "match_id": match_id,
        "prediction_type": "over_outcome"
    })
    
    # Has winner prediction
    has_winner = await db.match_predictions.find_one({
        "user_id": current_user.id,
        "match_id": match_id,
        "prediction_type": "winner"
    })
    
    return {
        "match_id": match_id,
        "ball_predictions": {
            "count": ball_count,
            "limit": BALL_PREDICTION_LIMIT_PER_MATCH,
            "remaining": max(0, BALL_PREDICTION_LIMIT_PER_MATCH - ball_count)
        },
        "over_predictions": {
            "count": over_count,
            "limit": 20  # Max 20 overs in T20
        },
        "winner_prediction": {
            "made": has_winner is not None,
            "value": has_winner.get("prediction_value") if has_winner else None
        }
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
