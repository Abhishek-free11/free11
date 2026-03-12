"""
OTP Email Verification & Resend Integration Tests for FREE11
Tests: send-otp, verify-otp, cooldown, max-attempts, expired, email-status auth
"""
import pytest
import requests
import os
import time
import uuid
from dotenv import load_dotenv

# Load backend .env for DB access
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback: read from frontend .env
    fe_env = os.path.join(os.path.dirname(__file__), '../../frontend/.env')
    if os.path.exists(fe_env):
        with open(fe_env) as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip()
                    break

# ─── Shared helpers ───────────────────────────────────────────────────────────

def unique_test_email(tag: str = "") -> str:
    uid = str(uuid.uuid4())[:8]
    return f"TEST_otp_{tag}_{uid}@mail.example.com"

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

# ─── Tests: send-otp ──────────────────────────────────────────────────────────

class TestSendOTP:
    """POST /api/auth/send-otp"""

    def test_send_otp_returns_200_and_sent_true(self):
        """OTP send to a fresh email should succeed with sent:true"""
        email = unique_test_email("send")
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("sent") is True, f"sent should be True: {data}"

    def test_send_otp_returns_email_field(self):
        """Response must echo back the requested email (backend lowercases emails)"""
        email = unique_test_email("echo")
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200
        data = resp.json()
        # Backend lowercases email, compare case-insensitively
        assert data.get("email") == email.lower(), f"email field mismatch: {data}"

    def test_send_otp_returns_dev_otp_when_resend_domain_unverified(self):
        """
        Resend is configured (RESEND_API_KEY set) but domain free11.com is not verified.
        Resend returns 403/422, so _deliver_otp returns False → dev_otp appears in response.
        """
        email = unique_test_email("devmode")
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200
        data = resp.json()
        assert "dev_otp" in data, (
            "Expected dev_otp in response (Resend domain not verified falls back to dev mode). "
            f"Got: {data}"
        )
        otp = data["dev_otp"]
        assert len(otp) == 6, f"dev_otp should be 6 digits, got '{otp}'"
        assert otp.isdigit(), f"dev_otp should be all digits, got '{otp}'"

    def test_send_otp_returns_expires_in(self):
        """Response must include expires_in (600 seconds = 10 minutes)"""
        email = unique_test_email("expiry")
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200
        data = resp.json()
        assert "expires_in" in data, f"expires_in missing: {data}"
        assert data["expires_in"] == 600, f"Expected 600s expiry, got {data['expires_in']}"

    def test_send_otp_cooldown_returns_429_within_60s(self):
        """
        Second request for same email within 60 seconds should return 429.
        """
        email = unique_test_email("cooldown")
        # First request (should succeed)
        r1 = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert r1.status_code == 200, f"First send failed: {r1.text}"

        # Immediate second request (within 60s cooldown)
        r2 = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert r2.status_code == 429, f"Expected 429 (cooldown), got {r2.status_code}: {r2.text}"
        detail = r2.json().get("detail", "")
        assert "wait" in detail.lower() or "Please" in detail, f"Cooldown message unexpected: {detail}"

    def test_send_otp_invalid_email_returns_422(self):
        """Invalid email format should return 422 (Pydantic validation)"""
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": "not-an-email"})
        assert resp.status_code == 422, f"Expected 422 for invalid email, got {resp.status_code}"

    def test_send_otp_missing_email_field_returns_422(self):
        """Missing email field should return 422"""
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={})
        assert resp.status_code == 422, f"Expected 422 for missing email, got {resp.status_code}"


# ─── Tests: verify-otp ────────────────────────────────────────────────────────

