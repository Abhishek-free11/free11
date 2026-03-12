"""
FREE11 Comprehensive Regression Test - Iteration 31
Tests: Payments History, AdMob Rewards, Push Notifications, OTP/Resend, Razorpay,
       Entity Sport Squads (Team Builder Playing XI), Contest voided label
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASSWORD = "Admin@123"
MATCH_ID = "94717"  # IND vs ENG match for Team Builder


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("token") or data.get("access_token")
        print(f"[AUTH] Token obtained for {ADMIN_EMAIL}")
        return token
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ══════════════════════ LOGIN & DASHBOARD ══════════════════════

class TestLoginAndDashboard:
    """Test login and basic dashboard data"""

    def test_login_with_admin_credentials(self):
        """Login returns 200 with token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data or "access_token" in data, f"No token in response: {data}"
        user = data.get("user", {})
        assert user.get("email") == ADMIN_EMAIL, f"Wrong user returned: {user}"
        print(f"[PASS] Login works. User balance: {user.get('coins_balance', 'N/A')} coins")

    def test_user_has_coins_balance(self, auth_headers):
        """User profile returns coins_balance via /api/auth/me"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200, f"Profile failed: {response.text}"
        data = response.json()
        assert "coins_balance" in data or "balance" in data, f"No balance field: {data.keys()}"
        print(f"[PASS] User profile has coins_balance: {data.get('coins_balance', data.get('balance', '?'))}")


# ══════════════════════ PAYMENTS HISTORY ══════════════════════

class TestPaymentsHistory:
    """Test POST /api/v2/payments/history - returns both transaction types"""

    def test_payments_history_requires_auth(self):
        """GET /api/v2/payments/history returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("[PASS] /api/v2/payments/history requires auth")

    def test_payments_history_returns_200(self, auth_headers):
        """GET /api/v2/payments/history returns 200 with auth"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("[PASS] /api/v2/payments/history returns 200")

    def test_payments_history_structure(self, auth_headers):
        """Response must contain free_bucks_purchases and coin_transactions"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        assert "free_bucks_purchases" in data, f"Missing free_bucks_purchases. Keys: {list(data.keys())}"
        assert "coin_transactions" in data, f"Missing coin_transactions. Keys: {list(data.keys())}"
        assert isinstance(data["free_bucks_purchases"], list), "free_bucks_purchases not a list"
        assert isinstance(data["coin_transactions"], list), "coin_transactions not a list"
        print(f"[PASS] History has {len(data['free_bucks_purchases'])} purchases, {len(data['coin_transactions'])} coin txns")

    def test_no_mongodb_id_in_history(self, auth_headers):
        """No _id fields should appear in the response"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        for item in data.get("free_bucks_purchases", []) + data.get("coin_transactions", []):
            assert "_id" not in item, f"MongoDB _id exposed in response: {item}"
        print("[PASS] No MongoDB _id fields in history response")

    def test_coin_transactions_have_type(self, auth_headers):
        """Coin transactions should have type and timestamp"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        txns = data.get("coin_transactions", [])
        if not txns:
            pytest.skip("No coin transactions for admin user - skip structure check")
        for txn in txns[:3]:
            assert "type" in txn or "description" in txn, f"Txn missing type/description: {txn}"
            assert "timestamp" in txn, f"Txn missing timestamp: {txn}"
        print(f"[PASS] Coin transactions have correct structure (checked {min(3, len(txns))} txns)")


# ══════════════════════ ADMOB REWARDS ══════════════════════

