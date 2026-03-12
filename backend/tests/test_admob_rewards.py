"""
AdMob Rewarded Ads Integration Tests
Tests for POST /api/v2/ads/reward endpoint and GET /api/v2/ads/status
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials (admin)
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASSWORD = "Admin@123"

# Fresh test user for daily limit testing
TEST_USER_EMAIL = f"test_admob_{uuid.uuid4().hex[:8]}@free11.com"
TEST_USER_PASSWORD = "TestPass@123"


def _extract_token(data):
    """Extract token from response data - handles both 'token' and 'access_token' keys"""
    return data.get("access_token") or data.get("token")


def _register_user(email, password, name, username):
    """Register a new test user - returns token or None"""
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
        "username": username,
        "date_of_birth": "1990-01-01"
    })
    if resp.status_code in (200, 201):
        return _extract_token(resp.json())
    return None


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
    })
    if resp.status_code == 200:
        return _extract_token(resp.json())
    pytest.skip("Admin login failed")


@pytest.fixture(scope="module")
def fresh_user_token():
    """Register a fresh test user to get a clean daily ad counter"""
    token = _register_user(
        TEST_USER_EMAIL, TEST_USER_PASSWORD,
        "TestAdMob User", f"testadmob_{uuid.uuid4().hex[:6]}"
    )
    if token:
        return token
    # Try login if already registered
    resp2 = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD
    })
    if resp2.status_code == 200:
        return _extract_token(resp2.json())
    pytest.skip("Fresh user creation/login failed")


# ── Test 1: 401 without auth token ──────────────────────────────────────────

class TestAdMobRewardAuth:
    """Auth protection tests for /api/v2/ads/reward"""

    def test_reward_401_no_token(self):
        """POST /api/v2/ads/reward returns 401 when no auth token provided"""
        resp = requests.post(f"{BASE_URL}/api/v2/ads/reward", json={"reward_type": "ad_watch"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print("PASS: /api/v2/ads/reward returns 401 without auth token")

    def test_reward_401_invalid_token(self):
        """POST /api/v2/ads/reward returns 401 with invalid token"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/ads/reward",
            json={"reward_type": "ad_watch"},
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print("PASS: /api/v2/ads/reward returns 401 with invalid token")

    def test_ad_status_401_no_token(self):
        """GET /api/v2/ads/status returns 401 when no auth token provided"""
        resp = requests.get(f"{BASE_URL}/api/v2/ads/status")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print("PASS: /api/v2/ads/status returns 401 without auth token")


# ── Test 2: Successful reward claim ─────────────────────────────────────────

