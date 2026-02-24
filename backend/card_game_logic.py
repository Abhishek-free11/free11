"""
Card Game Logic Module for FREE11
Implements simplified rules for Rummy, Teen Patti, and Poker
"""

import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import copy

# ==================== CARD DEFINITIONS ====================

SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, 2)}  # 2-14 (Ace high)

@dataclass
class Card:
    suit: str
    rank: str
    
    def __str__(self):
        return f"{self.rank}{self.suit[0].upper()}"
    
    def to_dict(self):
        return {"suit": self.suit, "rank": self.rank}
    
    @property
    def value(self):
        return RANK_VALUES[self.rank]

def create_deck() -> List[Card]:
    """Create a standard 52-card deck"""
    return [Card(suit, rank) for suit in SUITS for rank in RANKS]

def shuffle_deck(deck: List[Card]) -> List[Card]:
    """Shuffle the deck"""
    shuffled = deck.copy()
    random.shuffle(shuffled)
    return shuffled

# ==================== TEEN PATTI LOGIC ====================

class TeenPattiHandRank(Enum):
    TRAIL = 6        # Three of a kind
    PURE_SEQUENCE = 5  # Straight flush
    SEQUENCE = 4     # Straight
    COLOR = 3        # Flush
    PAIR = 2         # Pair
    HIGH_CARD = 1    # High card