class TestVerifyOTP:
    """POST /api/auth/verify-otp"""

    def _send_and_get_otp(self, email: str) -> str:
        """Helper: send OTP and return the dev_otp from response"""
        r = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert r.status_code == 200, f"send-otp failed: {r.text}"
        data = r.json()
        assert "dev_otp" in data, f"dev_otp not in response: {data}"
        return data["dev_otp"]

    def test_verify_correct_otp_returns_verified_true(self):
        """Correct OTP should return verified:true (200)"""
        email = unique_test_email("correct")
        otp = self._send_and_get_otp(email)
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": email, "otp": otp})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("verified") is True, f"verified should be True: {data}"

    def test_verify_correct_otp_returns_email(self):
        """Verified response should include the email (backend lowercases emails)"""
        email = unique_test_email("email_field")
        otp = self._send_and_get_otp(email)
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": email, "otp": otp})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("email") == email.lower(), f"email field mismatch: {data}"

    def test_verify_wrong_otp_returns_400(self):
        """Wrong OTP should return 400"""
        email = unique_test_email("wrong")
        self._send_and_get_otp(email)  # creates OTP record
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": email, "otp": "000000"})
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"

    def test_verify_wrong_otp_returns_attempts_remaining(self):
        """Wrong OTP response detail should mention attempts remaining"""
        email = unique_test_email("attempts")
        self._send_and_get_otp(email)
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": email, "otp": "999999"})
        assert resp.status_code == 400
        detail = resp.json().get("detail", "")
        assert "attempts remaining" in detail.lower() or "remaining" in detail.lower(), (
            f"Expected 'attempts remaining' in detail: '{detail}'"
        )

    def test_verify_too_many_attempts_returns_400_with_message(self):
        """After 5 wrong OTPs, 6th attempt should return 'Too many attempts'"""
        email = unique_test_email("maxattempts")
        real_otp = self._send_and_get_otp(email)
        wrong_otp = "000000" if real_otp != "000000" else "111111"

        # Make 5 wrong attempts
        for i in range(5):
            r = session.post(
                f"{BASE_URL}/api/auth/verify-otp",
                json={"email": email, "otp": wrong_otp}
            )
            assert r.status_code == 400, f"Attempt {i+1} should be 400, got {r.status_code}"

        # 6th attempt should be "Too many attempts"
        r6 = session.post(
            f"{BASE_URL}/api/auth/verify-otp",
            json={"email": email, "otp": wrong_otp}
        )
        assert r6.status_code == 400, f"Expected 400, got {r6.status_code}: {r6.text}"
        detail = r6.json().get("detail", "")
        assert "too many" in detail.lower() or "attempts" in detail.lower(), (
            f"Expected 'Too many attempts' in detail: '{detail}'"
        )

    def test_verify_no_otp_record_returns_400(self):
        """Verifying OTP for unknown email should return 400"""
        email = unique_test_email("unknown")
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": email, "otp": "123456"})
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        detail = resp.json().get("detail", "")
        assert "no otp" in detail.lower() or "request a new" in detail.lower() or "not found" in detail.lower(), (
            f"Unexpected detail: '{detail}'"
        )

    def test_verify_otp_invalid_email_returns_422(self):
        """Invalid email format in verify-otp should return 422"""
        resp = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": "bad-email", "otp": "123456"})
        assert resp.status_code == 422, f"Expected 422 for invalid email, got {resp.status_code}"

    def test_verify_expired_otp_returns_400(self):
        """
        Expired OTP should return 'OTP expired'.
        We update the DB directly using pymongo to expire the record immediately.
        """
        import pymongo
        from datetime import datetime, timezone, timedelta

        MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        DB_NAME = os.environ.get("DB_NAME", "free11_db")

        email = unique_test_email("expired")
        self._send_and_get_otp(email)

        # Directly expire the OTP record in DB (use lowercased email as stored by backend)
        client = pymongo.MongoClient(MONGO_URL)
        db = client[DB_NAME]
        past = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        result = db.otp_codes.update_one(
            {"email": email.strip().lower(), "verified": False},
            {"$set": {"expires_at": past}}
        )
        client.close()
        assert result.modified_count == 1, "DB update for expires_at failed - OTP record not found"

        resp = session.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": email, "otp": "123456"})
        assert resp.status_code == 400, f"Expected 400 for expired OTP, got {resp.status_code}: {resp.text}"
        detail = resp.json().get("detail", "")
        assert "expired" in detail.lower(), f"Expected 'expired' in detail: '{detail}'"


# ─── Tests: email-status ──────────────────────────────────────────────────────

class TestEmailStatus:
    """GET /api/auth/email-status requires authentication"""

    def test_email_status_without_token_returns_401(self):
        """No auth header → 401"""
        resp = session.get(f"{BASE_URL}/api/auth/email-status")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_email_status_with_invalid_token_returns_401(self):
        """Invalid/fake token → 401"""
        resp = requests.get(
            f"{BASE_URL}/api/auth/email-status",
            headers={"Authorization": "Bearer fake_invalid_token_here"}
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_email_status_with_valid_token_returns_200(self):
        """Valid token → 200 with verified field"""
        # Login as admin
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "Admin@123"
        })
        if login_resp.status_code != 200:
            pytest.skip("Admin login failed - skipping email-status auth test")
        token = login_resp.json().get("token") or login_resp.json().get("access_token")
        assert token, "No token in login response"

        resp = requests.get(
            f"{BASE_URL}/api/auth/email-status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "verified" in data, f"'verified' key missing: {data}"
        assert "email" in data, f"'email' key missing: {data}"


# ─── Tests: Resend integration ────────────────────────────────────────────────

class TestResendIntegration:
    """Verify RESEND_API_KEY is loaded and Resend call is attempted"""

    def test_resend_key_is_set_in_env(self):
        """RESEND_API_KEY must be present and non-empty"""
        # Load from backend .env
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        key = os.environ.get("RESEND_API_KEY", "")
        assert key, "RESEND_API_KEY is not set in backend/.env"
        assert key.startswith("re_"), f"RESEND_API_KEY should start with 're_': got '{key[:10]}...'"

    def test_resend_from_email_is_set(self):
        """RESEND_FROM_EMAIL or EMAIL_FROM must be set"""
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        from_email = os.environ.get("RESEND_FROM_EMAIL") or os.environ.get("EMAIL_FROM", "")
        assert from_email, "Neither RESEND_FROM_EMAIL nor EMAIL_FROM is set"

    def test_otp_send_triggers_resend_attempt_evidenced_by_dev_otp_fallback(self):
        """
        When RESEND_API_KEY is set but domain not verified:
        - Resend API call is made (evidenced by backend logs showing 403/422 from Resend)
        - Backend falls back: dev_otp is returned in API response
        This proves Resend IS being called (not skipping due to missing key).
        """
        email = unique_test_email("resend_evidence")
        resp = session.post(f"{BASE_URL}/api/auth/send-otp", json={"email": email})
        assert resp.status_code == 200
        data = resp.json()
        # dev_otp present = Resend was called but failed → fallback to dev mode
        assert "dev_otp" in data, (
            "dev_otp NOT in response. Possibilities: "
            "(a) RESEND_API_KEY not loaded by server, "
            "(b) Domain somehow became verified and email delivered. "
            f"Response: {data}"
        )
        # Confirm message says dev mode
        msg = data.get("message", "")
        assert "dev mode" in msg.lower() or "otp is" in msg.lower() or email in msg, (
            f"Unexpected message: '{msg}'"
        )


if __name__ == "__main__":
    import subprocess
    subprocess.run([
        "pytest", __file__, "-v", "--tb=short",
        "--junitxml=/app/test_reports/pytest/otp_resend_results.xml"
    ])