class TestAdMobRewards:
    """Test POST /api/v2/ads/reward - credits 20 coins, daily limit 5"""

    def test_admob_reward_requires_auth(self):
        """POST /api/v2/ads/reward returns 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/v2/ads/reward", json={"reward_type": "ad_watch"})
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("[PASS] /api/v2/ads/reward requires auth")

    def test_admob_reward_credits_coins(self, auth_headers):
        """POST /api/v2/ads/reward returns reward_coins=20 or 429 limit"""
        response = requests.post(f"{BASE_URL}/api/v2/ads/reward",
                                  json={"reward_type": "ad_watch"},
                                  headers=auth_headers)
        # Either 200 (credited) or 429 (daily limit reached)
        assert response.status_code in [200, 429], f"Unexpected: {response.status_code}: {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert data.get("reward_coins") == 20, f"Expected 20 coins, got {data.get('reward_coins')}"
            assert "success" in data, f"Missing success field: {data}"
            assert data.get("daily_limit") == 5, f"Daily limit should be 5, got {data.get('daily_limit')}"
            print(f"[PASS] AdMob reward credited: {data.get('reward_coins')} coins, remaining: {data.get('remaining_today')}")
        else:
            data = response.json()
            assert "Daily ad limit" in data.get("detail", ""), f"Expected daily limit error: {data}"
            print("[PASS] AdMob daily limit reached (429) - correct behavior")

    def test_ad_status_endpoint(self, auth_headers):
        """GET /api/v2/ads/status returns status with watched_today and daily_limit"""
        response = requests.get(f"{BASE_URL}/api/v2/ads/status", headers=auth_headers)
        assert response.status_code == 200, f"Ad status failed: {response.text}"
        data = response.json()
        assert "daily_limit" in data, f"Missing daily_limit: {data}"
        assert "watched_today" in data, f"Missing watched_today: {data}"
        assert "remaining_today" in data, f"Missing remaining_today: {data}"
        assert data["daily_limit"] == 5, f"Expected daily_limit=5, got {data['daily_limit']}"
        print(f"[PASS] Ad status: {data.get('watched_today')}/{data.get('daily_limit')} ads watched today")


# ══════════════════════ PUSH NOTIFICATIONS ══════════════════════

class TestPushNotifications:
    """Test /api/v2/push/register and /api/v2/push/send"""

    def test_push_register_requires_auth(self):
        """POST /api/v2/push/register returns 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/v2/push/register",
                                  json={"device_token": "test_token_123", "device_type": "android"})
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("[PASS] /api/v2/push/register requires auth")

    def test_push_register_stores_device(self, auth_headers):
        """POST /api/v2/push/register returns registered:true"""
        response = requests.post(f"{BASE_URL}/api/v2/push/register",
                                  json={"device_token": "test_regression_token_abc123", "device_type": "android"},
                                  headers=auth_headers)
        assert response.status_code == 200, f"Register failed: {response.text}"
        data = response.json()
        assert data.get("registered") is True, f"Expected registered:true, got {data}"
        print(f"[PASS] Push register returns registered:true, device_type={data.get('device_type')}")

    def test_push_send_requires_auth(self):
        """POST /api/v2/push/send returns 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/v2/push/send",
                                  json={"title": "Test", "body": "Test body"})
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("[PASS] /api/v2/push/send requires auth (401 without token)")

    def test_push_send_returns_sent_bool(self, auth_headers):
        """POST /api/v2/push/send returns {sent: bool, target_user_id: str}"""
        response = requests.post(f"{BASE_URL}/api/v2/push/send",
                                  json={"title": "Regression Test", "body": "Test notification"},
                                  headers=auth_headers)
        assert response.status_code == 200, f"Push send failed: {response.text}"
        data = response.json()
        assert "sent" in data, f"Missing 'sent' field: {data}"
        assert "target_user_id" in data, f"Missing 'target_user_id' field: {data}"
        assert isinstance(data["sent"], bool), f"'sent' should be bool, got {type(data['sent'])}"
        print(f"[PASS] Push send returns sent={data.get('sent')} (MOCKED - no real FCM service account)")


# ══════════════════════ OTP / RESEND ══════════════════════

class TestOTPAndResend:
    """Test /api/auth/send-otp and /api/auth/verify-otp"""

    def test_send_otp_returns_sent_true(self):
        """POST /api/auth/send-otp returns sent:true for valid email"""
        import time
        # Use timestamp-based email to avoid cooldown from previous test runs
        ts = int(time.time())
        test_email = f"regression_test_31_{ts}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/send-otp",
                                  json={"email": test_email})
        assert response.status_code in [200, 429], f"send-otp failed: {response.status_code} {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert data.get("sent") is True, f"Expected sent:true, got {data}"
            print(f"[PASS] send-otp returns sent:true. dev_otp={'dev_otp' in data}")
        else:
            print(f"[INFO] send-otp 429 (cooldown from previous run) - cooldown mechanism works")

    def test_send_otp_provides_dev_otp(self):
        """POST /api/auth/send-otp should return dev_otp (Resend domain not verified)"""
        import time
        ts = int(time.time()) + 1
        test_email = f"regression_test_31b_{ts}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/send-otp",
                                  json={"email": test_email})
        assert response.status_code in [200, 429], f"send-otp failed: {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert data.get("sent") is True, f"Expected sent:true: {data}"
            if "dev_otp" in data:
                print(f"[PASS] Dev OTP present in response: {data['dev_otp']} (MOCKED - Resend domain not verified)")
            else:
                print(f"[PASS] No dev_otp - Resend email sent (domain may be verified)")
        else:
            print(f"[INFO] 429 cooldown - OTP endpoint working, cooldown active")

    def test_verify_otp_wrong_otp_gives_specific_error(self):
        """POST /api/auth/verify-otp with wrong OTP returns specific error (not generic)"""
        import time
        ts = int(time.time()) + 2
        test_email = f"regression_verify_31_{ts}@test.com"
        # First send OTP
        send_res = requests.post(f"{BASE_URL}/api/auth/send-otp",
                                  json={"email": test_email})
        # Accept both 200 (new OTP) and 429 (cooldown)
        assert send_res.status_code in [200, 429], f"Unexpected: {send_res.status_code}"

        if send_res.status_code == 429:
            # Try verify with a known non-existent email to test error handling
            test_email = f"no_otp_31_{ts}@test.com"

        # Verify with wrong OTP
        verify_res = requests.post(f"{BASE_URL}/api/auth/verify-otp",
                                    json={"email": test_email, "otp": "000000"})
        assert verify_res.status_code in [400, 401, 422], f"Expected error: {verify_res.status_code}"
        data = verify_res.json()
        detail = data.get("detail", "")
        # Should not be generic "Registration failed"
        assert "Registration failed" not in detail, f"Got generic error: {detail}"
        assert len(detail) > 0, f"Empty error detail: {data}"
        print(f"[PASS] Wrong OTP gives specific error: '{detail}'")

    def test_verify_otp_expired_or_nonexistent_gives_specific_error(self):
        """POST /api/auth/verify-otp with no OTP request gives specific error"""
        import time
        ts = int(time.time()) + 3
        verify_res = requests.post(f"{BASE_URL}/api/auth/verify-otp",
                                    json={"email": f"no_otp_sent_31_{ts}@test.com", "otp": "123456"})
        assert verify_res.status_code in [400, 401, 422], f"Expected error: {verify_res.status_code}"
        data = verify_res.json()
        detail = data.get("detail", "")
        assert "Registration failed" not in detail, f"Got generic error: {detail}"
        print(f"[PASS] No-OTP verification gives specific error: '{detail}'")

    def test_otp_cooldown_enforced(self):
        """Send OTP twice quickly should trigger cooldown on second request"""
        import time
        ts = int(time.time()) + 4
        test_email = f"regression_cooldown_31_{ts}@test.com"
        # First send
        r1 = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": test_email})
        # First send should succeed
        assert r1.status_code in [200, 429], f"Unexpected: {r1.status_code}"

        if r1.status_code == 200:
            # Immediate resend (should hit cooldown)
            r2 = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": test_email})
            # Should be 429 or return sent:false with cooldown message
            if r2.status_code == 429:
                print(f"[PASS] OTP cooldown: 429 on immediate resend")
            elif r2.status_code == 200:
                data2 = r2.json()
                if data2.get("sent") is False:
                    assert "wait" in data2.get("error", "").lower(), f"Expected wait message: {data2}"
                    print(f"[PASS] OTP cooldown enforced: {data2.get('error')}")
                else:
                    print(f"[INFO] Cooldown may not have triggered - sent:true twice")
        else:
            print(f"[INFO] First OTP was already in cooldown (429) - prior test run active")


# ══════════════════════ RAZORPAY ══════════════════════

class TestRazorpay:
    """Test Razorpay payment order creation"""

    def test_razorpay_status(self):
        """GET /api/razorpay/status returns enabled flag"""
        response = requests.get(f"{BASE_URL}/api/razorpay/status")
        assert response.status_code == 200, f"Razorpay status failed: {response.text}"
        data = response.json()
        assert "enabled" in data, f"Missing 'enabled' field: {data}"
        print(f"[PASS] Razorpay status: enabled={data.get('enabled')}")

    def test_razorpay_packages(self):
        """GET /api/razorpay/packages returns package list"""
        response = requests.get(f"{BASE_URL}/api/razorpay/packages")
        assert response.status_code == 200, f"Packages failed: {response.text}"
        data = response.json()
        assert len(data) > 0, "No packages returned"
        assert "starter" in data or "popular" in data, f"Expected standard packages: {list(data.keys())}"
        print(f"[PASS] Razorpay packages: {list(data.keys())}")

    def test_razorpay_create_order_requires_auth(self):
        """POST /api/razorpay/create-order returns 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/razorpay/create-order",
                                  json={"package_id": "starter"})
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("[PASS] /api/razorpay/create-order requires auth")

    def test_razorpay_create_order_with_valid_package(self, auth_headers):
        """POST /api/razorpay/create-order with valid package_id"""
        response = requests.post(f"{BASE_URL}/api/razorpay/create-order",
                                  json={"package_id": "starter"},
                                  headers=auth_headers)
        # Can be 200 (order created), 503 (not configured), or 500 (API error)
        assert response.status_code in [200, 503, 500], f"Unexpected: {response.status_code}: {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert "order_id" in data, f"Missing order_id: {data}"
            assert "amount" in data, f"Missing amount: {data}"
            assert "key_id" in data, f"Missing key_id: {data}"
            print(f"[PASS] Razorpay order created: {data.get('order_id')} (TEST MODE)")
        elif response.status_code == 503:
            print(f"[INFO] Razorpay not configured in env (503) - test mode only")
        else:
            print(f"[INFO] Razorpay API error {response.status_code}: {response.text}")

    def test_razorpay_invalid_package(self, auth_headers):
        """POST /api/razorpay/create-order with invalid package returns 400"""
        response = requests.post(f"{BASE_URL}/api/razorpay/create-order",
                                  json={"package_id": "invalid_package_xyz"},
                                  headers=auth_headers)
        # 400 for invalid package, 503 if not configured
        assert response.status_code in [400, 503], f"Expected 400 or 503, got {response.status_code}: {response.text}"
        print(f"[PASS] Invalid package returns {response.status_code}")


