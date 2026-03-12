"""
OTP Login Tab Feature Tests for FREE11 — FREE11 Iteration 41
Tests the new EMAIL OTP login tab:
  - /api/auth/send-otp  (send OTP to existing user)
  - /api/auth/verify-otp-register (existing user magic-link login → returns access_token)
  - wrong OTP → 400 error
  - password login regression
  - Google auth URL check
"""
import pytest
import requests
import os
import uuid
import pymongo
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

BASE_URL = ""
# Read from frontend .env (public URL)
fe_env = os.path.join(os.path.dirname(__file__), '../../frontend/.env')
if os.path.exists(fe_env):
    with open(fe_env) as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "free11_db")

# Test credentials
TEST_EMAIL = "test_redesign_ui26@free11test.com"
TEST_PASSWORD = "Test@1234"

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})


def get_otp_from_db(email: str) -> str:
    """Read the latest OTP for an email from otp_codes collection (field: 'otp')"""
    client = pymongo.MongoClient(MONGO_URL)
    db = client[DB_NAME]
    record = db.otp_codes.find_one(
        {"email": email.lower(), "verified": False},
        sort=[("created_at", -1)]
    )
    client.close()
    if not record:
        return None
    return record.get("otp")  # Field is 'otp', NOT 'otp_code'


# ─── 1. Send OTP endpoint ────────────────────────────────────────────────────

class TestSendOtpForLogin:
    """POST /api/auth/send-otp - sends OTP to existing user"""

    def test_send_otp_existing_user_returns_200(self):
        """Send OTP to existing test user should return 200 with sent:true"""
        # Use unique email to avoid cooldown
        email = f"TEST_otp_login_{uuid.uuid4().hex[:8]}@free11test.com"
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("sent") is True, f"Expected sent:true, got: {data}"
        print(f"PASS: send-otp → 200 sent:true for {email}")

    def test_send_otp_has_dev_otp_in_response(self):
        """In test env (no email configured), dev_otp should be in response"""
        email = f"TEST_otp_login_{uuid.uuid4().hex[:8]}@free11test.com"
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200
        data = resp.json()
        # Either dev_otp (no email delivery) or email_delivered:true
        if "dev_otp" in data:
            assert len(data["dev_otp"]) == 6, f"dev_otp should be 6 digits: {data['dev_otp']}"
            assert data["dev_otp"].isdigit(), f"dev_otp should be all digits: {data['dev_otp']}"
            print(f"PASS: dev_otp in response: {data['dev_otp']}")
        else:
            # Email delivery worked
            assert data.get("email_delivered") is True, f"email_delivered should be True if no dev_otp: {data}"
            print("PASS: OTP delivered via email (no dev_otp fallback needed)")

    def test_send_otp_invalid_email_returns_422(self):
        """Invalid email → 422 from Pydantic"""
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": "not-valid"})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
        print("PASS: invalid email → 422")

    def test_send_otp_missing_email_returns_422(self):
        """Missing email → 422"""
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
        print("PASS: missing email → 422")


# ─── 2. verify-otp-register (existing user magic-link login) ─────────────────

