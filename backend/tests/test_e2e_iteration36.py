"""
FREE11 E2E Regression Test — Iteration 36
Focus: New features (IPL countdown, Tutorial API, PWA banner logic, OTP registration),
plus smoke tests for all critical paths.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "test_redesign_ui26@free11test.com"
TEST_PASS = "Test@1234"
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASS = "Admin@123"


class TokenCache:
    """Token cache for test suite"""
    test_token = None
    admin_token = None

    @classmethod
    def get_test_token(cls):
        if cls.test_token:
            return cls.test_token
        resp = requests.post(f"{BASE_URL}/api/auth/login",
                             json={"email": TEST_EMAIL, "password": TEST_PASS}, timeout=15)
        if resp.status_code == 200:
            cls.test_token = resp.json().get("access_token")
        return cls.test_token

    @classmethod
    def get_admin_token(cls):
        if cls.admin_token:
            return cls.admin_token
        resp = requests.post(f"{BASE_URL}/api/auth/login",
                             json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=15)
        if resp.status_code == 200:
            cls.admin_token = resp.json().get("access_token")
        return cls.admin_token


# ─── HEALTH CHECKS ────────────────────────────────────────────────────────────
class TestHealth:
    """Health endpoint tests"""

    def test_api_health_endpoint(self):
        """GET /api/health — API health (external URL — /health is frontend)"""
        resp = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert resp.status_code == 200, f"API health check failed: {resp.text}"
        data = resp.json()
        assert "status" in data
        assert data["status"] == "ok", f"Unexpected status: {data['status']}"
        print(f"✅ /api/health: status={data['status']}, db={data.get('database_status')}")

    def test_api_health_database_connected(self):
        """DB should be connected in health check"""
        resp = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("database_status") == "connected", f"DB not connected: {data}"
        print(f"✅ DB connected, redis={data.get('redis_status')}")


# ─── OTP REGISTRATION FLOW ────────────────────────────────────────────────────
class TestOTPRegistrationFlow:
    """OTP registration — new single-page flow"""

    def test_send_otp_valid_email(self):
        """POST /api/auth/send-otp returns success"""
        unique = f"test36_otp_{int(time.time())}@free11test.com"
        resp = requests.post(f"{BASE_URL}/api/auth/send-otp",
                             json={"email": unique}, timeout=15)
        assert resp.status_code == 200, f"send-otp failed: {resp.text}"
        data = resp.json()
        assert "message" in data or "dev_otp" in data
        print(f"✅ send-otp: message={data.get('message')}, has_dev_otp={bool(data.get('dev_otp'))}")

    def test_send_otp_missing_email_returns_422(self):
        """POST /api/auth/send-otp with no email returns 422"""
        resp = requests.post(f"{BASE_URL}/api/auth/send-otp",
                             json={}, timeout=15)
        assert resp.status_code in [400, 422], f"Expected validation error, got {resp.status_code}"
        print(f"✅ send-otp missing email: {resp.status_code}")

    def test_verify_otp_wrong_code_rejected(self):
        """POST /api/auth/verify-otp with wrong code returns error"""
        resp = requests.post(f"{BASE_URL}/api/auth/verify-otp",
                             json={"email": "any@test.com", "otp": "000000"}, timeout=15)
        assert resp.status_code in [400, 404, 422], f"Expected error, got {resp.status_code}: {resp.text}"
        print(f"✅ Wrong OTP rejected: {resp.status_code}")

    def test_verify_otp_register_wrong_code_rejected(self):
        """POST /api/auth/verify-otp-register with wrong code returns error"""
        resp = requests.post(f"{BASE_URL}/api/auth/verify-otp-register",
                             json={"email": "any@test.com", "otp": "000000"}, timeout=15)
        assert resp.status_code in [400, 404, 422], f"Expected error, got {resp.status_code}: {resp.text}"
        print(f"✅ Wrong OTP register rejected: {resp.status_code}")


# ─── AUTHENTICATION ────────────────────────────────────────────────────────────
class TestAuth:
    """Authentication tests"""

    def test_login_test_user(self):
        """Standard login for test user"""
        token = TokenCache.get_test_token()
        assert token is not None, "Test user login failed"
        print(f"✅ Test user login: token received")

    def test_login_admin_user(self):
        """Admin login"""
        token = TokenCache.get_admin_token()
        assert token is not None, "Admin login failed"
        print(f"✅ Admin login: token received")

    def test_login_invalid_credentials(self):
        """Invalid credentials return 401"""
        resp = requests.post(f"{BASE_URL}/api/auth/login",
                             json={"email": "fake@fake.com", "password": "wrong"}, timeout=15)
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print(f"✅ Invalid credentials rejected: {resp.status_code}")


# ─── TUTORIAL API ─────────────────────────────────────────────────────────────
class TestTutorialAPI:
    """FirstTimeTutorial API endpoints — /api/user/tutorial-status, /api/user/complete-tutorial"""

    def test_get_tutorial_status(self):
        """GET /api/user/tutorial-status — returns tutorial completion state"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/user/tutorial-status",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"tutorial-status failed: {resp.text}"
        data = resp.json()
        assert "tutorial_completed" in data, f"tutorial_completed field missing: {data}"
        assert isinstance(data["tutorial_completed"], bool)
        print(f"✅ tutorial-status: tutorial_completed={data['tutorial_completed']}")

    def test_complete_tutorial(self):
        """POST /api/user/complete-tutorial — marks tutorial as completed"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.post(f"{BASE_URL}/api/user/complete-tutorial",
                             headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"complete-tutorial failed: {resp.text}"
        data = resp.json()
        assert "message" in data or "tutorial_completed" in data
        print(f"✅ complete-tutorial: {data}")

    def test_tutorial_status_after_completion(self):
        """After marking complete, tutorial_completed should be True"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        # Complete tutorial
        requests.post(f"{BASE_URL}/api/user/complete-tutorial",
                      headers={"Authorization": f"Bearer {token}"}, timeout=15)
        # Check status
        resp = requests.get(f"{BASE_URL}/api/user/tutorial-status",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("tutorial_completed") is True, f"Expected True after completion: {data}"
        print(f"✅ tutorial_completed=True after calling complete-tutorial")

    def test_reset_tutorial(self):
        """POST /api/user/reset-tutorial — resets tutorial for replay"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.post(f"{BASE_URL}/api/user/reset-tutorial",
                             headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"reset-tutorial failed: {resp.text}"
        print(f"✅ reset-tutorial: {resp.json()}")
        # Verify it reset
        check = requests.get(f"{BASE_URL}/api/user/tutorial-status",
                             headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert check.status_code == 200
        assert check.json().get("tutorial_completed") is False, "Tutorial should be reset to False"
        print(f"✅ tutorial reset to False correctly")


# ─── DASHBOARD DATA ────────────────────────────────────────────────────────────
class TestDashboard:
    """Dashboard API endpoints"""

    def test_get_user_profile(self):
        """GET /api/auth/me — returns user data"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/auth/me",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"me failed: {resp.text}"
        data = resp.json()
        assert "email" in data
        assert data["email"] == TEST_EMAIL
        print(f"✅ /me: email={data['email']}, coins={data.get('coins_balance')}")

    def test_get_demand_progress(self):
        """GET /api/user/demand-progress"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/user/demand-progress",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"demand-progress failed: {resp.text}"
        data = resp.json()
        assert "rank" in data or "next_reward" in data or "prediction_stats" in data
        print(f"✅ /user/demand-progress: {list(data.keys())}")

    def test_get_leaderboard(self):
        """GET /api/leaderboard — for dashboard widget"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/leaderboard",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"leaderboard failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"✅ /leaderboard: {len(data)} entries")


# ─── MATCHES API ─────────────────────────────────────────────────────────────
class TestMatches:
    """Match data APIs"""

    def test_get_upcoming_matches_es(self):
        """GET /api/v2/es/matches?status_id=1 — upcoming via EntitySport"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/v2/es/matches?status_id=1&limit=5",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code in [200, 404], f"upcoming matches failed: {resp.text}"
        if resp.status_code == 200:
            assert isinstance(resp.json(), list)
        print(f"✅ /v2/es/matches (upcoming): {resp.status_code}, {len(resp.json()) if resp.status_code == 200 else 0} matches")

    def test_get_live_matches_es(self):
        """GET /api/v2/es/matches?status_id=3 — live via EntitySport"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/v2/es/matches?status_id=3&limit=10",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code in [200, 404], f"live matches failed: {resp.text}"
        if resp.status_code == 200:
            assert isinstance(resp.json(), list)
        print(f"✅ /v2/es/matches (live): {resp.status_code}")

    def test_get_prediction_stats(self):
        """GET /api/v2/predictions/stats"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/v2/predictions/stats",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"prediction-stats failed: {resp.text}"
        data = resp.json()
        assert "total" in data or "accuracy" in data
        print(f"✅ /v2/predictions/stats: {data}")

    def test_get_prediction_streak(self):
        """GET /api/v2/predictions/streak"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/v2/predictions/streak",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"streak failed: {resp.text}"
        data = resp.json()
        assert "streak" in data
        print(f"✅ /v2/predictions/streak: streak={data['streak']}")


# ─── LEADERBOARDS ─────────────────────────────────────────────────────────────
class TestLeaderboards:
    """Leaderboard endpoints"""

    def test_global_leaderboard(self):
        """GET /api/leaderboards/global — returns {leaderboard: [...]} object"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/leaderboards/global",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"global leaderboard failed: {resp.text}"
        data = resp.json()
        # Returns {"leaderboard": [...], "metric": ..., "min_predictions": ...}
        assert "leaderboard" in data, f"leaderboard key missing: {list(data.keys())}"
        assert isinstance(data["leaderboard"], list)
        print(f"✅ /leaderboards/global: {len(data['leaderboard'])} entries, metric={data.get('metric')}")

    def test_weekly_leaderboard(self):
        """GET /api/leaderboards/weekly"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/leaderboards/weekly",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"weekly leaderboard failed: {resp.text}"
        data = resp.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        print(f"✅ /leaderboards/weekly: {len(data['leaderboard'])} entries")

    def test_streak_leaderboard(self):
        """GET /api/leaderboards/streak"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/leaderboards/streak",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"streak leaderboard failed: {resp.text}"
        data = resp.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        print(f"✅ /leaderboards/streak: {len(data['leaderboard'])} entries")


# ─── SHOP & PRODUCTS ─────────────────────────────────────────────────────────
class TestShop:
    """Shop API tests"""

    def test_get_products(self):
        """GET /api/products — returns product list"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/products",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"products failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 10, f"Expected >=10 products, got {len(data)}"
        first = data[0]
        assert "name" in first
        print(f"✅ /products: {len(data)} products, first={first['name']}")

    def test_get_redemptions(self):
        """GET /api/redemptions"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/redemptions",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"redemptions failed: {resp.text}"
        assert isinstance(resp.json(), list)
        print(f"✅ /redemptions: {len(resp.json())} records")


# ─── SPONSORED POOLS ─────────────────────────────────────────────────────────
class TestSponsoredPools:
    """Sponsored pools API"""

    def test_get_sponsored_pools(self):
        """GET /api/v2/sponsored — sponsored pools list"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"sponsored-pools failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1, f"Expected >=1 pools, got {len(data)}"
        print(f"✅ /v2/sponsored: {len(data)} pools")


# ─── ADMIN V2 ─────────────────────────────────────────────────────────────────
class TestAdminV2:
    """Admin V2 KPI endpoints"""

    def test_admin_kpis(self):
        """GET /api/v2/kpis — admin KPI dashboard"""
        token = TokenCache.get_admin_token()
        if not token:
            pytest.skip("Admin login failed")
        resp = requests.get(f"{BASE_URL}/api/v2/kpis",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"admin kpis failed: {resp.text}"
        data = resp.json()
        # Response: {"users": {"total": 47, ...}, "redemptions": {...}, ...}
        assert "users" in data, f"users key missing: {list(data.keys())}"
        assert data["users"]["total"] > 0, f"No users: {data['users']}"
        print(f"✅ /v2/kpis: total_users={data['users']['total']}")

    def test_admin_feature_flags(self):
        """GET /api/admin/v2/feature-flags — returns list of flags"""
        token = TokenCache.get_admin_token()
        if not token:
            pytest.skip("Admin login failed")
        resp = requests.get(f"{BASE_URL}/api/admin/v2/feature-flags",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"feature-flags failed: {resp.text}"
        data = resp.json()
        # Returns a list of flag objects
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✅ /admin/v2/feature-flags: {len(data)} flags")

    def test_admin_action_log(self):
        """GET /api/admin/v2/action-log"""
        token = TokenCache.get_admin_token()
        if not token:
            pytest.skip("Admin login failed")
        resp = requests.get(f"{BASE_URL}/api/admin/v2/action-log",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"action-log failed: {resp.text}"
        assert isinstance(resp.json(), list)
        print(f"✅ /admin/v2/action-log: {len(resp.json())} entries")


# ─── EARN COINS ─────────────────────────────────────────────────────────────
class TestEarnCoins:
    """Earn coins / tasks API"""

    def test_get_tasks(self):
        """GET /api/tasks — returns task list"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/tasks",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"tasks failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"✅ /tasks: {len(data)} tasks")

    def test_get_prediction_stats(self):
        """GET /api/v2/predictions/stats"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/v2/predictions/stats",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"prediction-stats failed: {resp.text}"
        print(f"✅ /v2/predictions/stats: {resp.json()}")

    def test_get_transactions(self):
        """GET /api/coins/transactions"""
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("Login failed")
        resp = requests.get(f"{BASE_URL}/api/coins/transactions",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert resp.status_code == 200, f"transactions failed: {resp.text}"
        assert isinstance(resp.json(), list)
        print(f"✅ /coins/transactions: {len(resp.json())} records")
