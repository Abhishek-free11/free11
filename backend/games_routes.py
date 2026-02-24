"""
Card Games Routes for FREE11
Rummy, Teen Patti, Poker - all coins only
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
import random

from server import db, get_current_user, add_coins, User

games_router = APIRouter(prefix="/games", tags=["Card Games"])

# ==================== CONSTANTS ====================

# Game types
GAME_TYPES = ["rummy", "teen_patti", "poker"]

# Coin rewards/stakes (all free - no buy-ins)
GAME_CONFIG = {
    "rummy": {
        "name": "Rummy",
        "description": "Classic 13-card Indian Rummy",
        "min_players": 2,
        "max_players": 6,
        "coins_to_play": 0,  # FREE to play
        "coins_reward": {"win": 50, "second": 20, "participate": 5},
        "rules": "Form valid sets and sequences to declare",
        "duration_mins": 15
    },
    "teen_patti": {
        "name": "Teen Patti",
        "description": "Indian 3-card poker game",
        "min_players": 3,
        "max_players": 6,
        "coins_to_play": 0,  # FREE to play
        "coins_reward": {"win": 40, "second": 15, "participate": 5},
        "rules": "Best 3-card hand wins",
        "duration_mins": 10
    },
    "poker": {
        "name": "Poker",
        "description": "Texas Hold'em style poker",
        "min_players": 2,
        "max_players": 9,
        "coins_to_play": 0,  # FREE to play
        "coins_reward": {"win": 60, "second": 25, "participate": 5},
        "rules": "Best 5-card hand wins",
        "duration_mins": 20
    }
}

# Hand rankings for Teen Patti
TEEN_PATTI_HANDS = [
    "Trail/Set (Three of a Kind)",
    "Pure Sequence (Straight Flush)",
    "Sequence (Straight)",
    "Color (Flush)",
    "Pair",
    "High Card"
]

# Hand rankings for Poker
POKER_HANDS = [
    "Royal Flush",
    "Straight Flush",
    "Four of a Kind",
    "Full House",
    "Flush",
    "Straight",
    "Three of a Kind",
    "Two Pair",
    "One Pair",
    "High Card"
]

# ==================== MODELS ====================

class GameRoom(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_type: str  # rummy, teen_patti, poker
    name: str
    host_id: str
    player_ids: List[str] = Field(default_factory=list)
    max_players: int
    status: str = "waiting"  # waiting, playing, completed
    is_private: bool = False
    room_code: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class GameResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str
    game_type: str
    player_results: List[Dict]  # [{user_id, rank, coins_earned, hand}]
    winner_id: str
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PlayerStats(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    game_type: str
    games_played: int = 0
    games_won: int = 0
    total_coins_earned: int = 0
    win_rate: float = 0
    best_hand: Optional[str] = None
    current_streak: int = 0
    best_streak: int = 0

# Request Models
class CreateRoomRequest(BaseModel):
    game_type: str
    name: str
    max_players: int = 4
    is_private: bool = False

class JoinRoomRequest(BaseModel):
    room_code: Optional[str] = None

# ==================== HELPER FUNCTIONS ====================

def generate_room_code() -> str:
    """Generate a 6-character room code"""
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def simulate_game_result(game_type: str, player_ids: List[str]) -> List[Dict]:
    """Simulate a game result (in production, this would be real game logic)"""
    config = GAME_CONFIG[game_type]
    
    # Shuffle players for random ranking
    shuffled = player_ids.copy()
    random.shuffle(shuffled)
    
    results = []
    for rank, player_id in enumerate(shuffled, 1):
        if rank == 1:
            coins = config["coins_reward"]["win"]
            hand = random.choice(POKER_HANDS[:3] if game_type == "poker" else TEEN_PATTI_HANDS[:3])
        elif rank == 2:
            coins = config["coins_reward"]["second"]
            hand = random.choice(POKER_HANDS[3:6] if game_type == "poker" else TEEN_PATTI_HANDS[2:4])
        else:
            coins = config["coins_reward"]["participate"]
            hand = random.choice(POKER_HANDS[6:] if game_type == "poker" else TEEN_PATTI_HANDS[4:])
        
        results.append({
            "user_id": player_id,
            "rank": rank,
            "coins_earned": coins,
            "hand": hand if game_type != "rummy" else f"Declared with {random.randint(0, 30)} points"
        })
    
    return results

# ==================== ROUTES ====================

@games_router.get("/config")
async def get_games_config():
    """Get configuration for all card games"""
    return {
        "games": GAME_CONFIG,
        "note": "All games are FREE to play. Earn coins by winning!",
        "coin_model": "earn-only, non-cash, non-withdrawable"
    }

@games_router.get("/{game_type}/info")
async def get_game_info(game_type: str):
    """Get detailed info for a specific game"""
    if game_type not in GAME_TYPES:
        raise HTTPException(status_code=404, detail=f"Game type must be one of: {GAME_TYPES}")
    
    config = GAME_CONFIG[game_type]
    
    # Get hand rankings
    if game_type == "teen_patti":
        hands = TEEN_PATTI_HANDS
    elif game_type == "poker":
        hands = POKER_HANDS
    else:
        hands = ["Pure Sequence", "Sequence", "Set", "Two Sequences", "Invalid Hand"]
    
    return {
        **config,
        "game_type": game_type,
        "hand_rankings": hands,
        "entry_fee": "FREE",
        "coin_rewards": config["coins_reward"]
    }

@games_router.get("/{game_type}/rooms")
async def get_available_rooms(
    game_type: str,
    current_user: User = Depends(get_current_user)
):
    """Get available rooms to join for a game type"""
    if game_type not in GAME_TYPES:
        raise HTTPException(status_code=404, detail=f"Invalid game type")
    
    rooms = await db.game_rooms.find({
        "game_type": game_type,
        "status": "waiting",
        "is_private": False
    }, {"_id": 0}).to_list(20)
    
    # Add player count info
    for room in rooms:
        room["current_players"] = len(room.get("player_ids", []))
        room["spots_left"] = room["max_players"] - room["current_players"]
    
    return {
        "game_type": game_type,
        "rooms": rooms,
        "total": len(rooms)
    }

@games_router.post("/{game_type}/rooms/create")
async def create_game_room(
    game_type: str,
    request: CreateRoomRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new game room"""
    if game_type not in GAME_TYPES:
        raise HTTPException(status_code=404, detail=f"Invalid game type")
    
    config = GAME_CONFIG[game_type]
    
    # Validate max players
    if request.max_players < config["min_players"] or request.max_players > config["max_players"]:
        raise HTTPException(
            status_code=400,
            detail=f"Players must be between {config['min_players']} and {config['max_players']}"
        )
    
    # Generate room code for private rooms
    room_code = generate_room_code() if request.is_private else None
    
    room = GameRoom(
        game_type=game_type,
        name=request.name,
        host_id=current_user.id,
        player_ids=[current_user.id],
        max_players=request.max_players,
        is_private=request.is_private,
        room_code=room_code
    )
    
    await db.game_rooms.insert_one(room.model_dump())
    
    return {
        "message": f"{config['name']} room created!",
        "room": room.model_dump(),
        "room_code": room_code,
        "share_message": f"Join my {config['name']} game on FREE11! Code: {room_code}" if room_code else None
    }

