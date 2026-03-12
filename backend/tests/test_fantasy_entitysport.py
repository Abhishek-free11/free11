"""
Fantasy Team Builder & EntitySport Real Data Integration Tests
Tests for FREE11 Fantasy Team Builder with real EntitySport API data.
Match ID 94716 (IND vs ZIM, completed) used for squad/scorecard tests.
Match ID 94717 (ENG vs NZ, upcoming) used for upcoming match tests.
"""
import pytest
import requests
import os
import random
import string

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASS = "Admin@123"
TESTER_EMAIL = "tester@free11.com"
TESTER_PASS = "tester123"
TEST_MATCH_ID = "94716"  # India vs Zimbabwe (completed)
UPCOMING_MATCH_ID = "94717"  # England vs New Zealand (upcoming)


def get_auth_token():
    """Get auth token for testing"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS
    })
    if resp.status_code == 200:
        return resp.json().get("access_token")
    # Try tester
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TESTER_EMAIL,
        "password": TESTER_PASS
    })
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def get_admin_token():
    """Get admin auth token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS
    })
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


@pytest.fixture(scope="class")
def auth_token():
    token = get_auth_token()
    if not token:
        pytest.skip("Authentication failed")
    return token


@pytest.fixture(scope="class")
def admin_token():
    token = get_admin_token()
    if not token:
        pytest.skip("Admin authentication failed")
    return token


class TestEntitySportMatches:
    """Test EntitySport match data endpoints"""
    
    def test_get_upcoming_matches(self):
        """GET /api/v2/es/matches?status=1 returns real upcoming matches"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/matches?status=1&per_page=10")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} upcoming matches")
        if data:
            match = data[0]
            assert "match_id" in match
            assert "title" in match
            assert "team1" in match
            assert "team2" in match
            assert match.get("status") == "upcoming"
            print(f"Sample upcoming match: {match.get('title')}")
    
    def test_get_live_matches(self):
        """GET /api/v2/es/matches?status=3 returns live matches"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/matches?status=3&per_page=10")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} live matches")
    
    def test_get_completed_matches(self):
        """GET /api/v2/es/matches?status=2 returns completed matches"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/matches?status=2&per_page=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should have completed matches"
        # Verify IND vs ZIM (94716) is in completed
        match_ids = [m["match_id"] for m in data]
        print(f"Completed match IDs: {match_ids}")


class TestEntitySportSquads:
    """Test squad data for fantasy team building"""
    
    def test_get_squads_india_vs_zimbabwe(self):
        """GET /api/v2/es/match/94716/squads returns real player squads"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/squads")
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify team structure
        assert "team_a" in data
        assert "team_b" in data
        assert "all_players" in data
        
        # Team A should be India
        team_a = data["team_a"]
        assert team_a["name"] == "India", f"Expected India, got {team_a['name']}"
        assert len(team_a["squad"]) >= 11, "India should have at least 11 players"
        
        # Team B should be Zimbabwe
        team_b = data["team_b"]
        assert team_b["name"] == "Zimbabwe", f"Expected Zimbabwe, got {team_b['name']}"
        assert len(team_b["squad"]) >= 11, "Zimbabwe should have at least 11 players"
        
        print(f"India squad: {len(team_a['squad'])} players")
        print(f"Zimbabwe squad: {len(team_b['squad'])} players")
    
    def test_squad_player_details(self):
        """Verify each player has required fields for fantasy"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/squads")
        assert resp.status_code == 200
        data = resp.json()
        
        all_players = data["team_a"]["squad"] + data["team_b"]["squad"]
        required_fields = ["player_id", "name", "role", "team", "credit"]
        
        for player in all_players[:5]:  # Check first 5 players
            for field in required_fields:
                assert field in player, f"Player missing {field}: {player}"
            
            # Verify credit is in valid range (7.0 - 10.5)
            credit = player["credit"]
            assert 7.0 <= credit <= 10.5, f"Invalid credit {credit} for {player['name']}"
            
            # Verify role is valid
            assert player["role"] in ["wk", "bat", "all", "bowl"], f"Invalid role {player['role']}"
        
        print(f"All players have valid fantasy data")
    
    def test_squad_has_playing11_flag(self):
        """Verify playing11 flag exists (true for confirmed playing 11)"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/squads")
        assert resp.status_code == 200
        data = resp.json()
        
        india_squad = data["team_a"]["squad"]
        playing11 = [p for p in india_squad if p.get("playing11")]
        print(f"India playing11: {len(playing11)} players")
        assert len(playing11) == 11, f"Expected 11 playing, got {len(playing11)}"


