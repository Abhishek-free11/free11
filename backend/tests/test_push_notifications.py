"""
FREE11 Push Notification API Tests (Iteration 30)
Testing: POST /api/v2/push/register, POST /api/v2/push/send
Covers: auth, upsert, 401 guards, response structure
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASS = "Admin@123"

# ─── Helpers ────────────────────────────────────────────────────────────────

def get_admin_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS,
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json().get("access_token"), resp.json().get("user", {}).get("id")


# ─── Tests ──────────────────────────────────────────────────────────────────

class TestPushRegister:
    """POST /api/v2/push/register — device token upsert"""

    def test_register_returns_registered_true(self):
        """Valid token + device_type returns {registered: true}"""
        token, _ = get_admin_token()
        fake_device_token = f"fcm_test_token_{uuid.uuid4().hex[:16]}"
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/register",
            json={"device_token": fake_device_token, "device_type": "android"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("registered") is True, f"Expected registered=true, got {data}"

    def test_register_response_has_device_type(self):
        """Response echoes the device_type back"""
        token, _ = get_admin_token()
        fake_device_token = f"fcm_test_token_{uuid.uuid4().hex[:16]}"
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/register",
            json={"device_token": fake_device_token, "device_type": "web"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("device_type") == "web", f"Expected device_type=web, got {data}"

    def test_register_upsert_same_device_type(self):
        """Second call with same device_type updates same record (upsert)"""
        token, _ = get_admin_token()
        first_token = f"fcm_first_{uuid.uuid4().hex[:16]}"
        second_token = f"fcm_second_{uuid.uuid4().hex[:16]}"

        # First registration
        resp1 = requests.post(
            f"{BASE_URL}/api/v2/push/register",
            json={"device_token": first_token, "device_type": "android"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 200, f"First register failed: {resp1.text}"
        assert resp1.json().get("registered") is True

        # Second registration with different token but same device_type
        resp2 = requests.post(
            f"{BASE_URL}/api/v2/push/register",
            json={"device_token": second_token, "device_type": "android"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 200, f"Second register (upsert) failed: {resp2.text}"
        assert resp2.json().get("registered") is True, f"Upsert expected registered=true, got {resp2.json()}"

    def test_register_requires_auth_401(self):
        """Without auth token → 401"""
        fake_device_token = f"fcm_test_token_{uuid.uuid4().hex[:16]}"
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/register",
            json={"device_token": fake_device_token, "device_type": "android"},
        )
        assert resp.status_code == 401, f"Expected 401 without auth, got {resp.status_code}: {resp.text}"

    def test_register_invalid_auth_token_401(self):
        """With invalid bearer token → 401"""
        fake_device_token = f"fcm_test_token_{uuid.uuid4().hex[:16]}"
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/register",
            json={"device_token": fake_device_token, "device_type": "android"},
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401, f"Expected 401 with invalid token, got {resp.status_code}: {resp.text}"

    def test_register_missing_device_token_422(self):
        """Missing device_token field → 422 Unprocessable Entity"""
        token, _ = get_admin_token()
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/register",
            json={"device_type": "android"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422, f"Expected 422 for missing device_token, got {resp.status_code}: {resp.text}"

    def test_register_default_device_type_android(self):
        """device_type defaults to 'android' if not provided"""
        token, _ = get_admin_token()
        fake_device_token = f"fcm_default_{uuid.uuid4().hex[:16]}"
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/register",
            json={"device_token": fake_device_token},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("registered") is True
        assert data.get("device_type") == "android", f"Expected default device_type=android, got {data}"


class TestPushSend:
    """POST /api/v2/push/send — send push notification"""

    def test_send_returns_sent_bool_and_target_user_id(self):
        """Returns {sent: bool, target_user_id: string}"""
        token, admin_id = get_admin_token()
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/send",
            json={"title": "Test Notification", "body": "Hello from test!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "sent" in data, f"Expected 'sent' field in response: {data}"
        assert "target_user_id" in data, f"Expected 'target_user_id' field in response: {data}"
        assert isinstance(data["sent"], bool), f"'sent' must be bool, got {type(data['sent'])}"
        assert isinstance(data["target_user_id"], str), f"'target_user_id' must be str"

    def test_send_sent_is_false_without_service_account(self):
        """sent=false when Firebase service account not configured (expected in dev/test)"""
        token, _ = get_admin_token()
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/send",
            json={"title": "Test", "body": "Dev mode push"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # In dev mode (no service account), sent should be False
        assert data.get("sent") is False, f"Expected sent=false in dev mode, got {data}"

    def test_send_requires_auth_401(self):
        """Without auth token → 401"""
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/send",
            json={"title": "Test", "body": "No auth push"},
        )
        assert resp.status_code == 401, f"Expected 401 without auth, got {resp.status_code}: {resp.text}"

    def test_send_with_user_id_param_targets_specific_user(self):
        """user_id param overrides target_user_id in response"""
        token, admin_id = get_admin_token()
        target_user_id = admin_id  # send to self (admin) for testing
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/send",
            json={"title": "Targeted Push", "body": "To specific user", "user_id": target_user_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("target_user_id") == target_user_id, (
            f"Expected target_user_id={target_user_id}, got {data.get('target_user_id')}"
        )

    def test_send_without_user_id_uses_self(self):
        """When user_id not provided, target_user_id is the caller's id"""
        token, admin_id = get_admin_token()
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/send",
            json={"title": "Self Push", "body": "To self"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("target_user_id") == admin_id, (
            f"Expected target_user_id={admin_id}, got {data.get('target_user_id')}"
        )

    def test_send_missing_title_422(self):
        """Missing title field → 422"""
        token, _ = get_admin_token()
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/send",
            json={"body": "No title push"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422, f"Expected 422 for missing title, got {resp.status_code}: {resp.text}"

    def test_send_missing_body_422(self):
        """Missing body field → 422"""
        token, _ = get_admin_token()
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/send",
            json={"title": "No body push"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422, f"Expected 422 for missing body, got {resp.status_code}: {resp.text}"

    def test_send_with_deep_link(self):
        """Push with deep_link in payload returns 200"""
        token, _ = get_admin_token()
        resp = requests.post(
            f"{BASE_URL}/api/v2/push/send",
            json={"title": "Deep Link Push", "body": "Click to open", "deep_link": "https://free11.com/dashboard"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Expected 200 with deep_link, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "sent" in data and "target_user_id" in data
