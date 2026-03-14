"""
Backend Tests: Rummy-win, Poker-win, Card Leaderboard, Card Streak
New endpoints added in iteration 48
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://multilingual-preview.preview.emergentagent.com').rstrip('/')

# Test user credentials (use test user, not admin - admin may have already claimed today)
TEST_EMAIL = "test_redesign_ui26@free11test.com"
TEST_PASSWORD = "Test@1234"

@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if resp.status_code != 200:
        pytest.skip(f"Login failed: {resp.text}")
    return resp.json().get("access_token")

@pytest.fixture(scope="module")
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# ── Rummy Win Endpoint ────────────────────────────────────────────────────────

class TestRummyWin:
    """POST /api/v2/earn/rummy-win - once per day award 50 coins"""

    def test_rummy_win_requires_auth(self):
        """Without auth token, should return 401"""
        resp = requests.post(f"{BASE_URL}/api/v2/earn/rummy-win")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print("✓ rummy-win: 401 without auth")

    def test_rummy_win_with_auth(self, headers):
        """With auth, first call returns 200 OR 400 if already claimed today"""
        resp = requests.post(f"{BASE_URL}/api/v2/earn/rummy-win", headers=headers)
        assert resp.status_code in [200, 400], f"Expected 200 or 400, got {resp.status_code}: {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("success") == True, "success field must be True"
            assert data.get("coins_earned") == 50, f"Expected 50 coins, got {data.get('coins_earned')}"
            assert "new_balance" in data, "new_balance must be in response"
            print(f"✓ rummy-win: 200 OK, coins_earned={data['coins_earned']}, new_balance={data['new_balance']}")
        else:
            data = resp.json()
            detail = data.get("detail", "")
            assert "already claimed" in detail.lower() or "rummy" in detail.lower(), \
                f"400 message should mention already claimed: {detail}"
            print(f"✓ rummy-win: 400 already claimed today - {detail}")

    def test_rummy_win_duplicate_returns_400(self, headers):
        """Second call on same day must return 400"""
        # First call (may succeed or already claimed)
        resp1 = requests.post(f"{BASE_URL}/api/v2/earn/rummy-win", headers=headers)
        
        # Second call must be 400
        resp2 = requests.post(f"{BASE_URL}/api/v2/earn/rummy-win", headers=headers)
        assert resp2.status_code == 400, f"Duplicate should return 400, got {resp2.status_code}"
        
        data = resp2.json()
        assert "detail" in data, "Error response should have 'detail' field"
        print(f"✓ rummy-win: Duplicate correctly returns 400: {data.get('detail')}")

    def test_rummy_win_response_structure(self, headers):
        """Verify response structure on 200 (if not already claimed)"""
        resp = requests.post(f"{BASE_URL}/api/v2/earn/rummy-win", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            required_fields = ["success", "coins_earned", "new_balance"]
            for field in required_fields:
                assert field in data, f"Missing field '{field}' in response"
            assert isinstance(data["coins_earned"], int), "coins_earned must be an integer"
            assert isinstance(data["new_balance"], (int, float)), "new_balance must be numeric"
            print(f"✓ rummy-win: Response structure valid: {data}")
        else:
            print(f"✓ rummy-win: Already claimed (400), structure test skipped")


# ── Poker Win Endpoint ────────────────────────────────────────────────────────

class TestPokerWin:
    """POST /api/v2/earn/poker-win - once per day award 60 coins"""

    def test_poker_win_requires_auth(self):
        """Without auth token, should return 401"""
        resp = requests.post(f"{BASE_URL}/api/v2/earn/poker-win")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print("✓ poker-win: 401 without auth")

    def test_poker_win_with_auth(self, headers):
        """With auth, first call returns 200 OR 400 if already claimed today"""
        resp = requests.post(f"{BASE_URL}/api/v2/earn/poker-win", headers=headers)
        assert resp.status_code in [200, 400], f"Expected 200 or 400, got {resp.status_code}: {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("success") == True, "success field must be True"
            assert data.get("coins_earned") == 60, f"Expected 60 coins, got {data.get('coins_earned')}"
            assert "new_balance" in data, "new_balance must be in response"
            print(f"✓ poker-win: 200 OK, coins_earned={data['coins_earned']}, new_balance={data['new_balance']}")
        else:
            data = resp.json()
            detail = data.get("detail", "")
            assert "already claimed" in detail.lower() or "poker" in detail.lower(), \
                f"400 message should mention already claimed: {detail}"
            print(f"✓ poker-win: 400 already claimed today - {detail}")

    def test_poker_win_duplicate_returns_400(self, headers):
        """Second call on same day must return 400"""
        resp1 = requests.post(f"{BASE_URL}/api/v2/earn/poker-win", headers=headers)
        resp2 = requests.post(f"{BASE_URL}/api/v2/earn/poker-win", headers=headers)
        assert resp2.status_code == 400, f"Duplicate should return 400, got {resp2.status_code}"
        data = resp2.json()
        assert "detail" in data, "Error response should have 'detail' field"
        print(f"✓ poker-win: Duplicate correctly returns 400: {data.get('detail')}")

    def test_poker_win_coins_amount(self, headers):
        """Verify poker win awards exactly 60 coins"""
        resp = requests.post(f"{BASE_URL}/api/v2/earn/poker-win", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            assert data["coins_earned"] == 60, f"Poker should award 60 coins, got {data['coins_earned']}"
            print(f"✓ poker-win: Correct amount = 60 coins")
        else:
            print(f"✓ poker-win: Already claimed (400), amount check skipped - expected 60 coins")


# ── Card Leaderboard ──────────────────────────────────────────────────────────

class TestCardLeaderboard:
    """GET /api/v2/games/card-leaderboard - no auth required"""

    def test_card_leaderboard_returns_200(self):
        """Leaderboard endpoint should return 200 without auth"""
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-leaderboard")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"✓ card-leaderboard: 200 OK")

    def test_card_leaderboard_response_structure(self):
        """Response must have leaderboard array"""
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-leaderboard")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "leaderboard" in data, "Response must have 'leaderboard' key"
        assert isinstance(data["leaderboard"], list), "leaderboard must be a list"
        print(f"✓ card-leaderboard: Response structure OK, {len(data['leaderboard'])} entries")

    def test_card_leaderboard_entry_structure(self):
        """Each leaderboard entry should have expected fields"""
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-leaderboard")
        data = resp.json()
        
        if data["leaderboard"]:
            entry = data["leaderboard"][0]
            assert "total_coins" in entry, "Entry must have total_coins"
            assert "wins" in entry, "Entry must have wins"
            assert isinstance(entry["total_coins"], (int, float)), "total_coins must be numeric"
            assert isinstance(entry["wins"], int), "wins must be an integer"
            print(f"✓ card-leaderboard: Entry structure OK: top player has {entry['total_coins']} coins")
        else:
            print("✓ card-leaderboard: Empty leaderboard (no games played this week)")

    def test_card_leaderboard_max_10_entries(self):
        """Leaderboard should return at most 10 entries"""
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-leaderboard")
        data = resp.json()
        assert len(data["leaderboard"]) <= 10, f"Expected max 10 entries, got {len(data['leaderboard'])}"
        print(f"✓ card-leaderboard: Correctly limited to {len(data['leaderboard'])} entries (≤ 10)")


# ── Card Streak ────────────────────────────────────────────────────────────────

class TestCardStreak:
    """GET /api/v2/games/card-streak - requires auth"""

    def test_card_streak_requires_auth(self):
        """Without auth, should return 401"""
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-streak")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ card-streak: 401 without auth")

    def test_card_streak_with_auth(self, headers):
        """With auth, should return streak and played_today"""
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-streak", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"✓ card-streak: 200 OK")

    def test_card_streak_response_structure(self, headers):
        """Response must have streak and played_today fields"""
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-streak", headers=headers)
        assert resp.status_code == 200
        
        data = resp.json()
        assert "streak" in data, "Response must have 'streak' field"
        assert "played_today" in data, "Response must have 'played_today' field"
        assert isinstance(data["streak"], int), f"streak must be integer, got {type(data['streak'])}"
        assert isinstance(data["played_today"], bool), f"played_today must be boolean, got {type(data['played_today'])}"
        assert data["streak"] >= 0, "streak must be non-negative"
        print(f"✓ card-streak: streak={data['streak']}, played_today={data['played_today']}")

    def test_card_streak_values_valid(self, headers):
        """Streak value should be within bounds (0-30)"""
        resp = requests.get(f"{BASE_URL}/api/v2/games/card-streak", headers=headers)
        data = resp.json()
        assert 0 <= data["streak"] <= 30, f"Streak {data['streak']} out of expected range [0, 30]"
        print(f"✓ card-streak: Streak value {data['streak']} is valid (0-30)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