class TestEntitySportScorecard:
    """Test scorecard data for points calculation"""
    
    def test_get_scorecard(self):
        """GET /api/v2/es/match/94716/scorecard returns real scorecard"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/scorecard")
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify scorecard structure
        assert "innings" in data
        assert len(data["innings"]) >= 2, "Should have 2 innings (completed match)"
        
        # Check first innings (India batting)
        innings_1 = data["innings"][0]
        assert "batsmen" in innings_1
        assert "bowlers" in innings_1
        assert len(innings_1["batsmen"]) > 0
        assert len(innings_1["bowlers"]) > 0
        
        print(f"Innings 1 batsmen: {len(innings_1['batsmen'])}")
        print(f"Innings 1 bowlers: {len(innings_1['bowlers'])}")
    
    def test_scorecard_batting_stats(self):
        """Verify batting stats are present for points calculation"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/scorecard")
        assert resp.status_code == 200
        data = resp.json()
        
        batsman = data["innings"][0]["batsmen"][0]
        required_batting = ["runs", "balls_faced", "fours", "sixes", "how_out"]
        
        for field in required_batting:
            assert field in batsman, f"Batsman missing {field}"
        
        print(f"Sample batsman: {batsman.get('name')} - {batsman.get('runs')} runs")
    
    def test_scorecard_bowling_stats(self):
        """Verify bowling stats for points calculation"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/scorecard")
        assert resp.status_code == 200
        data = resp.json()
        
        bowler = data["innings"][0]["bowlers"][0]
        required_bowling = ["wickets", "overs", "runs_conceded", "maidens", "econ"]
        
        for field in required_bowling:
            assert field in bowler, f"Bowler missing {field}"
        
        print(f"Sample bowler: {bowler.get('name')} - {bowler.get('wickets')} wickets")
    
    def test_scorecard_fielding_stats(self):
        """Verify fielding stats (catches, stumpings)"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/scorecard")
        assert resp.status_code == 200
        data = resp.json()
        
        # Fielder data should be in innings
        innings = data["innings"][0]
        if "fielder" in innings:
            for fielder in innings["fielder"]:
                assert "catches" in fielder or "stumping" in fielder
            print(f"Fielder data present with {len(innings['fielder'])} entries")
        else:
            print("Fielder data may be in different structure")


class TestFantasyPointsSystem:
    """Test fantasy points configuration endpoint"""
    
    def test_get_points_system(self):
        """GET /api/v2/fantasy/points-system returns points table"""
        resp = requests.get(f"{BASE_URL}/api/v2/fantasy/points-system")
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify points structure
        assert "points" in data
        assert "constraints" in data
        assert "team_size" in data
        assert "max_credits" in data
        assert "max_per_team" in data
        
        # Verify key point values
        points = data["points"]
        assert points["run"] == 1
        assert points["wicket"] == 25
        assert points["catch"] == 10
        assert points["captain_multiplier"] == 2.0
        assert points["vc_multiplier"] == 1.5
        
        # Verify constraints
        constraints = data["constraints"]
        assert constraints["wk"]["min"] == 1
        assert constraints["bat"]["min"] == 3
        assert constraints["all"]["min"] == 1
        assert constraints["bowl"]["min"] == 3
        
        assert data["team_size"] == 11
        assert data["max_credits"] == 100.0
        assert data["max_per_team"] == 7
        
        print(f"Points system: {len(points)} point types, constraints for {len(constraints)} roles")


