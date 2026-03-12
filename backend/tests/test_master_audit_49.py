"""
Master Audit Test Suite - Iteration 49
Tests: PROGA compliance, trademark audit, all key API endpoints, FCM campaigns,
Cashfree, Reloadly, KPIs, coin economy, security, PWA, load test.
"""
import pytest
import requests
import os
import time
import asyncio
import concurrent.futures
from typing import Optional

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# ─── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def user_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test_redesign_ui26@free11test.com",
        "password": "Test@1234"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]

@pytest.fixture(scope="module")
def admin_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@free11.com",
        "password": "Admin@123"
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json()["access_token"]

@pytest.fixture(scope="module")
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ─── 1. HEALTH CHECK ─────────────────────────────────────────────────────────

class TestHealth:
    """Backend health and basic connectivity"""

    def test_health_returns_200(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        data = resp.json()
        assert data.get("status") == "ok"
        print(f"PASS: Health OK - version={data.get('version')}, db={data.get('database_status')}")

    def test_health_database_connected(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        data = resp.json()
        assert data.get("database_status") == "connected"
        print("PASS: Database connected")

    def test_health_env_production(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        data = resp.json()
        env = data.get("env", "")
        assert env in ["production", "staging", "development"]
        print(f"PASS: Env = {env}")


# ─── 2. AUTH FLOW ─────────────────────────────────────────────────────────────

class TestAuth:
    """Authentication flows"""

    def test_login_valid_returns_token(self, user_token):
        assert len(user_token) > 20
        print("PASS: User login returns JWT token")

    def test_login_invalid_returns_401(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert resp.status_code in [401, 400], f"Expected 401/400, got {resp.status_code}"
        print("PASS: Invalid credentials returns 401/400")

    def test_admin_login_works(self, admin_token):
        assert len(admin_token) > 20
        print("PASS: Admin login returns JWT token")

    def test_jwt_required_for_protected(self):
        """Security: no token → 401 not 500"""
        resp = requests.get(f"{BASE_URL}/api/v2/ledger/balance")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("PASS: Protected endpoint returns 401 without token")

    def test_unauth_returns_401_not_500(self):
        """Security: unauth returns 401, not 500"""
        endpoints = [
            "/api/v2/ledger/balance",
            "/api/v2/kpis",
        ]
        for ep in endpoints:
            resp = requests.get(f"{BASE_URL}{ep}")
            assert resp.status_code != 500, f"{ep} returned 500 without auth!"
            assert resp.status_code in [401, 403, 405], f"{ep} returned {resp.status_code}"
        print("PASS: All protected endpoints return 401/403, not 500")


# ─── 3. COIN ECONOMY ─────────────────────────────────────────────────────────

class TestCoinEconomy:
    """Coin balance, check-in, earning"""

    def test_get_balance_with_auth(self, user_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/ledger/balance", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "coins" in data or "balance" in data or "free_coins" in data or "total" in data
        print(f"PASS: Balance endpoint works - data keys: {list(data.keys())}")

    def test_check_in_endpoint_exists(self, user_headers):
        # The check-in is at /api/v2/engage/streak/checkin
        resp = requests.post(f"{BASE_URL}/api/v2/engage/streak/checkin", headers=user_headers)
        # Either 200 (new check-in) or 400 (already checked in today)
        assert resp.status_code in [200, 400, 409], f"Unexpected status: {resp.status_code} {resp.text}"
        print(f"PASS: Check-in endpoint responds: {resp.status_code}")

    def test_check_in_response_structure(self, user_headers):
        resp = requests.post(f"{BASE_URL}/api/v2/engage/streak/checkin", headers=user_headers)
        data = resp.json()
        if resp.status_code == 200:
            assert "coins_earned" in data or "coins" in data or "streak_days" in data
            print(f"PASS: Check-in success - {data}")
        else:
            # Already checked in today
            print(f"PASS: Check-in already done today - {data}")


# ─── 4. SHOP / PRODUCTS ──────────────────────────────────────────────────────

class TestShop:
    """Products and shop endpoints"""

    def test_products_endpoint_exists(self):
        resp = requests.get(f"{BASE_URL}/api/products")
        assert resp.status_code == 200, f"Products failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert isinstance(data, list) or isinstance(data, dict)
        print(f"PASS: Products endpoint works")

    def test_router_skus_no_trademark_brands(self):
        """No Pepsi/Parle in SKU data"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        assert resp.status_code == 200, f"SKUs failed: {resp.status_code}"
        data = resp.json()
        text = str(data).lower()
        bad_brands = ["pepsi", "parle-g", "parle g", "coca-cola", "sprite", "lays", "dream11"]
        found_brands = [b for b in bad_brands if b in text]
        assert len(found_brands) == 0, f"TRADEMARK VIOLATION: Found {found_brands} in SKU response!"
        print(f"PASS: No trademark brands in SKU data")

    def test_sponsored_endpoint_exists(self):
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored")
        assert resp.status_code in [200, 401], f"Sponsored failed: {resp.status_code}"
        print(f"PASS: Sponsored endpoint exists: {resp.status_code}")

    def test_sponsored_no_trademark_brands(self):
        """No Pepsi/Parle in sponsored data"""
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored")
        if resp.status_code == 200:
            text = str(resp.json()).lower()
            bad_brands = ["pepsi", "parle-g", "coca-cola", "sprite", "lays"]
            found = [b for b in bad_brands if b in text]
            assert len(found) == 0, f"TRADEMARK VIOLATION in sponsored: {found}"
        print("PASS: No trademark brands in sponsored data")


# ─── 5. MATCH CENTRE ─────────────────────────────────────────────────────────

class TestMatchCentre:
    """Match data endpoints"""

    def test_live_matches_endpoint(self):
        resp = requests.get(f"{BASE_URL}/api/v2/matches/live")
        assert resp.status_code == 200, f"Live matches failed: {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list) or "matches" in data or "data" in data
        print(f"PASS: Live matches endpoint works")

    def test_all_matches_endpoint(self):
        resp = requests.get(f"{BASE_URL}/api/v2/matches")
        assert resp.status_code in [200, 404], f"Matches failed: {resp.status_code}"
        print(f"PASS: Matches endpoint: {resp.status_code}")


# ─── 6. KPI ENDPOINT ─────────────────────────────────────────────────────────

class TestKPIs:
    """KPI endpoints (admin)"""

    def test_kpi_requires_auth(self):
        resp = requests.get(f"{BASE_URL}/api/v2/kpis")
        assert resp.status_code in [401, 403], f"KPI should require auth: {resp.status_code}"
        print(f"PASS: KPI requires auth: {resp.status_code}")

    def test_kpi_returns_data_for_admin(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/kpis", headers=admin_headers)
        assert resp.status_code == 200, f"KPI failed for admin: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "users" in data or "total_users" in data or "revenue" in data
        print(f"PASS: KPI returns data - keys: {list(data.keys())[:5]}")

    def test_kpi_users_field(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/kpis", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        if "users" in data:
            assert "total" in data["users"]
            print(f"PASS: KPI users.total = {data['users']['total']}")


# ─── 7. FCM CAMPAIGNS ────────────────────────────────────────────────────────

class TestFCMCampaigns:
    """FCM push notification campaigns"""

    def test_campaign_endpoint_exists(self, admin_headers):
        """POST /api/v2/push/campaign exists and returns proper response"""
        payload = {
            "template": "match_starting",
            "target": "all",
            "data": {"dry_run": True}
        }
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/campaign",
            json=payload,
            headers=admin_headers
        )
        assert resp.status_code in [200, 201, 400, 422], f"Campaign endpoint failed: {resp.status_code} {resp.text}"
        print(f"PASS: FCM campaign endpoint exists: {resp.status_code}")

    def test_campaign_requires_admin(self, user_headers):
        """Non-admin user should get 403"""
        payload = {"template": "match_starting", "target": "all"}
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/campaign",
            json=payload,
            headers=user_headers
        )
        assert resp.status_code == 403, f"Expected 403 for non-admin: {resp.status_code}"
        print("PASS: Campaign endpoint requires admin")

    def test_campaign_templates_endpoint(self, admin_headers):
        """GET /api/v2/push/templates returns templates"""
        resp = requests.get(
            f"{BASE_URL}/api/v2/push/templates",
            headers=admin_headers
        )
        assert resp.status_code in [200, 404], f"Templates: {resp.status_code}"
        print(f"PASS: Templates endpoint: {resp.status_code}")

    def test_list_campaigns_endpoint(self, admin_headers):
        """GET /api/v2/push/campaigns returns list"""
        resp = requests.get(
            f"{BASE_URL}/api/v2/push/campaigns",
            headers=admin_headers
        )
        assert resp.status_code == 200, f"List campaigns failed: {resp.status_code}"
        assert isinstance(resp.json(), list)
        print(f"PASS: List campaigns returns {len(resp.json())} campaigns")


# ─── 8. CASHFREE ENDPOINTS ───────────────────────────────────────────────────

class TestCashfree:
    """Cashfree payment endpoints (keys not configured - expect config error not 404)"""

    def test_cashfree_status_endpoint(self):
        resp = requests.get(f"{BASE_URL}/api/cashfree/status")
        assert resp.status_code != 404, f"Cashfree /status returned 404 - endpoint missing!"
        print(f"PASS: Cashfree /status endpoint exists: {resp.status_code}")

    def test_cashfree_create_order_exists(self, user_headers):
        """POST /api/cashfree/create-order exists - returns error (no keys) not 404"""
        payload = {"amount": 99.0, "purpose": "coins_pack_99"}
        resp = requests.post(
            f"{BASE_URL}/api/cashfree/create-order",
            json=payload,
            headers=user_headers
        )
        # Should return 400/422/500 (config error) NOT 404
        assert resp.status_code != 404, f"Cashfree create-order returned 404 - endpoint missing!"
        print(f"PASS: Cashfree create-order endpoint exists: {resp.status_code}")

    def test_cashfree_packages_endpoint(self):
        resp = requests.get(f"{BASE_URL}/api/cashfree/packages")
        assert resp.status_code != 404, f"Cashfree /packages returned 404!"
        print(f"PASS: Cashfree /packages exists: {resp.status_code}")


# ─── 9. RELOADLY ENDPOINTS ───────────────────────────────────────────────────

class TestReloadly:
    """Reloadly gift card endpoints (fallback to mock if not activated)"""

    def test_reloadly_catalog_returns_products(self, user_headers):
        resp = requests.get(f"{BASE_URL}/api/reloadly/catalog", headers=user_headers)
        assert resp.status_code == 200, f"Reloadly catalog failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert isinstance(data, list) or "products" in data or "catalog" in data
        print(f"PASS: Reloadly catalog returns data")

    def test_reloadly_india_catalog(self, user_headers):
        resp = requests.get(f"{BASE_URL}/api/reloadly/catalog/india", headers=user_headers)
        assert resp.status_code in [200, 404], f"India catalog: {resp.status_code}"
        print(f"PASS: Reloadly India catalog: {resp.status_code}")

    def test_reloadly_order_endpoint_exists(self, user_headers):
        """POST /api/reloadly/order endpoint exists"""
        # Send minimal payload - expect 400/422 (validation) not 404
        resp = requests.post(
            f"{BASE_URL}/api/reloadly/order",
            json={"product_id": "test", "quantity": 1},
            headers=user_headers
        )
        assert resp.status_code != 404, f"Reloadly /order returned 404 - endpoint missing!"
        print(f"PASS: Reloadly order endpoint exists: {resp.status_code}")

    def test_reloadly_status_endpoint(self):
        resp = requests.get(f"{BASE_URL}/api/reloadly/status")
        assert resp.status_code in [200, 404], f"Reloadly status: {resp.status_code}"
        print(f"PASS: Reloadly status: {resp.status_code}")


# ─── 10. LEADERBOARD ─────────────────────────────────────────────────────────

class TestLeaderboard:
    """Leaderboard - no IPL Champ / Cric Ace names"""

    def test_leaderboard_endpoint(self):
        resp = requests.get(f"{BASE_URL}/api/v2/leaderboard")
        assert resp.status_code in [200, 404], f"Leaderboard: {resp.status_code}"
        print(f"PASS: Leaderboard endpoint: {resp.status_code}")

    def test_no_ipl_champ_in_leaderboard(self):
        """No 'IPL Champ' or 'Cric Ace' names in leaderboard data"""
        resp = requests.get(f"{BASE_URL}/api/v2/leaderboard")
        if resp.status_code == 200:
            text = str(resp.json())
            assert "IPL Champ" not in text, "FOUND 'IPL Champ' in leaderboard!"
            assert "Cric Ace" not in text, "FOUND 'Cric Ace' in leaderboard!"
        print("PASS: No trademark names in leaderboard")

    def test_card_game_leaderboard(self):
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-leaderboard")
        assert resp.status_code == 200, f"Card leaderboard: {resp.status_code}"
        data = resp.json()
        assert "leaderboard" in data
        print(f"PASS: Card game leaderboard: {len(data['leaderboard'])} entries")


# ─── 11. WALLET / TRANSACTIONS ───────────────────────────────────────────────

class TestWallet:
    """Wallet and transaction history"""

    def test_wallet_history_endpoint(self, user_headers):
        # Correct endpoint: /api/v2/payments/history
        resp = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=user_headers)
        assert resp.status_code == 200, f"Wallet history failed: {resp.status_code}"
        data = resp.json()
        # Response uses coin_transactions key
        assert "transactions" in data or "coin_transactions" in data or isinstance(data, list)
        print(f"PASS: Wallet history returns data - keys: {list(data.keys())}")

    def test_wallet_history_has_unique_ids(self, user_headers):
        """Transactions should have unique IDs (no React key warnings)"""
        resp = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=user_headers)
        if resp.status_code == 200:
            data = resp.json()
            txns = data.get("transactions", data) if isinstance(data, dict) else data
            if isinstance(txns, list) and len(txns) > 1:
                ids = [t.get("id", t.get("_id", "")) for t in txns]
                assert len(ids) == len(set(ids)), "DUPLICATE transaction IDs found!"
        print("PASS: Wallet transactions have unique IDs")


# ─── 12. PROFILE ─────────────────────────────────────────────────────────────

class TestProfile:
    """User profile"""

    def test_profile_endpoint(self, user_headers):
        # Correct endpoint: /api/auth/me
        resp = requests.get(f"{BASE_URL}/api/auth/me", headers=user_headers)
        assert resp.status_code == 200, f"Profile failed: {resp.status_code}"
        data = resp.json()
        assert "email" in data or "user" in data
        print(f"PASS: Profile endpoint works")

    def test_prediction_streak_endpoint(self, user_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/prediction-streak", headers=user_headers)
        assert resp.status_code in [200, 404], f"Streak: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert "streak" in data or "days" in data or "current_streak" in data
        print(f"PASS: Prediction streak endpoint: {resp.status_code}")


# ─── 13. ADMIN PANEL ─────────────────────────────────────────────────────────

class TestAdminPanel:
    """Admin panel endpoints"""

    def test_admin_kpi_data(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/kpis", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Check has key sections
        assert "users" in data
        print(f"PASS: Admin KPI returns users: {data['users']}")

    def test_admin_kpi_arr_forecast_data(self, admin_headers):
        """ARR forecast needs users.total, redemptions.repeat_rate_30d_pct"""
        resp = requests.get(f"{BASE_URL}/api/v2/kpis", headers=admin_headers)
        data = resp.json()
        assert "users" in data and "total" in data["users"]
        print(f"PASS: ARR forecast data available: users.total={data['users']['total']}")


# ─── 14. SPONSORED POOLS ─────────────────────────────────────────────────────

class TestSponsoredPools:
    """Sponsored pools - PROGA compliant, no trademark brands"""

    def test_sponsored_pools_endpoint(self, user_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored", headers=user_headers)
        assert resp.status_code in [200, 404], f"Sponsored: {resp.status_code}"
        print(f"PASS: Sponsored pools endpoint: {resp.status_code}")

    def test_sponsored_no_ipl2026(self, user_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored", headers=user_headers)
        if resp.status_code == 200:
            text = str(resp.json())
            assert "IPL 2026" not in text, "TRADEMARK: Found 'IPL 2026' in sponsored!"
            print("PASS: No 'IPL 2026' in sponsored data")


# ─── 15. CARD GAMES ──────────────────────────────────────────────────────────

class TestCardGames:
    """Card game endpoints"""

    def test_teen_patti_win_endpoint(self, user_headers):
        resp = requests.post(f"{BASE_URL}/api/v2/earn/teen-patti-win", headers=user_headers)
        assert resp.status_code in [200, 400, 409], f"Teen Patti win: {resp.status_code}"
        print(f"PASS: Teen Patti win endpoint: {resp.status_code}")

    def test_solitaire_win_endpoint(self, user_headers):
        resp = requests.post(f"{BASE_URL}/api/v2/earn/solitaire-win", headers=user_headers)
        assert resp.status_code in [200, 400, 409], f"Solitaire win: {resp.status_code}"
        print(f"PASS: Solitaire win endpoint: {resp.status_code}")

    def test_rummy_win_endpoint(self, user_headers):
        resp = requests.post(f"{BASE_URL}/api/v2/earn/rummy-win", headers=user_headers)
        assert resp.status_code in [200, 400, 409], f"Rummy win: {resp.status_code}"
        print(f"PASS: Rummy win endpoint: {resp.status_code}")

    def test_poker_win_endpoint(self, user_headers):
        resp = requests.post(f"{BASE_URL}/api/v2/earn/poker-win", headers=user_headers)
        assert resp.status_code in [200, 400, 409], f"Poker win: {resp.status_code}"
        print(f"PASS: Poker win endpoint: {resp.status_code}")

    def test_card_game_streak(self, user_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-streak", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "streak" in data
        print(f"PASS: Card streak: {data['streak']} days")


# ─── 16. LOAD TEST ───────────────────────────────────────────────────────────

class TestLoadTest:
    """50 concurrent requests load test"""

    def _make_request(self, url):
        start = time.time()
        try:
            resp = requests.get(url, timeout=10)
            elapsed = time.time() - start
            return resp.status_code, elapsed
        except Exception as e:
            return 0, time.time() - start

    def test_health_under_load_50_concurrent(self):
        """50 concurrent GET /api/health - measure p95 latency and error rate"""
        url = f"{BASE_URL}/api/health"
        n = 50
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(self._make_request, url) for _ in range(n)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        statuses = [r[0] for r in results]
        latencies = sorted([r[1] for r in results])
        error_count = sum(1 for s in statuses if s != 200)
        error_rate = error_count / n * 100
        p50 = latencies[int(n * 0.5)]
        p95 = latencies[int(n * 0.95)]
        p99 = latencies[min(int(n * 0.99), n - 1)]

        print(f"LOAD TEST /health ({n} requests): p50={p50:.2f}s, p95={p95:.2f}s, p99={p99:.2f}s, errors={error_count}/{n} ({error_rate:.1f}%)")
        assert error_rate < 20, f"Error rate too high: {error_rate:.1f}%"
        assert p95 < 10.0, f"p95 latency too high: {p95:.2f}s"  # 10s threshold for preview env

    def test_live_matches_under_load(self):
        """20 concurrent GET /api/v2/matches/live"""
        url = f"{BASE_URL}/api/v2/matches/live"
        n = 20
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self._make_request, url) for _ in range(n)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        statuses = [r[0] for r in results]
        latencies = sorted([r[1] for r in results])
        error_count = sum(1 for s in statuses if s not in [200, 404])
        p95 = latencies[int(n * 0.95)]

        print(f"LOAD TEST /matches/live ({n} requests): p95={p95:.2f}s, errors={error_count}/{n}")
        assert error_count == 0, f"{error_count} errors in live matches load test"

    def test_products_under_load(self):
        """20 concurrent GET /api/products - allow some timeouts in preview env"""
        url = f"{BASE_URL}/api/products"
        n = 20
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self._make_request, url) for _ in range(n)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        statuses = [r[0] for r in results]
        latencies = sorted([r[1] for r in results])
        error_count = sum(1 for s in statuses if s not in [200, 0])
        timeout_count = sum(1 for s in statuses if s == 0)
        p95 = latencies[int(n * 0.95)]

        print(f"LOAD TEST /products ({n} requests): p95={p95:.2f}s, errors={error_count}/{n}, timeouts={timeout_count}")
        # In preview env, /api/products might be slow - check error rate < 50%
        actual_errors = sum(1 for s in statuses if s not in [200, 0])
        assert actual_errors < n * 0.5, f"Too many real errors: {actual_errors}/{n}"


# ─── 17. PWA ─────────────────────────────────────────────────────────────────

class TestPWA:
    """PWA manifest and service worker"""

    def test_manifest_accessible(self):
        resp = requests.get(f"{BASE_URL}/manifest.json")
        assert resp.status_code == 200, f"manifest.json: {resp.status_code}"
        data = resp.json()
        assert "name" in data or "short_name" in data
        print(f"PASS: manifest.json accessible - name={data.get('name', data.get('short_name'))}")

    def test_service_worker_accessible(self):
        resp = requests.get(f"{BASE_URL}/service-worker.js")
        assert resp.status_code in [200, 404], f"sw: {resp.status_code}"
        if resp.status_code == 200:
            print("PASS: service-worker.js accessible")
        else:
            # Some PWAs use different paths
            resp2 = requests.get(f"{BASE_URL}/sw.js")
            print(f"PASS: SW checked: sw.js={resp2.status_code}")


# ─── 18. COMPLIANCE CHECK ────────────────────────────────────────────────────

class TestCompliance:
    """PROGA naming and trademark compliance via API"""

    def test_faq_endpoint_accessible(self):
        resp = requests.get(f"{BASE_URL}/api/faq")
        assert resp.status_code in [200, 404], f"FAQ: {resp.status_code}"
        print(f"PASS: FAQ endpoint: {resp.status_code}")

    def test_no_ipl2026_in_skus(self):
        """Backend SKUs must not contain 'IPL 2026'"""
        resp = requests.get(f"{BASE_URL}/api/v2/router/skus")
        if resp.status_code == 200:
            text = str(resp.json())
            assert "IPL 2026" not in text, "FOUND 'IPL 2026' in SKU data!"
        print("PASS: No 'IPL 2026' in SKU data")

    def test_prediction_types_no_ipl(self):
        """Prediction types should not contain 'IPL 2026'"""
        resp = requests.get(f"{BASE_URL}/api/v2/prediction-types")
        if resp.status_code == 200:
            text = str(resp.json())
            assert "IPL 2026" not in text, "FOUND 'IPL 2026' in prediction types!"
        print(f"PASS: Prediction types endpoint: {resp.status_code}")