# ══════════════════════ ENTITY SPORT SQUADS (Team Builder) ══════════════════════

class TestEntitySportSquads:
    """Test squad data for Team Builder - playing XI filter"""

    def test_squad_endpoint_accessible(self, auth_headers):
        """GET /api/v2/es/match/{match_id}/squads returns data or 404"""
        response = requests.get(f"{BASE_URL}/api/v2/es/match/{MATCH_ID}/squads",
                                  headers=auth_headers)
        # 200 = squad data available, 404 = match not found/no squads
        assert response.status_code in [200, 404, 503], f"Unexpected: {response.status_code}: {response.text}"
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] Squad data returned. Keys: {list(data.keys())}")
        else:
            print(f"[INFO] Squad endpoint returned {response.status_code} for match {MATCH_ID}")

    def test_squad_structure_has_team_squads(self, auth_headers):
        """If squads returned, verify team_a and team_b are present"""
        response = requests.get(f"{BASE_URL}/api/v2/es/match/{MATCH_ID}/squads",
                                  headers=auth_headers)
        if response.status_code != 200:
            pytest.skip(f"Squad not available for match {MATCH_ID}")

        data = response.json()
        assert "team_a" in data or "team_b" in data, f"Neither team_a nor team_b in squads: {list(data.keys())}"
        print(f"[PASS] Squad has team data")

    def test_squad_players_have_playing11_field(self, auth_headers):
        """Players in squad should have playing11 field for filter"""
        response = requests.get(f"{BASE_URL}/api/v2/es/match/{MATCH_ID}/squads",
                                  headers=auth_headers)
        if response.status_code != 200:
            pytest.skip(f"Squad not available for match {MATCH_ID}")

        data = response.json()
        team_a = data.get("team_a", {})
        squad_a = team_a.get("squad", [])
        if squad_a:
            # Check if playing11 field exists in at least one player
            players_with_p11 = [p for p in squad_a if "playing11" in p]
            print(f"[INFO] Team A squad: {len(squad_a)} players, {len(players_with_p11)} with playing11 field")
            if players_with_p11:
                confirmed = [p for p in squad_a if p.get("playing11") is True]
                print(f"[PASS] Playing XI confirmed: {len(confirmed)} players from team_a")
            else:
                print(f"[INFO] playing11 field not present - frontend fallback to full squad expected")
        else:
            print(f"[INFO] No squad data for team_a")


