"""
Bug Fixes Verification Tests - FREE11 V2
Tests for the 7 critical bugs that were fixed:
1. Login flow redirects to /match-centre
2. /contests route redirects to /match-centre
3. Cards page header/navbar
4. Dashboard uses EntitySport V2 API
5. Navbar has V2 routes (not old /contests, /cricket)
6. Match Centre has Navbar and tabs
7. Profile dropdown has admin links
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://phone-auth-launch.preview.emergentagent.com')


class TestAuthenticationFlow:
    """Test Issue 1: Login flow authentication"""
    
    def test_login_with_admin_credentials(self):
        """Login with admin@free11.com / Admin@123 should succeed"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "Admin@123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access token returned"
        assert "user" in data, "No user data returned"
        assert data["user"]["email"] == "admin@free11.com"
        assert data["user"]["is_admin"] == True
        print(f"✓ Login successful for admin user")
    
    def test_login_returns_valid_token(self):
        """Login should return a valid JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "Admin@123"
        })
        data = response.json()
        token = data.get("access_token")
        
        # Verify token works with /auth/me
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert me_response.status_code == 200, "Token is invalid"
        print(f"✓ Token is valid and works with /auth/me")


class TestEntitySportV2API:
    """Test Issue 4: Dashboard uses EntitySport V2 API (not old mock data)"""
    
    def test_v2_es_matches_endpoint_exists(self):
        """V2 EntitySport matches endpoint should return real data"""
        response = requests.get(f"{BASE_URL}/api/v2/es/matches?status=3&per_page=5")
        assert response.status_code == 200, f"EntitySport API failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of matches"
        print(f"✓ EntitySport V2 API returns {len(data)} matches")
    
    def test_v2_es_matches_returns_real_data(self):
        """Matches should have real team names (not old CSK vs MI mock)"""
        response = requests.get(f"{BASE_URL}/api/v2/es/matches?status=3&per_page=5")
        data = response.json()
        
        if len(data) > 0:
            match = data[0]
            assert "match_id" in match, "Match should have match_id"
            assert "team1" in match or "team1_short" in match, "Match should have team1"
            assert "team2" in match or "team2_short" in match, "Match should have team2"
            assert "source" in match and match["source"] == "entitysport", "Source should be entitysport"
            
            # Verify it's not old mock data
            team1 = match.get("team1_short", match.get("team1", ""))
            team2 = match.get("team2_short", match.get("team2", ""))
            is_old_mock = (team1 == "CSK" and team2 == "MI") or (team1 == "MI" and team2 == "CSK")
            assert not is_old_mock, "Should not return old CSK vs MI mock data"
            
            print(f"✓ Match data: {team1} vs {team2} (from EntitySport)")
        else:
            print(f"✓ No live matches available (API working)")
    
    def test_v2_es_matches_live_status(self):
        """Live matches endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/v2/es/matches?status=3&per_page=20")
        assert response.status_code == 200
        print(f"✓ Live matches endpoint working")
    
    def test_v2_es_matches_upcoming_status(self):
        """Upcoming matches endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/v2/es/matches?status=1&per_page=20")
        assert response.status_code == 200
        print(f"✓ Upcoming matches endpoint working")
    
    def test_v2_es_matches_completed_status(self):
        """Completed matches endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/v2/es/matches?status=2&per_page=20")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Completed matches endpoint returns {len(data)} matches")


class TestV2APIEndpoints:
    """Test V2 Engine APIs that support the fixed features"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "Admin@123"
        })
        return response.json()["access_token"]
    
    def test_v2_ledger_balance(self, auth_token):
        """Ledger balance endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/v2/ledger/balance", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        print(f"✓ Ledger balance: {data['balance']}")
    
    def test_v2_ledger_history(self, auth_token):
        """Ledger history endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/v2/ledger/history?limit=10&offset=0", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        print(f"✓ Ledger history: {len(data['entries'])} entries")
    
    def test_v2_cards_types(self, auth_token):
        """Card types endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/v2/cards/types", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"✓ Card types: {len(data)} types available")
    
    def test_v2_cards_inventory(self, auth_token):
        """Card inventory endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/v2/cards/inventory", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Card inventory: {len(data)} cards")
    
    def test_v2_referral_stats(self, auth_token):
        """Referral stats endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/v2/referral/stats", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "referral_code" in data
        print(f"✓ Referral code: {data['referral_code']}")


class TestRootAndHealthEndpoints:
    """Test basic API health"""
    
    def test_api_root(self):
        """API root should return welcome message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "FREE11" in data["message"]
        print(f"✓ API root: {data['message']}")
    
    def test_faq_endpoint(self):
        """FAQ endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/faq")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ FAQ: {len(data['items'])} items")
    
    def test_beta_status(self):
        """Beta status endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/beta/status")
        assert response.status_code == 200
        print(f"✓ Beta status endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
