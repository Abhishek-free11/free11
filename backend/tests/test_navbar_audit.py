"""
Test suite for FREE11 Platform Audit after Navbar Fix
Tests: API endpoints, health, routes accessibility
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pwa-submission.preview.emergentagent.com')
BASE_URL = BASE_URL.rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASSWORD = "Admin@123"


class TestHealthAndBasics:
    """Test health endpoint and basic API functionality"""
    
    def test_health_endpoint(self):
        """Test /api/health returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        print(f"Health: {data}")
    
    def test_api_accessible(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200


class TestAuthentication:
    """Test login and authentication flows"""
    
    def test_admin_login(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"Login successful. User: {data['user'].get('email')}")
        return data["access_token"]
    
    def test_login_wrong_password(self):
        """Test login fails with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400]


@pytest.fixture
def auth_token():
    """Get authentication token for protected endpoints"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Authentication failed")


@pytest.fixture
def auth_headers(auth_token):
    """Get auth headers with token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestTutorialAPI:
    """Test tutorial status API - critical for returning user experience"""
    
    def test_tutorial_status(self, auth_headers):
        """Test tutorial status endpoint returns completed=true for admin"""
        response = requests.get(f"{BASE_URL}/api/user/tutorial-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tutorial_completed" in data
        print(f"Tutorial status: {data}")
        # Admin should have tutorial_completed=True
        assert data["tutorial_completed"] == True, "Admin user should have tutorial_completed=True"


class TestEntitySportMatches:
    """Test EntitySport matches API - real data source"""
    
    def test_upcoming_matches(self, auth_headers):
        """Test fetching upcoming matches"""
        response = requests.get(f"{BASE_URL}/api/v2/es/matches?status=1&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Upcoming matches count: {len(data)}")
    
    def test_live_matches(self, auth_headers):
        """Test fetching live matches"""
        response = requests.get(f"{BASE_URL}/api/v2/es/matches?status=3&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Live matches count: {len(data)}")
    
    def test_completed_matches(self, auth_headers):
        """Test fetching completed matches"""
        response = requests.get(f"{BASE_URL}/api/v2/es/matches?status=2&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Completed matches count: {len(data)}")


class TestFreeBucksAPI:
    """Test FREE Bucks endpoints"""
    
    def test_freebucks_balance(self, auth_headers):
        """Test FREE Bucks balance endpoint"""
        response = requests.get(f"{BASE_URL}/api/v2/freebucks/balance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data or "freebucks" in data or "wallet" in data
        print(f"FREE Bucks: {data}")
    
    def test_freebucks_packages(self, auth_headers):
        """Test FREE Bucks packages endpoint"""
        response = requests.get(f"{BASE_URL}/api/v2/freebucks/packages", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Packages returned as dict with starter/pro/elite keys
        assert isinstance(data, dict)
        assert "starter" in data or "pro" in data
        print(f"Packages: {list(data.keys())}")


class TestCardsAPI:
    """Test Power-Ups/Cards endpoints"""
    
    def test_cards_inventory(self, auth_headers):
        """Test cards inventory endpoint"""
        response = requests.get(f"{BASE_URL}/api/v2/cards/inventory", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Cards inventory: {data}")


class TestPredictionsAPI:
    """Test predictions endpoints"""
    
    def test_predictions_stats(self, auth_headers):
        """Test predictions stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/v2/predictions/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Prediction stats: {data}")


class TestUserAPI:
    """Test user endpoints"""
    
    def test_user_stats(self, auth_headers):
        """Test user stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/user/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"User stats: {data}")
    
    def test_user_profile_me(self, auth_headers):
        """Test /auth/me endpoint"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == ADMIN_EMAIL
        print(f"Profile: {data.get('name')} ({data.get('email')})")


class TestLedgerAPI:
    """Test wallet/ledger endpoints"""
    
    def test_ledger_balance(self, auth_headers):
        """Test ledger balance endpoint"""
        response = requests.get(f"{BASE_URL}/api/v2/ledger/balance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Ledger balance: {data}")
    
    def test_ledger_history(self, auth_headers):
        """Test ledger history endpoint"""
        response = requests.get(f"{BASE_URL}/api/v2/ledger/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Ledger history: {type(data)}")


class TestReferralsAPI:
    """Test referral endpoints"""
    
    def test_referral_code(self, auth_headers):
        """Test getting referral code"""
        response = requests.get(f"{BASE_URL}/api/v2/referral/code", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "code" in data or "referral_code" in data
        print(f"Referral: {data}")
    
    def test_referral_stats(self, auth_headers):
        """Test getting referral stats"""
        response = requests.get(f"{BASE_URL}/api/v2/referral/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Referral stats: {data}")


class TestGamesAPI:
    """Test card games endpoints (coin-earning games)"""
    
    def test_coins_balance(self, auth_headers):
        """Test coins balance endpoint"""
        response = requests.get(f"{BASE_URL}/api/coins/balance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Coins balance: {data}")
    
    def test_tasks(self, auth_headers):
        """Test tasks endpoint"""
        response = requests.get(f"{BASE_URL}/api/tasks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Tasks: {type(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