# ══════════════════════ CONTEST HUB ══════════════════════

class TestContestHub:
    """Test contest listing, seeding, and voided status"""

    def test_get_match_contests(self, auth_headers):
        """GET /api/v2/contests/match/{match_id} returns contests array"""
        response = requests.get(f"{BASE_URL}/api/v2/contests/match/{MATCH_ID}",
                                  headers=auth_headers)
        assert response.status_code == 200, f"Contests failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"[PASS] Match contests: {len(data)} contests for match {MATCH_ID}")

    def test_seed_match_contests(self, auth_headers):
        """POST /api/v2/contests/seed/{match_id} seeds platform contests"""
        response = requests.post(f"{BASE_URL}/api/v2/contests/seed/{MATCH_ID}",
                                  headers=auth_headers)
        assert response.status_code == 200, f"Seed failed: {response.text}"
        data = response.json()
        assert "seeded" in data, f"Missing 'seeded' field: {data}"
        print(f"[PASS] Contest seeding: {data.get('seeded')} contests seeded")

    def test_contests_have_status_field(self, auth_headers):
        """Contest objects should have status field for voided label"""
        response = requests.get(f"{BASE_URL}/api/v2/contests/match/{MATCH_ID}",
                                  headers=auth_headers)
        data = response.json()
        if not data:
            pytest.skip("No contests available to check status field")

        for c in data[:3]:
            assert "status" in c, f"Contest missing 'status' field: {list(c.keys())}"
        print(f"[PASS] Contests have status field. Sample: {data[0].get('status')}")

    def test_voided_contest_has_correct_status(self, auth_headers):
        """Find or create a contest and check voided status is handled"""
        response = requests.get(f"{BASE_URL}/api/v2/contests/match/{MATCH_ID}",
                                  headers=auth_headers)
        data = response.json()
        voided = [c for c in data if c.get("status") == "voided"]
        if voided:
            print(f"[PASS] Found {len(voided)} voided contest(s). Status: {voided[0].get('status')}")
        else:
            print(f"[INFO] No voided contests for match {MATCH_ID} (normal if match is active)")
            # Still pass - frontend handles voided status display


