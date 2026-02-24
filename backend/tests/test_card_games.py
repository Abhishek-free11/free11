"""
Card Games API Tests for FREE11
Tests: Room creation, WebSocket, Stats, Quick Play
"""
import pytest
import requests
import os
import json
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cricket-coins.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "abhishek@free11.com"
TEST_PASSWORD = "admin123"


class TestGamesConfig:
    """Test game configuration endpoint - no auth required"""
    
    def test_get_games_config(self):
        """Test /api/games/config returns correct game configuration"""
        response = requests.get(f"{BASE_URL}/api/games/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "games" in data, "Response should contain 'games' key"
        assert "note" in data, "Response should contain 'note' key"
        assert "coin_model" in data, "Response should contain 'coin_model' key"
        
        # Verify all 3 game types exist
        games = data["games"]
        assert "rummy" in games, "Rummy game should be in config"
        assert "teen_patti" in games, "Teen Patti game should be in config"
        assert "poker" in games, "Poker game should be in config"
        
        print("✓ Games config API returns all 3 game types")
        
    def test_rummy_config_values(self):
        """Test Rummy game has correct configuration"""
        response = requests.get(f"{BASE_URL}/api/games/config")
        data = response.json()
        
        rummy = data["games"]["rummy"]
        assert rummy["name"] == "Rummy"
        assert rummy["min_players"] == 2
        assert rummy["max_players"] == 6
        assert rummy["coins_to_play"] == 0, "Game should be FREE to play"
        assert rummy["coins_reward"]["win"] == 50
        assert rummy["coins_reward"]["second"] == 20
        assert rummy["coins_reward"]["participate"] == 5
        
        print("✓ Rummy config: FREE entry, Win=50, Second=20, Participate=5")
        
    def test_teen_patti_config_values(self):
        """Test Teen Patti game has correct configuration"""
        response = requests.get(f"{BASE_URL}/api/games/config")
        data = response.json()
        
        teen_patti = data["games"]["teen_patti"]
        assert teen_patti["name"] == "Teen Patti"
        assert teen_patti["min_players"] == 3
        assert teen_patti["max_players"] == 6
        assert teen_patti["coins_to_play"] == 0, "Game should be FREE to play"
        assert teen_patti["coins_reward"]["win"] == 40
        assert teen_patti["coins_reward"]["second"] == 15
        assert teen_patti["coins_reward"]["participate"] == 5
        
        print("✓ Teen Patti config: FREE entry, Win=40, Second=15, Participate=5")
        
    def test_poker_config_values(self):
        """Test Poker game has correct configuration"""
        response = requests.get(f"{BASE_URL}/api/games/config")
        data = response.json()
        
        poker = data["games"]["poker"]
        assert poker["name"] == "Poker"
        assert poker["min_players"] == 2
        assert poker["max_players"] == 9
        assert poker["coins_to_play"] == 0, "Game should be FREE to play"
        assert poker["coins_reward"]["win"] == 60
        assert poker["coins_reward"]["second"] == 25
        assert poker["coins_reward"]["participate"] == 5
        
        print("✓ Poker config: FREE entry, Win=60, Second=25, Participate=5")


class TestGamesAuth:
    """Test authenticated card games endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to login: {response.text}")
        
        self.token = response.json()["access_token"]
        self.user_id = response.json()["user"]["id"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_game_info_rummy(self):
        """Test /api/games/rummy/info returns detailed game info"""
        response = requests.get(f"{BASE_URL}/api/games/rummy/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["game_type"] == "rummy"
        assert "hand_rankings" in data
        assert data["entry_fee"] == "FREE"
        
        print("✓ Rummy info endpoint returns hand rankings and FREE entry")
        
    def test_get_game_info_teen_patti(self):
        """Test /api/games/teen_patti/info returns detailed game info"""
        response = requests.get(f"{BASE_URL}/api/games/teen_patti/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["game_type"] == "teen_patti"
        assert "hand_rankings" in data
        assert len(data["hand_rankings"]) == 6, "Teen Patti should have 6 hand rankings"
        
        print("✓ Teen Patti info returns 6 hand rankings: Trail, Pure Sequence, etc.")
        
    def test_get_game_info_poker(self):
        """Test /api/games/poker/info returns detailed game info"""
        response = requests.get(f"{BASE_URL}/api/games/poker/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["game_type"] == "poker"
        assert "hand_rankings" in data
        assert len(data["hand_rankings"]) == 10, "Poker should have 10 hand rankings"
        
        print("✓ Poker info returns 10 hand rankings: Royal Flush to High Card")
    
    def test_get_invalid_game_type(self):
        """Test invalid game type returns 404"""
        response = requests.get(f"{BASE_URL}/api/games/blackjack/info")
        assert response.status_code == 404
        
        print("✓ Invalid game type 'blackjack' correctly returns 404")
        
    def test_get_my_stats_rummy(self):
        """Test /api/games/rummy/stats/my returns user stats"""
        response = requests.get(
            f"{BASE_URL}/api/games/rummy/stats/my",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "game_type" in data
        assert data["game_type"] == "rummy"
        assert "games_played" in data
        assert "games_won" in data
        assert "total_coins_earned" in data
        assert "win_rate" in data
        
        print(f"✓ User rummy stats: {data['games_played']} games played, {data['win_rate']}% win rate")
        
    def test_get_my_stats_teen_patti(self):
        """Test /api/games/teen_patti/stats/my returns user stats"""
        response = requests.get(
            f"{BASE_URL}/api/games/teen_patti/stats/my",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["game_type"] == "teen_patti"
        
        print(f"✓ User teen_patti stats: {data['games_played']} games played")
        
    def test_get_my_stats_poker(self):
        """Test /api/games/poker/stats/my returns user stats"""
        response = requests.get(
            f"{BASE_URL}/api/games/poker/stats/my",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["game_type"] == "poker"
        
        print(f"✓ User poker stats: {data['games_played']} games played")


class TestRoomCreation:
    """Test game room creation and management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to login: {response.text}")
        
        self.token = response.json()["access_token"]
        self.user_id = response.json()["user"]["id"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_create_public_room_rummy(self):
        """Test creating a public Rummy room"""
        response = requests.post(
            f"{BASE_URL}/api/games/rummy/rooms/create",
            headers=self.headers,
            json={
                "game_type": "rummy",
                "name": "Test Rummy Room",
                "max_players": 4,
                "is_private": False
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "room" in data
        assert data["room"]["game_type"] == "rummy"
        assert data["room"]["name"] == "Test Rummy Room"
        assert data["room"]["status"] == "waiting"
        assert self.user_id in data["room"]["player_ids"], "Creator should be in player list"
        assert data["room_code"] is None, "Public room should not have code"
        
        print(f"✓ Created public Rummy room: {data['room']['id']}")
        return data["room"]["id"]
    
    def test_create_private_room_teen_patti(self):
        """Test creating a private Teen Patti room with room code"""
        response = requests.post(
            f"{BASE_URL}/api/games/teen_patti/rooms/create",
            headers=self.headers,
            json={
                "game_type": "teen_patti",
                "name": "Private Teen Patti",
                "max_players": 6,
                "is_private": True
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["room"]["is_private"] == True
        assert data["room_code"] is not None, "Private room should have a code"
        assert len(data["room_code"]) == 6, "Room code should be 6 characters"
        assert "share_message" in data, "Should include share message"
        
        print(f"✓ Created private Teen Patti room with code: {data['room_code']}")
        
    def test_create_private_room_poker(self):
        """Test creating a private Poker room"""
        response = requests.post(
            f"{BASE_URL}/api/games/poker/rooms/create",
            headers=self.headers,
            json={
                "game_type": "poker",
                "name": "Poker Night",
                "max_players": 9,
                "is_private": True
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["room"]["game_type"] == "poker"
        assert data["room"]["max_players"] == 9
        assert data["room_code"] is not None
        
        print(f"✓ Created private Poker room with code: {data['room_code']}")
        
    def test_create_room_invalid_players(self):
        """Test room creation with invalid player count"""
        # Teen Patti requires min 3 players
        response = requests.post(
            f"{BASE_URL}/api/games/teen_patti/rooms/create",
            headers=self.headers,
            json={
                "game_type": "teen_patti",
                "name": "Invalid Room",
                "max_players": 2,  # Below minimum
                "is_private": False
            }
        )
        assert response.status_code == 400
        
        print("✓ Room creation correctly rejects invalid player count for Teen Patti")


class TestQuickPlay:
    """Test quick play functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to login: {response.text}")
        
        self.token = response.json()["access_token"]
        self.user_id = response.json()["user"]["id"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_quick_play_rummy(self):
        """Test quick play creates or joins a Rummy room"""
        response = requests.post(
            f"{BASE_URL}/api/games/rummy/quick-play",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "action" in data, "Response should indicate action taken"
        assert data["action"] in ["created", "joined"], "Action should be 'created' or 'joined'"
        assert "room" in data
        assert data["room"]["game_type"] == "rummy"
        
        print(f"✓ Quick Play Rummy: {data['action']} room {data['room']['id']}")
        
    def test_quick_play_poker(self):
        """Test quick play for Poker"""
        response = requests.post(
            f"{BASE_URL}/api/games/poker/quick-play",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["action"] in ["created", "joined"]
        
        print(f"✓ Quick Play Poker: {data['action']} room")


class TestAvailableRooms:
    """Test fetching available rooms"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to login: {response.text}")
        
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_available_rooms_rummy(self):
        """Test /api/games/rummy/rooms returns available rooms"""
        response = requests.get(
            f"{BASE_URL}/api/games/rummy/rooms",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "rooms" in data
        assert "total" in data
        assert data["game_type"] == "rummy"
        assert isinstance(data["rooms"], list)
        
        # Check room structure if any rooms exist
        if data["rooms"]:
            room = data["rooms"][0]
            assert "current_players" in room
            assert "spots_left" in room
        
        print(f"✓ Found {data['total']} available Rummy rooms")
        
    def test_get_my_rooms(self):
        """Test /api/games/my-rooms returns user's active rooms"""
        response = requests.get(
            f"{BASE_URL}/api/games/my-rooms",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "rooms" in data
        assert "total" in data
        
        print(f"✓ User has {data['total']} active game rooms")


class TestLeaderboard:
    """Test game leaderboard functionality"""
    
    def test_get_rummy_leaderboard(self):
        """Test /api/games/rummy/leaderboard returns rankings"""
        response = requests.get(f"{BASE_URL}/api/games/rummy/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        assert data["game_type"] == "rummy"
        assert data["game_name"] == "Rummy"
        assert "leaderboard" in data
        
        print(f"✓ Rummy leaderboard has {len(data['leaderboard'])} entries")
        
    def test_get_poker_leaderboard(self):
        """Test /api/games/poker/leaderboard returns rankings"""
        response = requests.get(f"{BASE_URL}/api/games/poker/leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        assert data["game_type"] == "poker"
        assert data["game_name"] == "Poker"
        
        print(f"✓ Poker leaderboard has {len(data['leaderboard'])} entries")


class TestJoinByCode:
    """Test joining private rooms by code"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to login: {response.text}")
        
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_join_invalid_code(self):
        """Test joining with invalid room code returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/games/rooms/join-by-code",
            headers=self.headers,
            params={"code": "INVALID"}
        )
        assert response.status_code == 404
        
        print("✓ Invalid room code correctly returns 404")


class TestRoomState:
    """Test getting room state for reconnection"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token, create a room"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to login: {response.text}")
        
        self.token = response.json()["access_token"]
        self.user_id = response.json()["user"]["id"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Create a room for testing
        room_response = requests.post(
            f"{BASE_URL}/api/games/rummy/rooms/create",
            headers=self.headers,
            json={
                "game_type": "rummy",
                "name": "State Test Room",
                "max_players": 4,
                "is_private": False
            }
        )
        if room_response.status_code == 200:
            self.room_id = room_response.json()["room"]["id"]
        else:
            self.room_id = None
    
    def test_get_room_state(self):
        """Test /api/games/{game_type}/rooms/{room_id}/state returns room state"""
        if not self.room_id:
            pytest.skip("No room created")
            
        response = requests.get(
            f"{BASE_URL}/api/games/rummy/rooms/{self.room_id}/state",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "players" in data
        assert "game_active" in data or "room" in data
        
        print(f"✓ Room state returned for {self.room_id}")
        
    def test_get_invalid_room_state(self):
        """Test getting state for non-existent room returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/games/rummy/rooms/invalid-room-id/state",
            headers=self.headers
        )
        assert response.status_code == 404
        
        print("✓ Invalid room ID correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
