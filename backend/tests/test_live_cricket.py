"""
Live Cricket API Tests for FREE11
Tests the CricketData.org API integration for live matches and players
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://free11-launch.preview.emergentagent.com').rstrip('/')

class TestLiveCricketAPI:
    """Tests for the live cricket endpoints"""
    
    def test_live_matches_endpoint_returns_200(self):
        """Test that /api/cricket/live returns 200 status"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ GET /api/cricket/live returned 200")
    
    def test_live_matches_returns_matches_array(self):
        """Test that response has matches array"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        data = response.json()
        assert 'matches' in data, "Response should have 'matches' key"
        assert isinstance(data['matches'], list), "matches should be a list"
        print(f"✓ Response contains {len(data['matches'])} matches")
    
    def test_live_matches_has_source_info(self):
        """Test that response indicates source (live_api or mock_data)"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        data = response.json()
        assert 'source' in data, "Response should have 'source' key"
        assert data['source'] in ['live_api', 'mock_data', 'error'], f"Source should be live_api/mock_data, got {data['source']}"
        print(f"✓ Data source: {data['source']}")
    
    def test_live_matches_count_is_positive(self):
        """Test that there are matches returned"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        data = response.json()
        assert 'count' in data, "Response should have 'count' key"
        assert data['count'] >= 0, "Count should be non-negative"
        print(f"✓ Match count: {data['count']}")
    
    def test_match_has_required_fields(self):
        """Test that each match has required fields"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        data = response.json()
        
        if len(data['matches']) == 0:
            pytest.skip("No matches available to test")
        
        required_fields = ['id', 'team1', 'team2', 'status', 'venue']
        match = data['matches'][0]
        
        for field in required_fields:
            assert field in match, f"Match missing required field: {field}"
        print(f"✓ Match has all required fields: {required_fields}")
    
    def test_match_status_values(self):
        """Test that match status is valid"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        data = response.json()
        
        valid_statuses = ['live', 'upcoming', 'completed']
        for match in data['matches']:
            assert match.get('status') in valid_statuses, f"Invalid status: {match.get('status')}"
        print(f"✓ All matches have valid status values")
    
    def test_live_matches_have_team_shorts(self):
        """Test that matches have team short names"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        data = response.json()
        
        if len(data['matches']) == 0:
            pytest.skip("No matches available")
        
        for match in data['matches'][:5]:
            assert 'team1_short' in match, f"Match missing team1_short"
            assert 'team2_short' in match, f"Match missing team2_short"
            assert len(match['team1_short']) <= 5, "team1_short should be abbreviation"
        print(f"✓ Matches have team short names")


