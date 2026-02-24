"""
WebSocket Game Manager for FREE11 Card Games
Real-time multiplayer game communication
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
from dataclasses import dataclass, field
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from card_game_logic import (
    TeenPattiGameState, PokerGameState, RummyGameState,
    get_teen_patti_hand_name, get_poker_hand_name, get_best_poker_hand
)

logger = logging.getLogger(__name__)

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
        player_ids = list(session.connections.keys())
        
        # Create game state based on type
        if game_type == "teen_patti":
            session.game_state = TeenPattiGameState()
            session.game_state.deal_cards(player_ids)
        elif game_type == "poker":
            session.game_state = PokerGameState()
            session.game_state.deal_cards(player_ids)
        elif game_type == "rummy":
            session.game_state = RummyGameState()
            session.game_state.deal_cards(player_ids)
        else:
            return False
        
        session.status = "playing"
        
        # Send initial state to each player (personalized)
        for player_id in player_ids:
            await self.send_game_state(room_id, player_id)
        
        # Broadcast game started
        await self.broadcast(room_id, {
            "type": "game_started",
            "game_type": game_type,
            "players": [
                {"id": pid, "name": session.player_names.get(pid, "Player")}
                for pid in player_ids
            ]
        })
        
        return True
    
    async def send_game_state(self, room_id: str, player_id: str):
        """Send current game state to a player"""
        session = self.sessions.get(room_id)
        if not session or not session.game_state:
            return
        
        state_dict = session.game_state.to_dict(for_player=player_id)
        state_dict["type"] = "game_state"
        state_dict["player_names"] = session.player_names
        
        await self.send_to_player(room_id, player_id, state_dict)
    
    async def handle_action(self, room_id: str, player_id: str, action: dict) -> dict:
        """Handle a player action"""
        session = self.sessions.get(room_id)
        if not session or not session.game_state:
            return {"error": "Game not found or not started"}
        
        game_state = session.game_state
        action_type = action.get("action")
        
        # Validate it's the player's turn (for most actions)
        current_player = game_state.get_current_player()
        if action_type not in ["see", "chat"] and current_player != player_id:
            return {"error": "Not your turn"}
        
        result = {"success": True}
        
        # Handle actions based on game type
        if session.game_type == "teen_patti":
            result = await self._handle_teen_patti_action(session, player_id, action)
        elif session.game_type == "poker":
            result = await self._handle_poker_action(session, player_id, action)
        elif session.game_type == "rummy":
            result = await self._handle_rummy_action(session, player_id, action)
        
        # Broadcast updated state to all players
        if result.get("success"):
            for pid in session.connections:
                await self.send_game_state(room_id, pid)
            
            # Check for game completion
            if game_state.is_complete:
                await self._complete_game(session)
        
        return result
    
    async def _handle_teen_patti_action(
        self, session: GameSession, player_id: str, action: dict
    ) -> dict:
        """Handle Teen Patti specific actions"""
        game_state: TeenPattiGameState = session.game_state
        action_type = action.get("action")
        
        if action_type == "see":
            game_state.see_cards(player_id)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "seen"
            })
            return {"success": True}
        
        elif action_type == "fold":
            game_state.fold(player_id)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "fold"
            })
            return {"success": True}
        
        elif action_type == "call":
            amount = game_state.call(player_id)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "call",
                "amount": amount
            })
            return {"success": True, "amount": amount}
        
        elif action_type == "raise":
            amount = action.get("amount", game_state.current_bet * 2)
            actual_amount = game_state.raise_bet(player_id, amount)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "raise",
                "amount": actual_amount
            })
            return {"success": True, "amount": actual_amount}
        
        elif action_type == "show":
            game_state.show(player_id)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "show"
            })
            return {"success": True}
        
        return {"error": "Invalid action"}
    
    async def _handle_poker_action(
        self, session: GameSession, player_id: str, action: dict
    ) -> dict:
        """Handle Poker specific actions"""
        game_state: PokerGameState = session.game_state
        action_type = action.get("action")
        
        if action_type == "fold":
            game_state.fold(player_id)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "fold"
            })
            return {"success": True}
        
        elif action_type == "check":
            if game_state.current_bet > game_state.player_bets.get(player_id, 0):
                return {"error": "Cannot check, must call or fold"}
            game_state.check(player_id)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "check"
            })
            return {"success": True}
        
        elif action_type == "call":
            amount = game_state.call(player_id)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "call",
                "amount": amount
            })
            return {"success": True, "amount": amount}
        
        elif action_type == "raise":
            amount = action.get("amount", 20)
            actual_amount = game_state.raise_bet(player_id, amount)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "raise",
                "amount": actual_amount
            })
            return {"success": True, "amount": actual_amount}
        
        elif action_type == "all_in":
            amount = action.get("amount", 0)
            actual_amount = game_state.all_in(player_id, amount)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "all_in",
                "amount": actual_amount
            })
            return {"success": True, "amount": actual_amount}
        
        return {"error": "Invalid action"}
    
    async def _handle_rummy_action(
        self, session: GameSession, player_id: str, action: dict
    ) -> dict:
        """Handle Rummy specific actions"""
        game_state: RummyGameState = session.game_state
        action_type = action.get("action")
        
        if action_type == "draw_deck":
            if game_state.has_drawn.get(player_id, False):
                return {"error": "Already drew this turn"}
            card = game_state.draw_from_deck(player_id)
            await self.broadcast(session.room_id, {
                "type": "player_action",
                "player_id": player_id,
                "player_name": session.player_names.get(player_id),
                "action": "draw_deck"
            })
            return {"success": True}
        
        elif action_type == "draw_discard":
            if game_state.has_drawn.get(player_id, False):
                return {"error": "Already drew this turn"}
            card = game_state.draw_from_discard(player_id)
            if card:
                await self.broadcast(session.room_id, {
                    "type": "player_action",
                    "player_id": player_id,
                    "player_name": session.player_names.get(player_id),
                    "action": "draw_discard"
                })
                return {"success": True}
            return {"error": "Discard pile is empty"}
        
        elif action_type == "discard":
            if not game_state.has_drawn.get(player_id, False):
                return {"error": "Must draw before discarding"}
            card_idx = action.get("card_index", -1)
            card = game_state.discard_card(player_id, card_idx)
            if card:
                await self.broadcast(session.room_id, {
                    "type": "player_action",
                    "player_id": player_id,
                    "player_name": session.player_names.get(player_id),
                    "action": "discard"
                })
                return {"success": True}
            return {"error": "Invalid card index"}
        
        elif action_type == "declare":
            melds = action.get("melds", [])
            if game_state.declare(player_id, melds):
                await self.broadcast(session.room_id, {
                    "type": "player_action",
                    "player_id": player_id,
                    "player_name": session.player_names.get(player_id),
                    "action": "declare"
                })
                return {"success": True}
            return {"error": "Invalid declaration"}
        
        return {"error": "Invalid action"}
    
    async def _complete_game(self, session: GameSession):
        """Handle game completion"""
        game_state = session.game_state
        session.status = "complete"
        
        winner_id = game_state.winner_id
        winner_name = session.player_names.get(winner_id, "Unknown")
        
        # Get winner's hand description
        hand_name = ""
        if session.game_type == "teen_patti":
            if winner_id in game_state.player_hands:
                hand_name = get_teen_patti_hand_name(game_state.player_hands[winner_id])
        elif session.game_type == "poker":
            if winner_id in game_state.player_hands:
                best_hand, rank, _ = get_best_poker_hand(
                    game_state.player_hands[winner_id],
                    game_state.community_cards
                )
                hand_name = rank.name.replace("_", " ").title()
        
        # Calculate rewards
        rewards = self._calculate_rewards(session)
        
        # Broadcast game complete
        await self.broadcast(session.room_id, {
            "type": "game_complete",
            "winner_id": winner_id,
            "winner_name": winner_name,
            "hand_name": hand_name,
            "rewards": rewards,
            "final_state": game_state.to_dict()
        })
    
    def _calculate_rewards(self, session: GameSession) -> List[dict]:
        """Calculate coin rewards for all players"""
        game_state = session.game_state
        game_type = session.game_type
        
        # Reward structure
        REWARDS = {
            "rummy": {"win": 50, "second": 20, "participate": 5},
            "teen_patti": {"win": 40, "second": 15, "participate": 5},
            "poker": {"win": 60, "second": 25, "participate": 5}
        }
        
        rewards_config = REWARDS.get(game_type, REWARDS["poker"])
        results = []
        
        player_ids = session.player_ids
        winner_id = game_state.winner_id
        
        for i, player_id in enumerate(player_ids):
            if player_id == winner_id:
                coins = rewards_config["win"]
                rank = 1
            elif i == 1:
                coins = rewards_config["second"]
                rank = 2
            else:
                coins = rewards_config["participate"]
                rank = i + 1
            
            results.append({
                "user_id": player_id,
                "name": session.player_names.get(player_id, "Player"),
                "rank": rank,
                "coins": coins
            })
        
        # Sort by rank
        results.sort(key=lambda x: x["rank"])
        return results

# Global game manager instance
game_manager = GameManager()
