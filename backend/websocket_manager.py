"""
WebSocket Managers for FREE11
1. Game Manager - Card games (Rummy, Teen Patti, Poker)
2. Cricket Manager - Real-time match updates
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field
import uuid

from fastapi import WebSocket, WebSocketDisconnect
try:
    from card_game_logic import (
        TeenPattiGameState, PokerGameState, RummyGameState,
        get_teen_patti_hand_name, get_poker_hand_name, get_best_poker_hand
    )
except ImportError:
    TeenPattiGameState = None
    PokerGameState = None
    RummyGameState = None

logger = logging.getLogger(__name__)


# =============================================================================
# CARD GAMES WEBSOCKET MANAGER
# =============================================================================

@dataclass
class GameSession:
    """Represents an active game session"""
    room_id: str
    game_type: str
    host_id: str
    player_ids: List[str] = field(default_factory=list)
    player_names: Dict[str, str] = field(default_factory=dict)
    connections: Dict[str, WebSocket] = field(default_factory=dict)
    game_state: Optional[object] = None
    status: str = "waiting"  # waiting, playing, complete
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def add_player(self, player_id: str, player_name: str, websocket: WebSocket):
        """Add a player to the session"""
        if player_id not in self.player_ids:
            self.player_ids.append(player_id)
        self.player_names[player_id] = player_name
        self.connections[player_id] = websocket
    
    def remove_player(self, player_id: str):
        """Remove a player from the session"""
        if player_id in self.connections:
            del self.connections[player_id]
    
    def get_player_count(self) -> int:
        """Get number of connected players"""
        return len(self.connections)
    
    def is_player_connected(self, player_id: str) -> bool:
        """Check if a player is connected"""
        return player_id in self.connections


class GameManager:
    """Manages all active game sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self._lock = asyncio.Lock()
    
    async def create_session(
        self, 
        room_id: str, 
        game_type: str, 
        host_id: str,
        host_name: str,
        websocket: WebSocket
    ) -> GameSession:
        """Create a new game session"""
        async with self._lock:
            session = GameSession(
                room_id=room_id,
                game_type=game_type,
                host_id=host_id
            )
            session.add_player(host_id, host_name, websocket)
            self.sessions[room_id] = session
            logger.info(f"Created session {room_id} for {game_type}")
            return session
    
    async def join_session(
        self, 
        room_id: str, 
        player_id: str,
        player_name: str,
        websocket: WebSocket
    ) -> Optional[GameSession]:
        """Join an existing session"""
        async with self._lock:
            session = self.sessions.get(room_id)
            if session:
                session.add_player(player_id, player_name, websocket)
                logger.info(f"Player {player_name} joined session {room_id}")
            return session
    
    async def leave_session(self, room_id: str, player_id: str):
        """Leave a session"""
        async with self._lock:
            session = self.sessions.get(room_id)
            if session:
                session.remove_player(player_id)
                if session.get_player_count() == 0:
                    del self.sessions[room_id]
                    logger.info(f"Session {room_id} removed (empty)")
    
    def get_session(self, room_id: str) -> Optional[GameSession]:
        """Get a session by room ID"""
        return self.sessions.get(room_id)
    
    async def broadcast(self, room_id: str, message: dict, exclude: Optional[str] = None):
        """Broadcast a message to all players in a session"""
        session = self.sessions.get(room_id)
        if not session:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for player_id, ws in session.connections.items():
            if exclude and player_id == exclude:
                continue
            try:
                await ws.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to send to {player_id}: {e}")
                disconnected.append(player_id)
        
        # Clean up disconnected players
        for player_id in disconnected:
            session.remove_player(player_id)
    
    async def send_to_player(self, room_id: str, player_id: str, message: dict):
        """Send a message to a specific player"""
        session = self.sessions.get(room_id)
        if not session or player_id not in session.connections:
            return
        
        try:
            await session.connections[player_id].send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send to {player_id}: {e}")
    
    async def start_game(self, room_id: str) -> bool:
        """Initialize and start a game"""
        session = self.sessions.get(room_id)
        if not session:
            return False
        
        game_type = session.game_type
        player_ids = session.player_ids
        
        try:
            if game_type == "teen_patti" and TeenPattiGameState:
                session.game_state = TeenPattiGameState(player_ids)
            elif game_type == "poker" and PokerGameState:
                session.game_state = PokerGameState(player_ids)
            elif game_type == "rummy" and RummyGameState:
                session.game_state = RummyGameState(player_ids)
            else:
                logger.error(f"Unknown game type: {game_type}")
                return False
            
            session.status = "playing"
            return True
        except Exception as e:
            logger.error(f"Failed to start game: {e}")
            return False
    
    def get_active_sessions(self) -> List[Dict]:
        """Get list of active sessions"""
        return [
            {
                "room_id": s.room_id,
                "game_type": s.game_type,
                "status": s.status,
                "player_count": s.get_player_count(),
                "players": list(s.player_names.values())
            }
            for s in self.sessions.values()
        ]


# Singleton instance for card games
game_manager = GameManager()


# =============================================================================
# CRICKET WEBSOCKET MANAGER
# =============================================================================

@dataclass
class MatchSubscription:
    """Tracks subscribers for a specific match."""
    match_id: str
    subscribers: Set[WebSocket] = field(default_factory=set)
    last_update: Optional[datetime] = None
    poll_task: Optional[asyncio.Task] = None


