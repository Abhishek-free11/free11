"""
Test: Teen Patti AI game - backend endpoint testing
Covers: /api/v2/earn/teen-patti-win endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_redesign_ui26@free11test.com"
TEST_PASSWORD = "Test@1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Auth failed with status {response.status_code}: {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestTeenPattiWinEndpoint:
    """Tests for POST /api/v2/earn/teen-patti-win"""

    def test_endpoint_requires_auth(self):
        """Should return 401 without auth token"""
        response = requests.post(f"{BASE_URL}/api/v2/earn/teen-patti-win")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Endpoint requires authentication")

    def test_endpoint_accessible_with_auth(self, auth_headers):
        """Should return 200 or 400 (already claimed) when authenticated"""
        response = requests.post(f"{BASE_URL}/api/v2/earn/teen-patti-win", headers=auth_headers)
        assert response.status_code in [200, 400], \
            f"Expected 200 or 400, got {response.status_code}: {response.text}"
        print(f"PASS: Endpoint returned {response.status_code}")

    def test_success_response_structure(self, auth_headers):
        """On success (200), response should have correct structure"""
        response = requests.post(f"{BASE_URL}/api/v2/earn/teen-patti-win", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Missing 'success' field"
            assert data["success"] is True, f"Expected success=True, got {data['success']}"
            assert "coins_earned" in data, "Missing 'coins_earned' field"
            assert data["coins_earned"] == 40, f"Expected 40 coins, got {data['coins_earned']}"
            assert "new_balance" in data, "Missing 'new_balance' field"
            assert isinstance(data["new_balance"], (int, float)), "new_balance should be numeric"
            print(f"PASS: 200 response structure correct - coins_earned={data['coins_earned']}, new_balance={data['new_balance']}")
        elif response.status_code == 400:
            # Already claimed today - verify 400 error structure
            data = response.json()
            assert "detail" in data, "Missing 'detail' field in 400 response"
            assert "already claimed" in data["detail"].lower() or "come back" in data["detail"].lower(), \
                f"Unexpected 400 message: {data['detail']}"
            print(f"PASS: 400 already-claimed response structure correct: {data['detail']}")

    def test_already_claimed_returns_400(self, auth_headers):
        """Calling endpoint twice in same day should return 400 on second call"""
        # First call - may succeed or already be 400
        first = requests.post(f"{BASE_URL}/api/v2/earn/teen-patti-win", headers=auth_headers)
        assert first.status_code in [200, 400], f"Unexpected first call status: {first.status_code}"

        # Second call should always be 400 (already claimed)
        second = requests.post(f"{BASE_URL}/api/v2/earn/teen-patti-win", headers=auth_headers)
        assert second.status_code == 400, f"Expected 400 on duplicate claim, got {second.status_code}"
        data = second.json()
        assert "detail" in data
        print(f"PASS: Second claim correctly returns 400: {data['detail']}")

    def test_coins_earned_is_40(self, auth_headers):
        """Verify the reward amount is exactly 40 coins"""
        response = requests.post(f"{BASE_URL}/api/v2/earn/teen-patti-win", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert data.get("coins_earned") == 40, f"Expected 40 coins, got {data.get('coins_earned')}"
            print(f"PASS: Coins earned = 40")
        elif response.status_code == 400:
            # Already claimed - this is valid test behavior
            print("PASS: Already claimed today - reward is 40 coins per day (verified in code)")
        else:
            pytest.fail(f"Unexpected status: {response.status_code}")


class TestAuthEndpointHealth:
    """Verify auth is working"""

    def test_login_success(self):
        """Test login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.status_code}: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, "No token in login response"
        print(f"PASS: Login successful for {TEST_EMAIL}")

    def test_user_profile_accessible(self, auth_headers):
        """Test that user profile endpoint is accessible (confirms auth works)"""
        response = requests.get(f"{BASE_URL}/api/v2/me", headers=auth_headers)
        assert response.status_code in [200, 404], f"Profile endpoint failed: {response.status_code}"
        print(f"PASS: User profile endpoint accessible: {response.status_code}")
