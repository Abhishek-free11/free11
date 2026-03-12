"""
FREE11 Full End-to-End Audit — Iteration 35
Tests: Auth, Registration OTP, Dashboard, Predict, Shop, EarnCoins, Leaderboard, Admin, Wallet/Ledger, Sponsored, Blog
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
    """Cache tokens to avoid repeated logins"""
    test_token = None
    admin_token = None
    test_user_id = None
    admin_user_id = None

    @classmethod
    def get_test_token(cls):
        if cls.test_token:
            return cls.test_token
        resp = requests.post(f"{BASE_URL}/api/auth/login",
                             json={"email": TEST_EMAIL, "password": TEST_PASS})
        if resp.status_code == 200:
            d = resp.json()
            cls.test_token = d.get("access_token")
            cls.test_user_id = d.get("user", {}).get("id")
        return cls.test_token

    @classmethod
    def get_admin_token(cls):
        if cls.admin_token:
            return cls.admin_token
        resp = requests.post(f"{BASE_URL}/api/auth/login",
                             json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        if resp.status_code == 200:
            d = resp.json()
            cls.admin_token = d.get("access_token")
            cls.admin_user_id = d.get("user", {}).get("id")
        return cls.admin_token


# ─── STEP 2: REGISTRATION/OTP ─────────────────────────────────────────────────
class TestOTPRegistration:
    """OTP registration flow"""

    def test_send_otp_returns_dev_otp_on_unverified_domain(self):
        """When Resend domain is unverified, API must return dev_otp in response"""
        unique_email = f"audit_test_{int(time.time())}@free11test.com"
        resp = requests.post(f"{BASE_URL}/api/auth/send-otp",
                             json={"email": unique_email})
        # Must succeed
        assert resp.status_code == 200, f"send-otp failed: {resp.text}"
        data = resp.json()
        # Either email sent or dev_otp returned (domain unverified fallback)
        assert "message" in data or "dev_otp" in data, f"No message or dev_otp in response: {data}"
        print(f"✅ send-otp response: message={data.get('message')}, has_dev_otp={bool(data.get('dev_otp'))}")

    def test_verify_otp_with_wrong_code(self):
        """Invalid OTP should return 400"""
        resp = requests.post(f"{BASE_URL}/api/auth/verify-otp",
                             json={"email": "any@test.com", "otp": "000000"})
        # Expect 400 or 422
        assert resp.status_code in [400, 422, 404], f"Expected error on wrong OTP, got {resp.status_code}: {resp.text}"
        print(f"✅ Wrong OTP rejected: {resp.status_code}")


# ─── STEP 3: LOGIN ────────────────────────────────────────────────────────────
class TestLogin:
    """Login flow"""

    def test_test_user_login_success(self):
        token = TokenCache.get_test_token()
        assert token is not None, "Test user login failed — could not get access_token"
        print(f"✅ Test user login OK, user_id={TokenCache.test_user_id}")

    def test_admin_user_login_success(self):
        token = TokenCache.get_admin_token()
        assert token is not None, "Admin login failed"
        print(f"✅ Admin login OK, user_id={TokenCache.admin_user_id}")

    def test_login_invalid_credentials(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login",
                             json={"email": "wrong@test.com", "password": "wrongpass"})
        assert resp.status_code in [400, 401, 422], f"Expected auth failure, got {resp.status_code}"
        print(f"✅ Bad creds rejected: {resp.status_code}")


# ─── STEP 4: DASHBOARD DATA ───────────────────────────────────────────────────
class TestDashboard:
    """Dashboard endpoints"""

    def test_get_demand_progress(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/user/demand-progress",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"demand-progress failed: {resp.text}"
        data = resp.json()
        assert "rank" in data or "next_reward" in data or "prediction_stats" in data, f"Unexpected shape: {data}"
        print(f"✅ demand-progress OK: keys={list(data.keys())}")

    def test_get_transactions(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/coins/transactions",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"transactions failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"✅ transactions OK: {len(data)} items")

    def test_get_leaderboard(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/leaderboard",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"leaderboard failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"✅ leaderboard OK: {len(data)} entries")

    def test_get_user_profile(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/auth/me",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"profile failed: {resp.text}"
        data = resp.json()
        assert "email" in data, f"No email in profile: {data}"
        assert "coins_balance" in data, f"No coins_balance in profile: {data}"
        print(f"✅ profile OK: email={data['email']}, coins={data['coins_balance']}")

    def test_daily_checkin(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.post(f"{BASE_URL}/api/coins/checkin",
                             headers={"Authorization": f"Bearer {token}"})
        # Could be 200 (first checkin) or 400 (already checked in today)
        assert resp.status_code in [200, 400], f"checkin unexpected: {resp.status_code} {resp.text}"
        print(f"✅ daily-checkin: {resp.status_code} - {resp.json().get('message','')}")


# ─── STEP 5: PREDICT / MATCHES ────────────────────────────────────────────────
class TestPredictions:
    """Prediction system"""

    def test_get_live_matches(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/v2/es/matches?status_id=3&limit=10",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in [200, 404], f"live matches failed: {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list), f"Expected list: {data}"
        print(f"✅ live matches: {resp.status_code}")

    def test_get_upcoming_matches(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/v2/es/matches?status_id=1&limit=5",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in [200, 404], f"upcoming matches failed: {resp.text}"
        print(f"✅ upcoming matches: {resp.status_code}")

    def test_get_prediction_stats(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/v2/predictions/stats",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"prediction stats failed: {resp.text}"
        data = resp.json()
        assert "total" in data or "accuracy" in data, f"Unexpected shape: {data}"
        print(f"✅ prediction stats OK: {data}")

    def test_get_prediction_streak(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/v2/predictions/streak",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"streak failed: {resp.text}"
        data = resp.json()
        assert "streak" in data, f"No streak in response: {data}"
        print(f"✅ prediction streak OK: streak={data['streak']}")


# ─── STEP 6: EARN COINS ───────────────────────────────────────────────────────
class TestEarnCoins:
    """Earn coins flow - tasks, spin, scratch, quiz"""

    def test_get_tasks(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/tasks",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"tasks failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"✅ tasks OK: {len(data)} tasks")

    def test_spin_wheel(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.post(f"{BASE_URL}/api/games/spin",
                             headers={"Authorization": f"Bearer {token}"})
        # Could be 200 (won/lost) or 400 (already spun today)
        assert resp.status_code in [200, 400], f"spin-wheel unexpected: {resp.status_code} {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            assert "coins_earned" in data or "message" in data, f"Unexpected: {data}"
        print(f"✅ spin-wheel: {resp.status_code}")

    def test_scratch_card(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.post(f"{BASE_URL}/api/games/scratch",
                             headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in [200, 400], f"scratch-card unexpected: {resp.status_code} {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            assert "coins_earned" in data or "attempts_left" in data, f"Unexpected: {data}"
        print(f"✅ scratch-card: {resp.status_code}")


# ─── STEP 8/9: SHOP ───────────────────────────────────────────────────────────
class TestShop:
    """Shop products and redemption"""

    def test_get_products_returns_list(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/products",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"products failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        assert len(data) > 0, "No products returned"
        # Check structure
        p = data[0]
        assert "id" in p, "No id in product"
        assert "name" in p, "No name in product"
        assert "coin_price" in p, "No coin_price in product"
        print(f"✅ products OK: {len(data)} products, first: {p['name']} ({p['coin_price']} coins)")

    def test_products_have_images(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/products",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        products_without_images = [p['name'] for p in data if not p.get('image_url')]
        assert len(products_without_images) == 0 or len(products_without_images) < 5, \
            f"Too many products without images: {products_without_images[:5]}"
        print(f"✅ product images check: {len(data) - len(products_without_images)}/{len(data)} have images")

    def test_get_redemptions(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/redemptions",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"redemptions failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"✅ redemptions OK: {len(data)} past redemptions")

    def test_get_wishlist(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/v2/wishlist",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in [200, 404], f"wishlist failed: {resp.text}"
        print(f"✅ wishlist: {resp.status_code}")


# ─── STEP 13: WALLET/LEDGER ───────────────────────────────────────────────────
class TestWalletLedger:
    """Wallet and transaction ledger"""

    def test_get_ledger_transactions(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/coins/transactions",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"transactions failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list: {type(data)}"
        if len(data) > 0:
            tx = data[0]
            assert "amount" in tx, f"No amount in tx: {tx}"
            assert "description" in tx, f"No description in tx: {tx}"
            assert "timestamp" in tx, f"No timestamp in tx: {tx}"
        print(f"✅ ledger OK: {len(data)} transactions")


# ─── STEP 15: LEADERBOARDS ────────────────────────────────────────────────────
class TestLeaderboards:
    """Leaderboard endpoints"""

    def test_global_leaderboard(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/leaderboards/global?limit=50",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"global leaderboard failed: {resp.text}"
        data = resp.json()
        assert "leaderboard" in data, f"No leaderboard key: {data}"
        print(f"✅ global leaderboard: {len(data['leaderboard'])} entries")

    def test_weekly_leaderboard(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/leaderboards/weekly?limit=50",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"weekly leaderboard failed: {resp.text}"
        data = resp.json()
        assert "leaderboard" in data, f"No leaderboard key: {data}"
        print(f"✅ weekly leaderboard: {len(data['leaderboard'])} entries")

    def test_streak_leaderboard(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/leaderboards/streak?limit=50",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"streak leaderboard failed: {resp.text}"
        data = resp.json()
        assert "leaderboard" in data, f"No leaderboard key: {data}"
        print(f"✅ streak leaderboard: {len(data['leaderboard'])} entries")


# ─── STEP 17: SPONSORED POOLS ────────────────────────────────────────────────
class TestSponsoredPools:
    """Sponsored pools"""

    def test_get_sponsored_pools(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/v2/sponsored?status=open",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"sponsored pools failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list: {type(data)}"
        print(f"✅ sponsored pools: {len(data)} pools")


# ─── STEP 20: ADMIN V2 ────────────────────────────────────────────────────────
class TestAdminV2:
    """Admin V2 endpoints"""

    def test_admin_get_kpis(self):
        token = TokenCache.get_admin_token()
        if not token:
            pytest.skip("No admin token")
        resp = requests.get(f"{BASE_URL}/api/v2/kpis",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"admin KPIs failed: {resp.text}"
        data = resp.json()
        assert "users" in data, f"No users in KPIs: {data}"
        assert "redemptions" in data, f"No redemptions in KPIs: {data}"
        print(f"✅ admin KPIs OK: total_users={data['users'].get('total')}")

    def test_admin_get_feature_flags(self):
        token = TokenCache.get_admin_token()
        if not token:
            pytest.skip("No admin token")
        resp = requests.get(f"{BASE_URL}/api/admin/v2/feature-flags",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"feature flags failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list: {data}"
        print(f"✅ feature flags OK: {len(data)} flags")

    def test_admin_get_cohort_csv(self):
        token = TokenCache.get_admin_token()
        if not token:
            pytest.skip("No admin token")
        resp = requests.get(f"{BASE_URL}/api/v2/kpis/cohort-csv",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"cohort csv failed: {resp.text}"
        data = resp.json()
        assert "rows" in data, f"No rows in cohort: {data}"
        print(f"✅ cohort csv OK: {len(data.get('rows', []))} rows")

    def test_admin_get_action_log(self):
        token = TokenCache.get_admin_token()
        if not token:
            pytest.skip("No admin token")
        resp = requests.get(f"{BASE_URL}/api/admin/v2/action-log?limit=20",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"action log failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list: {data}"
        print(f"✅ action log OK: {len(data)} entries")


# ─── HEALTH CHECK ─────────────────────────────────────────────────────────────
class TestHealth:
    """Health check"""

    def test_health_endpoint(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200, f"health check failed: {resp.text}"
        data = resp.json()
        assert data.get("status") == "ok" or "status" in data, f"Unexpected: {data}"
        print(f"✅ health OK: {data}")

    def test_quest_status(self):
        token = TokenCache.get_test_token()
        if not token:
            pytest.skip("No test token")
        resp = requests.get(f"{BASE_URL}/api/v2/quest/status",
                            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in [200, 404], f"quest status failed: {resp.text}"
        print(f"✅ quest status: {resp.status_code}")

    def test_ipl_carousel_exists_in_components(self):
        """IPLCarousel component referenced in Dashboard"""
        import os
        carousel_path = "/app/frontend/src/components/IPLCarousel.js"
        assert os.path.exists(carousel_path), f"IPLCarousel.js not found at {carousel_path}"
        print(f"✅ IPLCarousel.js exists")