def evaluate_teen_patti_hand(cards: List[Card]) -> Tuple[TeenPattiHandRank, List[int]]:
    """Evaluate a 3-card Teen Patti hand"""
    if len(cards) != 3:
        raise ValueError("Teen Patti requires exactly 3 cards")
    
    ranks = sorted([c.value for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    
    is_flush = len(set(suits)) == 1
    
    # Check for sequence (straight)
    sorted_ranks = sorted(ranks)
    is_sequence = (sorted_ranks[2] - sorted_ranks[0] == 2 and 
                   sorted_ranks[1] - sorted_ranks[0] == 1)
    # Special case: A-2-3
    if set(ranks) == {14, 2, 3}:
        is_sequence = True
        ranks = [3, 2, 1]  # A-2-3 ranks lower
    
    # Check for trail (three of a kind)
    if len(set(ranks)) == 1:
        return TeenPattiHandRank.TRAIL, ranks
    
    # Pure sequence (straight flush)
    if is_flush and is_sequence:
        return TeenPattiHandRank.PURE_SEQUENCE, ranks
    
    # Sequence (straight)
    if is_sequence:
        return TeenPattiHandRank.SEQUENCE, ranks
    
    # Color (flush)
    if is_flush:
        return TeenPattiHandRank.COLOR, ranks
    
    # Pair
    if len(set(ranks)) == 2:
        # Put pair first
        pair_rank = max(set(ranks), key=ranks.count)
        kicker = [r for r in ranks if r != pair_rank][0]
        return TeenPattiHandRank.PAIR, [pair_rank, pair_rank, kicker]
    
    return TeenPattiHandRank.HIGH_CARD, ranks

def compare_teen_patti_hands(hand1: List[Card], hand2: List[Card]) -> int:
    """Compare two Teen Patti hands. Returns 1 if hand1 wins, -1 if hand2 wins, 0 for tie"""
    rank1, values1 = evaluate_teen_patti_hand(hand1)
    rank2, values2 = evaluate_teen_patti_hand(hand2)
    
    if rank1.value > rank2.value:
        return 1
    elif rank1.value < rank2.value:
        return -1
    
    # Same rank, compare high cards
    for v1, v2 in zip(values1, values2):
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    
    return 0

# ==================== POKER LOGIC (SIMPLIFIED) ====================

class PokerHandRank(Enum):
    ROYAL_FLUSH = 10
    STRAIGHT_FLUSH = 9
    FOUR_OF_A_KIND = 8
    FULL_HOUSE = 7
    FLUSH = 6
    STRAIGHT = 5
    THREE_OF_A_KIND = 4
    TWO_PAIR = 3
    ONE_PAIR = 2
    HIGH_CARD = 1

def evaluate_poker_hand(cards: List[Card]) -> Tuple[PokerHandRank, List[int]]:
    """Evaluate a 5-card poker hand"""
    if len(cards) != 5:
        raise ValueError("Poker requires exactly 5 cards")
    
    ranks = sorted([c.value for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    
    is_flush = len(set(suits)) == 1
    
    # Check for straight
    sorted_ranks = sorted(set(ranks))
    is_straight = (len(sorted_ranks) == 5 and 
                   sorted_ranks[4] - sorted_ranks[0] == 4)
    # A-2-3-4-5 straight (wheel)
    if set(ranks) == {14, 2, 3, 4, 5}:
        is_straight = True
        ranks = [5, 4, 3, 2, 1]
    
    rank_counts = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1
    
    counts = sorted(rank_counts.values(), reverse=True)
    
    # Royal flush
    if is_flush and is_straight and max(ranks) == 14 and min(ranks) == 10:
        return PokerHandRank.ROYAL_FLUSH, ranks
    
    # Straight flush
    if is_flush and is_straight:
        return PokerHandRank.STRAIGHT_FLUSH, ranks
    
    # Four of a kind
    if counts == [4, 1]:
        quad_rank = max(rank_counts, key=rank_counts.get)
        kicker = [r for r in ranks if r != quad_rank][0]
        return PokerHandRank.FOUR_OF_A_KIND, [quad_rank] * 4 + [kicker]
    
    # Full house
    if counts == [3, 2]:
        trip_rank = max(rank_counts, key=rank_counts.get)
        pair_rank = min(rank_counts, key=rank_counts.get)
        return PokerHandRank.FULL_HOUSE, [trip_rank] * 3 + [pair_rank] * 2
    
    # Flush
    if is_flush:
        return PokerHandRank.FLUSH, ranks
    
    # Straight
    if is_straight:
        return PokerHandRank.STRAIGHT, ranks
    
    # Three of a kind
    if counts == [3, 1, 1]:
        trip_rank = max(rank_counts, key=rank_counts.get)
        kickers = sorted([r for r in ranks if r != trip_rank], reverse=True)
        return PokerHandRank.THREE_OF_A_KIND, [trip_rank] * 3 + kickers
    
    # Two pair
    if counts == [2, 2, 1]:
        pairs = [r for r, c in rank_counts.items() if c == 2]
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        pairs.sort(reverse=True)
        return PokerHandRank.TWO_PAIR, [pairs[0], pairs[0], pairs[1], pairs[1], kicker]
    
    # One pair
    if counts == [2, 1, 1, 1]:
        pair_rank = max(rank_counts, key=rank_counts.get)
        kickers = sorted([r for r in ranks if r != pair_rank], reverse=True)
        return PokerHandRank.ONE_PAIR, [pair_rank, pair_rank] + kickers
    
    return PokerHandRank.HIGH_CARD, ranks

def get_best_poker_hand(hole_cards: List[Card], community_cards: List[Card]) -> Tuple[List[Card], PokerHandRank, List[int]]:
    """Get the best 5-card hand from hole cards + community cards"""
    from itertools import combinations
    
    all_cards = hole_cards + community_cards
    best_hand = None
    best_rank = None
    best_values = None
    
    for combo in combinations(all_cards, 5):
        hand = list(combo)
        rank, values = evaluate_poker_hand(hand)
        
        if best_rank is None or rank.value > best_rank.value or \
           (rank.value == best_rank.value and values > best_values):
            best_hand = hand
            best_rank = rank
            best_values = values
    
    return best_hand, best_rank, best_values

# ==================== RUMMY LOGIC (SIMPLIFIED) ====================

def is_valid_set(cards: List[Card]) -> bool:
    """Check if cards form a valid set (same rank, different suits)"""
    if len(cards) < 3 or len(cards) > 4:
        return False
    
    ranks = set(c.rank for c in cards)
    suits = [c.suit for c in cards]
    
    return len(ranks) == 1 and len(suits) == len(set(suits))

def is_valid_sequence(cards: List[Card]) -> bool:
    """Check if cards form a valid sequence (consecutive ranks, same suit)"""
    if len(cards) < 3:
        return False
    
    suits = set(c.suit for c in cards)
    if len(suits) != 1:
        return False
    
    values = sorted([c.value for c in cards])
    for i in range(1, len(values)):
        if values[i] - values[i-1] != 1:
            return False
    
    return True

def calculate_rummy_points(hand: List[Card], melds: List[List[Card]]) -> int:
    """Calculate deadwood points (unmelded cards)"""
    melded_cards = []
    for meld in melds:
        melded_cards.extend(meld)
    
    deadwood = [c for c in hand if c not in melded_cards]
    
    points = 0
    for card in deadwood:
        if card.rank in ['J', 'Q', 'K']:
            points += 10
        elif card.rank == 'A':
            points += 1
        else:
            points += int(card.rank)
    
    return points

# ==================== GAME STATE CLASSES ====================

@dataclass
class TeenPattiGameState:
    """State for a Teen Patti game"""
    deck: List[Card] = field(default_factory=list)
    player_hands: Dict[str, List[Card]] = field(default_factory=dict)
    pot: int = 0
    current_bet: int = 10
    current_player_idx: int = 0
    player_order: List[str] = field(default_factory=list)
    folded_players: List[str] = field(default_factory=list)
    seen_players: List[str] = field(default_factory=list)
    is_started: bool = False
    is_complete: bool = False
    winner_id: Optional[str] = None
    
    def deal_cards(self, player_ids: List[str]):
        """Deal 3 cards to each player"""
        self.deck = shuffle_deck(create_deck())
        self.player_order = player_ids.copy()
        self.player_hands = {}
        
        for player_id in player_ids:
            self.player_hands[player_id] = [self.deck.pop() for _ in range(3)]
        
        self.is_started = True
    
    def get_active_players(self) -> List[str]:
        """Get players still in the game"""
        return [p for p in self.player_order if p not in self.folded_players]
    
    def get_current_player(self) -> Optional[str]:
        """Get the current player to act"""
        active = self.get_active_players()
        if not active:
            return None
        return active[self.current_player_idx % len(active)]
    
    def fold(self, player_id: str):
        """Player folds"""
        if player_id not in self.folded_players:
            self.folded_players.append(player_id)
        self.advance_turn()
    
    def see_cards(self, player_id: str):
        """Player sees their cards"""
        if player_id not in self.seen_players:
            self.seen_players.append(player_id)
    
    def call(self, player_id: str) -> int:
        """Player calls the current bet"""
        amount = self.current_bet if player_id in self.seen_players else self.current_bet // 2
        self.pot += amount
        self.advance_turn()
        return amount
    
    def raise_bet(self, player_id: str, amount: int) -> int:
        """Player raises the bet"""
        min_raise = self.current_bet * 2 if player_id in self.seen_players else self.current_bet
        actual_amount = max(amount, min_raise)
        self.current_bet = actual_amount
        self.pot += actual_amount
        self.advance_turn()
        return actual_amount
    
    def advance_turn(self):
        """Move to the next player"""
        active = self.get_active_players()
        if len(active) <= 1:
            self.complete_game()
        else:
            self.current_player_idx = (self.current_player_idx + 1) % len(active)
    
    def show(self, player_id: str):
        """Request showdown (requires at least 2 players)"""
        active = self.get_active_players()
        if len(active) == 2:
            self.complete_game()
    
    def complete_game(self):
        """Complete the game and determine winner"""
        self.is_complete = True
        active = self.get_active_players()
        
        if len(active) == 1:
            self.winner_id = active[0]
        else:
            # Compare hands
            best_player = None
            best_hand = None
            
            for player_id in active:
                hand = self.player_hands[player_id]
                if best_player is None:
                    best_player = player_id
                    best_hand = hand
                else:
                    if compare_teen_patti_hands(hand, best_hand) > 0:
                        best_player = player_id
                        best_hand = hand
            
            self.winner_id = best_player
    
    def to_dict(self, for_player: Optional[str] = None) -> dict:
        """Convert state to dictionary for transmission"""
        hands = {}
        for player_id, cards in self.player_hands.items():
            if for_player == player_id and player_id in self.seen_players:
                hands[player_id] = [c.to_dict() for c in cards]
            elif self.is_complete:
                hands[player_id] = [c.to_dict() for c in cards]
            else:
                hands[player_id] = [{"hidden": True}] * 3
        
        return {
            "pot": self.pot,
            "current_bet": self.current_bet,
            "current_player": self.get_current_player(),
            "player_order": self.player_order,
            "folded_players": self.folded_players,
            "seen_players": self.seen_players,
            "hands": hands,
            "is_complete": self.is_complete,
            "winner_id": self.winner_id,
            "active_players": self.get_active_players()
        }

@dataclass
class PokerGameState:
    """State for Texas Hold'em Poker"""
    deck: List[Card] = field(default_factory=list)
    player_hands: Dict[str, List[Card]] = field(default_factory=dict)
    community_cards: List[Card] = field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    player_bets: Dict[str, int] = field(default_factory=dict)
    current_player_idx: int = 0
    player_order: List[str] = field(default_factory=list)
    folded_players: List[str] = field(default_factory=list)
    all_in_players: List[str] = field(default_factory=list)
    phase: str = "preflop"  # preflop, flop, turn, river, showdown
    is_started: bool = False
    is_complete: bool = False
    winner_id: Optional[str] = None
    dealer_idx: int = 0
    
    def deal_cards(self, player_ids: List[str]):
        """Deal hole cards to each player"""
        self.deck = shuffle_deck(create_deck())
        self.player_order = player_ids.copy()
        self.player_hands = {}
        self.player_bets = {p: 0 for p in player_ids}
        self.community_cards = []
        self.phase = "preflop"
        
        for player_id in player_ids:
            self.player_hands[player_id] = [self.deck.pop() for _ in range(2)]
        
        self.is_started = True
    
    def deal_community_cards(self):
        """Deal community cards based on phase"""
        if self.phase == "preflop":
            # Deal flop (3 cards)
            self.community_cards = [self.deck.pop() for _ in range(3)]
            self.phase = "flop"
        elif self.phase == "flop":
            # Deal turn (1 card)
            self.community_cards.append(self.deck.pop())
            self.phase = "turn"
        elif self.phase == "turn":
            # Deal river (1 card)
            self.community_cards.append(self.deck.pop())
            self.phase = "river"
    
    def get_active_players(self) -> List[str]:
        """Get players still in the game"""
        return [p for p in self.player_order if p not in self.folded_players]
    
    def get_current_player(self) -> Optional[str]:
        """Get the current player to act"""
        active = [p for p in self.get_active_players() if p not in self.all_in_players]
        if not active:
            return None
        return active[self.current_player_idx % len(active)]
    
    def fold(self, player_id: str):
        """Player folds"""
        if player_id not in self.folded_players:
            self.folded_players.append(player_id)
        self.advance_turn()
    
    def check(self, player_id: str):
        """Player checks (only if no bet to call)"""
        self.advance_turn()
    
    def call(self, player_id: str) -> int:
        """Player calls the current bet"""
        amount = self.current_bet - self.player_bets.get(player_id, 0)
        self.player_bets[player_id] = self.current_bet
        self.pot += amount
        self.advance_turn()
        return amount
    
    def raise_bet(self, player_id: str, amount: int) -> int:
        """Player raises"""
        min_raise = self.current_bet * 2 if self.current_bet > 0 else 20
        actual_raise = max(amount, min_raise)
        call_amount = self.current_bet - self.player_bets.get(player_id, 0)
        total_amount = call_amount + actual_raise
        self.current_bet += actual_raise
        self.player_bets[player_id] = self.current_bet
        self.pot += total_amount
        self.advance_turn()
        return total_amount
    
    def all_in(self, player_id: str, amount: int) -> int:
        """Player goes all-in"""
        self.player_bets[player_id] = self.player_bets.get(player_id, 0) + amount
        self.pot += amount
        self.all_in_players.append(player_id)
        self.advance_turn()
        return amount
    
    def advance_turn(self):
        """Move to the next player or phase"""
        active = [p for p in self.get_active_players() if p not in self.all_in_players]
        
        if len(self.get_active_players()) <= 1:
            self.complete_game()
            return
        
        if not active:
            # All active players are all-in, deal remaining cards
            while self.phase != "river":
                self.deal_community_cards()
            self.complete_game()
            return
        
        self.current_player_idx = (self.current_player_idx + 1) % len(active)
        
        # Check if betting round is complete
        all_equal = all(
            self.player_bets.get(p, 0) == self.current_bet 
            for p in active
        )
        
        if all_equal and self.current_player_idx == 0:
            if self.phase == "river":
                self.complete_game()
            else:
                self.deal_community_cards()
                self.current_bet = 0
                self.player_bets = {p: 0 for p in self.player_order}
    
    def complete_game(self):
        """Complete the game and determine winner"""
        self.is_complete = True
        self.phase = "showdown"
        active = self.get_active_players()
        
        if len(active) == 1:
            self.winner_id = active[0]
        else:
            # Compare hands
            best_player = None
            best_rank = None
            best_values = None
            
            for player_id in active:
                _, rank, values = get_best_poker_hand(
                    self.player_hands[player_id],
                    self.community_cards
                )
                
                if best_rank is None or rank.value > best_rank.value or \
                   (rank.value == best_rank.value and values > best_values):
                    best_player = player_id
                    best_rank = rank
                    best_values = values
            
            self.winner_id = best_player
    
    def to_dict(self, for_player: Optional[str] = None) -> dict:
        """Convert state to dictionary for transmission"""
        hands = {}
        for player_id, cards in self.player_hands.items():
            if for_player == player_id:
                hands[player_id] = [c.to_dict() for c in cards]
            elif self.is_complete:
                hands[player_id] = [c.to_dict() for c in cards]
            else:
                hands[player_id] = [{"hidden": True}] * 2
        
        return {
            "pot": self.pot,
            "current_bet": self.current_bet,
            "current_player": self.get_current_player(),
            "player_order": self.player_order,
            "folded_players": self.folded_players,
            "all_in_players": self.all_in_players,
            "hands": hands,
            "community_cards": [c.to_dict() for c in self.community_cards],
            "phase": self.phase,
            "is_complete": self.is_complete,
            "winner_id": self.winner_id,
            "player_bets": self.player_bets,
            "active_players": self.get_active_players()
        }

@dataclass
class RummyGameState:
    """State for Indian Rummy (simplified)"""
    deck: List[Card] = field(default_factory=list)
    discard_pile: List[Card] = field(default_factory=list)
    player_hands: Dict[str, List[Card]] = field(default_factory=dict)
    current_player_idx: int = 0
    player_order: List[str] = field(default_factory=list)
    has_drawn: Dict[str, bool] = field(default_factory=dict)
    is_started: bool = False
    is_complete: bool = False
    winner_id: Optional[str] = None
    player_points: Dict[str, int] = field(default_factory=dict)
    
    def deal_cards(self, player_ids: List[str]):
        """Deal 13 cards to each player"""
        # Use 2 decks for more players
        self.deck = shuffle_deck(create_deck() + create_deck())
        self.player_order = player_ids.copy()
        self.player_hands = {}
        self.has_drawn = {p: False for p in player_ids}
        
        for player_id in player_ids:
            self.player_hands[player_id] = [self.deck.pop() for _ in range(13)]
        
        # Put first card in discard pile
        self.discard_pile = [self.deck.pop()]
        self.is_started = True
    
    def get_current_player(self) -> Optional[str]:
        """Get the current player to act"""
        return self.player_order[self.current_player_idx]
    
    def draw_from_deck(self, player_id: str) -> Optional[Card]:
        """Draw a card from the deck"""
        if not self.deck:
            # Reshuffle discard pile
            top_card = self.discard_pile.pop()
            self.deck = shuffle_deck(self.discard_pile)
            self.discard_pile = [top_card]
        
        card = self.deck.pop()
        self.player_hands[player_id].append(card)
        self.has_drawn[player_id] = True
        return card
    
    def draw_from_discard(self, player_id: str) -> Optional[Card]:
        """Draw the top card from discard pile"""
        if self.discard_pile:
            card = self.discard_pile.pop()
            self.player_hands[player_id].append(card)
            self.has_drawn[player_id] = True
            return card
        return None
    
    def discard_card(self, player_id: str, card_idx: int) -> Optional[Card]:
        """Discard a card from hand"""
        hand = self.player_hands.get(player_id, [])
        if 0 <= card_idx < len(hand):
            card = hand.pop(card_idx)
            self.discard_pile.append(card)
            self.has_drawn[player_id] = False
            self.advance_turn()
            return card
        return None
    
    def declare(self, player_id: str, melds: List[List[int]]) -> bool:
        """Player declares their hand"""
        hand = self.player_hands.get(player_id, [])
        
        # Validate melds (simplified - just check total cards)
        all_meld_cards = []
        for meld in melds:
            meld_cards = [hand[i] for i in meld if 0 <= i < len(hand)]
            all_meld_cards.extend(meld)
            
            # Check if valid set or sequence
            if not (is_valid_set(meld_cards) or is_valid_sequence(meld_cards)):
                return False
        
        # Check all cards are melded
        if len(set(all_meld_cards)) != 14:  # 13 cards + 1 drawn
            return False
        
        # Valid declaration
        self.winner_id = player_id
        self.is_complete = True
        
        # Calculate points for other players
        for pid, cards in self.player_hands.items():
            if pid != player_id:
                self.player_points[pid] = calculate_rummy_points(cards, [])
        
        return True
    
    def advance_turn(self):
        """Move to the next player"""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.player_order)
    
    def to_dict(self, for_player: Optional[str] = None) -> dict:
        """Convert state to dictionary for transmission"""
        hands = {}
        for player_id, cards in self.player_hands.items():
            if for_player == player_id:
                hands[player_id] = [c.to_dict() for c in cards]
            elif self.is_complete:
                hands[player_id] = [c.to_dict() for c in cards]
            else:
                hands[player_id] = [{"hidden": True}] * len(cards)
        
        return {
            "current_player": self.get_current_player(),
            "player_order": self.player_order,
            "hands": hands,
            "hand_sizes": {p: len(h) for p, h in self.player_hands.items()},
            "discard_top": self.discard_pile[-1].to_dict() if self.discard_pile else None,
            "deck_size": len(self.deck),
            "is_complete": self.is_complete,
            "winner_id": self.winner_id,
            "player_points": self.player_points,
            "has_drawn": self.has_drawn
        }

# ==================== HAND NAME HELPERS ====================

def get_teen_patti_hand_name(cards: List[Card]) -> str:
    """Get the name of a Teen Patti hand"""
    rank, _ = evaluate_teen_patti_hand(cards)
    names = {
        TeenPattiHandRank.TRAIL: "Trail (Three of a Kind)",
        TeenPattiHandRank.PURE_SEQUENCE: "Pure Sequence",
        TeenPattiHandRank.SEQUENCE: "Sequence",
        TeenPattiHandRank.COLOR: "Color (Flush)",
        TeenPattiHandRank.PAIR: "Pair",
        TeenPattiHandRank.HIGH_CARD: "High Card"
    }
    return names.get(rank, "Unknown")

def get_poker_hand_name(cards: List[Card]) -> str:
    """Get the name of a poker hand"""
    rank, _ = evaluate_poker_hand(cards)
    names = {
        PokerHandRank.ROYAL_FLUSH: "Royal Flush",
        PokerHandRank.STRAIGHT_FLUSH: "Straight Flush",
        PokerHandRank.FOUR_OF_A_KIND: "Four of a Kind",
        PokerHandRank.FULL_HOUSE: "Full House",
        PokerHandRank.FLUSH: "Flush",
        PokerHandRank.STRAIGHT: "Straight",
        PokerHandRank.THREE_OF_A_KIND: "Three of a Kind",
        PokerHandRank.TWO_PAIR: "Two Pair",
        PokerHandRank.ONE_PAIR: "One Pair",
        PokerHandRank.HIGH_CARD: "High Card"
    }
    return names.get(rank, "Unknown")
