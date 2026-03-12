"""
Backend tests for FREE11 Production Release Candidate (Iteration 33):
- KPI Breakage endpoint (GET /api/v2/kpis/breakage)
- Push Templates endpoint (GET /api/v2/push/templates)
- Google OAuth with invalid session (POST /api/auth/google-oauth?session_id=invalid → 401)
- Router SKUs with dynamic_coin_price (GET /api/v2/router/skus)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def admin_token():
    """Get auth token for admin user"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@free11.com",
        "password": "Admin@123"
    })
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Admin auth failed: {resp.status_code} {resp.text}")


@pytest.fixture
def admin_auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ── 1. KPI Breakage endpoint ──────────────────────────────────────────────────
class TestKPIBreakage:
    """Test /api/v2/kpis/breakage returns unredeemed_coin_ratio_pct"""

    def test_breakage_requires_auth(self):
        """Returns 401/403 without auth"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/breakage")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print(f"PASS: breakage without auth returns {resp.status_code}")

    def test_breakage_returns_200(self, admin_auth):
        """Admin can fetch breakage metrics"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/breakage", headers=admin_auth)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"PASS: breakage returns 200")

    def test_breakage_has_unredeemed_coin_ratio_pct(self, admin_auth):
        """Response contains unredeemed_coin_ratio_pct field"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/breakage", headers=admin_auth)
        assert resp.status_code == 200
        data = resp.json()
        assert "unredeemed_coin_ratio_pct" in data, f"Missing unredeemed_coin_ratio_pct. Keys: {list(data.keys())}"
        assert isinstance(data["unredeemed_coin_ratio_pct"], (int, float)), \
            f"unredeemed_coin_ratio_pct should be numeric, got {type(data['unredeemed_coin_ratio_pct'])}"
        print(f"PASS: unredeemed_coin_ratio_pct = {data['unredeemed_coin_ratio_pct']}")

    def test_breakage_has_all_required_fields(self, admin_auth):
        """Response contains all required breakage fields"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/breakage", headers=admin_auth)
        assert resp.status_code == 200
        data = resp.json()
        required_fields = [
            "total_coins_issued",
            "total_coins_spent",
            "live_wallet_balance",
            "unredeemed_coins",
            "unredeemed_coin_ratio_pct",
            "target_breakage_pct",
            "status",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}. Keys: {list(data.keys())}"
        print(f"PASS: all breakage fields present. Status={data['status']}, ratio={data['unredeemed_coin_ratio_pct']}%")

    def test_breakage_target_is_10(self, admin_auth):
        """target_breakage_pct should be 10.0"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/breakage", headers=admin_auth)
        data = resp.json()
        assert data.get("target_breakage_pct") == 10.0, f"Expected 10.0, got {data.get('target_breakage_pct')}"
        print(f"PASS: target_breakage_pct = 10.0")


# ── 2. Push Templates endpoint ────────────────────────────────────────────────
class TestPushTemplates:
    """Test /api/v2/push/templates returns campaign templates list"""

    def test_templates_endpoint_accessible_without_auth(self):
        """Push templates endpoint is public (no auth required)"""
        resp = requests.get(f"{BASE_URL}/api/v2/push/templates")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"PASS: /api/v2/push/templates returns 200")

    def test_templates_returns_list(self):
        """Response is a list"""
        resp = requests.get(f"{BASE_URL}/api/v2/push/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "Templates list should not be empty"
        print(f"PASS: templates list has {len(data)} templates")

    def test_templates_have_required_keys(self):
        """Each template has key, title, body"""
        resp = requests.get(f"{BASE_URL}/api/v2/push/templates")
        data = resp.json()
        for template in data:
            assert "key" in template, f"Template missing 'key': {template}"
            assert "title" in template, f"Template missing 'title': {template}"
            assert "body" in template, f"Template missing 'body': {template}"
        print(f"PASS: all templates have key/title/body")

    def test_templates_contains_expected_keys(self):
        """Expected campaign types present"""
        resp = requests.get(f"{BASE_URL}/api/v2/push/templates")
        data = resp.json()
        keys = [t["key"] for t in data]
        expected_keys = ["predict_live", "streak_reminder", "reward_drop"]
        for k in expected_keys:
            assert k in keys, f"Expected template key '{k}' not found in {keys}"
        print(f"PASS: expected template keys found: {keys}")


# ── 3. Google OAuth with invalid session → 401 ────────────────────────────────
class TestGoogleOAuthInvalidSession:
    """POST /api/auth/google-oauth?session_id=invalid should return 401"""

    def test_google_oauth_invalid_session_returns_401(self):
        """Invalid session_id returns 401 Unauthorized"""
        resp = requests.post(f"{BASE_URL}/api/auth/google-oauth?session_id=invalid_session_xyz")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print(f"PASS: invalid session_id returns 401")

    def test_google_oauth_random_session_returns_401(self):
        """Random session_id also returns 401"""
        import uuid
        random_session = str(uuid.uuid4())
        resp = requests.post(f"{BASE_URL}/api/auth/google-oauth?session_id={random_session}")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print(f"PASS: random session_id returns 401")

    def test_google_oauth_missing_session_id_returns_422(self):
        """Missing session_id returns 422 (Unprocessable Entity)"""
        resp = requests.post(f"{BASE_URL}/api/auth/google-oauth")
        assert resp.status_code == 422, f"Expected 422 for missing session_id, got {resp.status_code}"
        print(f"PASS: missing session_id returns 422")


# ── 4. Router SKUs with dynamic_coin_price ────────────────────────────────────
class TestRouterSKUs:
    """GET /api/v2/router/skus returns dynamic_coin_price field per SKU"""

    def test_router_skus_returns_200(self):
        """Endpoint is accessible without auth"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"PASS: /api/v2/router/skus returns 200")

    def test_router_skus_returns_list(self):
        """Response is a list of SKUs"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "SKU list should not be empty"
        print(f"PASS: {len(data)} SKUs returned")

    def test_router_skus_have_dynamic_coin_price(self):
        """Each SKU has dynamic_coin_price field"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        for sku in data:
            assert "dynamic_coin_price" in sku, f"SKU missing dynamic_coin_price: {sku.get('sku', sku)}"
            assert isinstance(sku["dynamic_coin_price"], (int, float)), \
                f"dynamic_coin_price should be numeric: {sku['dynamic_coin_price']}"
        print(f"PASS: all {len(data)} SKUs have dynamic_coin_price")

    def test_router_skus_have_demand_factor(self):
        """Each SKU has demand_factor field"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        for sku in data:
            assert "demand_factor" in sku, f"SKU missing demand_factor: {sku.get('sku', sku)}"
        print(f"PASS: all SKUs have demand_factor")

    def test_router_skus_dynamic_price_positive(self):
        """dynamic_coin_price should be > 0"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        data = resp.json()
        for sku in data:
            price = sku.get("dynamic_coin_price", 0)
            assert price > 0, f"dynamic_coin_price should be > 0, got {price} for {sku.get('sku')}"
        print(f"PASS: all dynamic_coin_prices are positive")


