"""
Iteration 51 — Regression tests for GlobalAnalyticsTracker + core flows
Tests: health, analytics events (auth + anon), login/dashboard, shop
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_token(api_client):
    resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test_redesign_ui26@free11test.com",
        "password": "Test@1234"
    })
    if resp.status_code == 200:
        data = resp.json()
        return data.get("token") or data.get("access_token")
    pytest.skip(f"Auth failed: {resp.status_code} {resp.text[:200]}")


@pytest.fixture(scope="module")
def authed_client(api_client, auth_token):
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ── 1. Backend Health ─────────────────────────────────────────────────────────

class TestHealth:
    """Backend health check"""

    def test_health_returns_200(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        data = resp.json()
        assert data.get("status") in ("ok", "healthy"), f"Unexpected status: {data}"
        print(f"PASS: /api/health → {data.get('status')}")

    def test_health_db_connected(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/health")
        data = resp.json()
        assert data.get("db_connected") is not False, f"DB not connected: {data}"
        print(f"PASS: DB connected → {data.get('db_connected')}")


# ── 2. Analytics Event API ────────────────────────────────────────────────────

class TestAnalyticsEventAPI:
    """POST /api/v2/analytics/event and /api/v2/analytics/event/anon"""

    def test_anon_event_returns_ok(self):
        """Unauthenticated event tracking"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/analytics/event/anon",
            json={"event": "button_click", "properties": {"label": "test_btn", "tag": "button"}},
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 200, f"Anon event failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected {{ok: true}}, got: {data}"
        print(f"PASS: /api/v2/analytics/event/anon → {data}")

    def test_authenticated_event_returns_ok(self, authed_client):
        """Authenticated event tracking (as GlobalAnalyticsTracker sends)"""
        resp = authed_client.post(
            f"{BASE_URL}/api/v2/analytics/event",
            json={
                "event": "button_click",
                "properties": {
                    "label": "shop_nav_btn",
                    "tag": "button",
                    "path": "/dashboard",
                    "ts": int(time.time() * 1000)
                }
            }
        )
        assert resp.status_code == 200, f"Auth event failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected {{ok: true}}, got: {data}"
        print(f"PASS: /api/v2/analytics/event → {data}")

    def test_multiple_rapid_events_all_accepted(self, authed_client):
        """Backend accepts multiple rapid events (dedup is frontend-side)"""
        results = []
        for i in range(5):
            resp = authed_client.post(
                f"{BASE_URL}/api/v2/analytics/event",
                json={"event": "button_click", "properties": {"label": "test_rapid", "seq": i}}
            )
            results.append(resp.status_code)
        assert all(s == 200 for s in results), f"Some rapid events failed: {results}"
        print(f"PASS: 5 rapid events all returned 200: {results}")

    def test_event_without_properties(self, authed_client):
        """Event with no properties is handled gracefully"""
        resp = authed_client.post(
            f"{BASE_URL}/api/v2/analytics/event",
            json={"event": "page_view"}
        )
        assert resp.status_code == 200, f"No-properties event failed: {resp.text}"
        assert resp.json().get("ok") is True
        print("PASS: Event without properties → ok")

    def test_anon_event_empty_body(self):
        """Empty body handled gracefully for anon endpoint"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/analytics/event/anon",
            json={},
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 200, f"Empty body anon event failed: {resp.text}"
        assert resp.json().get("ok") is True
        print("PASS: Empty body anon event → ok")

    def test_auth_event_requires_token(self):
        """POST /api/v2/analytics/event without auth returns 401"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/analytics/event",
            json={"event": "button_click"},
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code in (401, 403), f"Expected 401/403 got {resp.status_code}: {resp.text}"
        print(f"PASS: No-auth analytics event → {resp.status_code}")


# ── 3. Authentication ─────────────────────────────────────────────────────────

