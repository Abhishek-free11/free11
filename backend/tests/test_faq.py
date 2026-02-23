"""
Test FAQ feature - Verifies FAQ endpoint returns proper data with coin policy disclaimer
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFAQEndpoint:
    """FAQ endpoint tests"""
    
    def test_faq_endpoint_returns_200(self):
        """Test that FAQ endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/faq")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: FAQ endpoint returns 200 OK")
    
    def test_faq_returns_items_array(self):
        """Test that FAQ endpoint returns items array"""
        response = requests.get(f"{BASE_URL}/api/faq")
        data = response.json()
        
        assert "items" in data, "Response should contain 'items' key"
        assert isinstance(data["items"], list), "items should be a list"
        assert len(data["items"]) > 0, "items should not be empty"
        print(f"PASS: FAQ returns {len(data['items'])} FAQ items")
    
    def test_faq_returns_disclaimer(self):
        """Test that FAQ endpoint returns the coin policy disclaimer"""
        response = requests.get(f"{BASE_URL}/api/faq")
        data = response.json()
        
        assert "disclaimer" in data, "Response should contain 'disclaimer' key"
        
        expected_disclaimer = "FREE11 Coins are non-withdrawable reward tokens redeemable only for goods/services. No cash. No betting. Brand-funded rewards."
        assert data["disclaimer"] == expected_disclaimer, f"Disclaimer mismatch. Got: {data['disclaimer']}"
        print("PASS: FAQ returns correct coin policy disclaimer")
    
    def test_faq_coin_policy_item_exists(self):
        """Test that FAQ contains coin-policy item as first priority"""
        response = requests.get(f"{BASE_URL}/api/faq")
        data = response.json()
        
        # Find coin-policy item
        coin_policy_item = None
        for item in data["items"]:
            if item.get("id") == "coin-policy":
                coin_policy_item = item
                break
        
        assert coin_policy_item is not None, "coin-policy FAQ item should exist"
        assert coin_policy_item["priority"] == 1, "coin-policy should have priority 1"
        assert coin_policy_item["category"] == "coins", "coin-policy should be in 'coins' category"
        assert "non-withdrawable" in coin_policy_item["answer"].lower(), "Answer should mention non-withdrawable"
        print("PASS: coin-policy FAQ item exists with correct content and priority 1")
    
    def test_faq_items_have_required_fields(self):
        """Test that all FAQ items have required fields"""
        response = requests.get(f"{BASE_URL}/api/faq")
        data = response.json()
        
        required_fields = ["id", "question", "answer", "category", "priority"]
        
        for item in data["items"]:
            for field in required_fields:
                assert field in item, f"FAQ item {item.get('id', 'unknown')} missing field: {field}"
        
        print(f"PASS: All {len(data['items'])} FAQ items have required fields")
    
    def test_faq_categories_are_valid(self):
        """Test that FAQ items have valid categories"""
        response = requests.get(f"{BASE_URL}/api/faq")
        data = response.json()
        
        valid_categories = ["coins", "earning", "redemption", "progression", "rewards", "legal"]
        
        for item in data["items"]:
            assert item["category"] in valid_categories, f"Invalid category '{item['category']}' for item {item['id']}"
        
        print("PASS: All FAQ items have valid categories")
    
    def test_faq_items_sorted_by_priority(self):
        """Test that FAQ items are returned in priority order"""
        response = requests.get(f"{BASE_URL}/api/faq")
        data = response.json()
        
        priorities = [item["priority"] for item in data["items"]]
        assert priorities == sorted(priorities), "FAQ items should be sorted by priority"
        print("PASS: FAQ items are sorted by priority")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