# ── 5. Push Campaign Creation (Admin) ────────────────────────────────────────
class TestPushCampaign:
    """POST /api/v2/push/campaign — admin creates a push campaign"""

    def test_push_campaign_requires_auth(self):
        """Campaign creation requires auth"""
        resp = requests.post(f"{BASE_URL}/api/v2/push/campaign", json={
            "template": "predict_live",
            "target": "all"
        })
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print(f"PASS: /api/v2/push/campaign requires auth: {resp.status_code}")

    def test_push_campaign_create_success(self, admin_auth):
        """Admin can create a push campaign"""
        resp = requests.post(f"{BASE_URL}/api/v2/push/campaign",
            headers=admin_auth,
            json={
                "template": "predict_live",
                "target": "all"
            }
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "id" in data, f"Campaign should have id: {data}"
        assert data.get("template") == "predict_live"
        assert data.get("status") in ["ready", "scheduled"]
        print(f"PASS: campaign created: {data['id']}, status={data['status']}")


# ── 6. robots.txt and sitemap.xml (static files) ─────────────────────────────
class TestStaticFiles:
    """Verify robots.txt and sitemap.xml are accessible"""

    def test_robots_txt_accessible(self):
        """robots.txt is accessible at /robots.txt"""
        resp = requests.get(f"{BASE_URL}/robots.txt")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        content = resp.text
        assert "User-agent" in content or "user-agent" in content.lower(), \
            f"robots.txt should contain User-agent directive: {content[:200]}"
        print(f"PASS: /robots.txt accessible with content: {content[:100]}")

    def test_robots_txt_allows_all(self):
        """robots.txt should allow all crawlers"""
        resp = requests.get(f"{BASE_URL}/robots.txt")
        content = resp.text
        assert "Allow: /" in content, f"robots.txt should have 'Allow: /': {content}"
        print(f"PASS: robots.txt contains 'Allow: /'")

    def test_sitemap_xml_accessible(self):
        """sitemap.xml is accessible at /sitemap.xml"""
        resp = requests.get(f"{BASE_URL}/sitemap.xml")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print(f"PASS: /sitemap.xml accessible, content-type={resp.headers.get('content-type')}")

    def test_sitemap_contains_ipl_guide(self):
        """sitemap.xml includes /blog/ipl-guide"""
        resp = requests.get(f"{BASE_URL}/sitemap.xml")
        content = resp.text
        assert "blog/ipl-guide" in content, f"sitemap.xml should contain blog/ipl-guide: {content[:500]}"
        print(f"PASS: sitemap.xml contains blog/ipl-guide")