class TestAuth:
    """Login and user profile"""

    def test_login_returns_token(self, api_client):
        resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_redesign_ui26@free11test.com",
            "password": "Test@1234"
        })
        assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
        data = resp.json()
        token = data.get("token") or data.get("access_token")
        assert token, f"No token in response: {data}"
        print(f"PASS: Login → token (len={len(token)})")

    def test_login_returns_user_info(self, api_client):
        resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_redesign_ui26@free11test.com",
            "password": "Test@1234"
        })
        assert resp.status_code == 200
        data = resp.json()
        user = data.get("user", {})
        assert user.get("email") == "test_redesign_ui26@free11test.com", f"Email mismatch: {user}"
        print(f"PASS: Login returns user email: {user.get('email')}")

    def test_login_wrong_credentials_rejected(self, api_client):
        resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nobody@free11test.com",
            "password": "WrongPwd99"
        })
        assert resp.status_code in (400, 401, 422), f"Expected 4xx, got {resp.status_code}"
        print(f"PASS: Wrong creds → {resp.status_code}")


# ── 4. User Profile & Wallet (coin balance) ──────────────────────────────────

class TestUserDashboard:
    """User profile and wallet endpoints used by Dashboard"""

    def test_user_profile_returns_200(self, authed_client):
        resp = authed_client.get(f"{BASE_URL}/api/auth/me")
        assert resp.status_code == 200, f"Profile failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "email" in data or "name" in data, f"Profile missing fields: {data}"
        print(f"PASS: /api/auth/me → user: {data.get('email')}")

    def test_user_wallet_has_coin_balance(self, authed_client):
        resp = authed_client.get(f"{BASE_URL}/api/coins/balance")
        assert resp.status_code == 200, f"Coins balance failed: {resp.status_code} {resp.text}"
        data = resp.json()
        # Coin balance can be in 'coins', 'balance', or 'coins_balance' field
        coins = data.get("coins") or data.get("coin_balance") or data.get("balance") or data.get("coins_balance") or 0
        assert isinstance(coins, (int, float)), f"Coins not numeric: {coins} | data: {data}"
        print(f"PASS: Coin balance: {coins}")


# ── 5. Shop Page Endpoints ────────────────────────────────────────────────────

class TestShopEndpoints:
    """Endpoints used by the Shop page"""

    def test_products_endpoint_returns_list(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/products", timeout=15)
        assert resp.status_code == 200, f"Products failed: {resp.status_code} {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"PASS: /api/products → {len(data)} products")

    def test_gift_cards_endpoint(self, authed_client):
        """Gift cards available endpoint"""
        resp = authed_client.get(f"{BASE_URL}/api/gift-cards/available", timeout=15)
        assert resp.status_code in (200, 404), f"Gift cards failed: {resp.status_code} {resp.text[:200]}"
        print(f"PASS: /api/gift-cards/available → {resp.status_code}")

    def test_airtime_catalog_endpoint(self, authed_client):
        """Airtime catalog for mobile recharge"""
        resp = authed_client.get(f"{BASE_URL}/api/airtime/catalog", timeout=15)
        assert resp.status_code in (200, 404), f"Airtime catalog failed: {resp.status_code} {resp.text[:200]}"
        print(f"PASS: /api/airtime/catalog → {resp.status_code}")

    def test_router_skus_returns_200(self, api_client):
        """Smart Commerce Router SKUs"""
        resp = api_client.get(f"{BASE_URL}/api/v2/router/skus", timeout=15)
        assert resp.status_code == 200, f"Router SKUs failed: {resp.status_code} {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list: {type(data)}"
        print(f"PASS: /api/v2/router/skus → {len(data)} items")


# ── 6. Navigation Pages ───────────────────────────────────────────────────────

class TestNavigationEndpoints:
    """API endpoints used by navigation target pages"""

    def test_earn_coins_missions(self, authed_client):
        """Earn page uses missions/status"""
        resp = authed_client.get(f"{BASE_URL}/api/v2/missions/status", timeout=10)
        assert resp.status_code in (200, 404), f"Missions failed: {resp.status_code} {resp.text[:200]}"
        print(f"PASS: /api/v2/missions/status → {resp.status_code}")

    def test_predict_page_matches(self, authed_client):
        """Predict page uses cricket/matches"""
        resp = authed_client.get(f"{BASE_URL}/api/cricket/matches", timeout=10)
        assert resp.status_code in (200, 404), f"Cricket matches failed: {resp.status_code}"
        print(f"PASS: /api/cricket/matches → {resp.status_code}")