@games_router.post("/{game_type}/rooms/{room_id}/join")
async def join_game_room(
    game_type: str,
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    """Join an existing game room"""
    room = await db.game_rooms.find_one({
        "id": room_id,
        "game_type": game_type
    }, {"_id": 0})
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room["status"] != "waiting":
        raise HTTPException(status_code=400, detail="Game already started or completed")
    
    if current_user.id in room.get("player_ids", []):
        raise HTTPException(status_code=400, detail="Already in this room")
    
    if len(room.get("player_ids", [])) >= room["max_players"]:
        raise HTTPException(status_code=400, detail="Room is full")
    
    # Add player to room
    await db.game_rooms.update_one(
        {"id": room_id},
        {"$push": {"player_ids": current_user.id}}
    )
    
    return {
        "message": f"Joined {GAME_CONFIG[game_type]['name']} room!",
        "room_id": room_id,
        "players": len(room.get("player_ids", [])) + 1
    }

@games_router.post("/rooms/join-by-code")
async def join_room_by_code(
    code: str,
    current_user: User = Depends(get_current_user)
):
    """Join a private room using code"""
    room = await db.game_rooms.find_one({
        "room_code": code.upper(),
        "is_private": True,
        "status": "waiting"
    }, {"_id": 0})
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or game already started")
    
    if current_user.id in room.get("player_ids", []):
        raise HTTPException(status_code=400, detail="Already in this room")
    
    if len(room.get("player_ids", [])) >= room["max_players"]:
        raise HTTPException(status_code=400, detail="Room is full")
    
    # Add player
    await db.game_rooms.update_one(
        {"id": room["id"]},
        {"$push": {"player_ids": current_user.id}}
    )
    
    return {
        "message": f"Joined {GAME_CONFIG[room['game_type']]['name']} room!",
        "room": room
    }

@games_router.post("/{game_type}/rooms/{room_id}/start")
async def start_game(
    game_type: str,
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    """Start a game (host only)"""
    room = await db.game_rooms.find_one({
        "id": room_id,
        "game_type": game_type
    }, {"_id": 0})
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room["host_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Only host can start the game")
    
    if room["status"] != "waiting":
        raise HTTPException(status_code=400, detail="Game already started or completed")
    
    config = GAME_CONFIG[game_type]
    if len(room.get("player_ids", [])) < config["min_players"]:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {config['min_players']} players to start"
        )
    
    # Start the game
    await db.game_rooms.update_one(
        {"id": room_id},
        {
            "$set": {
                "status": "playing",
                "started_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": f"{config['name']} game started!",
        "room_id": room_id,
        "players": len(room.get("player_ids", []))
    }

@games_router.post("/{game_type}/rooms/{room_id}/complete")
async def complete_game(
    game_type: str,
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    """Complete a game and distribute rewards (simulated for demo)"""
    room = await db.game_rooms.find_one({
        "id": room_id,
        "game_type": game_type
    }, {"_id": 0})
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room["status"] != "playing":
        raise HTTPException(status_code=400, detail="Game not in progress")
    
    # Simulate game results
    results = simulate_game_result(game_type, room.get("player_ids", []))
    winner_id = results[0]["user_id"]
    
    # Award coins to all players
    for result in results:
        await add_coins(
            result["user_id"],
            result["coins_earned"],
            "earned",
            f"{GAME_CONFIG[game_type]['name']} - Rank #{result['rank']}"
        )
        
        # Update player stats
        existing_stats = await db.game_stats.find_one({
            "user_id": result["user_id"],
            "game_type": game_type
        })
        
        if existing_stats:
            games_played = existing_stats.get("games_played", 0) + 1
            games_won = existing_stats.get("games_won", 0) + (1 if result["rank"] == 1 else 0)
            total_coins = existing_stats.get("total_coins_earned", 0) + result["coins_earned"]
            
            await db.game_stats.update_one(
                {"user_id": result["user_id"], "game_type": game_type},
                {"$set": {
                    "games_played": games_played,
                    "games_won": games_won,
                    "total_coins_earned": total_coins,
                    "win_rate": round((games_won / games_played) * 100, 1)
                }}
            )
        else:
            stats = PlayerStats(
                user_id=result["user_id"],
                game_type=game_type,
                games_played=1,
                games_won=1 if result["rank"] == 1 else 0,
                total_coins_earned=result["coins_earned"],
                win_rate=100 if result["rank"] == 1 else 0
            )
            await db.game_stats.insert_one(stats.model_dump())
    
    # Mark room as completed
    await db.game_rooms.update_one(
        {"id": room_id},
        {"$set": {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Save game result
    game_result = GameResult(
        room_id=room_id,
        game_type=game_type,
        player_results=results,
        winner_id=winner_id
    )
    await db.game_results.insert_one(game_result.model_dump())
    
    return {
        "message": "Game completed!",
        "results": results,
        "winner_id": winner_id
    }

@games_router.get("/{game_type}/stats/my")
async def get_my_game_stats(
    game_type: str,
    current_user: User = Depends(get_current_user)
):
    """Get current user's stats for a game type"""
    if game_type not in GAME_TYPES:
        raise HTTPException(status_code=404, detail=f"Invalid game type")
    
    stats = await db.game_stats.find_one({
        "user_id": current_user.id,
        "game_type": game_type
    }, {"_id": 0})
    
    if not stats:
        stats = {
            "user_id": current_user.id,
            "game_type": game_type,
            "games_played": 0,
            "games_won": 0,
            "total_coins_earned": 0,
            "win_rate": 0
        }
    
    return stats

@games_router.get("/{game_type}/leaderboard")
async def get_game_leaderboard(game_type: str):
    """Get leaderboard for a game type"""
    if game_type not in GAME_TYPES:
        raise HTTPException(status_code=404, detail=f"Invalid game type")
    
    # Get top players by win rate (min 5 games)
    stats = await db.game_stats.find({
        "game_type": game_type,
        "games_played": {"$gte": 5}
    }, {"_id": 0}).sort("win_rate", -1).limit(50).to_list(50)
    
    # Enrich with user names
    leaderboard = []
    for i, stat in enumerate(stats, 1):
        user = await db.users.find_one({"id": stat["user_id"]}, {"_id": 0, "name": 1})
        leaderboard.append({
            "rank": i,
            "user_name": user.get("name", "Anonymous") if user else "Anonymous",
            "games_played": stat.get("games_played", 0),
            "games_won": stat.get("games_won", 0),
            "win_rate": stat.get("win_rate", 0),
            "total_coins_earned": stat.get("total_coins_earned", 0)
        })
    
    return {
        "game_type": game_type,
        "game_name": GAME_CONFIG[game_type]["name"],
        "leaderboard": leaderboard
    }

@games_router.get("/my-rooms")
async def get_my_rooms(current_user: User = Depends(get_current_user)):
    """Get all rooms user is currently in"""
    rooms = await db.game_rooms.find({
        "player_ids": current_user.id,
        "status": {"$in": ["waiting", "playing"]}
    }, {"_id": 0}).to_list(10)
    
    return {
        "rooms": rooms,
        "total": len(rooms)
    }

@games_router.post("/{game_type}/quick-play")
async def quick_play(
    game_type: str,
    current_user: User = Depends(get_current_user)
):
    """Quick play - join an available room or create one"""
    if game_type not in GAME_TYPES:
        raise HTTPException(status_code=404, detail=f"Invalid game type")
    
    config = GAME_CONFIG[game_type]
    
    # Find an available room
    room = await db.game_rooms.find_one({
        "game_type": game_type,
        "status": "waiting",
        "is_private": False,
        "player_ids": {"$nin": [current_user.id]},
        "$expr": {"$lt": [{"$size": "$player_ids"}, "$max_players"]}
    }, {"_id": 0})
    
    if room:
        # Join existing room
        await db.game_rooms.update_one(
            {"id": room["id"]},
            {"$push": {"player_ids": current_user.id}}
        )
        return {
            "action": "joined",
            "message": f"Joined {config['name']} room!",
            "room": room
        }
    else:
        # Create new room
        new_room = GameRoom(
            game_type=game_type,
            name=f"{config['name']} Quick Play",
            host_id=current_user.id,
            player_ids=[current_user.id],
            max_players=config["max_players"],
            is_private=False
        )
        await db.game_rooms.insert_one(new_room.model_dump())
        
        return {
            "action": "created",
            "message": f"Created new {config['name']} room. Waiting for players...",
            "room": new_room.model_dump()
        }
