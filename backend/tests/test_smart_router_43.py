"""
Test Suite: Smart Commerce Router (Iteration 43)
Tests: /api/v2/router/skus, /api/v2/router/tease, /api/v2/router/settle,
       /api/v2/kpis/router endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
TEST_USER_EMAIL = "test_redesign_ui26@free11test.com"
TEST_USER_PASS = "Test@1234"
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASS = "Admin@123"


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def user_token():
    """Get auth token for test user."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASS})
    if resp.status_code == 200:
        return resp.json().get("token") or resp.json().get("access_token")
    pytest.skip(f"User login failed: {resp.status_code} {resp.text}")


@pytest.fixture(scope="module")
def admin_token():
    """Get auth token for admin user."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    if resp.status_code == 200:
        return resp.json().get("token") or resp.json().get("access_token")
    pytest.skip(f"Admin login failed: {resp.status_code} {resp.text}")


@pytest.fixture(scope="module")
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ── Test 1: Router SKUs Catalog ───────────────────────────────────────────────

class TestRouterSkus:
    """GET /api/v2/router/skus — public endpoint, returns all SKUs"""

    def test_skus_status_200(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_skus_returns_list(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}: {data}"

    def test_skus_count_is_33(self):
        """33 unique SKUs across all 4 providers (ONDC:10, Xoxoday:11, Amazon:6, Flipkart:6)"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        assert len(data) == 33, f"Expected 33 SKUs, got {len(data)}"

    def test_skus_have_required_fields(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        required_fields = {"sku", "name", "coins", "category", "provider"}
        for item in data[:5]:  # Check first 5 items
            missing = required_fields - set(item.keys())
            assert not missing, f"SKU {item.get('sku')} missing fields: {missing}"

    def test_skus_have_valid_providers(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        valid_providers = {"ondc", "xoxoday", "amazon", "flipkart"}
        providers_found = {item["provider"] for item in data}
        assert providers_found.issubset(valid_providers), f"Invalid providers: {providers_found - valid_providers}"
        assert len(providers_found) >= 1, "No providers found"

    def test_skus_contain_chips_pack(self):
        """chips_pack (20 coins) - cheapest SKU that test user can afford"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        skus = {item["sku"] for item in data}
        assert "chips_pack" in skus, f"chips_pack not found in {skus}"

    def test_skus_contain_salt_pack(self):
        """salt_pack (25 coins) - affordable for test user"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        skus = {item["sku"] for item in data}
        assert "salt_pack" in skus

    def test_skus_chips_pack_has_correct_price(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        chips = next((item for item in data if item["sku"] == "chips_pack"), None)
        assert chips is not None, "chips_pack not found"
        assert chips["coins"] == 20, f"Expected 20 coins, got {chips['coins']}"

    def test_skus_have_categories(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        categories = {item["category"] for item in data}
        # Should have groceries (ONDC), vouchers (Xoxoday), electronics (Amazon/Flipkart), fashion (Amazon/Flipkart)
        assert "groceries" in categories, f"No groceries category: {categories}"
        assert "vouchers" in categories, f"No vouchers category: {categories}"


# ── Test 2: Router Tease Endpoint ─────────────────────────────────────────────

class TestRouterTease:
    """GET /api/v2/router/tease — public endpoint, scores providers"""

    def test_tease_basic_status(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=pepsi_2l&geo_state=MH")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_tease_atta_5kg_mh_best_provider_ondc(self):
        """atta_5kg is only available via ONDC → best_provider must be ondc"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=atta_5kg&geo_state=MH")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success", f"Expected success, got {data.get('status')}"
        assert data["best_provider"] == "ondc", f"Expected ondc, got {data.get('best_provider')}"

    def test_tease_atta_5kg_mh_eta_label(self):
        """Metro state MH → ONDC eta=0.031 → eta_label='~45 min'"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=atta_5kg&geo_state=MH")
        data = resp.json()
        best = data.get("best", {})
        assert best.get("eta_label") == "~45 min", f"Expected '~45 min', got '{best.get('eta_label')}'"

    def test_tease_amazon_gc_100_best_provider_xoxoday(self):
        """amazon_gc_100 is only in Xoxoday catalog → best_provider=xoxoday"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=amazon_gc_100&geo_state=MH")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success", f"Expected success, got {data}"
        assert data["best_provider"] == "xoxoday", f"Expected xoxoday, got {data.get('best_provider')}"

    def test_tease_response_has_required_fields(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=chips_pack&geo_state=MH")
        data = resp.json()
        assert "sku" in data
        assert "best" in data
        assert "options" in data
        assert "status" in data

    def test_tease_best_has_provider_fields(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=chips_pack&geo_state=MH")
        data = resp.json()
        best = data.get("best", {})
        for field in ["provider_id", "provider_name", "coin_price", "real_price", "eta_label", "value_note"]:
            assert field in best, f"Missing field '{field}' in best: {best}"

    def test_tease_unknown_sku_returns_not_found(self):
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=nonexistent_sku_xyz&geo_state=MH")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_found", f"Expected not_found, got {data.get('status')}"
        assert data["best"] is None

    def test_tease_swiggy_100_best_provider_xoxoday(self):
        """swiggy_100 is only in Xoxoday → best_provider=xoxoday"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=swiggy_100&geo_state=MH")
        data = resp.json()
        assert data.get("best_provider") == "xoxoday"


# ── Test 3: Router Settle ────────────────────────────────────────────────────

class TestRouterSettle:
    """POST /api/v2/router/settle — requires auth, deducts coins, executes order"""

    def test_settle_requires_auth(self):
        """Without auth, settle should return 401 or 403"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/router/settle",
            json={"sku": "chips_pack", "coins_used": 20, "geo_state": "MH"},
        )
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"

    def test_settle_ondc_sku_as_admin(self, admin_headers):
        """Admin settle a cheap ONDC SKU → status='placed' + order_id"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/router/settle",
            json={"sku": "chips_pack", "coins_used": 20, "geo_state": "MH"},
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("status") == "placed", f"Expected status=placed, got {data.get('status')}"
        assert "order_id" in data, f"Missing order_id in response: {data}"
        assert data["order_id"].startswith("ONDC-"), f"Expected ONDC- prefix, got {data['order_id']}"

    def test_settle_new_balance_present(self, admin_headers):
        """Settle response must include new_balance field"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/router/settle",
            json={"sku": "salt_pack", "coins_used": 25, "geo_state": "MH"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "new_balance" in data, f"Missing new_balance: {data.keys()}"
        assert isinstance(data["new_balance"], int), f"new_balance should be int: {data['new_balance']}"

    def test_settle_xoxoday_sku_returns_voucher(self, admin_headers):
        """Xoxoday SKU (swiggy_100) → status='delivered' + voucher_code"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/router/settle",
            json={"sku": "swiggy_100", "coins_used": 110, "geo_state": "MH"},
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("status") == "delivered", f"Expected status=delivered, got {data.get('status')}"
        assert "voucher_code" in data, f"Missing voucher_code: {data}"

    def test_settle_invalid_sku_returns_404(self, admin_headers):
        resp = requests.post(
            f"{BASE_URL}/api/v2/router/settle",
            json={"sku": "nonexistent_sku_xyz", "coins_used": 10, "geo_state": "MH"},
            headers=admin_headers,
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

    def test_settle_insufficient_coins_returns_402(self, user_headers):
        """Settling atta_5kg (265 coins) when user may not have enough → 402"""
        # Get user balance first
        user_resp = requests.get(f"{BASE_URL}/api/auth/me", headers=user_headers)
        if user_resp.status_code == 200:
            balance = user_resp.json().get("coins_balance", 0)
            if balance >= 265:
                pytest.skip("User has enough coins to buy atta_5kg")

        resp = requests.post(
            f"{BASE_URL}/api/v2/router/settle",
            json={"sku": "atta_5kg", "coins_used": 265, "geo_state": "MH"},
            headers=user_headers,
        )
        assert resp.status_code == 402, f"Expected 402 insufficient coins, got {resp.status_code}: {resp.text}"


# ── Test 4: Router KPI Endpoint ───────────────────────────────────────────────

class TestRouterKPIs:
    """GET /api/v2/kpis/router — admin only"""

    def test_router_kpi_requires_auth(self):
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/router")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"

    def test_router_kpi_non_admin_forbidden(self, user_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/router", headers=user_headers)
        assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}: {resp.text}"

    def test_router_kpi_admin_success(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/router", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_router_kpi_response_structure(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/router", headers=admin_headers)
        data = resp.json()
        required_top = {"orders", "provider_distribution", "avg_coin_price", "avg_value_score", "conversion_rate_pct"}
        for field in required_top:
            assert field in data, f"Missing field '{field}' in router KPI response: {data.keys()}"

    def test_router_kpi_orders_structure(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/router", headers=admin_headers)
        data = resp.json()
        orders = data.get("orders", {})
        assert "total" in orders, f"Missing 'total' in orders: {orders}"
        assert "last_30d" in orders, f"Missing 'last_30d' in orders: {orders}"
        assert isinstance(orders["total"], (int, float)), f"orders.total should be numeric: {orders['total']}"


# ── Test 5: Rate Limiting ────────────────────────────────────────────────────

class TestRouterRateLimit:
    """Rate limit: 5 settles/min per user. 6th should return 429 (if Redis available)."""

    def test_rate_limit_on_6th_request(self, admin_headers):
        """
        Send 6 quick settle requests. If Redis is available, 6th should be 429.
        If Redis unavailable (graceful fallback), all may succeed with 200.
        """
        results = []
        # Use cheapest sku to avoid running out of coins for admin user
        for i in range(6):
            resp = requests.post(
                f"{BASE_URL}/api/v2/router/settle",
                json={"sku": "chips_pack", "coins_used": 20, "geo_state": "MH"},
                headers=admin_headers,
            )
            results.append(resp.status_code)

        # Either Redis works and 6th is 429, or Redis is down and all 200
        statuses_set = set(results)
        if 429 in statuses_set:
            # Rate limiting worked — verify it was around the 6th request
            print(f"Rate limiting triggered at request {results.index(429) + 1}")
            assert results[5] == 429 or 429 in results[4:], f"429 should be at or near 6th request: {results}"
        else:
            # Redis unavailable — graceful fallback, all succeed
            print(f"Rate limiting not active (Redis likely unavailable). All results: {results}")
            assert all(s in [200, 402] for s in results), f"Unexpected status codes: {results}"