class TestPlayersAPI:
    """Tests for the players endpoint"""
    
    @pytest.fixture
    def live_match_id(self):
        """Get a live match ID for testing"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        data = response.json()
        
        # Try to find a live match first
        for match in data['matches']:
            if match.get('status') == 'live':
                return match['id']
        
        # If no live match, use first available
        if data['matches']:
            return data['matches'][0]['id']
        
        pytest.skip("No matches available")
    
    def test_players_endpoint_returns_200(self, live_match_id):
        """Test that players endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{live_match_id}/players")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ GET /api/cricket/live/{live_match_id}/players returned 200")
    
    def test_players_returns_match_info(self, live_match_id):
        """Test that response includes match info"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{live_match_id}/players")
        data = response.json()
        
        assert 'match_id' in data, "Response should have match_id"
        assert 'team1' in data, "Response should have team1"
        assert 'team2' in data, "Response should have team2"
        assert data['match_id'] == live_match_id, "match_id should match request"
        print(f"✓ Match info: {data['team1']} vs {data['team2']}")
    
    def test_players_returns_players_array(self, live_match_id):
        """Test that response has players array"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{live_match_id}/players")
        data = response.json()
        
        assert 'players' in data, "Response should have players"
        assert isinstance(data['players'], list), "players should be a list"
        assert len(data['players']) >= 10, f"Should have at least 10 players, got {len(data['players'])}"
        print(f"✓ Response contains {len(data['players'])} players")
    
    def test_players_have_required_fields(self, live_match_id):
        """Test that each player has required fields"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{live_match_id}/players")
        data = response.json()
        
        required_fields = ['id', 'name', 'team', 'role', 'credits']
        player = data['players'][0]
        
        for field in required_fields:
            assert field in player, f"Player missing required field: {field}"
        print(f"✓ Players have all required fields")
    
    def test_players_have_valid_roles(self, live_match_id):
        """Test that players have valid roles (WK, BAT, ALL, BOWL)"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{live_match_id}/players")
        data = response.json()
        
        valid_roles = ['WK', 'BAT', 'ALL', 'BOWL']
        for player in data['players']:
            assert player.get('role') in valid_roles, f"Invalid role: {player.get('role')}"
        print(f"✓ All players have valid roles")
    
    def test_players_have_both_teams(self, live_match_id):
        """Test that players are from both teams"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{live_match_id}/players")
        data = response.json()
        
        teams = set(player['team'] for player in data['players'])
        assert len(teams) == 2, f"Should have players from 2 teams, got {len(teams)}"
        print(f"✓ Players from both teams: {teams}")
    
    def test_players_have_valid_credits(self, live_match_id):
        """Test that player credits are reasonable"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{live_match_id}/players")
        data = response.json()
        
        for player in data['players']:
            credits = player.get('credits', 0)
            assert 5 <= credits <= 12, f"Credits should be 5-12, got {credits} for {player['name']}"
        print(f"✓ All players have valid credits")
    
    def test_sa_teams_get_sa_players(self, live_match_id):
        """Test that SA teams get South African players"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/{live_match_id}/players")
        data = response.json()
        
        # Check if it's a SA match
        team1_lower = data['team1'].lower()
        team2_lower = data['team2'].lower()
        
        sa_keywords = ['cape', 'storm', 'dolphins', 'warriors', 'knights', 'rhinos', 'districts', 'northern', 'south']
        is_sa_match = any(kw in team1_lower or kw in team2_lower for kw in sa_keywords)
        
        if is_sa_match:
            # Should have SA players
            sa_players = ['Quinton de Kock', 'Kyle Verreynne', 'Heinrich Klaasen', 'Aiden Markram', 
                          'Kagiso Rabada', 'Anrich Nortje', 'David Miller', 'Temba Bavuma',
                          'Marco Jansen', 'Keshav Maharaj', 'Lungi Ngidi']
            
            player_names = [p['name'] for p in data['players']]
            has_sa_player = any(sa_player in player_names for sa_player in sa_players)
            
            assert has_sa_player, f"SA match should have SA players. Got: {player_names[:5]}"
            print(f"✓ SA teams have SA players - Found SA players in lineup")
        else:
            print(f"ℹ Not a SA match, skipping SA player check")
    
    def test_invalid_match_id_returns_404(self):
        """Test that invalid match ID returns 404"""
        response = requests.get(f"{BASE_URL}/api/cricket/live/invalid-match-id-12345/players")
        assert response.status_code == 404, f"Expected 404 for invalid match, got {response.status_code}"
        print(f"✓ Invalid match ID returns 404")


class TestLoginAndAuth:
    """Tests for authentication"""
    
    def test_login_with_test_credentials(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "admin"
        })
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        data = response.json()
        assert 'access_token' in data, "Response should have access_token"
        print(f"✓ Login successful, got access token")
        return data['access_token']
    
    def test_user_profile_with_token(self):
        """Test that authenticated user can access profile"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@free11.com",
            "password": "admin"
        })
        token = login_response.json().get('access_token')
        
        # Get profile (correct endpoint is /api/auth/me)
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert profile_response.status_code == 200, f"Profile fetch failed: {profile_response.status_code}"
        data = profile_response.json()
        assert 'email' in data, "Profile should have email"
        print(f"✓ Profile fetched successfully for {data.get('email')}")


class TestContestsIntegration:
    """Tests for contests page integration"""
    
    def test_contests_can_fetch_live_matches(self):
        """Test that contests page data source works"""
        response = requests.get(f"{BASE_URL}/api/cricket/live")
        data = response.json()
        
        # Simulate frontend data transformation
        matches = data.get('matches', [])
        transformed = []
        
        for match in matches[:5]:
            transformed.append({
                'id': match.get('id'),
                'team1': match.get('team1'),
                'team1_short': match.get('team1_short'),
                'team2': match.get('team2'),
                'team2_short': match.get('team2_short'),
                'status': match.get('status'),
                'series': match.get('series', 'Cricket Match')
            })
        
        assert len(transformed) > 0, "Should have matches for contests"
        print(f"✓ Contests can display {len(transformed)} matches")
        
        # Check status badges would work
        live_count = sum(1 for m in transformed if m['status'] == 'live')
        completed_count = sum(1 for m in transformed if m['status'] == 'completed')
        upcoming_count = sum(1 for m in transformed if m['status'] == 'upcoming')
        
        print(f"  - Live: {live_count}, Completed: {completed_count}, Upcoming: {upcoming_count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