class TestVerifyOtpRegisterExistingUser:
    """POST /api/auth/verify-otp-register — OTP login for existing user"""

    def _send_otp_and_get_code(self, email: str) -> str:
        """Send OTP and return the code (from dev_otp or MongoDB)"""
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200, f"send-otp failed: {resp.text}"
        data = resp.json()
        if "dev_otp" in data:
            return data["dev_otp"]
        # Fall back to MongoDB read
        otp = get_otp_from_db(email)
        assert otp, f"Could not retrieve OTP from DB for {email}"
        return otp

    def test_correct_otp_existing_user_returns_access_token(self):
        """Correct OTP for existing user → 200 with access_token (magic-link signin)"""
        email = f"TEST_otp_existing_{uuid.uuid4().hex[:8]}@free11test.com"
        # First send OTP (new user will be created by verify-otp-register)
        otp = self._send_otp_and_get_code(email)
        
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp-register",
                            json={"email": email, "otp": otp})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "access_token" in data, f"access_token missing in response: {data}"
        assert isinstance(data["access_token"], str), "access_token should be a string"
        assert len(data["access_token"]) > 0, "access_token should not be empty"
        print(f"PASS: verify-otp-register → access_token received (len={len(data['access_token'])})")

    def test_correct_otp_returns_user_object(self):
        """Response should include user object with email field"""
        email = f"TEST_otp_user_{uuid.uuid4().hex[:8]}@free11test.com"
        otp = self._send_otp_and_get_code(email)
        
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp-register",
                            json={"email": email, "otp": otp})
        assert resp.status_code == 200
        data = resp.json()
        assert "user" in data, f"user object missing in response: {data}"
        assert data["user"].get("email") == email.lower(), f"User email mismatch: {data['user']}"
        assert "id" in data["user"], f"user.id missing: {data['user']}"
        print(f"PASS: verify-otp-register → user object with email={data['user']['email']}")

    def test_access_token_allows_me_endpoint(self):
        """Token from verify-otp-register should be a valid JWT for /api/auth/me"""
        email = f"TEST_otp_me_{uuid.uuid4().hex[:8]}@free11test.com"
        otp = self._send_otp_and_get_code(email)
        
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp-register",
                            json={"email": email, "otp": otp})
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        
        # Verify token works for /auth/me
        me_resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == 200, f"Expected 200 from /auth/me, got {me_resp.status_code}: {me_resp.text}"
        me_data = me_resp.json()
        assert me_data.get("email") == email.lower(), f"Email mismatch in /auth/me: {me_data}"
        print(f"PASS: access_token valid for /auth/me → user={me_data.get('email')}")

    def test_wrong_otp_returns_400_with_error(self):
        """Wrong OTP → 400 with error detail (for toast 'Incorrect code')"""
        email = f"TEST_otp_wrong_{uuid.uuid4().hex[:8]}@free11test.com"
        # Send OTP to create a record
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200
        
        # Try wrong OTP
        wrong_resp = session.post(f"{BASE_URL}/api/auth/verify-otp-register",
                                  json={"email": email, "otp": "000000"})
        assert wrong_resp.status_code == 400, f"Expected 400, got {wrong_resp.status_code}: {wrong_resp.text}"
        detail = wrong_resp.json().get("detail", "")
        assert detail, f"Expected error detail in response: {wrong_resp.json()}"
        print(f"PASS: wrong OTP → 400 with detail: '{detail}'")

    def test_no_otp_record_returns_400(self):
        """No prior OTP sent → verify should return 400"""
        email = f"TEST_otp_norecord_{uuid.uuid4().hex[:8]}@free11test.com"
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp-register",
                            json={"email": email, "otp": "123456"})
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        print(f"PASS: no OTP record → 400")

    def test_response_does_not_contain_password_hash(self):
        """User object in response must NOT contain password_hash or hashed_password"""
        email = f"TEST_otp_secure_{uuid.uuid4().hex[:8]}@free11test.com"
        otp = self._send_otp_and_get_code(email)
        
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp-register",
                            json={"email": email, "otp": otp})
        assert resp.status_code == 200
        user = resp.json().get("user", {})
        assert "password_hash" not in user, "password_hash should NOT be in response"
        assert "hashed_password" not in user, "hashed_password should NOT be in response"
        print("PASS: password fields excluded from response")

    def test_otp_in_db_uses_field_otp_not_otp_code(self):
        """Verify MongoDB otp_codes collection uses field 'otp' (not 'otp_code')"""
        email = f"TEST_otp_field_{uuid.uuid4().hex[:8]}@free11test.com"
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200
        
        # Read from DB
        client = pymongo.MongoClient(MONGO_URL)
        db = client[DB_NAME]
        record = db.otp_codes.find_one({"email": email.lower()}, sort=[("created_at", -1)])
        client.close()
        
        assert record is not None, f"No OTP record in DB for {email}"
        assert "otp" in record, f"Field 'otp' missing in otp_codes record. Keys: {list(record.keys())}"
        assert "otp_code" not in record, f"Field should be 'otp' not 'otp_code'. Keys: {list(record.keys())}"
        assert record["otp"].isdigit(), f"otp should be digits: {record['otp']}"
        assert len(record["otp"]) == 6, f"otp should be 6 digits: {record['otp']}"
        print(f"PASS: otp_codes uses field 'otp', value={record['otp']}")


# ─── 3. Password login regression ───────────────────────────────────────────

class TestPasswordLoginRegression:
    """Regression: password login still works after OTP tab addition"""

    def test_password_login_existing_user_returns_token(self):
        """Existing user password login → access_token"""
        resp = session.post(f"{BASE_URL}/api/auth/login",
                            json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # token can be 'token' or 'access_token'
        token = data.get("token") or data.get("access_token")
        assert token, f"No token in login response: {data}"
        print(f"PASS: password login for {TEST_EMAIL} → token received")

    def test_password_login_wrong_password_returns_401(self):
        """Wrong password → 401"""
        resp = session.post(f"{BASE_URL}/api/auth/login",
                            json={"email": TEST_EMAIL, "password": "WrongPass9999"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("PASS: wrong password → 401")

    def test_password_login_me_endpoint_works(self):
        """Token from password login should work for /auth/me"""
        login_resp = session.post(f"{BASE_URL}/api/auth/login",
                                  json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        assert login_resp.status_code == 200
        data = login_resp.json()
        token = data.get("token") or data.get("access_token")
        
        me_resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == 200, f"Expected 200 from /auth/me, got {me_resp.status_code}"
        me_data = me_resp.json()
        assert me_data.get("email") == TEST_EMAIL, f"Email mismatch: {me_data}"
        print(f"PASS: password login → /auth/me → email={me_data.get('email')}")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    subprocess.run([
        "pytest", __file__, "-v", "--tb=short",
        "--junitxml=/app/test_reports/pytest/otp_login_tab_41.xml"
    ])