class CricketWebSocketManager:
    """
    Manages WebSocket connections for real-time cricket match updates.
    
    Features:
    - Multiple clients per match
    - Auto-cleanup of disconnected clients
    - Background polling for EntitySport updates
    - Broadcast to all match subscribers
    """
    
    def __init__(self, poll_interval: float = 2.0):
        self.subscriptions: Dict[str, MatchSubscription] = {}
        self.poll_interval = poll_interval
        self._entitysport_service = None
    
    def set_entitysport_service(self, service):
        """Set the EntitySport service for data fetching."""
        self._entitysport_service = service
    
    async def connect(self, websocket: WebSocket, match_id: str) -> None:
        """Connect a client to receive match updates."""
        await websocket.accept()
        
        if match_id not in self.subscriptions:
            self.subscriptions[match_id] = MatchSubscription(match_id=match_id)
            if self._entitysport_service:
                task = asyncio.create_task(self._poll_match(match_id))
                self.subscriptions[match_id].poll_task = task
        
        self.subscriptions[match_id].subscribers.add(websocket)
        logger.info(f"Client connected to match {match_id}. Total: {len(self.subscriptions[match_id].subscribers)}")
        
        await self._send_initial_state(websocket, match_id)
    
    def disconnect(self, websocket: WebSocket, match_id: str) -> None:
        """Disconnect a client from match updates."""
        if match_id in self.subscriptions:
            self.subscriptions[match_id].subscribers.discard(websocket)
            logger.info(f"Client disconnected from match {match_id}. Remaining: {len(self.subscriptions[match_id].subscribers)}")
            
            if not self.subscriptions[match_id].subscribers:
                if self.subscriptions[match_id].poll_task:
                    self.subscriptions[match_id].poll_task.cancel()
                del self.subscriptions[match_id]
                logger.info(f"Stopped polling for match {match_id}")
    
    async def _send_initial_state(self, websocket: WebSocket, match_id: str) -> None:
        """Send current match state to newly connected client."""
        if not self._entitysport_service:
            return
        
        try:
            bbb_data = await self._entitysport_service.get_ball_by_ball(match_id)
            
            if bbb_data:
                await websocket.send_json({
                    "type": "initial_state",
                    "match_id": match_id,
                    "data": bbb_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            logger.error(f"Failed to send initial state: {e}")
    
    async def _poll_match(self, match_id: str) -> None:
        """Background task to poll and broadcast updates."""
        logger.info(f"Starting poll task for match {match_id}")
        last_ball_key = None
        
        while match_id in self.subscriptions:
            try:
                if not self._entitysport_service:
                    await asyncio.sleep(self.poll_interval)
                    continue
                
                bbb_data = await self._entitysport_service.get_ball_by_ball(match_id)
                
                if bbb_data:
                    current_ball = bbb_data.get("current_ball")
                    
                    if current_ball:
                        ball_key = f"{current_ball['innings']}_{current_ball['over']}_{current_ball['ball']}"
                        
                        if ball_key != last_ball_key:
                            last_ball_key = ball_key
                            await self._broadcast_ball_event(match_id, bbb_data, current_ball)
                
                await asyncio.sleep(self.poll_interval)
                
            except asyncio.CancelledError:
                logger.info(f"Poll task cancelled for match {match_id}")
                break
            except Exception as e:
                logger.error(f"Poll error for match {match_id}: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def _broadcast_ball_event(
        self, 
        match_id: str, 
        bbb_data: Dict, 
        current_ball: Dict
    ) -> None:
        """Broadcast a new ball event to all subscribers."""
        if match_id not in self.subscriptions:
            return
        
        message = {
            "type": "ball_update",
            "match_id": match_id,
            "current_ball": current_ball,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prediction_window": {
                "closed_for": f"{current_ball['over']}.{current_ball['ball']}",
                "open_for": self._get_next_ball(current_ball)
            }
        }
        
        for inning in bbb_data.get("innings", []):
            if inning.get("number") == current_ball["innings"]:
                message["innings_summary"] = {
                    "runs": inning.get("total_runs", 0),
                    "wickets": inning.get("total_wickets", 0),
                    "overs": inning.get("overs_completed", 0)
                }
                break
        
        disconnected = set()
        
        for websocket in self.subscriptions[match_id].subscribers:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.add(websocket)
        
        for ws in disconnected:
            self.subscriptions[match_id].subscribers.discard(ws)
        
        logger.debug(f"Broadcast ball {current_ball} to {len(self.subscriptions[match_id].subscribers)} clients")
    
    def _get_next_ball(self, current_ball: Dict) -> str:
        """Calculate the next ball in sequence."""
        next_ball = current_ball["ball"] + 1
        next_over = current_ball["over"]
        
        if next_ball > 6:
            next_ball = 1
            next_over += 1
        
        return f"{next_over}.{next_ball}"
    
    async def broadcast_prediction_lock(
        self, 
        match_id: str, 
        innings: int, 
        over: int, 
        ball: int
    ) -> None:
        """Broadcast that prediction window is closed for a ball."""
        if match_id not in self.subscriptions:
            return
        
        message = {
            "type": "prediction_lock",
            "match_id": match_id,
            "locked_ball": f"{over}.{ball}",
            "innings": innings,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Prediction window CLOSED for {over}.{ball}"
        }
        
        for websocket in self.subscriptions[match_id].subscribers:
            try:
                await websocket.send_json(message)
            except Exception:
                pass
    
    async def broadcast_score_update(
        self, 
        match_id: str, 
        score_data: Dict
    ) -> None:
        """Broadcast score update to all subscribers."""
        if match_id not in self.subscriptions:
            return
        
        message = {
            "type": "score_update",
            "match_id": match_id,
            "score": score_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        for websocket in self.subscriptions[match_id].subscribers:
            try:
                await websocket.send_json(message)
            except Exception:
                pass


# Singleton instance for cricket
cricket_websocket_manager = CricketWebSocketManager(poll_interval=2.0)
