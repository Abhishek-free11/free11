"""
Test suite for FREE11 Notifications Feature (iteration 57)
Tests: trigger-test endpoint, notifications GET/read-all, bell badge integration
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASS = "Admin@123"
USER_EMAIL = "test_redesign_ui26@free11test.com"
USER_PASS = "Test@1234"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token."""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert res.status_code == 200, f"Admin login failed: {res.status_code} {res.text}"
    token = res.json().get("token") or res.json().get("access_token")
    assert token, f"No token in login response: {res.json()}"
    return token


@pytest.fixture(scope="module")
def user_token():
    """Get non-admin user auth token."""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": USER_EMAIL, "password": USER_PASS})
    assert res.status_code == 200, f"User login failed: {res.status_code} {res.text}"
    token = res.json().get("token") or res.json().get("access_token")
    assert token, f"No token in login response: {res.json()}"
    return token


@pytest.fixture(scope="module")
def admin_client(admin_token):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def user_client(user_token):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"})
    return session


# ── Tests: trigger-test endpoint ──────────────────────────────────────────────

class TestTriggerTestEndpoint:
    """POST /api/v2/notifications/trigger-test"""

    def test_trigger_test_admin_returns_ok_true(self, admin_client):
        """Admin should get {ok: true, inserted: 2}"""
        res = admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("ok") is True, f"Expected ok=true, got: {data}"

    def test_trigger_test_admin_inserts_2(self, admin_client):
        """Admin trigger-test should insert exactly 2 notifications."""
        res = admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        assert res.status_code == 200
        data = res.json()
        assert data.get("inserted") == 2, f"Expected inserted=2, got: {data}"

    def test_trigger_test_non_admin_returns_403(self, user_client):
        """Non-admin should get 403."""
        res = user_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"

    def test_trigger_test_no_auth_returns_401(self):
        """No auth should get 401."""
        res = requests.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


# ── Tests: GET notifications ──────────────────────────────────────────────────

class TestGetNotifications:
    """GET /api/v2/notifications"""

    def test_get_notifications_returns_200(self, admin_client):
        """Should return 200 for logged-in user."""
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    def test_get_notifications_response_structure(self, admin_client):
        """Response should have 'notifications' list and 'unread' count."""
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        assert res.status_code == 200
        data = res.json()
        assert "notifications" in data, f"Missing 'notifications' key: {data}"
        assert "unread" in data, f"Missing 'unread' key: {data}"
        assert isinstance(data["notifications"], list), "notifications should be a list"
        assert isinstance(data["unread"], int), "unread should be an int"

    def test_get_notifications_has_items_after_trigger(self, admin_client):
        """After trigger-test, admin should have notifications."""
        # Fire trigger-test first to ensure at least 2 exist
        admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        assert res.status_code == 200
        data = res.json()
        assert len(data["notifications"]) > 0, "Should have at least 1 notification after trigger-test"

    def test_get_notifications_has_activation_trigger_type(self, admin_client):
        """After trigger-test, should have activation_trigger type notification."""
        admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        data = res.json()
        types = [n.get("type") for n in data["notifications"]]
        assert "activation_trigger" in types, f"activation_trigger not found in types: {types}"

    def test_get_notifications_has_streak_reminder_type(self, admin_client):
        """After trigger-test, should have streak_reminder type notification."""
        admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        data = res.json()
        types = [n.get("type") for n in data["notifications"]]
        assert "streak_reminder" in types, f"streak_reminder not found in types: {types}"

    def test_get_notifications_no_auth_returns_401(self):
        """No auth should return 401."""
        res = requests.get(f"{BASE_URL}/api/v2/notifications")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    def test_notifications_unread_count_reflects_unread_items(self, admin_client):
        """The 'unread' count should match the actual count of unread notifications."""
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        data = res.json()
        notifs = data["notifications"]
        actual_unread = sum(1 for n in notifs if not n.get("read"))
        assert data["unread"] == actual_unread, (
            f"Unread count {data['unread']} doesn't match actual unread items {actual_unread}"
        )

    def test_notifications_have_required_fields(self, admin_client):
        """Each notification should have id, type, title, body, read, created_at."""
        admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        data = res.json()
        required_fields = ["id", "type", "title", "body", "read", "created_at"]
        for notif in data["notifications"][:5]:  # Check first 5
            for field in required_fields:
                assert field in notif, f"Missing field '{field}' in notification: {notif}"

    def test_notifications_no_mongo_id_exposed(self, admin_client):
        """MongoDB _id should NOT be exposed in notifications."""
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        data = res.json()
        for notif in data["notifications"][:5]:
            assert "_id" not in notif, f"MongoDB _id exposed in notification: {notif}"

    def test_get_notifications_for_regular_user(self, user_client):
        """Regular user should also be able to get their notifications."""
        res = user_client.get(f"{BASE_URL}/api/v2/notifications")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "notifications" in data
        assert "unread" in data


