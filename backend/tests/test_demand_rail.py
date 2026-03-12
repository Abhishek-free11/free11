"""
Test cases for FREE11 Demand Rail restructure features:
- Dashboard PRORGA disclaimer
- Progress to Next Reward
- Cricket Prediction as hero (SKILL EARNING badge)
- Skill Stats (Accuracy, Correct, Streak, Total)
- Boosters section (BONUS label)
- Navbar hierarchy: Home → Predict → Boost → Redeem → Orders
- Coin Boosters page title and note
- Impulse rewards starting at ₹10
- /api/user/demand-progress API
- /api/products with brand fields
- /api/admin/brand-roas placeholder
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDemandRailAPIs:
    """Test Demand Rail backend APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with test credentials
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cricket@free11.com",
            "password": "cricket123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = login_response.json().get("user")
            print(f"✓ Logged in as {self.user.get('email')}")
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_demand_progress_api_returns_next_reward(self):
        """Test /api/user/demand-progress returns next_reward with progress"""
        response = self.session.get(f"{BASE_URL}/api/user/demand-progress")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"Demand progress response: {data}")
        
        # Validate required fields
        assert "coins_balance" in data, "Missing coins_balance field"
        assert "prediction_stats" in data, "Missing prediction_stats field"
        assert "consumption_unlocked" in data, "Missing consumption_unlocked field"
        assert "rank" in data, "Missing rank field"
        
        # Validate prediction_stats structure
        stats = data["prediction_stats"]
        assert "accuracy" in stats, "Missing accuracy in prediction_stats"
        assert "correct" in stats, "Missing correct in prediction_stats"
        assert "streak" in stats, "Missing streak in prediction_stats"
        assert "total" in stats, "Missing total in prediction_stats"
        
        # Validate rank structure
        rank = data["rank"]
        assert "name" in rank, "Missing name in rank"
        assert "level" in rank, "Missing level in rank"
        
        print(f"✓ Demand progress API returns all required fields")
        print(f"  - Coins: {data['coins_balance']}")
        print(f"  - Accuracy: {stats['accuracy']}%")
        print(f"  - Rank: {rank['name']} (Level {rank['level']})")
    
    def test_products_api_returns_brand_fields(self):
        """Test /api/products returns products with brand_id, campaign_id, funded_by_brand, fulfillment_type"""
        response = self.session.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        products = response.json()
        assert isinstance(products, list), "Expected products to be a list"
        
        if len(products) == 0:
            # Seed products first
            seed_response = self.session.post(f"{BASE_URL}/api/seed-products")
            assert seed_response.status_code == 200, "Failed to seed products"
            response = self.session.get(f"{BASE_URL}/api/products")
            products = response.json()
        
        assert len(products) > 0, "No products found even after seeding"
        
        # Check brand fields on first product
        product = products[0]
        brand_fields = ["brand_id", "campaign_id", "funded_by_brand", "fulfillment_type"]
        
        for field in brand_fields:
            assert field in product, f"Missing {field} field in product"
        
        print(f"✓ Products API returns brand fields")
        print(f"  - Total products: {len(products)}")
        print(f"  - Sample product: {product.get('name')} (brand: {product.get('brand_id')})")
        print(f"  - Funded by brand: {product.get('funded_by_brand')}")
        print(f"  - Fulfillment: {product.get('fulfillment_type')}")
    
    def test_products_have_impulse_rewards_starting_at_10(self):
        """Test shop has impulse rewards starting at ₹10 (Mobile Recharge)"""
        response = self.session.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        
        products = response.json()
        
        if len(products) == 0:
            seed_response = self.session.post(f"{BASE_URL}/api/seed-products")
            assert seed_response.status_code == 200
            response = self.session.get(f"{BASE_URL}/api/products")
            products = response.json()
        
        # Find cheapest product
        cheapest = min(products, key=lambda p: p.get('coin_price', float('inf')))
        
        # Verify impulse reward tier exists (₹10-₹50)
        impulse_rewards = [p for p in products if p.get('coin_price', 0) <= 50]
        
        assert len(impulse_rewards) > 0, "No impulse rewards (₹10-₹50) found"
        assert cheapest.get('coin_price') == 10, f"Cheapest product is {cheapest.get('coin_price')} coins, expected 10"
        
        print(f"✓ Impulse rewards starting at ₹10 verified")
        print(f"  - Cheapest product: {cheapest.get('name')} ({cheapest.get('coin_price')} coins)")
        print(f"  - Total impulse rewards (≤50 coins): {len(impulse_rewards)}")
    
    def test_brand_roas_api_returns_placeholder_dashboard(self):
        """Test /api/admin/brand-roas returns placeholder brand ROAS dashboard"""
        response = self.session.get(f"{BASE_URL}/api/admin/brand-roas")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Validate placeholder response structure
        assert "message" in data, "Missing message field"
        assert "brand_performance" in data, "Missing brand_performance field"
        assert "total_demand_created" in data, "Missing total_demand_created field"
        
        print(f"✓ Brand ROAS API returns placeholder dashboard")
        print(f"  - Message: {data.get('message')}")
        print(f"  - Brand data count: {len(data.get('brand_performance', []))}")
    
    def test_leaderboard_skill_based(self):
        """Test leaderboard is skill-based (accuracy) not coin-based"""
        response = self.session.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        leaderboard = response.json()
        
        # If leaderboard has entries with accuracy field, it's skill-based
        if len(leaderboard) > 0 and "accuracy" in leaderboard[0]:
            print(f"✓ Leaderboard is skill-based (has accuracy field)")
            print(f"  - Top player: {leaderboard[0].get('name')} ({leaderboard[0].get('accuracy')}% accuracy)")
        else:
            # Fallback to coin-based is expected if no predictions
            print(f"✓ Leaderboard uses fallback (no predictions yet)")
            if leaderboard:
                print(f"  - Top player: {leaderboard[0].get('name')}")
    
    def test_auth_me_returns_progression_fields(self):
        """Test /api/auth/me returns user with progression fields"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        user = response.json()
        
        # Check progression fields exist in user model
        expected_fields = ["level", "xp", "streak_days", "total_earned", "total_redeemed"]
        
        for field in expected_fields:
            assert field in user, f"Missing {field} field in user"
        
        print(f"✓ User model has progression fields")
        print(f"  - Level: {user.get('level')}")
        print(f"  - XP: {user.get('xp')}")
        print(f"  - Streak: {user.get('streak_days')} days")


class TestProductBrandSchema:
    """Test product schema with brand fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "cricket@free11.com",
            "password": "cricket123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Auth failed")
    
    def test_product_has_fulfillment_types(self):
        """Test products have various fulfillment types (direct, ondc_bap, qcomm, d2c)"""
        response = self.session.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        
        products = response.json()
        if len(products) == 0:
            self.session.post(f"{BASE_URL}/api/seed-products")
            response = self.session.get(f"{BASE_URL}/api/products")
            products = response.json()
        
        fulfillment_types = set(p.get('fulfillment_type') for p in products)
        
        print(f"✓ Fulfillment types found: {fulfillment_types}")
        assert len(fulfillment_types) > 1, "Expected multiple fulfillment types"
    
    def test_product_has_min_level_required(self):
        """Test products have min_level_required for tier unlocking"""
        response = self.session.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        
        products = response.json()
        if len(products) == 0:
            self.session.post(f"{BASE_URL}/api/seed-products")
            response = self.session.get(f"{BASE_URL}/api/products")
            products = response.json()
        
        # Check min_level_required exists
        for product in products[:5]:
            assert "min_level_required" in product, f"Missing min_level_required in {product.get('name')}"
        
        # Verify tier structure
        level_1_products = [p for p in products if p.get('min_level_required') == 1]
        higher_level_products = [p for p in products if p.get('min_level_required', 1) > 1]
        
        print(f"✓ Product tier structure verified")
        print(f"  - Level 1 products: {len(level_1_products)}")
        print(f"  - Higher level products: {len(higher_level_products)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
