"""
Cricket API Service for FREE11
Handles live match data, predictions, and cricket-related features
"""

import os
import httpx
from typing import Optional, Dict, List
from datetime import datetime, timezone
import asyncio
from enum import Enum

# Cricket API Configuration
CRICKET_API_KEY = os.environ.get('CRICKET_API_KEY', 'demo-key')
CRICKET_API_BASE = "https://api.cricapi.com/v1"

class PredictionType(str, Enum):
    BALL_OUTCOME = "ball_outcome"  # 0, 1, 2, 3, 4, 6, wicket, wide, no_ball
    MATCH_WINNER = "match_winner"
    SCORE_AT_6_OVERS = "score_at_6_overs"
    SCORE_AT_10_OVERS = "score_at_10_overs"
    FINAL_SCORE = "final_score"
    TOP_SCORER = "top_scorer"
    MAN_OF_MATCH = "man_of_match"

class CricketService:
    """Service to interact with Cricket API"""
    
    def __init__(self):
        self.api_key = CRICKET_API_KEY
        self.base_url = CRICKET_API_BASE
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_live_matches(self) -> List[Dict]:
        """Get all currently live matches"""
        try:
            response = await self.client.get(
                f"{self.base_url}/currentMatches",
                params={"apikey": self.api_key, "offset": 0}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except Exception as e:
            print(f"Error fetching live matches: {e}")
            return []
    
    async def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Get detailed info about a specific match"""
        try:
            response = await self.client.get(
                f"{self.base_url}/match_info",
                params={"apikey": self.api_key, "id": match_id}
            )
            if response.status_code == 200:
                return response.json().get('data')
            return None
        except Exception as e:
            print(f"Error fetching match details: {e}")
            return None
    
    async def get_match_scorecard(self, match_id: str) -> Optional[Dict]:
        """Get live scorecard for a match"""
        try:
            response = await self.client.get(
                f"{self.base_url}/match_scorecard",
                params={"apikey": self.api_key, "id": match_id}
            )
            if response.status_code == 200:
                return response.json().get('data')
            return None
        except Exception as e:
            print(f"Error fetching scorecard: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Singleton instance
cricket_service = CricketService()

def calculate_prediction_reward(prediction_type: str, accuracy: float = 1.0) -> int:
    """
    Calculate coin reward based on prediction type and accuracy
    
    Args:
        prediction_type: Type of prediction made
        accuracy: How accurate the prediction was (0.0 to 1.0)
    
    Returns:
        Number of coins to award
    """
    base_rewards = {
        PredictionType.BALL_OUTCOME: 5,
        PredictionType.MATCH_WINNER: 50,
        PredictionType.SCORE_AT_6_OVERS: 20,
        PredictionType.SCORE_AT_10_OVERS: 30,
        PredictionType.FINAL_SCORE: 40,
        PredictionType.TOP_SCORER: 35,
        PredictionType.MAN_OF_MATCH: 45,
    }
    
    base = base_rewards.get(prediction_type, 10)
    return int(base * accuracy)

def validate_ball_prediction(prediction: str, actual: str) -> bool:
    """Validate if a ball prediction was correct"""
    valid_outcomes = ['0', '1', '2', '3', '4', '6', 'wicket', 'wide', 'no_ball', 'dot']
    if prediction not in valid_outcomes:
        return False
    return prediction == actual

def calculate_score_accuracy(predicted: int, actual: int, tolerance: int = 10) -> float:
    """
    Calculate accuracy of score prediction
    Perfect match = 1.0
    Within tolerance = 0.5-0.9
    Outside tolerance = 0.0
    """
    diff = abs(predicted - actual)
    if diff == 0:
        return 1.0
    elif diff <= tolerance:
        return max(0.5, 1.0 - (diff / tolerance) * 0.5)
    else:
        return 0.0
