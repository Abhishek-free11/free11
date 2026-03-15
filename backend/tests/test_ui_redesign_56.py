"""
UI Redesign iteration 56 - backend regression tests
Tests: admin analytics-360, bottom nav regression, session timer analytics
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASSWORD = "Admin@123"
TEST_EMAIL = "test_redesign_ui26@free11test.com"
TEST_PASSWORD = "Test@1234"


def get_token(email, password):
    """Helper: get JWT token for a user."""
    resp = requests.post(f"{BASE_URL}/api/auth/login",
                         json={"email": email, "password": password},
                         timeout=15)
    if resp.status_code == 200:
        return resp.json().get("token") or resp.json().get("access_token")
    return None


class TestAdminAnalyticsRegression:
    """Regression: /api/admin/analytics-360 must return 200 for admin (iteration 55 fix)"""

    def test_admin_analytics_360_returns_200(self):
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        if not token:
            pytest.skip("Admin login failed")
        resp = requests.get(
            f"{BASE_URL}/api/admin/analytics-360",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        # Verify key fields present
        assert "high_level" in data, "Missing high_level in analytics-360 response"
        assert "funnel" in data, "Missing funnel in analytics-360 response"
        print(f"PASS: admin analytics-360 returned 200 with {len(data)} top-level keys")

    def test_admin_analytics_360_requires_auth(self):
        resp = requests.get(
            f"{BASE_URL}/api/admin/analytics-360",
            timeout=15
        )
        assert resp.status_code in [401, 403], \
            f"Expected 401/403 for unauthenticated, got {resp.status_code}"
        print(f"PASS: analytics-360 returns {resp.status_code} for unauthenticated request")

    def test_admin_analytics_360_requires_admin_role(self):
        token = get_token(TEST_EMAIL, TEST_PASSWORD)
        if not token:
            pytest.skip("Test user login failed")
        resp = requests.get(
            f"{BASE_URL}/api/admin/analytics-360",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        assert resp.status_code in [401, 403], \
            f"Expected 401/403 for non-admin, got {resp.status_code}"
        print(f"PASS: analytics-360 returns {resp.status_code} for non-admin user")


class TestAnalyticsEventEndpoint:
    """Analytics event tracking endpoints used by initSessionTimer and trackFirstPredictionTime"""

    def test_analytics_event_authenticated(self):
        token = get_token(TEST_EMAIL, TEST_PASSWORD)
        if not token:
            pytest.skip("Test user login failed")
        resp = requests.post(
            f"{BASE_URL}/api/v2/analytics/event",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"event": "time_to_first_prediction", "properties": {"duration_seconds": 30, "under_45s": True}},
            timeout=15
        )
        # Accept 200 or 201 (event accepted)
        assert resp.status_code in [200, 201], \
            f"Analytics event POST returned {resp.status_code}: {resp.text[:200]}"
        print(f"PASS: analytics event endpoint returned {resp.status_code}")

    def test_analytics_event_anon(self):
        resp = requests.post(
            f"{BASE_URL}/api/v2/analytics/event/anon",
            headers={"Content-Type": "application/json"},
            json={"event": "page_view", "properties": {"page": "/dashboard"}},
            timeout=15
        )
        assert resp.status_code in [200, 201], \
            f"Anon analytics event POST returned {resp.status_code}: {resp.text[:200]}"
        print(f"PASS: anon analytics event endpoint returned {resp.status_code}")


class TestDashboardAPIEndpoints:
    """APIs consumed by the new Dashboard (for new user flow)"""

    def test_login_test_user(self):
        token = get_token(TEST_EMAIL, TEST_PASSWORD)
        assert token is not None, "Test user login failed"
        print(f"PASS: Test user login successful, token starts with {token[:20]}...")

    def test_user_profile_has_total_predictions(self):
        """isNewUser logic checks user.total_predictions === 0"""
        token = get_token(TEST_EMAIL, TEST_PASSWORD)
        if not token:
            pytest.skip("Test user login failed")
        resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_predictions" in data, "Missing total_predictions in user profile"
        print(f"PASS: user has total_predictions={data['total_predictions']}")

    def test_v2_matches_endpoint(self):
        """Dashboard fetches matches for QuickPredict via v2EsGetMatches"""
        token = get_token(TEST_EMAIL, TEST_PASSWORD)
        if not token:
            pytest.skip("Test user login failed")
        # Status 3 = live matches
        resp = requests.get(
            f"{BASE_URL}/api/v2/es/matches?status=3&limit=5",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        assert resp.status_code in [200, 404], \
            f"Matches endpoint returned {resp.status_code}: {resp.text[:200]}"
        print(f"PASS: /api/v2/es/matches returned {resp.status_code}")

    def test_demand_progress_endpoint(self):
        """Dashboard fetches demand progress on mount"""
        token = get_token(TEST_EMAIL, TEST_PASSWORD)
        if not token:
            pytest.skip("Test user login failed")
        resp = requests.get(
            f"{BASE_URL}/api/demand-progress",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        assert resp.status_code == 200, \
            f"Demand progress returned {resp.status_code}: {resp.text[:200]}"
        print(f"PASS: /api/demand-progress returned 200")

    def test_checkin_endpoint_accessible(self):
        """Daily check-in endpoint used by checkin-btn"""
        token = get_token(TEST_EMAIL, TEST_PASSWORD)
        if not token:
            pytest.skip("Test user login failed")
        # Just verify endpoint exists (POST /api/daily-checkin)
        resp = requests.post(
            f"{BASE_URL}/api/daily-checkin",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        # 200 = checked in, 400 = already checked in, both are valid
        assert resp.status_code in [200, 400, 409], \
            f"Check-in endpoint returned unexpected {resp.status_code}: {resp.text[:200]}"
        print(f"PASS: /api/daily-checkin returned {resp.status_code} (valid)")
