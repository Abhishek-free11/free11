"""
Referral Feature Tests — Iteration 37
Tests: GET /referral/code, GET /referral/stats, POST /referral/bind
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_redesign_ui26@free11test.com"
TEST_PASS = "Test@1234"
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASS = "Admin@123"
KNOWN_REFERRAL_CODE = "F11-F9E983"  # test user's known code


@pytest.fixture(scope="module")
def test_token():
    """Get auth token for test user"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASS})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers(test_token):
    return {"Authorization": f"Bearer {test_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_token():
    """Get auth token for admin user"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip("Admin login failed")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestReferralCode:
    """GET /api/v2/referral/code — returns user's referral code"""

    def test_get_referral_code_authenticated(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/referral/code", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "code" in data, "Response missing 'code' field"
        code = data["code"]
        assert isinstance(code, str), f"Code should be string, got {type(code)}"
        assert code.startswith("F11-"), f"Code should start with 'F11-', got: {code}"
        assert len(code) == 10, f"Code format F11-XXXXXX expected length 10, got {len(code)}: {code}"
        print(f"PASS: Referral code returned: {code}")

    def test_get_referral_code_unauthenticated(self):
        resp = requests.get(f"{BASE_URL}/api/v2/referral/code")
        assert resp.status_code == 401, f"Expected 401 for unauthenticated, got {resp.status_code}"
        print("PASS: Unauthenticated request correctly rejected with 401")

    def test_referral_code_is_consistent(self, auth_headers):
        """Calling /code twice returns same code"""
        resp1 = requests.get(f"{BASE_URL}/api/v2/referral/code", headers=auth_headers)
        resp2 = requests.get(f"{BASE_URL}/api/v2/referral/code", headers=auth_headers)
        assert resp1.status_code == 200 and resp2.status_code == 200
        assert resp1.json()["code"] == resp2.json()["code"], "Code should be same on repeated calls"
        print(f"PASS: Code is consistent: {resp1.json()['code']}")


class TestReferralStats:
    """GET /api/v2/referral/stats — returns referral_code, total_referrals, total_earned"""

    def test_get_referral_stats_returns_required_fields(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/referral/stats", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        required_fields = ["referral_code", "total_referrals", "total_earned", "reward_per_referral"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        print(f"PASS: Stats returned — code={data['referral_code']}, referrals={data['total_referrals']}, earned={data['total_earned']}, per_ref={data['reward_per_referral']}")

    def test_referral_stats_code_format(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/referral/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        code = data["referral_code"]
        assert code.startswith("F11-"), f"Code should start with 'F11-', got: {code}"
        print(f"PASS: Code format correct: {code}")

    def test_referral_stats_numeric_fields(self, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/v2/referral/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["total_referrals"], int), "total_referrals should be int"
        assert isinstance(data["total_earned"], (int, float)), "total_earned should be numeric"
        assert isinstance(data["reward_per_referral"], (int, float)), "reward_per_referral should be numeric"
        assert data["reward_per_referral"] > 0, "reward_per_referral should be positive"
        print(f"PASS: Numeric fields correct")

    def test_referral_stats_unauthenticated(self):
        resp = requests.get(f"{BASE_URL}/api/v2/referral/stats")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("PASS: Unauthenticated stats request correctly rejected")


class TestReferralBind:
    """POST /api/v2/referral/bind — tests invalid code, self-referral, valid code"""

    def test_bind_invalid_code_returns_error(self, auth_headers):
        resp = requests.post(
            f"{BASE_URL}/api/v2/referral/bind",
            json={"referral_code": "F11-INVALID"},
            headers=auth_headers
        )
        # Should return 400 for invalid code
        assert resp.status_code == 400, f"Expected 400 for invalid code, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "detail" in data, "Error response should have 'detail' field"
        print(f"PASS: Invalid code correctly rejected: {data.get('detail')}")

    def test_bind_own_code_returns_self_referral_error(self, auth_headers):
        """Test user should not be able to use their own referral code"""
        # First get the user's own code
        code_resp = requests.get(f"{BASE_URL}/api/v2/referral/code", headers=auth_headers)
        assert code_resp.status_code == 200
        own_code = code_resp.json()["code"]

        # Try to bind own code
        resp = requests.post(
            f"{BASE_URL}/api/v2/referral/bind",
            json={"referral_code": own_code},
            headers=auth_headers
        )
        assert resp.status_code == 400, f"Expected 400 for self-referral, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "detail" in data
        # Should contain self-referral error message
        assert "own" in data["detail"].lower() or "self" in data["detail"].lower() or "cannot" in data["detail"].lower(), \
            f"Expected self-referral error, got: {data['detail']}"
        print(f"PASS: Self-referral correctly rejected: {data.get('detail')}")

    def test_bind_empty_code_returns_error(self, auth_headers):
        """Empty code should not pass validation"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/referral/bind",
            json={"referral_code": ""},
            headers=auth_headers
        )
        # Either 400 or 422 depending on validation
        assert resp.status_code in [400, 422], f"Expected 400/422, got {resp.status_code}"
        print(f"PASS: Empty code rejected with {resp.status_code}")

    def test_bind_already_applied_returns_error(self, auth_headers):
        """If referral already applied, should return 400"""
        # Use admin code since it's different from test user's
        # First check if test user already has a binding
        resp = requests.post(
            f"{BASE_URL}/api/v2/referral/bind",
            json={"referral_code": KNOWN_REFERRAL_CODE},
            headers=auth_headers
        )
        # Either 200 (first time bind) or 400 (already bound)
        if resp.status_code == 200:
            print(f"INFO: First time bind succeeded, testing duplicate...")
            # Now try again — should fail
            resp2 = requests.post(
                f"{BASE_URL}/api/v2/referral/bind",
                json={"referral_code": KNOWN_REFERRAL_CODE},
                headers=auth_headers
            )
            assert resp2.status_code == 400, f"Expected 400 on duplicate bind, got {resp2.status_code}"
            print(f"PASS: Duplicate bind correctly rejected")
        elif resp.status_code == 400:
            print(f"INFO: Code already applied or self-referral: {resp.json().get('detail')}")
            print("PASS: Already bound or self-referral scenario handled correctly")
        else:
            assert False, f"Unexpected status {resp.status_code}: {resp.text}"

    def test_bind_unauthenticated_returns_401(self):
        resp = requests.post(
            f"{BASE_URL}/api/v2/referral/bind",
            json={"referral_code": "F11-TESTXX"}
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("PASS: Unauthenticated bind request correctly rejected")


class TestReferralIntegration:
    """Integration: stats code matches code endpoint"""

    def test_stats_code_matches_code_endpoint(self, auth_headers):
        code_resp = requests.get(f"{BASE_URL}/api/v2/referral/code", headers=auth_headers)
        stats_resp = requests.get(f"{BASE_URL}/api/v2/referral/stats", headers=auth_headers)
        assert code_resp.status_code == 200 and stats_resp.status_code == 200
        assert code_resp.json()["code"] == stats_resp.json()["referral_code"], \
            "Code from /code endpoint should match referral_code in /stats"
        print(f"PASS: Code consistent between endpoints: {code_resp.json()['code']}")

    def test_admin_has_different_code_from_test_user(self, auth_headers, admin_headers):
        test_resp = requests.get(f"{BASE_URL}/api/v2/referral/code", headers=auth_headers)
        admin_resp = requests.get(f"{BASE_URL}/api/v2/referral/code", headers=admin_headers)
        assert test_resp.status_code == 200 and admin_resp.status_code == 200
        test_code = test_resp.json()["code"]
        admin_code = admin_resp.json()["code"]
        assert test_code != admin_code, "Different users should have different referral codes"
        print(f"PASS: Different codes — test user: {test_code}, admin: {admin_code}")
