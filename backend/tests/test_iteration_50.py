"""
Iteration 50 — Backend tests for UI/UX changes validation
Tests: analytics endpoints, health, router/skus, products, auth
"""
import pytest
import requests
import os

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
        return resp.json().get("token") or resp.json().get("access_token")
    pytest.skip(f"Auth failed: {resp.status_code} {resp.text[:200]}")


@pytest.fixture(scope="module")
def authed_client(api_client, auth_token):
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ── 1. Backend Health ─────────────────────────────────────────────────────────

class TestHealth:
    """Health check endpoint"""

    def test_health_returns_200(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        data = resp.json()
        assert data.get("status") in ("ok", "healthy"), f"Unexpected status: {data}"
        print(f"PASS: /api/health → {data}")

    def test_health_db_connected(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/health")
        data = resp.json()
        # db_connected should be true
        assert data.get("db_connected") is not False, f"DB not connected: {data}"
        print(f"PASS: DB connected: {data}")


# ── 2. Analytics Endpoints (NEW) ────────────────────────────────────────────

class TestAnalyticsEndpoints:
    """New analytics event tracking endpoints"""

    def test_anon_event_no_auth_returns_ok(self, api_client):
        """POST /api/v2/analytics/event/anon — no auth, should return {ok: true}"""
        # Remove auth header if set
        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            f"{BASE_URL}/api/v2/analytics/event/anon",
            json={"event": "test_anon_event", "properties": {"test": True}},
            headers=headers
        )
        assert resp.status_code == 200, f"Anon analytics failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected {{ok: true}}, got: {data}"
        print(f"PASS: /api/v2/analytics/event/anon → {data}")

    def test_authenticated_event_returns_ok(self, authed_client):
        """POST /api/v2/analytics/event — with JWT, should return {ok: true}"""
        resp = authed_client.post(
            f"{BASE_URL}/api/v2/analytics/event",
            json={"event": "button_click", "properties": {"label": "bottom_nav_home", "test": True}}
        )
        assert resp.status_code == 200, f"Auth analytics failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected {{ok: true}}, got: {data}"
        print(f"PASS: /api/v2/analytics/event → {data}")

    def test_anon_event_without_body_returns_ok(self, api_client):
        """POST /api/v2/analytics/event/anon — empty body handled gracefully"""
        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            f"{BASE_URL}/api/v2/analytics/event/anon",
            json={},
            headers=headers
        )
        assert resp.status_code == 200, f"Empty body anon analytics failed: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True
        print(f"PASS: Empty body anon analytics → {data}")

    def test_authenticated_event_requires_auth(self, api_client):
        """POST /api/v2/analytics/event — without auth, should return 401/403"""
        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            f"{BASE_URL}/api/v2/analytics/event",
            json={"event": "test"},
            headers=headers
        )
        assert resp.status_code in (401, 403), f"Expected 401/403, got: {resp.status_code} {resp.text}"
        print(f"PASS: No-auth analytics/event returns {resp.status_code}")


# ── 3. Trademark Clean — Router SKUs ────────────────────────────────────────

class TestRouterSkus:
    """Trademark cleanup verification for /api/v2/router/skus"""

    def test_router_skus_returns_200(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200, f"Router SKUs failed: {resp.status_code} {resp.text[:300]}"
        print(f"PASS: /api/v2/router/skus → 200")

    def test_router_skus_no_trademark_lays(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200
        text = resp.text.lower()
        assert "lay's" not in text and "lays chips" not in text, \
            f"Found Lay's trademark in router SKUs response"
        print("PASS: No Lay's trademark in router SKUs")

    def test_router_skus_no_trademark_pepsi(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200
        text = resp.text.lower()
        assert "pepsi" not in text, f"Found Pepsi trademark in router SKUs"
        print("PASS: No Pepsi trademark in router SKUs")

    def test_router_skus_no_trademark_parleg(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200
        text = resp.text.lower()
        assert "parle-g" not in text, f"Found Parle-G trademark in router SKUs"
        print("PASS: No Parle-G trademark in router SKUs")

    def test_router_skus_is_list(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"PASS: Router SKUs returns list with {len(data)} items")


# ── 4. Products ──────────────────────────────────────────────────────────────

class TestProducts:
    """Products endpoint"""

    def test_products_returns_200(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/products", timeout=15)
        assert resp.status_code == 200, f"Products failed: {resp.status_code} {resp.text[:300]}"
        print(f"PASS: /api/products → 200")

    def test_products_returns_list(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/products", timeout=15)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        assert len(data) > 0, "Products list is empty"
        print(f"PASS: /api/products returns {len(data)} products")

    def test_products_no_trademark_lays(self, api_client):
        resp = api_client.get(f"{BASE_URL}/api/products", timeout=15)
        assert resp.status_code == 200
        text = resp.text.lower()
        assert "lay's" not in text and "lays chips" not in text.replace("salted", ""), \
            "Found Lay's trademark in products"
        print("PASS: No Lay's trademark in products")


# ── 5. Auth Login ────────────────────────────────────────────────────────────

class TestAuth:
    """Authentication endpoints"""

    def test_login_returns_token(self, api_client):
        resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_redesign_ui26@free11test.com",
            "password": "Test@1234"
        })
        assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
        data = resp.json()
        token = data.get("token") or data.get("access_token")
        assert token is not None, f"No token in response: {data}"
        print(f"PASS: Login returns token (len={len(token)})")

    def test_login_returns_user_data(self, api_client):
        resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_redesign_ui26@free11test.com",
            "password": "Test@1234"
        })
        assert resp.status_code == 200
        data = resp.json()
        user = data.get("user")
        assert user is not None, f"No user in response: {data}"
        assert "email" in user or "id" in user, f"User missing fields: {user}"
        print(f"PASS: Login returns user data: {list(user.keys())}")

    def test_login_invalid_credentials_returns_401(self, api_client):
        resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@free11test.com",
            "password": "WrongPass123"
        })
        assert resp.status_code in (400, 401, 422), f"Expected 401, got {resp.status_code}"
        print(f"PASS: Invalid login returns {resp.status_code}")


# ── 6. Analytics Dashboard (admin) ──────────────────────────────────────────

class TestAdminAnalytics:
    """Admin analytics dashboard"""

    @pytest.fixture(scope="class")
    def admin_token(self, api_client):
        resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "Admin@123"
        })
        if resp.status_code == 200:
            data = resp.json()
            return data.get("token") or data.get("access_token")
        pytest.skip(f"Admin login failed: {resp.status_code}")

    def test_analytics_dashboard_admin_returns_200(self, api_client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = api_client.get(f"{BASE_URL}/api/v2/analytics/dashboard", headers=headers)
        assert resp.status_code == 200, f"Admin analytics dashboard failed: {resp.status_code} {resp.text}"
        print(f"PASS: /api/v2/analytics/dashboard → 200")