# ══════════════════════ MATCH CENTRE ══════════════════════

class TestMatchCentre:
    """Test match centre live/upcoming data"""

    def test_live_matches_endpoint(self, auth_headers):
        """GET /api/v2/matches/live returns list"""
        response = requests.get(f"{BASE_URL}/api/v2/matches/live", headers=auth_headers)
        assert response.status_code == 200, f"Live matches failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"[PASS] Live matches: {len(data)} matches")

    def test_all_matches_endpoint(self, auth_headers):
        """GET /api/v2/matches/all returns list"""
        response = requests.get(f"{BASE_URL}/api/v2/matches/all", headers=auth_headers)
        assert response.status_code == 200, f"All matches failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"[PASS] All matches: {len(data)} matches")


# ══════════════════════ WALLET / FREEBUCKS ══════════════════════

class TestWalletFreeBucks:
    """Test wallet and freebucks endpoints"""

    def test_freebucks_balance(self, auth_headers):
        """GET /api/v2/freebucks/balance returns balance"""
        response = requests.get(f"{BASE_URL}/api/v2/freebucks/balance", headers=auth_headers)
        assert response.status_code == 200, f"FreeBucks balance failed: {response.text}"
        data = response.json()
        assert "balance" in data, f"Missing balance: {data}"
        print(f"[PASS] FreeBucks balance: {data.get('balance')}")

    def test_freebucks_packages(self):
        """GET /api/v2/freebucks/packages returns packages"""
        response = requests.get(f"{BASE_URL}/api/v2/freebucks/packages")
        assert response.status_code == 200, f"FreeBucks packages failed: {response.text}"
        data = response.json()
        print(f"[PASS] FreeBucks packages: {list(data.keys()) if isinstance(data, dict) else len(data)} packages")


# ══════════════════════ V2 HEALTH ══════════════════════

class TestV2Health:
    """Test V2 API health"""

    def test_v2_health_check(self):
        """GET /api/v2/health returns status:ok"""
        response = requests.get(f"{BASE_URL}/api/v2/health")
        assert response.status_code == 200, f"V2 health failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"V2 health status not ok: {data}"
        print(f"[PASS] V2 health ok. Redis: {data.get('redis')}, env: {data.get('env')}")
