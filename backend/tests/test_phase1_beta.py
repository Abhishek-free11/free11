"""
Phase 1 Beta Tests for FREE11
Tests: Age Gate, Geo-blocking, Feature Flags, Over Outcome, Match Winner, 
Ball-by-Ball Limit, Private Leagues, Fantasy Players, Shop/Redemption
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "abhishek@free11.com"
ADMIN_PASSWORD = "admin123"
BETA_CODES = ["BETA01", "BETA02"]

# Test user tracking
TEST_PREFIX = "TEST_PHASE1_"

class TestFeatureFlags:
    """Test Feature Flags API at /api/features/flags"""
    
    def test_get_all_feature_flags(self):
        """GET /api/features/flags - Get all feature flags"""
        response = requests.get(f"{BASE_URL}/api/features/flags")
        assert response.status_code == 200
        
        data = response.json()
        assert "flags" in data
        assert "environment" in data
        
        # Verify key feature flags exist
        flags = data["flags"]
        assert "fantasy_contests" in flags
        assert "over_predictions" in flags
        assert "match_predictions" in flags
        assert "ball_by_ball" in flags
        assert "ball_by_ball_limit" in flags
        assert "private_leagues" in flags
        print(f"✅ Feature flags: {flags}")
    
    def test_get_single_feature_flag(self):
        """GET /api/features/flags/{flag_name}"""
        response = requests.get(f"{BASE_URL}/api/features/flags/ball_by_ball_limit")
        assert response.status_code == 200
        
        data = response.json()
        assert data["flag"] == "ball_by_ball_limit"
        assert data["value"] == 20  # Ball-by-ball limit should be 20
        print(f"✅ Ball-by-ball limit: {data['value']}")
    
    def test_get_blocked_states(self):
        """GET /api/features/blocked-states"""
        response = requests.get(f"{BASE_URL}/api/features/blocked-states")
        assert response.status_code == 200
        
        data = response.json()
        assert "blocked_states" in data
        assert "blocked_state_names" in data
        
        # Verify blocked states: AP, Telangana, Assam, Odisha, Sikkim, Nagaland
        blocked = data["blocked_states"]
        assert "AP" in blocked  # Andhra Pradesh
        assert "TG" in blocked  # Telangana
        assert "AS" in blocked  # Assam
        assert "OD" in blocked  # Odisha
        assert "SK" in blocked  # Sikkim
        assert "NL" in blocked  # Nagaland
        print(f"✅ Blocked states: {list(blocked.keys())}")


class TestAgeGate:
    """Test Age Gate verification at /api/features/verify-age"""
    
    def test_age_gate_over_18(self):
        """POST /api/features/verify-age - User is 18+"""
        # Calculate date 25 years ago
        dob = (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/features/verify-age",
            json={"date_of_birth": dob}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == True
        assert data["age"] >= 18
        print(f"✅ Age verification passed: Age {data['age']}")
    
    def test_age_gate_under_18(self):
        """POST /api/features/verify-age - User is under 18"""
        # Calculate date 16 years ago
        dob = (datetime.now() - timedelta(days=365*16)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/features/verify-age",
            json={"date_of_birth": dob}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == False
        assert data["age"] < 18
        assert "18" in data["message"]
        print(f"✅ Age gate blocked underage user: {data['message']}")
    
    def test_age_gate_invalid_format(self):
        """POST /api/features/verify-age - Invalid date format"""
        response = requests.post(
            f"{BASE_URL}/api/features/verify-age",
            json={"date_of_birth": "invalid-date"}
        )
        assert response.status_code == 400
        print("✅ Invalid date format rejected")


class TestGeoBlocking:
    """Test Geo-blocking at /api/features/check-geo"""
    
    def test_geo_allowed_state(self):
        """POST /api/features/check-geo - Allowed state (Maharashtra)"""
        response = requests.post(
            f"{BASE_URL}/api/features/check-geo",
            json={"state": "Maharashtra"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == True
        print(f"✅ Maharashtra allowed: {data['message']}")
    
    def test_geo_blocked_state_andhra(self):
        """POST /api/features/check-geo - Blocked state (Andhra Pradesh)"""
        response = requests.post(
            f"{BASE_URL}/api/features/check-geo",
            json={"state": "Andhra Pradesh", "state_code": "AP"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == False
        assert "not available" in data["message"].lower()
        print(f"✅ Andhra Pradesh blocked: {data['message']}")
    
    def test_geo_blocked_state_telangana(self):
        """POST /api/features/check-geo - Blocked state (Telangana)"""
        response = requests.post(
            f"{BASE_URL}/api/features/check-geo",
            json={"state": "Telangana", "state_code": "TG"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == False
        print(f"✅ Telangana blocked: {data['message']}")
    
    def test_geo_blocked_state_sikkim(self):
        """POST /api/features/check-geo - Blocked state (Sikkim)"""
        response = requests.post(
            f"{BASE_URL}/api/features/check-geo",
            json={"state": "Sikkim"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == False
        print(f"✅ Sikkim blocked: {data['message']}")


class TestComplianceCheck:
    """Test full compliance check at /api/features/compliance-check"""
    
    def test_compliance_all_pass(self):
        """POST /api/features/compliance-check - Valid user"""
        dob = (datetime.now() - timedelta(days=365*25)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/features/compliance-check",
            params={
                "date_of_birth": dob,
                "state": "Maharashtra"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == True
        assert len(data["errors"]) == 0
        print("✅ Full compliance check passed")
    
    def test_compliance_underage_blocked_state(self):
        """POST /api/features/compliance-check - Underage in blocked state"""
        dob = (datetime.now() - timedelta(days=365*16)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/features/compliance-check",
            params={
                "date_of_birth": dob,
                "state": "Telangana",
                "state_code": "TG"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] == False
        assert len(data["errors"]) == 2  # Both age and geo errors
        print(f"✅ Multiple compliance failures detected: {len(data['errors'])} errors")


class TestBetaRegistration:
    """Test Beta registration with invite codes"""
    
    def test_beta_status(self):
        """GET /api/beta/status"""
        response = requests.get(f"{BASE_URL}/api/beta/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "require_invite_code" in data
        print(f"✅ Beta status: require_invite_code={data['require_invite_code']}")
    
    def test_validate_invite_code_valid(self):
        """POST /api/beta/validate-invite - Valid code"""
        response = requests.post(
            f"{BASE_URL}/api/beta/validate-invite",
            json={"code": "BETA02"}  # BETA01 may be used up
        )
        # May be 200 (valid) or 400 (used up)
        assert response.status_code in [200, 400]
        print(f"✅ BETA02 validation: {response.json()}")
    
    def test_validate_invite_code_invalid(self):
        """POST /api/beta/validate-invite - Invalid code"""
        response = requests.post(
            f"{BASE_URL}/api/beta/validate-invite",
            json={"code": "INVALID123"}
        )
        assert response.status_code in [400, 404]
        print("✅ Invalid invite code rejected")


class TestCricketMatches:
    """Test Cricket matches API"""
    
    def test_get_matches(self):
        """GET /api/cricket/matches"""
        response = requests.get(f"{BASE_URL}/api/cricket/matches")
        assert response.status_code == 200
        
        matches = response.json()
        assert isinstance(matches, list)
        if matches:
            match = matches[0]
            assert "match_id" in match
            assert "team1" in match
            assert "team2" in match
            assert "status" in match
            print(f"✅ Found {len(matches)} matches, first: {match.get('team1_short')} vs {match.get('team2_short')}")
        else:
            print("✅ Matches API working (no matches yet)")
    
    def test_get_live_matches(self):
        """GET /api/cricket/matches/live"""
        response = requests.get(f"{BASE_URL}/api/cricket/matches/live")
        assert response.status_code == 200
        
        matches = response.json()
        assert isinstance(matches, list)
        live_count = len(matches)
        print(f"✅ Live matches: {live_count}")


class TestCricketPredictions:
    """Test Cricket predictions - Over, Winner, Ball-by-Ball"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user with auth"""
        self.session = requests.Session()
        self.token = self._get_or_create_test_user()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def _get_or_create_test_user(self):
        """Get existing test user or create new one"""
        # Try login with existing test user
        test_email = f"test_cricket@free11.com"
        test_password = "cricket123"
        
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": test_password}
        )
        
        if login_response.status_code == 200:
            return login_response.json().get("access_token")
        
        # If login fails, skip authenticated tests
        return None
    
    def test_get_cricket_leaderboard(self):
        """GET /api/cricket/leaderboard"""
        response = requests.get(f"{BASE_URL}/api/cricket/leaderboard")
        assert response.status_code == 200
        print("✅ Cricket leaderboard accessible")
    
    def test_over_prediction_endpoint_exists(self):
        """POST /api/cricket/predict/over - Endpoint exists"""
        if not self.token:
            pytest.skip("No auth token available")
        
        # Get a live match
        matches_response = self.session.get(f"{BASE_URL}/api/cricket/matches/live")
        matches = matches_response.json()
        
        if not matches:
            pytest.skip("No live matches available")
        
        match_id = matches[0].get("match_id")
        
        response = self.session.post(
            f"{BASE_URL}/api/cricket/predict/over",
            json={
                "match_id": match_id,
                "over_number": 1,
                "prediction": "6-10"
            }
        )
        # Should be 200 (success) or 400 (already predicted/not live)
        assert response.status_code in [200, 400]
        print(f"✅ Over prediction endpoint working: {response.status_code}")
    
    def test_winner_prediction_endpoint_exists(self):
        """POST /api/cricket/predict/winner - Endpoint exists"""
        if not self.token:
            pytest.skip("No auth token available")
        
        # Get a live match
        matches_response = self.session.get(f"{BASE_URL}/api/cricket/matches/live")
        matches = matches_response.json()
        
        if not matches:
            pytest.skip("No live matches available")
        
        match = matches[0]
        match_id = match.get("match_id")
        team = match.get("team1_short")
        
        response = self.session.post(
            f"{BASE_URL}/api/cricket/predict/winner",
            json={
                "match_id": match_id,
                "winner": team
            }
        )
        # Should be 200 (success) or 400 (already predicted)
        assert response.status_code in [200, 400]
        print(f"✅ Winner prediction endpoint working: {response.status_code}")
    
    def test_prediction_status(self):
        """GET /api/cricket/matches/{match_id}/prediction-status"""
        if not self.token:
            pytest.skip("No auth token available")
        
        # Get a match
        matches_response = self.session.get(f"{BASE_URL}/api/cricket/matches")
        matches = matches_response.json()
        
        if not matches:
            pytest.skip("No matches available")
        
        match_id = matches[0].get("match_id")
        
        response = self.session.get(f"{BASE_URL}/api/cricket/matches/{match_id}/prediction-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "ball_predictions" in data
        assert data["ball_predictions"]["limit"] == 20  # Ball limit should be 20
        print(f"✅ Prediction status: {data['ball_predictions']}")


class TestPrivateLeagues:
    """Test Private Leagues at /api/leagues/*"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user with auth"""
        self.session = requests.Session()
        self.token = self._get_auth_token()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def _get_auth_token(self):
        """Get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_cricket@free11.com", "password": "cricket123"}
        )
        if login_response.status_code == 200:
            return login_response.json().get("access_token")
        return None
    
    def test_create_league(self):
        """POST /api/leagues/create"""
        if not self.token:
            pytest.skip("No auth token available")
        
        unique_name = f"{TEST_PREFIX}League_{uuid.uuid4().hex[:8]}"
        
        response = self.session.post(
            f"{BASE_URL}/api/leagues/create",
            json={
                "name": unique_name,
                "description": "Test league for Phase 1 Beta",
                "max_members": 20,
                "scoring_type": "accuracy"
            }
        )
        
        # May be 200 (created) or 400 (limit reached)
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert "league" in data
            assert "join_code" in data
            assert len(data["join_code"]) == 8
            print(f"✅ League created: {data['league']['name']}, code: {data['join_code']}")
        else:
            print(f"✅ League create limit reached: {response.json()}")
    
    def test_get_my_leagues(self):
        """GET /api/leagues/my"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = self.session.get(f"{BASE_URL}/api/leagues/my")
        assert response.status_code == 200
        
        data = response.json()
        assert "leagues" in data
        assert "total" in data
        print(f"✅ User leagues: {data['total']}")
    
    def test_join_league_invalid_code(self):
        """POST /api/leagues/join - Invalid code"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = self.session.post(
            f"{BASE_URL}/api/leagues/join",
            json={"code": "INVALID1"}
        )
        assert response.status_code == 404
        print("✅ Invalid league code rejected")


class TestFantasyPlayers:
    """Test Fantasy Players API"""
    
    def test_get_players_for_match(self):
        """GET /api/fantasy/matches/{match_id}/players"""
        # Get a match first
        matches_response = requests.get(f"{BASE_URL}/api/cricket/matches")
        matches = matches_response.json()
        
        if not matches:
            pytest.skip("No matches available")
        
        match_id = matches[0].get("match_id")
        
        response = requests.get(f"{BASE_URL}/api/fantasy/matches/{match_id}/players")
        assert response.status_code == 200
        
        data = response.json()
        assert "players" in data
        assert "by_role" in data
        assert "constraints" in data
        
        # Verify constraints
        constraints = data["constraints"]
        assert constraints["max_players"] == 11
        assert constraints["credit_limit"] == 100
        
        print(f"✅ Fantasy players: {len(data['players'])} players for match {match_id}")
    
    def test_get_match_contests(self):
        """GET /api/fantasy/matches/{match_id}/contests"""
        # Get a match first
        matches_response = requests.get(f"{BASE_URL}/api/cricket/matches")
        matches = matches_response.json()
        
        if not matches:
            pytest.skip("No matches available")
        
        match_id = matches[0].get("match_id")
        
        response = requests.get(f"{BASE_URL}/api/fantasy/matches/{match_id}/contests")
        assert response.status_code == 200
        
        data = response.json()
        assert "contests" in data
        print(f"✅ Fantasy contests: {data['total']} contests for match {match_id}")
    
    def test_get_points_system(self):
        """GET /api/fantasy/points-system"""
        response = requests.get(f"{BASE_URL}/api/fantasy/points-system")
        assert response.status_code == 200
        
        data = response.json()
        assert "batting" in data
        assert "bowling" in data
        assert "fielding" in data
        assert "captain_multiplier" in data
        assert data["captain_multiplier"] == 2
        print(f"✅ Fantasy points system retrieved")


class TestShopRedemption:
    """Test Shop and Redemption still works"""
    
    def test_get_products(self):
        """GET /api/products"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        
        products = response.json()
        assert isinstance(products, list)
        print(f"✅ Products: {len(products)} available")
    
    def test_get_products_by_category(self):
        """GET /api/products?category=recharge"""
        response = requests.get(f"{BASE_URL}/api/products", params={"category": "recharge"})
        assert response.status_code == 200
        
        products = response.json()
        print(f"✅ Recharge products: {len(products)}")
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Setup test user with auth for redemption tests"""
        self.session = requests.Session()
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_cricket@free11.com", "password": "cricket123"}
        )
        if login_response.status_code == 200:
            self.token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            self.token = None
    
    def test_get_redemptions(self):
        """GET /api/redemptions"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = self.session.get(f"{BASE_URL}/api/redemptions")
        assert response.status_code == 200
        
        redemptions = response.json()
        assert isinstance(redemptions, list)
        print(f"✅ User redemptions: {len(redemptions)}")


class TestDashboardCommunity:
    """Test Dashboard 'Join the Community' section without Watch Ads"""
    
    def test_dashboard_api(self):
        """Verify dashboard endpoints don't have Watch Ads references"""
        # Check user stats
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_cricket@free11.com", "password": "cricket123"}
        )
        
        if login_response.status_code != 200:
            pytest.skip("No auth token available")
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get demand progress
        response = requests.get(f"{BASE_URL}/api/user/demand-progress", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Verify no ads-related fields
        response_text = str(data).lower()
        assert "watch_ads" not in response_text
        assert "ads_watched" not in response_text
        print("✅ Dashboard API has no Watch Ads references")


class TestNoAdsFeature:
    """Verify Ads have been removed from the system"""
    
    def test_no_ads_endpoints(self):
        """Verify no ads-related endpoints exist"""
        ads_endpoints = [
            "/api/ads/watch",
            "/api/ads/reward",
            "/api/earn/watch-ad"
        ]
        
        for endpoint in ads_endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            # Should be 404 (not found) or 422 (method not allowed)
            assert response.status_code in [404, 405, 422]
        
        print("✅ No ads endpoints found")
    
    def test_tasks_no_ads(self):
        """GET /api/tasks - Verify no watch ad tasks"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_cricket@free11.com", "password": "cricket123"}
        )
        
        if login_response.status_code != 200:
            pytest.skip("No auth token available")
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/tasks", headers=headers)
        assert response.status_code == 200
        
        tasks = response.json()
        for task in tasks:
            task_str = str(task).lower()
            assert "watch ad" not in task_str
            assert "video ad" not in task_str
        
        print(f"✅ Tasks ({len(tasks)}) have no ads")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
