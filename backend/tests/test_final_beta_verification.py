"""
FREE11 Final Beta Verification Tests
Tests all critical endpoints with multi-source API verification
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://skill-sports-app.preview.emergentagent.com')

class TestHealthAndBasics:
    """Basic health and auth tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "FREE11" in data.get("message", "")
    
    def test_login_success(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "admin"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@free11.com"
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestCricketLiveData:
    """Tests for multi-source live cricket data API"""
    
    def test_live_cricket_endpoint(self):
        """Test /api/cricket/live returns data from API or mock fallback"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "source" in data
        assert "matches" in data
        assert "count" in data
        assert "is_mock" in data
        
        # Source should be one of: cricketdata_api, thesportsdb_api, mock_data, no_data
        valid_sources = ['cricketdata_api', 'thesportsdb_api', 'mock_data', 'no_data', 'error']
        assert data["source"] in valid_sources, f"Unexpected source: {data['source']}"
        
        # If we have matches, verify structure
        if data["count"] > 0:
            assert len(data["matches"]) > 0
    
    def test_live_cricket_match_structure(self):
        """Verify live matches have proper structure"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        assert response.status_code == 200
        data = response.json()
        
        matches = data["matches"]
        if len(matches) > 0:
            first_match = matches[0]
            
            # Check required fields
            assert "id" in first_match
            assert "team1" in first_match
            assert "team2" in first_match
            assert "team1_short" in first_match
            assert "team2_short" in first_match
            assert "status" in first_match
            assert "source" in first_match
            assert "is_mock" in first_match
    
    def test_mock_data_is_labeled(self):
        """Verify mock data is properly labeled"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        assert response.status_code == 200
        data = response.json()
        
        if data["source"] == "mock_data":
            # is_mock should be True
            assert data["is_mock"] == True
            # Notice should warn about mock data
            assert data.get("notice") is not None
            assert "MOCK" in data["notice"].upper() or "DEMO" in data["notice"].upper()


class TestFantasyPlayersAPI:
    """Tests for Fantasy team player API - contextual player generation"""
    
    @pytest.fixture
    def nz_sl_match_id(self):
        """Get NZ vs SL match ID"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        data = response.json()
        
        for match in data["matches"]:
            if "NZ" in match.get("team1_short", "") or "NZ" in match.get("team2_short", ""):
                return match["id"]
        
        # Fallback to first match ID
        return data["matches"][0]["id"] if data["matches"] else "139404"
    
    def test_players_endpoint_returns_data(self, nz_sl_match_id):
        """Test players endpoint returns players"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{nz_sl_match_id}/players")
        assert response.status_code == 200
        data = response.json()
        
        assert "players" in data
        assert len(data["players"]) >= 20, f"Expected at least 20 players, got {len(data['players'])}"
    
    def test_players_have_nz_players(self, nz_sl_match_id):
        """Verify NZ players are included for NZ vs SL match"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{nz_sl_match_id}/players")
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected NZ players
        nz_player_names = ["Tom Latham", "Devon Conway", "Kane Williamson", "Tim Southee", 
                          "Lockie Ferguson", "Matt Henry", "Glenn Phillips", "Rachin Ravindra"]
        
        players = data["players"]
        found_nz_players = [p["name"] for p in players if p.get("team_short") == "NZ"]
        
        # At least some NZ players should match
        matches = [name for name in nz_player_names if name in found_nz_players]
        assert len(matches) >= 3, f"Expected at least 3 NZ players, found: {found_nz_players}"
    
    def test_players_have_sl_players(self, nz_sl_match_id):
        """Verify SL players are included for NZ vs SL match"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{nz_sl_match_id}/players")
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected SL players
        sl_player_names = ["Kusal Perera", "Kusal Mendis", "Pathum Nissanka", 
                          "Matheesha Pathirana", "Wanindu Hasaranga", "Maheesh Theekshana"]
        
        players = data["players"]
        found_sl_players = [p["name"] for p in players if p.get("team_short") == "SL"]
        
        # At least some SL players should match
        matches = [name for name in sl_player_names if name in found_sl_players]
        assert len(matches) >= 2, f"Expected at least 2 SL players, found: {found_sl_players}"
    
    def test_players_have_all_roles(self, nz_sl_match_id):
        """Verify all roles are represented"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{nz_sl_match_id}/players")
        assert response.status_code == 200
        data = response.json()
        
        roles = set(p["role"] for p in data["players"])
        
        assert "WK" in roles, "Missing Wicket Keepers"
        assert "BAT" in roles, "Missing Batsmen"
        assert "ALL" in roles, "Missing All-Rounders"
        assert "BOWL" in roles, "Missing Bowlers"


class TestAuthenticatedEndpoints:
    """Tests requiring authentication"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "admin"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_get_user_profile(self, auth_token):
        """Test /api/auth/me endpoint"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "email" in data
        assert data["email"] == "admin@free11.com"
        assert "coins_balance" in data
    
    def test_get_user_stats(self, auth_token):
        """Test /api/user/stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/user/stats", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "activities_count" in data or "redemptions_count" in data
    
    def test_get_demand_progress(self, auth_token):
        """Test /api/user/demand-progress endpoint"""
        response = requests.get(f"{BASE_URL}/api/user/demand-progress", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "coins_balance" in data
        assert "rank" in data
    
    def test_get_leaderboard(self, auth_token):
        """Test /api/leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/leaderboard", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should be a list
        assert isinstance(data, list)


class TestCardGamesAPI:
    """Tests for card games functionality"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "admin"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_games_config(self):
        """Test /api/games/config endpoint"""
        response = requests.get(f"{BASE_URL}/api/games/config")
        assert response.status_code == 200
        data = response.json()
        
        # Check for game types (games is a dict, not list)
        assert "games" in data
        games = data["games"]
        assert "teen_patti" in games
        assert "rummy" in games
        assert "poker" in games
        
        # Verify structure
        assert games["teen_patti"]["name"] == "Teen Patti"
        assert games["rummy"]["name"] == "Rummy"
    
    def test_get_rooms_requires_auth(self):
        """Test that rooms endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/games/teen_patti/rooms")
        # Should return 401 or similar auth error
        assert response.status_code in [401, 403]
    
    def test_get_rooms_with_auth(self, auth_token):
        """Test getting rooms list with authentication"""
        response = requests.get(f"{BASE_URL}/api/games/teen_patti/rooms", 
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        # Should return rooms wrapper
        assert "rooms" in data
        assert "game_type" in data
        assert data["game_type"] == "teen_patti"
        assert isinstance(data["rooms"], list)


class TestShopAndProducts:
    """Tests for shop and redemption"""
    
    def test_get_products(self):
        """Test /api/products endpoint"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            product = data[0]
            assert "name" in product
            assert "coin_price" in product


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
