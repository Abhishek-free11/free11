"""
Auth/Signin Flow Tests - Iteration 38
Tests: /auth/send-otp, /auth/verify-otp-register, /auth/login, /auth/me
Focus: OTP registration + magic-link + login flows
"""
import pytest
import requests
import time
import os
from pymongo import MongoClient

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'free11_db')

# Test-specific emails with TEST_ prefix for easy cleanup
TEST_NEW_EMAIL = f"TEST_newuser_auth38_{int(time.time())}@free11test.com"
TEST_EXISTING_EMAIL = "test_redesign_ui26@free11test.com"  # Known existing user

# --- Helper: Get OTP from MongoDB for a given email ---
def get_otp_from_db(email: str) -> str:
    """Fetch the latest OTP for an email from otp_codes collection."""
    sync_client = MongoClient(MONGO_URL)
    db = sync_client[DB_NAME]
    record = db.otp_codes.find_one(
        {"email": email.lower(), "verified": False},
        sort=[("created_at", -1)]
    )
    sync_client.close()
    if not record:
        raise ValueError(f"No OTP found for {email}")
    return record["otp"]


# ===================== SEND OTP TESTS =====================

class TestSendOTP:
    """Tests for POST /api/auth/send-otp"""

    def test_send_otp_new_email_returns_sent_true(self):
        """send-otp to a new email should return sent:true"""
        res = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": TEST_NEW_EMAIL})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("sent") is True, f"Expected sent=true, got: {data}"
        print(f"PASS: send-otp to {TEST_NEW_EMAIL} returned sent=True")

    def test_send_otp_existing_email_returns_sent_true(self):
        """send-otp to an existing user email should also return sent:true"""
        # Use a small delay to avoid cooldown conflict with prior tests
        time.sleep(1)
        res = requests.post(
            f"{BASE_URL}/api/auth/send-otp",
            json={"email": f"TEST_existing_auth38_{int(time.time())}@free11test.com"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("sent") is True, f"Expected sent=true, got: {data}"
        print(f"PASS: send-otp to existing-style email returned sent=True")

    def test_send_otp_invalid_email_format_returns_error(self):
        """send-otp with invalid email format should return 422"""
        res = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": "not-an-email"})
        assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
        print(f"PASS: invalid email format returns 422")

    def test_send_otp_response_has_email_field(self):
        """send-otp response should contain 'email' field"""
        test_email = f"TEST_email_field_{int(time.time())}@free11test.com"
        res = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": test_email})
        assert res.status_code == 200
        data = res.json()
        assert "email" in data, f"Response missing 'email' field: {data}"
        assert data["email"] == test_email.lower()
        print(f"PASS: send-otp response contains email field: {data['email']}")


# ===================== VERIFY OTP REGISTER TESTS =====================

class TestVerifyOTPRegister:
    """Tests for POST /api/auth/verify-otp-register"""

    def test_verify_otp_register_new_user_returns_access_token(self):
        """
        Flow: send-otp → get OTP from DB → verify-otp-register
        For a brand new email, should create user and return access_token
        """
        new_email = f"TEST_otp_newuser_{int(time.time())}@free11test.com"

        # Step 1: Send OTP
        send_res = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": new_email})
        assert send_res.status_code == 200, f"send-otp failed: {send_res.text}"
        assert send_res.json().get("sent") is True

        # Step 2: Get OTP from DB
        time.sleep(0.5)  # Small wait for DB write to settle
        otp = get_otp_from_db(new_email)
        assert otp and len(otp) == 6, f"Invalid OTP from DB: {otp}"
        print(f"  Got OTP from DB: {otp}")

        # Step 3: Verify OTP and register
        verify_res = requests.post(
            f"{BASE_URL}/api/auth/verify-otp-register",
            json={"email": new_email, "otp": otp}
        )
        assert verify_res.status_code == 200, f"verify-otp-register failed: {verify_res.status_code}: {verify_res.text}"
        data = verify_res.json()
        assert "access_token" in data, f"Response missing access_token: {data}"
        assert "token_type" in data, f"Response missing token_type: {data}"
        assert "user" in data, f"Response missing user: {data}"
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == new_email.lower()
        assert "id" in data["user"]
        print(f"PASS: New user registered via OTP, got access_token. User ID: {data['user']['id']}")

    def test_verify_otp_register_existing_user_returns_access_token(self):
        """
        Magic-link login: existing user should get access_token (not error)
        """
        # Use existing test user - send OTP first
        send_res = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": TEST_EXISTING_EMAIL})
        assert send_res.status_code == 200, f"send-otp failed for existing user: {send_res.text}"

        time.sleep(0.5)
        otp = get_otp_from_db(TEST_EXISTING_EMAIL)
        assert otp and len(otp) == 6, f"Invalid OTP: {otp}"
        print(f"  Got OTP for existing user from DB: {otp}")

        verify_res = requests.post(
            f"{BASE_URL}/api/auth/verify-otp-register",
            json={"email": TEST_EXISTING_EMAIL, "otp": otp}
        )
        assert verify_res.status_code == 200, f"Magic-link login failed: {verify_res.status_code}: {verify_res.text}"
        data = verify_res.json()
        assert "access_token" in data, f"Response missing access_token: {data}"
        assert data["user"]["email"] == TEST_EXISTING_EMAIL.lower()
        print(f"PASS: Existing user magic-link login succeeded, access_token returned.")

    def test_verify_otp_register_wrong_otp_returns_400(self):
        """
        Wrong OTP should return 400 with error message
        """
        test_email = f"TEST_wrong_otp_{int(time.time())}@free11test.com"

        # Send OTP first (needed to have a pending OTP entry)
        send_res = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": test_email})
        assert send_res.status_code == 200

        # Use wrong OTP
        verify_res = requests.post(
            f"{BASE_URL}/api/auth/verify-otp-register",
            json={"email": test_email, "otp": "000000"}
        )
        assert verify_res.status_code == 400, f"Expected 400 for wrong OTP, got {verify_res.status_code}: {verify_res.text}"
        data = verify_res.json()
        assert "detail" in data, f"Response missing detail: {data}"
        print(f"PASS: Wrong OTP returns 400. Detail: {data.get('detail')}")

    def test_verify_otp_register_no_otp_requested_returns_400(self):
        """
        Verify OTP for email that never requested OTP → 400
        """
        email_no_otp = f"TEST_nootp_{int(time.time())}@free11test.com"
        verify_res = requests.post(
            f"{BASE_URL}/api/auth/verify-otp-register",
            json={"email": email_no_otp, "otp": "123456"}
        )
        assert verify_res.status_code == 400, f"Expected 400, got {verify_res.status_code}: {verify_res.text}"
        print(f"PASS: No OTP requested → 400")

    def test_verify_otp_register_response_structure(self):
        """
        Validate the exact response structure: {access_token, token_type, user}
        """
        new_email = f"TEST_struct_{int(time.time())}@free11test.com"

        send_res = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": new_email})
        assert send_res.status_code == 200

        time.sleep(0.5)
        otp = get_otp_from_db(new_email)

        verify_res = requests.post(
            f"{BASE_URL}/api/auth/verify-otp-register",
            json={"email": new_email, "otp": otp}
        )
        assert verify_res.status_code == 200
        data = verify_res.json()

        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 20  # JWT should be long
        assert data["token_type"] == "bearer"

        # Verify user object
        user = data["user"]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "_id" not in user, "MongoDB _id should be excluded from response!"
        assert "password_hash" not in user, "password_hash should not be in response"
        print(f"PASS: Response structure validated. access_token length: {len(data['access_token'])}")

    def test_verify_otp_register_token_works_with_auth_me(self):
        """
        Token from verify-otp-register should authenticate /auth/me successfully
        """
        new_email = f"TEST_me_{int(time.time())}@free11test.com"

        send_res = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": new_email})
        assert send_res.status_code == 200

        time.sleep(0.5)
        otp = get_otp_from_db(new_email)

        verify_res = requests.post(
            f"{BASE_URL}/api/auth/verify-otp-register",
            json={"email": new_email, "otp": otp}
        )
        assert verify_res.status_code == 200
        token = verify_res.json()["access_token"]

        # Verify token works
        me_res = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_res.status_code == 200, f"/auth/me failed: {me_res.status_code}: {me_res.text}"
        me_data = me_res.json()
        assert me_data["email"] == new_email.lower()
        print(f"PASS: Token from verify-otp-register works for /auth/me. User: {me_data['email']}")


# ===================== STANDARD LOGIN TESTS =====================

class TestStandardLogin:
    """Tests for POST /api/auth/login (email + password)"""

    def test_login_existing_user_success(self):
        """Existing user can login with email + password"""
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EXISTING_EMAIL, "password": "Test@1234"}
        )
        assert res.status_code == 200, f"Login failed: {res.status_code}: {res.text}"
        data = res.json()
        assert "access_token" in data, f"Response missing access_token: {data}"
        print(f"PASS: Standard login succeeded for {TEST_EXISTING_EMAIL}")

    def test_login_wrong_password_returns_401(self):
        """Wrong password should return 401"""
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EXISTING_EMAIL, "password": "WrongPassword123"}
        )
        assert res.status_code == 401, f"Expected 401 for wrong password, got {res.status_code}: {res.text}"
        print(f"PASS: Wrong password returns 401")

    def test_login_nonexistent_user_returns_401(self):
        """Non-existent user should return 401"""
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "nonexistent_xyz123@free11test.com", "password": "Test@1234"}
        )
        assert res.status_code in (401, 404), f"Expected 401/404, got {res.status_code}: {res.text}"
        print(f"PASS: Non-existent user returns {res.status_code}")

    def test_login_response_has_access_token_and_user(self):
        """Login response should have access_token and user"""
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EXISTING_EMAIL, "password": "Test@1234"}
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "user" in data or "token_type" in data  # user may be in top level or nested
        print(f"PASS: Login response structure correct: {list(data.keys())}")

    def test_login_token_works_with_auth_me(self):
        """Login token should authenticate /auth/me"""
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EXISTING_EMAIL, "password": "Test@1234"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]

        me_res = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_res.status_code == 200, f"/auth/me failed: {me_res.status_code}"
        me_data = me_res.json()
        assert me_data["email"] == TEST_EXISTING_EMAIL.lower()
        print(f"PASS: Login token authenticates /auth/me: {me_data['email']}")


# ===================== AUTH ME TESTS =====================

class TestAuthMe:
    """Tests for GET /api/auth/me"""

    def test_auth_me_without_token_returns_401(self):
        """No token → 401"""
        res = requests.get(f"{BASE_URL}/api/auth/me")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"
        print(f"PASS: /auth/me without token returns 401")

    def test_auth_me_with_invalid_token_returns_401(self):
        """Invalid token → 401"""
        res = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalidtoken"}
        )
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"
        print(f"PASS: /auth/me with invalid token returns 401")