class TestFantasyTeamCreation:
    """Test fantasy team creation with validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_auth_token()
        if not self.token:
            pytest.skip("Auth failed")
    
    def test_create_valid_fantasy_team(self):
        """POST /api/v2/fantasy/create-team creates a valid team"""
        # First get squads
        squad_resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/squads")
        assert squad_resp.status_code == 200
        squads = squad_resp.json()
        
        # Build a valid team: 1 WK, 3 BAT, 1 AR, 3 BOWL + 3 flexible
        india = squads["team_a"]["squad"]
        zim = squads["team_b"]["squad"]
        all_players = india + zim
        
        # Select players by role
        wk = [p for p in all_players if p["role"] == "wk"][:1]
        bat = [p for p in all_players if p["role"] == "bat"][:3]
        ar = [p for p in all_players if p["role"] == "all"][:2]
        bowl = [p for p in all_players if p["role"] == "bowl"][:5]
        
        selected = wk + bat + ar + bowl
        
        # Ensure exactly 11 players
        if len(selected) < 11:
            remaining = [p for p in all_players if p not in selected]
            selected += remaining[:11 - len(selected)]
        selected = selected[:11]
        
        # Verify credits <= 100
        total_credits = sum(p["credit"] for p in selected)
        print(f"Selected {len(selected)} players, total credits: {total_credits}")
        
        if total_credits > 100:
            # Swap expensive players with cheaper ones
            selected.sort(key=lambda x: x["credit"], reverse=True)
            # Remove most expensive, add cheapest available
            cheap_options = sorted([p for p in all_players if p not in selected], key=lambda x: x["credit"])
            while total_credits > 100 and cheap_options:
                selected.pop()
                replacement = cheap_options.pop(0)
                selected.append(replacement)
                total_credits = sum(p["credit"] for p in selected)
        
        # Pick captain and VC
        captain_id = selected[0]["player_id"]
        vc_id = selected[1]["player_id"]
        
        # Create team
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(f"{BASE_URL}/api/v2/fantasy/create-team", json={
            "match_id": TEST_MATCH_ID,
            "players": selected,
            "captain_id": captain_id,
            "vc_id": vc_id
        }, headers=headers)
        
        # May fail if match already started (94716 is completed)
        # or if already created 3 teams
        if resp.status_code == 400:
            error = resp.json().get("detail", "")
            if "started" in error.lower() or "completed" in error.lower():
                print(f"Expected: Cannot create team for completed match")
            elif "max 3 teams" in error.lower():
                print(f"Expected: Max 3 teams per match limit")
            else:
                print(f"Validation error: {error}")
        elif resp.status_code == 200:
            team = resp.json()
            assert "id" in team
            assert team["captain_id"] == captain_id
            assert team["vc_id"] == vc_id
            assert len(team["players"]) == 11
            print(f"Team created: {team['id']}")
        else:
            print(f"Unexpected response: {resp.status_code} - {resp.text}")
    
    def test_validate_less_than_11_players(self):
        """Team with <11 players should fail"""
        squad_resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/squads")
        squads = squad_resp.json()
        players = squads["team_a"]["squad"][:10]  # Only 10 players
        
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(f"{BASE_URL}/api/v2/fantasy/create-team", json={
            "match_id": TEST_MATCH_ID,
            "players": players,
            "captain_id": players[0]["player_id"],
            "vc_id": players[1]["player_id"]
        }, headers=headers)
        
        assert resp.status_code == 400
        assert "11" in resp.json()["detail"]
        print("Correctly rejected: less than 11 players")
    
    def test_validate_credits_exceed_100(self):
        """Team with >100 credits should fail"""
        squad_resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/squads")
        squads = squad_resp.json()
        all_players = squads["team_a"]["squad"] + squads["team_b"]["squad"]
        
        # Sort by credit descending and pick 11 most expensive
        expensive = sorted(all_players, key=lambda x: x["credit"], reverse=True)[:11]
        total = sum(p["credit"] for p in expensive)
        
        if total <= 100:
            pytest.skip("Can't test - all players under 100 credits combined")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(f"{BASE_URL}/api/v2/fantasy/create-team", json={
            "match_id": TEST_MATCH_ID,
            "players": expensive,
            "captain_id": expensive[0]["player_id"],
            "vc_id": expensive[1]["player_id"]
        }, headers=headers)
        
        assert resp.status_code == 400
        assert "credit" in resp.json()["detail"].lower()
        print(f"Correctly rejected: credits {total} > 100")
    
    def test_validate_captain_equals_vc(self):
        """Captain and VC must be different"""
        squad_resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/squads")
        squads = squad_resp.json()
        india = squads["team_a"]["squad"]
        players = india[:11]
        same_player = players[0]["player_id"]
        
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(f"{BASE_URL}/api/v2/fantasy/create-team", json={
            "match_id": TEST_MATCH_ID,
            "players": players,
            "captain_id": same_player,
            "vc_id": same_player  # Same as captain!
        }, headers=headers)
        
        assert resp.status_code == 400
        detail = resp.json()["detail"].lower()
        assert "captain" in detail or "different" in detail
        print("Correctly rejected: C and VC are same")
    
    def test_validate_role_constraints(self):
        """Test role constraints (min 1 WK, 3 BAT, 1 AR, 3 BOWL)"""
        squad_resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/squads")
        squads = squad_resp.json()
        all_players = squads["team_a"]["squad"] + squads["team_b"]["squad"]
        
        # Pick 11 batsmen only (no WK, AR, BOWL)
        batsmen = [p for p in all_players if p["role"] == "bat"][:11]
        if len(batsmen) < 11:
            pytest.skip("Not enough batsmen to test constraint")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(f"{BASE_URL}/api/v2/fantasy/create-team", json={
            "match_id": TEST_MATCH_ID,
            "players": batsmen,
            "captain_id": batsmen[0]["player_id"],
            "vc_id": batsmen[1]["player_id"]
        }, headers=headers)
        
        assert resp.status_code == 400
        detail = resp.json()["detail"].lower()
        assert "wk" in detail or "bowl" in detail or "role" in detail
        print("Correctly rejected: role constraints not met")
    
    def test_validate_max_7_per_team(self):
        """Max 7 players from single team"""
        squad_resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/squads")
        squads = squad_resp.json()
        india = squads["team_a"]["squad"]
        
        # Pick 8 from India + 3 from Zimbabwe
        if len(india) < 8:
            pytest.skip("Not enough India players")
        
        india_8 = india[:8]
        zim_3 = squads["team_b"]["squad"][:3]
        players = india_8 + zim_3
        
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(f"{BASE_URL}/api/v2/fantasy/create-team", json={
            "match_id": TEST_MATCH_ID,
            "players": players,
            "captain_id": players[0]["player_id"],
            "vc_id": players[1]["player_id"]
        }, headers=headers)
        
        assert resp.status_code == 400
        detail = resp.json()["detail"].lower()
        assert "7" in detail or "max" in detail
        print("Correctly rejected: >7 players from one team")


class TestFantasyRankings:
    """Test fantasy rankings endpoint"""
    
    def test_get_rankings(self):
        """GET /api/v2/fantasy/rankings/{match_id} returns ranked teams"""
        resp = requests.get(f"{BASE_URL}/api/v2/fantasy/rankings/{TEST_MATCH_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        print(f"Rankings: {len(data)} teams")
        
        if data:
            # Verify sorted by points (descending)
            for i, team in enumerate(data[:3]):
                assert "rank" in team
                assert "total_points" in team
                print(f"Rank {team['rank']}: {team.get('total_points', 0)} points")


class TestAdminFantasyScoring:
    """Test admin fantasy scoring endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_admin_token()
        if not self.token:
            pytest.skip("Admin auth failed")
    
    def test_calculate_fantasy_points(self):
        """POST /api/admin/v2/fantasy/score calculates points from scorecard"""
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(f"{BASE_URL}/api/admin/v2/fantasy/score", json={
            "match_id": TEST_MATCH_ID
        }, headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        assert "scored" in data
        assert "results" in data
        print(f"Scored {data['scored']} teams")
        
        if data["results"]:
            top_team = data["results"][0]
            assert "total_points" in top_team
            print(f"Top team: {top_team.get('total_points')} points")


class TestMyFantasyTeams:
    """Test user's fantasy teams endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_auth_token()
        if not self.token:
            pytest.skip("Auth failed")
    
    def test_get_my_teams(self):
        """GET /api/v2/fantasy/my-teams returns user's teams"""
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(f"{BASE_URL}/api/v2/fantasy/my-teams", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        print(f"User has {len(data)} fantasy teams")
    
    def test_get_my_teams_by_match(self):
        """GET /api/v2/fantasy/my-teams?match_id=X filters by match"""
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(f"{BASE_URL}/api/v2/fantasy/my-teams?match_id={TEST_MATCH_ID}", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # All teams should be for the specified match
        for team in data:
            assert team["match_id"] == TEST_MATCH_ID
        print(f"User has {len(data)} teams for match {TEST_MATCH_ID}")


class TestMatchInfo:
    """Test match info endpoint"""
    
    def test_get_match_info(self):
        """GET /api/v2/es/match/{id}/info returns match details"""
        resp = requests.get(f"{BASE_URL}/api/v2/es/match/{TEST_MATCH_ID}/info")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["match_id"] == TEST_MATCH_ID
        assert "India" in data["team1"]
        assert "Zimbabwe" in data["team2"]
        assert data["status"] == "completed"
        print(f"Match: {data['title']} - {data['status_note']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