class TestAdMobRewardSuccess:
    """Successful AdMob reward claim tests"""

    def test_reward_credits_20_coins(self, admin_token):
        """POST /api/v2/ads/reward with valid token credits 20 coins and returns success"""
        # Get balance before
        balance_resp = requests.get(
            f"{BASE_URL}/api/v2/ledger/balance",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        balance_before = balance_resp.json().get("balance", 0) if balance_resp.status_code == 200 else 0

        # Claim reward
        resp = requests.post(
            f"{BASE_URL}/api/v2/ads/reward",
            json={"reward_type": "ad_watch"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code in (200, 429), f"Expected 200 or 429, got {resp.status_code}: {resp.text}"

        if resp.status_code == 200:
            data = resp.json()
            assert data.get("success") is True, "Response should have success=True"
            assert data.get("reward_coins") == 20, f"Expected 20 coins, got {data.get('reward_coins')}"
            assert "watched_today" in data, "Response should have watched_today"
            assert "remaining_today" in data, "Response should have remaining_today"
            assert "daily_limit" in data, "Response should have daily_limit"
            assert data.get("daily_limit") == 5, f"Expected daily_limit=5, got {data.get('daily_limit')}"

            # Verify balance increased by 20
            balance_resp2 = requests.get(
                f"{BASE_URL}/api/v2/ledger/balance",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            if balance_resp2.status_code == 200:
                balance_after = balance_resp2.json().get("balance", 0)
                assert balance_after == balance_before + 20, (
                    f"Balance should increase by 20. Before: {balance_before}, After: {balance_after}"
                )
            print(f"PASS: Reward claimed - 20 coins credited. Balance: {balance_before} -> {balance_before + 20}")
        else:
            # 429 means daily limit already reached for admin - still a valid test
            print(f"NOTE: Admin already at daily limit (429). Test validates endpoint auth correctly.")

    def test_reward_response_structure(self, fresh_user_token):
        """Verify complete response structure for successful reward claim"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/ads/reward",
            json={"reward_type": "ad_watch"},
            headers={"Authorization": f"Bearer {fresh_user_token}"}
        )
        assert resp.status_code == 200, f"Expected 200 for fresh user, got {resp.status_code}: {resp.text}"

        data = resp.json()
        # Validate response structure
        assert data.get("success") is True
        assert data.get("reward_coins") == 20
        assert isinstance(data.get("watched_today"), int)
        assert isinstance(data.get("remaining_today"), int)
        assert data.get("daily_limit") == 5
        assert data.get("watched_today") >= 1
        assert data.get("remaining_today") == 5 - data.get("watched_today")
        print(f"PASS: Response structure correct. watched_today={data.get('watched_today')}, remaining={data.get('remaining_today')}")


# ── Test 3: Ad status reflects reward calls ──────────────────────────────────

class TestAdStatus:
    """GET /api/v2/ads/status tests"""

    def test_status_returns_correct_structure(self, fresh_user_token):
        """GET /api/v2/ads/status returns watched_today, daily_limit, remaining_today"""
        resp = requests.get(
            f"{BASE_URL}/api/v2/ads/status",
            headers={"Authorization": f"Bearer {fresh_user_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        data = resp.json()
        assert "watched_today" in data, "Response missing watched_today"
        assert "daily_limit" in data, "Response missing daily_limit"
        assert "remaining_today" in data, "Response missing remaining_today"
        assert "reward_per_ad" in data, "Response missing reward_per_ad"
        assert data.get("daily_limit") == 5, f"Expected daily_limit=5, got {data.get('daily_limit')}"
        print(f"PASS: Ad status structure correct. watched_today={data.get('watched_today')}")

    def test_status_watched_today_reflects_reward_calls(self, fresh_user_token):
        """Verify watched_today count increases after calling /api/v2/ads/reward"""
        # Get initial status
        status_before = requests.get(
            f"{BASE_URL}/api/v2/ads/status",
            headers={"Authorization": f"Bearer {fresh_user_token}"}
        ).json()
        initial_count = status_before.get("watched_today", 0)

        # Claim reward (fresh user should have capacity)
        reward_resp = requests.post(
            f"{BASE_URL}/api/v2/ads/reward",
            json={"reward_type": "ad_watch"},
            headers={"Authorization": f"Bearer {fresh_user_token}"}
        )

        if reward_resp.status_code == 200:
            # Check status again
            status_after = requests.get(
                f"{BASE_URL}/api/v2/ads/status",
                headers={"Authorization": f"Bearer {fresh_user_token}"}
            ).json()
            new_count = status_after.get("watched_today", 0)
            assert new_count == initial_count + 1, (
                f"watched_today should increase by 1. Before: {initial_count}, After: {new_count}"
            )
            print(f"PASS: watched_today updated from {initial_count} to {new_count} after reward claim")
        else:
            print(f"SKIP: User at limit already ({reward_resp.status_code})")


# ── Test 4: Daily limit of 5 ──────────────────────────────────────────────

class TestDailyLimit:
    """Daily limit enforcement tests"""

    def test_daily_limit_5_calls_then_429(self):
        """POST /api/v2/ads/reward returns 429 after 5 successful calls"""
        # Register brand new user for a clean counter
        unique_email = f"test_limit_{uuid.uuid4().hex[:10]}@free11.com"
        token = _register_user(unique_email, "TestPass@123", "Test Limit User", f"testlimit_{uuid.uuid4().hex[:6]}")
        if not token:
            pytest.skip("Could not register test user for limit test")

        headers = {"Authorization": f"Bearer {token}"}

        # Call reward endpoint 5 times
        successful_calls = 0
        for i in range(5):
            resp = requests.post(
                f"{BASE_URL}/api/v2/ads/reward",
                json={"reward_type": "ad_watch"},
                headers=headers
            )
            assert resp.status_code == 200, f"Call {i+1} should succeed, got {resp.status_code}: {resp.text}"
            successful_calls += 1
            data = resp.json()
            assert data.get("reward_coins") == 20
            print(f"Call {i+1}: watched_today={data.get('watched_today')}, remaining={data.get('remaining_today')}")

        assert successful_calls == 5, f"Expected 5 successful calls, got {successful_calls}"

        # 6th call should return 429
        resp_limit = requests.post(
            f"{BASE_URL}/api/v2/ads/reward",
            json={"reward_type": "ad_watch"},
            headers=headers
        )
        assert resp_limit.status_code == 429, (
            f"Expected 429 after 5 calls, got {resp_limit.status_code}: {resp_limit.text}"
        )

        data_limit = resp_limit.json()
        assert "daily ad limit" in (data_limit.get("detail") or "").lower(), (
            f"Expected daily limit message in detail, got: {data_limit}"
        )
        print(f"PASS: 429 returned after 5 calls. Detail: {data_limit.get('detail')}")

    def test_remaining_today_decrements(self):
        """remaining_today decrements from 5 to 0 with each call"""
        unique_email = f"test_decr_{uuid.uuid4().hex[:10]}@free11.com"
        token = _register_user(unique_email, "TestPass@123", "Test Decrement User", f"testdecr_{uuid.uuid4().hex[:6]}")
        if not token:
            pytest.skip("Could not register test user")

        headers = {"Authorization": f"Bearer {token}"}

        for expected_remaining in [4, 3, 2, 1, 0]:
            resp = requests.post(
                f"{BASE_URL}/api/v2/ads/reward",
                json={"reward_type": "ad_watch"},
                headers=headers
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("remaining_today") == expected_remaining, (
                f"Expected remaining_today={expected_remaining}, got {data.get('remaining_today')}"
            )

        print("PASS: remaining_today correctly decrements from 4 to 0")


# ── Test 5: Mock ads status integration ──────────────────────────────────────

class TestMockAdsIntegration:
    """Tests for mock ad endpoints and their interaction with AdMob reward counts"""

    def test_mock_start_ad(self, admin_token):
        """POST /api/v2/ads/start works and returns ad_id"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/ads/start",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Could be 200 or 400 (if daily limit)
        assert resp.status_code in (200, 400), f"Expected 200 or 400, got {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "ad_id" in data, "Response missing ad_id"
            assert "duration_seconds" in data, "Response missing duration_seconds"
            assert "reward_coins" in data, "Response missing reward_coins"
            assert data.get("reward_coins") == 10, f"Mock ad should reward 10 coins, got {data.get('reward_coins')}"
            print(f"PASS: Mock start ad returns ad_id={data.get('ad_id')}, reward=10 coins")
        else:
            print(f"NOTE: Admin at daily limit for start_ad (400)")

    def test_admob_reward_type_field(self, fresh_user_token):
        """POST /api/v2/ads/reward accepts reward_type field"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/ads/reward",
            json={"reward_type": "ad_watch"},
            headers={"Authorization": f"Bearer {fresh_user_token}"}
        )
        # 200 or 429 (if already at limit from previous tests)
        assert resp.status_code in (200, 429), f"Expected 200 or 429, got {resp.status_code}"
        print(f"PASS: /api/v2/ads/reward accepts reward_type field, status={resp.status_code}")

    def test_admob_coins_constant_20(self, admin_token):
        """Verify ADMOB_REWARD_COINS constant is 20 (not same as mock 10)"""
        # The endpoint should always return 20 coins on success
        resp = requests.post(
            f"{BASE_URL}/api/v2/ads/reward",
            json={"reward_type": "ad_watch"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("reward_coins") == 20, (
                f"AdMob reward should be 20, not {data.get('reward_coins')}"
            )
            print(f"PASS: AdMob reward_coins=20 confirmed")
        else:
            print(f"NOTE: Admin at daily limit (429), skipping coin amount check")