# ── Tests: read-all endpoint ──────────────────────────────────────────────────

class TestReadAllNotifications:
    """POST /api/v2/notifications/read-all"""

    def test_read_all_returns_200(self, admin_client):
        """read-all should return 200 with {ok: true}."""
        # First add some unread notifications
        admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        res = admin_client.post(f"{BASE_URL}/api/v2/notifications/read-all")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    def test_read_all_returns_ok_true(self, admin_client):
        """read-all should return {ok: true}."""
        admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        res = admin_client.post(f"{BASE_URL}/api/v2/notifications/read-all")
        data = res.json()
        assert data.get("ok") is True, f"Expected ok=true, got: {data}"

    def test_read_all_marks_notifications_as_read(self, admin_client):
        """After read-all, unread count should drop to 0."""
        # First add unread notifications
        admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        # Verify there are unread notifications
        pre = admin_client.get(f"{BASE_URL}/api/v2/notifications").json()
        assert pre["unread"] > 0, "Should have unread notifications before read-all"
        # Mark all read
        admin_client.post(f"{BASE_URL}/api/v2/notifications/read-all")
        # Verify unread count is now 0
        post = admin_client.get(f"{BASE_URL}/api/v2/notifications").json()
        assert post["unread"] == 0, f"Expected 0 unread after read-all, got: {post['unread']}"

    def test_read_all_no_auth_returns_401(self):
        """No auth should return 401."""
        res = requests.post(f"{BASE_URL}/api/v2/notifications/read-all")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"


# ── Tests: Activation trigger campaign logic ──────────────────────────────────

class TestActivationTriggerCampaignLogic:
    """Verify the activation trigger logic in fcm_campaigns.py"""

    def test_trigger_test_response_has_note_field(self, admin_client):
        """trigger-test response should include a 'note' field."""
        res = admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        data = res.json()
        assert "note" in data, f"Expected 'note' field, got: {data}"

    def test_trigger_test_creates_activation_notification_with_correct_fields(self, admin_client):
        """Trigger-test should create activation_trigger notification with correct content."""
        admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        data = res.json()
        activation_notifs = [n for n in data["notifications"] if n.get("type") == "activation_trigger"]
        assert len(activation_notifs) > 0, "No activation_trigger notifications found"
        n = activation_notifs[0]
        assert n.get("deep_link") == "/match-centre", f"Expected deep_link=/match-centre, got: {n.get('deep_link')}"
        assert n.get("read") is not None, "read field should exist"

    def test_trigger_test_creates_streak_reminder_with_correct_fields(self, admin_client):
        """Trigger-test should create streak_reminder notification with correct content."""
        admin_client.post(f"{BASE_URL}/api/v2/notifications/trigger-test")
        res = admin_client.get(f"{BASE_URL}/api/v2/notifications")
        data = res.json()
        streak_notifs = [n for n in data["notifications"] if n.get("type") == "streak_reminder"]
        assert len(streak_notifs) > 0, "No streak_reminder notifications found"
        n = streak_notifs[0]
        assert n.get("deep_link") == "/dashboard", f"Expected deep_link=/dashboard, got: {n.get('deep_link')}"
