"""
Backend tests for FREE11 V2 Features (Iteration 32):
- Quest Engine (GET /api/v2/quest/status, POST /api/v2/quest/offer)
- Smart Router (GET /api/v2/router/tease, GET /api/v2/router/skus)
- Sponsored Pools (GET /api/v2/sponsored, POST /api/v2/sponsored/join)
- KPI Routes (GET /api/v2/kpis, GET /api/v2/kpis/cohort-csv)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def user_token():
    """Get auth token for test user"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test_redesign_ui26@free11test.com",
        "password": "Test@1234"
    })
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"User auth failed: {resp.status_code} {resp.text}")


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
def user_auth(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ── Smart Router Tests ─────────────────────────────────────────────────────────

class TestSmartRouter:
    """Smart Router / Ration Rails Aggregator"""

    def test_router_tease_pepsi_mh(self):
        """GET /api/v2/router/tease?sku=pepsi_2l&geo_state=MH returns scored options"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=pepsi_2l&geo_state=MH")
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"

        data = resp.json()
        assert "sku" in data
        assert data["sku"] == "pepsi_2l"
        assert data["geo_state"] == "MH"
        assert "options" in data
        assert isinstance(data["options"], list)
        assert len(data["options"]) > 0, "Should return at least one provider option"
        assert "best" in data
        assert data["best"] is not None, "Should have a best provider"
        print(f"Router tease: {len(data['options'])} options, best={data['best']['provider_name']}")

    def test_router_tease_options_have_required_fields(self):
        """Each provider option should have score, eta, price fields"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=pepsi_2l&geo_state=MH")
        assert resp.status_code == 200
        data = resp.json()

        for option in data["options"]:
            assert "score" in option, f"Option missing 'score': {option}"
            assert "eta_minutes" in option, f"Option missing 'eta_minutes': {option}"
            assert "discounted_price" in option, f"Option missing 'discounted_price': {option}"
            assert "provider_name" in option, f"Option missing 'provider_name': {option}"
        print(f"Router options validated: {[o['provider_name'] for o in data['options']]}")

    def test_router_tease_best_has_highest_score(self):
        """Best provider should have highest score (sorted correctly)"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=pepsi_2l&geo_state=MH")
        assert resp.status_code == 200
        data = resp.json()
        if len(data["options"]) > 1:
            best_score = data["best"]["score"]
            all_scores = [o["score"] for o in data["options"]]
            assert best_score == max(all_scores), f"Best provider should have highest score. Best: {best_score}, Max: {max(all_scores)}"
        print(f"Best provider score: {data['best']['score']}")

    def test_router_skus_returns_catalog(self):
        """GET /api/v2/router/skus returns all ration SKUs"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"

        data = resp.json()
        assert isinstance(data, list), "Should return a list of SKUs"
        assert len(data) > 0, "Should have at least one SKU"

        # Verify required fields
        sku_names = [item["sku"] for item in data]
        assert "pepsi_2l" in sku_names, "Cola 2L should be in catalog"
        assert "atta_5kg" in sku_names, "Atta should be in catalog"
        assert "biscuits_pack" in sku_names, "Biscuits should be in catalog"
        print(f"Router SKUs: {len(data)} items. Includes: {sku_names[:5]}")

    def test_router_tease_different_geo(self):
        """Router tease with different geo_state should work"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/tease?sku=atta_5kg&geo_state=DL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["geo_state"] == "DL"
        assert "options" in data
        print(f"Router tease DL/atta: {len(data['options'])} options")


# ── Sponsored Pools Tests ──────────────────────────────────────────────────────

class TestSponsoredPools:
    """Sponsored Pools (Brand-funded contest pools)"""

    def test_get_sponsored_pools_returns_3_seeded(self):
        """GET /api/v2/sponsored returns 3 seeded pools"""
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored", headers={"Authorization": "Bearer test"})
        # May or may not require auth - try without auth first
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored")
        if resp.status_code == 401:
            pytest.skip("Sponsored pools requires auth - test with user token separately")
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Should return a list of pools"
        assert len(data) >= 3, f"Expected at least 3 seeded pools, got {len(data)}"
        print(f"Sponsored pools: {len(data)} pools")

    def test_get_sponsored_pools_with_auth(self, user_auth):
        """GET /api/v2/sponsored with auth returns pools"""
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored", headers=user_auth)
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3, f"Expected ≥3 pools, got {len(data)}"
        brand_names = [p["brand_name"] for p in data]
        print(f"Sponsored pool brands: {brand_names}")

    def test_seeded_pools_have_brands(self, user_auth):
        """Seeded pools should have CoolDrink Co., Biscuit Brand, Fortune Foods"""
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored", headers=user_auth)
        assert resp.status_code == 200
        data = resp.json()
        brand_names_lower = [p["brand_name"].lower() for p in data]
        assert any("cooldrink" in b or "drink" in b or "cola" in b or "beverage" in b for b in brand_names_lower), f"Cola/drink pool not found in: {brand_names_lower}"
        assert any("biscuit" in b or "snack" in b for b in brand_names_lower), f"Biscuit pool not found in: {brand_names_lower}"
        assert any("fortune" in b for b in brand_names_lower), f"Fortune pool not found in: {brand_names_lower}"
        print(f"Found all 3 brand pools: {brand_names_lower}")

    def test_join_pool_requires_auth(self):
        """POST /api/v2/sponsored/join should require auth (401 without token)"""
        resp = requests.post(f"{BASE_URL}/api/v2/sponsored/join", json={"pool_id": "test-id"})
        assert resp.status_code == 401, f"Expected 401 without auth, got {resp.status_code}"
        print("JOIN requires auth - confirmed 401 without token")

    def test_join_pool_with_auth_invalid_id(self, user_auth):
        """POST /api/v2/sponsored/join with invalid pool_id returns 404"""
        resp = requests.post(f"{BASE_URL}/api/v2/sponsored/join",
                             json={"pool_id": "invalid-pool-id-xyz"},
                             headers=user_auth)
        assert resp.status_code == 404, f"Expected 404 for invalid pool, got {resp.status_code}"
        print("Invalid pool join correctly returns 404")

    def test_join_pool_with_valid_id(self, user_auth):
        """POST /api/v2/sponsored/join with valid pool_id should succeed"""
        # First get a pool ID
        pools_resp = requests.get(f"{BASE_URL}/api/v2/sponsored", headers=user_auth)
        assert pools_resp.status_code == 200
        pools = pools_resp.json()
        if not pools:
            pytest.skip("No pools available to join")

        pool_id = pools[0]["id"]
        resp = requests.post(f"{BASE_URL}/api/v2/sponsored/join",
                             json={"pool_id": pool_id},
                             headers=user_auth)
        # Either success (200) or "already joined" (400)
        assert resp.status_code in [200, 400], f"Expected 200 or 400, got {resp.status_code}: {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("success") == True, f"Expected success:True, got {data}"
        print(f"Join pool result: {resp.status_code} - {resp.json()}")


# ── Quest Engine Tests ─────────────────────────────────────────────────────────

class TestQuestEngine:
    """Quest Engine - Rebound Quest System"""

    def test_quest_status_requires_auth(self):
        """GET /api/v2/quest/status returns 401 without auth"""
        resp = requests.get(f"{BASE_URL}/api/v2/quest/status")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("Quest status requires auth - confirmed 401")

    def test_quest_status_with_auth(self, user_auth):
        """GET /api/v2/quest/status returns eligibility info"""
        resp = requests.get(f"{BASE_URL}/api/v2/quest/status", headers=user_auth)
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "eligible" in data, f"'eligible' field missing from: {data}"
        assert "streak" in data or "reason" in data, f"Missing streak/reason: {data}"
        print(f"Quest status: eligible={data.get('eligible')}, reason={data.get('reason')}")

    def test_quest_offer_creates_session(self, user_auth):
        """POST /api/v2/quest/offer creates or returns existing quest session"""
        resp = requests.post(f"{BASE_URL}/api/v2/quest/offer", json={}, headers=user_auth)
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "id" in data, f"'id' (quest_id) missing from: {data}"
        assert "status" in data, f"'status' missing from: {data}"
        assert "user_id" in data, f"'user_id' missing from: {data}"
        print(f"Quest offer: quest_id={data.get('id')}, status={data.get('status')}")

    def test_quest_offer_idempotent(self, user_auth):
        """POST /api/v2/quest/offer is idempotent - same quest returned today"""
        resp1 = requests.post(f"{BASE_URL}/api/v2/quest/offer", json={}, headers=user_auth)
        resp2 = requests.post(f"{BASE_URL}/api/v2/quest/offer", json={}, headers=user_auth)
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        data1 = resp1.json()
        data2 = resp2.json()
        assert data1["id"] == data2["id"], f"Quest IDs should be same. Got {data1['id']} vs {data2['id']}"
        print(f"Quest offer idempotent: both calls return same quest_id={data1['id']}")

    def test_quest_offer_requires_auth(self):
        """POST /api/v2/quest/offer returns 401 without auth"""
        resp = requests.post(f"{BASE_URL}/api/v2/quest/offer", json={})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("Quest offer requires auth - confirmed 401")


# ── KPI Routes Tests ──────────────────────────────────────────────────────────

class TestKPIRoutes:
    """KPI Analytics Routes - Admin only"""

    def test_kpis_requires_admin_auth(self):
        """GET /api/v2/kpis returns 401 without auth"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("KPIs requires auth - confirmed 401")

    def test_kpis_returns_403_for_non_admin(self, user_auth):
        """GET /api/v2/kpis returns 403 for non-admin user"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis", headers=user_auth)
        assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}: {resp.text}"
        print("KPIs returns 403 for non-admin - confirmed")

    def test_kpis_with_admin_auth(self, admin_auth):
        """GET /api/v2/kpis with admin auth returns KPI data"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis", headers=admin_auth)
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Verify structure
        assert "users" in data, f"'users' missing from KPIs: {data.keys()}"
        assert "quests" in data, f"'quests' missing from KPIs: {data.keys()}"
        assert "redemptions" in data, f"'redemptions' missing from KPIs: {data.keys()}"
        assert "sponsored_pools" in data, f"'sponsored_pools' missing from KPIs: {data.keys()}"
        assert "revenue_estimates" in data, f"'revenue_estimates' missing from KPIs: {data.keys()}"
        # Nested checks
        assert "total" in data["users"]
        assert "opt_in_rate_pct" in data["quests"]
        assert "pool_lift_pct" in data["sponsored_pools"]
        print(f"KPIs: users={data['users']['total']}, quest_opt_in={data['quests']['opt_in_rate_pct']}%, pool_lift={data['sponsored_pools']['pool_lift_pct']}%")

    def test_cohort_csv_requires_admin_auth(self):
        """GET /api/v2/kpis/cohort-csv returns 401 without auth"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/cohort-csv")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("Cohort CSV requires auth - confirmed 401")

    def test_cohort_csv_with_admin_auth(self, admin_auth):
        """GET /api/v2/kpis/cohort-csv returns 7-day cohort data"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/cohort-csv", headers=admin_auth)
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "rows" in data, f"'rows' missing from cohort data: {data}"
        assert "columns" in data, f"'columns' missing from cohort data: {data}"
        assert isinstance(data["rows"], list)
        assert len(data["rows"]) == 8, f"Expected 8 days (7+today), got {len(data['rows'])}"
        # Check row structure
        if data["rows"]:
            row = data["rows"][0]
            assert "date" in row, f"Row missing 'date': {row}"
            assert "registrations" in row, f"Row missing 'registrations': {row}"
            assert "redemptions" in row, f"Row missing 'redemptions': {row}"
        print(f"Cohort CSV: {len(data['rows'])} days, columns: {data['columns']}")

    def test_cohort_csv_returns_403_for_non_admin(self, user_auth):
        """GET /api/v2/kpis/cohort-csv returns 403 for non-admin"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/cohort-csv", headers=user_auth)
        assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}"
        print("Cohort CSV returns 403 for non-admin - confirmed")
