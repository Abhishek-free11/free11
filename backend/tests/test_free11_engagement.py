"""
FREE11 Engagement Features Backend Tests (Iteration 25)
Tests: Wishlist, Streak, Crowd Meter, Daily Puzzle, Weekly Report Card
Admin: admin@free11.com / Admin@123
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def get_admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@free11.com", "password": "Admin@123"
    })
    if r.status_code == 200:
        data = r.json()
        return data.get("access_token") or data.get("token")
    return None


def register_new_user():
    """Register a fresh test user for puzzle testing."""
    uid = str(uuid.uuid4())[:8]
    email = f"test_eng_{uid}@free11test.com"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email,
        "password": "Test@12345",
        "name": "Engagement Tester",
        "date_of_birth": "1995-06-15",
    })
    if r.status_code in (200, 201):
        data = r.json()
        token = data.get("access_token") or data.get("token")
        return token, email
    return None, None


@pytest.fixture(scope="module")
def admin_token():
    token = get_admin_token()
    if not token:
        pytest.skip("Admin login failed")
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def new_user_token():
    """Fresh user who hasn't answered today's puzzle."""
    token, email = register_new_user()
    if not token:
        pytest.skip("New user registration failed")
    return token


@pytest.fixture(scope="module")
def new_user_headers(new_user_token):
    return {"Authorization": f"Bearer {new_user_token}", "Content-Type": "application/json"}


# ─────────────────────────────────────────────────────────────────────────────
# REGRESSION: Health check and auth
# ─────────────────────────────────────────────────────────────────────────────

class TestRegression:
    """Regression: Basic health and auth"""

    def test_health_returns_ok(self):
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        print(f"Health: {data}")

    def test_admin_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com", "password": "Admin@123"
        })
        assert r.status_code == 200
        data = r.json()
        token = data.get("access_token") or data.get("token")
        assert token is not None, f"No token in response: {data}"
        user_data = data.get("user", {})
        assert user_data.get("is_admin") is True, f"Expected is_admin=True, got {user_data}"
        print(f"Admin login: PASS, coins={user_data.get('coins_balance')}")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 1 — Wishlist
# ─────────────────────────────────────────────────────────────────────────────

class TestWishlist:
    """Feature 1: Wishlist Progress Tracker"""

    def test_get_wishlist_requires_auth(self):
        # No auth → 401
        r = requests.get(f"{BASE_URL}/api/v2/wishlist")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("GET /wishlist without auth: 401 PASS")

    def test_get_wishlist_authenticated(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/v2/wishlist", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "pinned" in data
        print(f"GET /wishlist: {data}")

    def test_pin_requires_valid_product(self, admin_headers):
        # Try to pin a non-existent product
        r = requests.post(f"{BASE_URL}/api/v2/wishlist/pin", json={"product_id": "nonexistent_xyz"}, headers=admin_headers)
        assert r.status_code == 404
        print("PIN nonexistent product: 404 PASS")

    def test_pin_and_get_wishlist(self, admin_headers):
        # First get available products
        prod_r = requests.get(f"{BASE_URL}/api/products")
        assert prod_r.status_code == 200
        products = prod_r.json()
        assert len(products) > 0, "No products available to pin"
        product = products[0]
        product_id = product["id"]

        # Pin the product
        pin_r = requests.post(f"{BASE_URL}/api/v2/wishlist/pin", json={"product_id": product_id}, headers=admin_headers)
        assert pin_r.status_code == 200
        pin_data = pin_r.json()
        assert pin_data.get("pinned") is True
        assert pin_data.get("product_id") == product_id
        print(f"PIN product {product_id}: PASS")

        # Get wishlist and verify progress fields
        get_r = requests.get(f"{BASE_URL}/api/v2/wishlist", headers=admin_headers)
        assert get_r.status_code == 200
        wd = get_r.json()
        assert wd.get("pinned") is True
        assert "progress" in wd
        assert "coins_needed" in wd
        assert "coins_balance" in wd
        assert "product" in wd and wd["product"] is not None
        assert isinstance(wd["progress"], (int, float))
        assert isinstance(wd["coins_needed"], (int, float))
        assert isinstance(wd["coins_balance"], (int, float))
        print(f"GET wishlist after pin: progress={wd['progress']}%, coins_needed={wd['coins_needed']}, balance={wd['coins_balance']}")

    def test_unpin_wishlist(self, admin_headers):
        # Unpin
        r = requests.delete(f"{BASE_URL}/api/v2/wishlist/unpin", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data.get("unpinned") is True
        print("DELETE /wishlist/unpin: PASS")

        # Verify it's removed
        get_r = requests.get(f"{BASE_URL}/api/v2/wishlist", headers=admin_headers)
        assert get_r.status_code == 200
        wd = get_r.json()
        assert wd.get("pinned") is False
        print("GET wishlist after unpin: pinned=False PASS")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 2 — Streak / Hot Hand
# ─────────────────────────────────────────────────────────────────────────────

class TestStreak:
    """Feature 2: Streak Multiplier / Hot Hand"""

    def test_streak_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/v2/predictions/streak")
        assert r.status_code == 401
        print("GET /predictions/streak without auth: 401 PASS")

    def test_streak_returns_valid_data(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/v2/predictions/streak", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "streak" in data
        assert "multiplier" in data
        assert "hot_hand" in data
        streak = data["streak"]
        multiplier = data["multiplier"]
        hot_hand = data["hot_hand"]
        # Verify logic
        if streak >= 7:
            assert multiplier == 4
        elif streak >= 5:
            assert multiplier == 3
        elif streak >= 3:
            assert multiplier == 2
        else:
            assert multiplier == 1
        assert hot_hand == (streak >= 3)
        print(f"Streak: streak={streak}, multiplier={multiplier}, hot_hand={hot_hand} PASS")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 3 — Crowd Meter
# ─────────────────────────────────────────────────────────────────────────────

class TestCrowdMeter:
    """Feature 3: Live Crowd Meter"""

    def test_crowd_meter_is_public(self):
        # No auth required
        r = requests.get(f"{BASE_URL}/api/v2/crowd-meter/94722")
        assert r.status_code == 200
        data = r.json()
        assert "match_id" in data
        assert "meter" in data
        print(f"GET /crowd-meter/94722 (public): meter keys={list(data.get('meter', {}).keys())} PASS")

    def test_crowd_meter_structure(self):
        r = requests.get(f"{BASE_URL}/api/v2/crowd-meter/94722")
        assert r.status_code == 200
        data = r.json()
        assert data["match_id"] == "94722"
        meter = data.get("meter", {})
        # If predictions exist, verify structure
        for pred_type, type_data in meter.items():
            assert "total_predictions" in type_data, f"Missing total_predictions in {pred_type}"
            assert "options" in type_data, f"Missing options in {pred_type}"
            for opt, opt_data in type_data["options"].items():
                assert "count" in opt_data
                assert "pct" in opt_data
            print(f"Crowd meter type '{pred_type}': {type_data['total_predictions']} predictions, options={list(type_data['options'].keys())}")
        print(f"Crowd meter structure: PASS (types={list(meter.keys())})")

    def test_crowd_meter_non_existent_match(self):
        # A match with no predictions should return empty meter
        r = requests.get(f"{BASE_URL}/api/v2/crowd-meter/9999999")
        assert r.status_code == 200
        data = r.json()
        assert data["meter"] == {} or len(data["meter"]) == 0
        print("GET /crowd-meter/9999999 (no predictions): empty meter PASS")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 4 — Daily Cricket Puzzle
# ─────────────────────────────────────────────────────────────────────────────

class TestDailyPuzzle:
    """Feature 4: Daily Cricket Puzzle"""

    def test_get_today_puzzle_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/v2/puzzle/today")
        assert r.status_code == 401
        print("GET /puzzle/today without auth: 401 PASS")

    def test_get_today_puzzle(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/v2/puzzle/today", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "question" in data
        assert "options" in data
        assert "already_answered" in data
        assert "first_100_reward" in data
        assert "late_reward" in data
        assert data["first_100_reward"] == 25
        assert data["late_reward"] == 5
        assert len(data["options"]) == 4
        # Verify correct answer is NOT exposed
        assert "correct" not in data
        print(f"GET /puzzle/today: question='{data['question'][:50]}...', already_answered={data['already_answered']}, reward={data['first_100_reward']} PASS")

    def test_admin_already_answered(self, admin_headers):
        """Admin has already answered today's puzzle per context note."""
        r = requests.get(f"{BASE_URL}/api/v2/puzzle/today", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        # Admin already answered per test context
        assert data["already_answered"] is True, f"Expected admin already_answered=True but got {data['already_answered']}"
        print(f"Admin already_answered=True: PASS (previous_result={data.get('previous_result')})")

    def test_new_user_puzzle_answer_correct(self, new_user_headers):
        """New user answers with the correct answer for Wednesday puzzle."""
        # Today is Wednesday (day_of_week=2), correct answer is '1 wicket per 15 balls'
        correct_answer = "1 wicket per 15 balls"
        r = requests.post(f"{BASE_URL}/api/v2/puzzle/answer", json={"answer": correct_answer}, headers=new_user_headers)
        assert r.status_code == 200
        data = r.json()
        assert "is_correct" in data
        assert "coins_earned" in data
        assert "correct_answer" in data
        assert "explanation" in data
        assert "already_answered" in data
        assert data["already_answered"] is False  # First submission
        assert data["is_correct"] is True, f"Expected correct, got is_correct={data['is_correct']}, correct_answer={data['correct_answer']}"
        assert data["coins_earned"] > 0, "Expected coins earned for correct answer"
        assert data["coins_earned"] in [25, 5], f"Expected 25 or 5 coins, got {data['coins_earned']}"
        print(f"New user correct answer: is_correct=True, coins_earned={data['coins_earned']} PASS")

    def test_idempotency_second_submission_returns_already_answered(self, new_user_headers):
        """Second submission should return already_answered=True (idempotent)."""
        r = requests.post(f"{BASE_URL}/api/v2/puzzle/answer", json={"answer": "1 wicket per 15 balls"}, headers=new_user_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["already_answered"] is True, f"Expected already_answered=True on second submission, got {data}"
        print(f"Idempotency: already_answered=True on 2nd submission PASS")

    def test_coins_credited_after_correct_answer(self, new_user_headers):
        """After correct answer, verify coins appear in ledger history (db.ledger collection)."""
        time.sleep(1)  # Give time for ledger to process
        # Puzzle rewards go through LedgerEngine (db.ledger), NOT db.coin_transactions
        r = requests.get(f"{BASE_URL}/api/v2/ledger/history", headers=new_user_headers)
        assert r.status_code == 200
        data = r.json()
        entries = data.get("entries", [])
        puzzle_txns = [t for t in entries if "puzzle" in t.get("type", "").lower() or "puzzle" in t.get("description", "").lower()]
        assert len(puzzle_txns) > 0, f"No puzzle reward in ledger. Entries: {entries}"
        print(f"Puzzle coins in ledger: {puzzle_txns[0]}")

    def test_wrong_answer(self, admin_headers):
        """Admin already answered. Submit wrong answer via a different new user to check wrong answer logic."""
        # Register another new user for wrong answer test
        token2, _ = register_new_user()
        if not token2:
            pytest.skip("Could not register 2nd test user")
        headers2 = {"Authorization": f"Bearer {token2}"}
        r = requests.post(f"{BASE_URL}/api/v2/puzzle/answer", json={"answer": "1 wicket per 30 balls"}, headers=headers2)
        assert r.status_code == 200
        data = r.json()
        assert data["is_correct"] is False
        assert data["coins_earned"] == 0
        assert data["already_answered"] is False
        print(f"Wrong answer: is_correct=False, coins_earned=0 PASS")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 5 — Weekly Report Card
# ─────────────────────────────────────────────────────────────────────────────

class TestWeeklyReportCard:
    """Feature 5: Weekly Report Card"""

    def test_weekly_report_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/v2/report-card/weekly")
        assert r.status_code == 401
        print("GET /report-card/weekly without auth: 401 PASS")

    def test_get_weekly_report(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/v2/report-card/weekly", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        # Required fields
        for field in ["week_start", "accuracy", "rank", "rank_change", "predictions_total",
                      "contests_joined", "coins_earned_this_week", "is_new"]:
            assert field in data, f"Missing field: {field}"
        assert isinstance(data["accuracy"], (int, float))
        assert isinstance(data["rank"], int)
        assert isinstance(data["predictions_total"], int)
        assert isinstance(data["is_new"], bool)
        print(f"GET /report-card/weekly: week={data['week_start']}, accuracy={data['accuracy']}, rank={data['rank']}, is_new={data['is_new']} PASS")

    def test_dismiss_weekly_report(self, admin_headers):
        r = requests.post(f"{BASE_URL}/api/v2/report-card/dismiss", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data.get("dismissed") is True
        print("POST /report-card/dismiss: dismissed=True PASS")

    def test_is_new_false_after_dismiss(self, admin_headers):
        """After dismiss, is_new should be False."""
        r = requests.get(f"{BASE_URL}/api/v2/report-card/weekly", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["is_new"] is False, f"Expected is_new=False after dismiss, got {data['is_new']}"
        print("is_new=False after dismiss: PASS")

    def test_weekly_report_new_user(self, new_user_headers):
        """New user with 0 predictions should get a valid report (is_new=True)."""
        r = requests.get(f"{BASE_URL}/api/v2/report-card/weekly", headers=new_user_headers)
        assert r.status_code == 200
        data = r.json()
        assert "predictions_total" in data
        # New user has 0 predictions, so weekly modal won't show (is_new but predictions_total=0)
        print(f"New user weekly report: predictions_total={data['predictions_total']}, is_new={data['is_new']} PASS")
