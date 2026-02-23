"""
Backend Tests for FREE11 Phase 1: Cricket Predictions, Ads, and Gift Cards
Tests all APIs from the cricket_routes.py, ads_routes.py, and gift_card_routes.py
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://free11-cricket.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "cricket@free11.com"
TEST_PASSWORD = "cricket123"


class TestAuth:
    """Authentication tests - must pass first"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Shared session for auth tests"""
        return requests.Session()
    
    def test_login_success(self, session):
        """Test login with valid credentials"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Missing access_token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["email"] == TEST_EMAIL
        # Store token for other tests
        pytest.auth_token = data["access_token"]
        print(f"✅ Login successful for {TEST_EMAIL}")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for all tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        # Try registering the user if login fails
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": "Cricket Test User"
        })
        if reg_response.status_code == 200:
            return reg_response.json()["access_token"]
        pytest.skip(f"Authentication failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Headers with authorization"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ==================== CRICKET API TESTS ====================

class TestCricketMatches:
    """Cricket Matches API tests"""
    
    def test_get_all_matches(self):
        """Test GET /api/cricket/matches - returns IPL mock matches"""
        response = requests.get(f"{BASE_URL}/api/cricket/matches")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of matches"
        assert len(data) > 0, "Expected at least one match"
        
        # Check match structure
        match = data[0]
        assert "match_id" in match, "Missing match_id"
        assert "team1" in match, "Missing team1"
        assert "team2" in match, "Missing team2"
        assert "team1_short" in match, "Missing team1_short"
        assert "team2_short" in match, "Missing team2_short"
        assert "venue" in match, "Missing venue"
        assert "status" in match, "Missing status"
        assert "series" in match, "Missing series"
        
        # Verify IPL 2026 data
        assert any("IPL" in m.get("series", "") for m in data), "Expected IPL series matches"
        print(f"✅ Got {len(data)} cricket matches")
    
    def test_get_live_matches(self):
        """Test GET /api/cricket/matches/live - returns live match"""
        response = requests.get(f"{BASE_URL}/api/cricket/matches/live")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of matches"
        
        # If there are live matches, verify structure
        if len(data) > 0:
            live_match = data[0]
            assert live_match["status"] == "live", "Expected live status"
            assert "current_ball" in live_match or live_match.get("current_ball") is not None, "Live match should have current_ball"
            print(f"✅ Found {len(data)} live match(es)")
        else:
            print("⚠️ No live matches currently (mock data may have expired)")
    
    def test_get_specific_match(self):
        """Test GET /api/cricket/matches/{match_id}"""
        # First get list of matches
        response = requests.get(f"{BASE_URL}/api/cricket/matches")
        matches = response.json()
        if len(matches) == 0:
            pytest.skip("No matches available")
        
        match_id = matches[0]["match_id"]
        response = requests.get(f"{BASE_URL}/api/cricket/matches/{match_id}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["match_id"] == match_id
        print(f"✅ Got match details for {match_id}")
    
    def test_get_nonexistent_match(self):
        """Test GET /api/cricket/matches/{id} with invalid ID"""
        response = requests.get(f"{BASE_URL}/api/cricket/matches/nonexistent123")
        assert response.status_code == 404


class TestCricketPredictions:
    """Ball-by-ball and match prediction tests"""
    
    def test_predict_ball_unauthorized(self):
        """Test ball prediction without auth fails"""
        response = requests.post(f"{BASE_URL}/api/cricket/predict/ball", json={
            "match_id": "ipl2026_001",
            "ball_number": "18.4",
            "prediction": "4"
        })
        assert response.status_code == 401, "Should require authentication"
    
    def test_predict_ball_authorized(self, auth_headers):
        """Test POST /api/cricket/predict/ball - ball prediction with coins"""
        # Get live match
        response = requests.get(f"{BASE_URL}/api/cricket/matches/live")
        live_matches = response.json()
        
        if len(live_matches) == 0:
            pytest.skip("No live matches for ball prediction")
        
        live_match = live_matches[0]
        current_ball = live_match.get("current_ball", "18.4")
        
        # Make prediction - use unique ball number to avoid duplicate
        unique_ball = f"{int(time.time()) % 100}.{int(time.time()) % 6}"
        response = requests.post(
            f"{BASE_URL}/api/cricket/predict/ball",
            json={
                "match_id": live_match["match_id"],
                "ball_number": unique_ball,
                "prediction": "4"
            },
            headers=auth_headers
        )
        
        # Could be 200 (success) or 400 (already predicted/not live)
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}, {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "prediction" in data
            assert "actual_result" in data
            assert "is_correct" in data
            assert "coins_earned" in data
            assert "message" in data
            print(f"✅ Ball prediction made - Result: {data['actual_result']}, Earned: {data['coins_earned']} coins")
        else:
            print(f"⚠️ Ball prediction: {response.json().get('detail', 'Unknown error')}")
    
    def test_predict_ball_invalid_prediction(self, auth_headers):
        """Test ball prediction with invalid prediction value"""
        response = requests.post(
            f"{BASE_URL}/api/cricket/predict/ball",
            json={
                "match_id": "ipl2026_001",
                "ball_number": "1.1",
                "prediction": "invalid"
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid prediction" in response.json()["detail"]
    
    def test_predict_match_winner(self, auth_headers):
        """Test POST /api/cricket/predict/match - match prediction"""
        # Get an upcoming match
        response = requests.get(f"{BASE_URL}/api/cricket/matches")
        matches = response.json()
        
        if len(matches) == 0:
            pytest.skip("No matches available")
        
        # Find an upcoming match or use first match
        match = next((m for m in matches if m["status"] == "upcoming"), matches[0])
        
        response = requests.post(
            f"{BASE_URL}/api/cricket/predict/match",
            json={
                "match_id": match["match_id"],
                "prediction_type": "winner",
                "prediction_value": match["team1_short"]
            },
            headers=auth_headers
        )
        
        # Could be 200 (success) or 400 (already predicted)
        assert response.status_code in [200, 400], f"Unexpected: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "prediction_type" in data
            assert "prediction_value" in data
            print(f"✅ Match prediction recorded: {match['team1_short']} to win")
        else:
            print(f"⚠️ Match prediction: {response.json().get('detail', 'Already made')}")
    
    def test_predict_match_invalid_type(self, auth_headers):
        """Test match prediction with invalid type"""
        response = requests.post(
            f"{BASE_URL}/api/cricket/predict/match",
            json={
                "match_id": "ipl2026_001",
                "prediction_type": "invalid_type",
                "prediction_value": "CSK"
            },
            headers=auth_headers
        )
        assert response.status_code == 400


class TestCricketLeaderboard:
    """Cricket leaderboard tests"""
    
    def test_get_leaderboard(self):
        """Test GET /api/cricket/leaderboard - returns top predictors"""
        response = requests.get(f"{BASE_URL}/api/cricket/leaderboard")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list"
        
        # If there are entries, verify structure
        if len(data) > 0:
            entry = data[0]
            assert "rank" in entry, "Missing rank"
            assert "name" in entry, "Missing name"
            assert "correct_predictions" in entry, "Missing correct_predictions"
            assert "coins_earned" in entry, "Missing coins_earned"
            print(f"✅ Leaderboard has {len(data)} entries")
        else:
            print("⚠️ Leaderboard is empty (no predictions yet)")


class TestMyPredictions:
    """User's own predictions tests"""
    
    def test_get_my_predictions(self, auth_headers):
        """Test GET /api/cricket/predictions/my"""
        response = requests.get(
            f"{BASE_URL}/api/cricket/predictions/my",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "ball_predictions" in data
        assert "match_predictions" in data
        assert "stats" in data
        assert isinstance(data["stats"], dict)
        print(f"✅ Got user predictions - {len(data['ball_predictions'])} ball, {len(data['match_predictions'])} match")


# ==================== ADS API TESTS ====================

class TestAdsConfig:
    """Ad configuration tests"""
    
    def test_get_ad_config(self):
        """Test GET /api/ads/config - returns ad settings"""
        response = requests.get(f"{BASE_URL}/api/ads/config")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "enabled" in data
        assert "reward_coins" in data
        assert data["reward_coins"] == 50, "Expected 50 coins per ad"
        assert "max_per_day" in data
        assert data["max_per_day"] == 5, "Expected 5 ads per day max"
        assert "ad_units" in data
        print(f"✅ Ad config: {data['reward_coins']} coins/ad, {data['max_per_day']} max/day")


class TestAdsStatus:
    """Ad status tests"""
    
    def test_get_ad_status_unauthorized(self):
        """Test ad status without auth fails"""
        response = requests.get(f"{BASE_URL}/api/ads/status")
        assert response.status_code == 401
    
    def test_get_ad_status(self, auth_headers):
        """Test GET /api/ads/status - returns user's daily ad status"""
        response = requests.get(f"{BASE_URL}/api/ads/status", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "ads_watched_today" in data
        assert "ads_remaining" in data
        assert "max_per_day" in data
        assert "reward_per_ad" in data
        assert "can_watch" in data
        assert "potential_earnings" in data
        
        # Verify data types
        assert isinstance(data["ads_watched_today"], int)
        assert isinstance(data["ads_remaining"], int)
        assert isinstance(data["can_watch"], bool)
        
        print(f"✅ Ad status: {data['ads_watched_today']} watched, {data['ads_remaining']} remaining")


class TestAdsReward:
    """Ad reward claiming tests"""
    
    def test_claim_ad_reward_unauthorized(self):
        """Test claiming ad reward without auth fails"""
        response = requests.post(f"{BASE_URL}/api/ads/reward", json={"ad_type": "rewarded"})
        assert response.status_code == 401
    
    def test_claim_ad_reward(self, auth_headers):
        """Test POST /api/ads/reward - claim reward after watching ad"""
        # First check status
        status_response = requests.get(f"{BASE_URL}/api/ads/status", headers=auth_headers)
        status = status_response.json()
        
        if not status["can_watch"]:
            print(f"⚠️ Daily ad limit reached, skipping reward claim test")
            pytest.skip("Daily ad limit reached")
        
        # Wait to avoid cooldown
        time.sleep(1)
        
        response = requests.post(
            f"{BASE_URL}/api/ads/reward",
            json={"ad_type": "rewarded"},
            headers=auth_headers
        )
        
        # Could be 200 (success), 400 (limit), or 429 (cooldown)
        assert response.status_code in [200, 400, 429], f"Unexpected: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "coins_earned" in data
            assert data["coins_earned"] == 50
            assert "new_balance" in data
            assert "ads_watched_today" in data
            assert "ads_remaining" in data
            print(f"✅ Ad reward claimed: +{data['coins_earned']} coins")
        elif response.status_code == 429:
            print(f"⚠️ Ad cooldown active: {response.json().get('detail')}")
        else:
            print(f"⚠️ Ad reward: {response.json().get('detail')}")


# ==================== GIFT CARD API TESTS ====================

class TestGiftCardsAvailable:
    """Gift card availability tests"""
    
    def test_get_available_gift_cards_unauthorized(self):
        """Test gift cards without auth fails"""
        response = requests.get(f"{BASE_URL}/api/gift-cards/available")
        assert response.status_code == 401
    
    def test_get_available_gift_cards(self, auth_headers):
        """Test GET /api/gift-cards/available - returns gift card options"""
        response = requests.get(
            f"{BASE_URL}/api/gift-cards/available",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of gift card options"
        
        # If there are cards, verify structure
        if len(data) > 0:
            card = data[0]
            assert "brand" in card
            assert "value" in card
            assert "coin_price" in card
            assert "available_count" in card
            print(f"✅ Got {len(data)} gift card options")
        else:
            print("⚠️ No gift cards available (need admin to upload)")


class TestGiftCardStats:
    """Gift card stats tests"""
    
    def test_get_gift_card_stats(self):
        """Test GET /api/gift-cards/stats"""
        response = requests.get(f"{BASE_URL}/api/gift-cards/stats")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "total_redemptions" in data
        assert "total_value_redeemed" in data
        print(f"✅ Gift card stats: {data['total_redemptions']} total redemptions")


# ==================== INTEGRATION TESTS ====================

class TestEndToEndFlow:
    """End-to-end integration tests"""
    
    def test_cricket_prediction_flow(self, auth_headers):
        """Test full cricket prediction flow"""
        # 1. Get matches
        matches_res = requests.get(f"{BASE_URL}/api/cricket/matches")
        assert matches_res.status_code == 200
        matches = matches_res.json()
        assert len(matches) > 0
        
        # 2. Get leaderboard
        leaderboard_res = requests.get(f"{BASE_URL}/api/cricket/leaderboard")
        assert leaderboard_res.status_code == 200
        
        # 3. Get user predictions
        my_preds_res = requests.get(
            f"{BASE_URL}/api/cricket/predictions/my",
            headers=auth_headers
        )
        assert my_preds_res.status_code == 200
        
        print("✅ Cricket prediction flow works end-to-end")
    
    def test_ads_flow(self, auth_headers):
        """Test full ads flow"""
        # 1. Get config
        config_res = requests.get(f"{BASE_URL}/api/ads/config")
        assert config_res.status_code == 200
        
        # 2. Get status
        status_res = requests.get(f"{BASE_URL}/api/ads/status", headers=auth_headers)
        assert status_res.status_code == 200
        
        print("✅ Ads flow works end-to-end")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
