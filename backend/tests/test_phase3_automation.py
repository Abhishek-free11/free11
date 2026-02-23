"""
Phase 3: Automation & Brand Tools Testing
Tests: Voucher fulfillment, Support chatbot, Brand Portal APIs
Guardrails: ROAS metrics only (no CPM/impressions), MOCKED voucher providers
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
USER_EMAIL = "cricket@free11.com"
USER_PASSWORD = "cricket123"
BRAND_EMAIL = "amazon@test.com"
BRAND_PASSWORD = "amazon123"


class TestVoucherFulfillment:
    """Test fulfillment provider status endpoint (MOCKED providers)"""

    def test_providers_status_returns_all_providers(self):
        """GET /api/fulfillment/providers/status returns all provider statuses"""
        response = requests.get(f"{BASE_URL}/api/fulfillment/providers/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "providers" in data
        providers = data["providers"]
        
        # All expected providers should be present
        expected_providers = ["amazon", "swiggy", "flipkart", "netflix", "spotify", "generic"]
        for provider in expected_providers:
            assert provider in providers, f"Provider {provider} missing"
    
    def test_providers_are_mocked(self):
        """All providers should be marked as MOCKED"""
        response = requests.get(f"{BASE_URL}/api/fulfillment/providers/status")
        assert response.status_code == 200
        
        data = response.json()
        for provider_name, provider_info in data["providers"].items():
            assert provider_info.get("is_mocked") == True, f"Provider {provider_name} not marked as mocked"
            assert provider_info.get("available") == True, f"Provider {provider_name} not available"
    
    def test_amazon_provider_details(self):
        """Amazon provider has correct name"""
        response = requests.get(f"{BASE_URL}/api/fulfillment/providers/status")
        assert response.status_code == 200
        
        data = response.json()
        amazon = data["providers"]["amazon"]
        assert amazon["name"] == "Amazon Gift Cards"


class TestSupportChatbot:
    """Test support chatbot - deterministic FAQ responses"""
    
    @pytest.fixture
    def user_token(self):
        """Get user token for authenticated endpoints"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": USER_EMAIL, "password": USER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User login failed")
    
    def test_chat_suggestions_returns_initial_options(self):
        """GET /api/support/chat/suggestions returns FAQ suggestions"""
        response = requests.get(f"{BASE_URL}/api/support/chat/suggestions")
        assert response.status_code == 200
        
        data = response.json()
        assert "greeting" in data
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        
        # Should have common support options
        suggestions_text = " ".join(data["suggestions"]).lower()
        assert "order" in suggestions_text or "coins" in suggestions_text
    
    def test_chat_faq_coins_response(self, user_token):
        """POST /api/support/chat returns FAQ response about coins"""
        response = requests.post(
            f"{BASE_URL}/api/support/chat",
            json={"message": "What are coins and how do they work?"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        # Should mention coins/predictions
        assert "coin" in data["response"].lower() or "predict" in data["response"].lower()
    
    def test_chat_faq_redeem_response(self, user_token):
        """POST /api/support/chat returns FAQ response about redemption"""
        response = requests.post(
            f"{BASE_URL}/api/support/chat",
            json={"message": "How do I redeem my rewards?"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "suggestions" in data
    
    def test_chat_support_ticket_action(self, user_token):
        """POST /api/support/chat with issue returns create_ticket action"""
        response = requests.post(
            f"{BASE_URL}/api/support/chat",
            json={"message": "I have a problem and need help from support"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        # Should suggest talking to support or creating ticket
        assert data.get("action") == "create_ticket" or "support" in data["response"].lower()
    
    def test_chat_requires_authentication(self):
        """POST /api/support/chat without token returns 403"""
        response = requests.post(
            f"{BASE_URL}/api/support/chat",
            json={"message": "test"}
        )
        assert response.status_code in [401, 403]


class TestSupportTickets:
    """Test support ticket creation and retrieval"""
    
    @pytest.fixture
    def user_token(self):
        """Get user token for authenticated endpoints"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": USER_EMAIL, "password": USER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User login failed")
    
    def test_create_ticket_success(self, user_token):
        """POST /api/support/tickets creates a ticket"""
        response = requests.post(
            f"{BASE_URL}/api/support/tickets",
            json={
                "subject": "TEST_Automated Test Ticket",
                "description": "This is an automated test ticket for Phase 3 testing",
                "category": "technical"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "ticket_id" in data
        assert "message" in data
        assert "created" in data["message"].lower()
    
    def test_get_my_tickets(self, user_token):
        """GET /api/support/tickets returns user's tickets"""
        response = requests.get(
            f"{BASE_URL}/api/support/tickets",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "tickets" in data
        assert isinstance(data["tickets"], list)
    
    def test_create_ticket_requires_auth(self):
        """POST /api/support/tickets without auth fails"""
        response = requests.post(
            f"{BASE_URL}/api/support/tickets",
            json={"subject": "Test", "description": "Test", "category": "other"}
        )
        assert response.status_code in [401, 403]


class TestBrandAuth:
    """Test brand portal authentication"""
    
    def test_brand_register_new_account(self):
        """POST /api/brand/auth/register creates brand account"""
        import uuid
        unique_email = f"testbrand_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/api/brand/auth/register",
            json={
                "email": unique_email,
                "password": "test123",
                "company_name": "Test Company",
                "contact_name": "Test Contact",
                "brand_name": "TestBrand"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "brand_id" in data
        assert "message" in data
    
    def test_brand_register_duplicate_email_fails(self):
        """POST /api/brand/auth/register with existing email fails"""
        response = requests.post(
            f"{BASE_URL}/api/brand/auth/register",
            json={
                "email": BRAND_EMAIL,
                "password": "test123",
                "company_name": "Test",
                "contact_name": "Test",
                "brand_name": "Test"
            }
        )
        assert response.status_code == 400
    
    def test_brand_login_success(self):
        """POST /api/brand/auth/login returns JWT token"""
        response = requests.post(
            f"{BASE_URL}/api/brand/auth/login",
            json={"email": BRAND_EMAIL, "password": BRAND_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "brand" in data
        assert data["brand"]["brand_name"] == "Amazon"
    
    def test_brand_login_invalid_credentials(self):
        """POST /api/brand/auth/login with wrong password fails"""
        response = requests.post(
            f"{BASE_URL}/api/brand/auth/login",
            json={"email": BRAND_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code == 401


class TestBrandDashboard:
    """Test brand dashboard - ROAS metrics, NO impressions/CPM"""
    
    @pytest.fixture
    def brand_token(self):
        """Get brand token"""
        response = requests.post(
            f"{BASE_URL}/api/brand/auth/login",
            json={"email": BRAND_EMAIL, "password": BRAND_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Brand login failed")
    
    def test_dashboard_returns_roas_metrics(self, brand_token):
        """GET /api/brand/dashboard returns ROAS metrics"""
        response = requests.get(
            f"{BASE_URL}/api/brand/dashboard",
            headers={"Authorization": f"Bearer {brand_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "demand_metrics" in data
        assert "roas" in data
        
        # Verify ROAS structure
        assert "value" in data["roas"]
        assert "description" in data["roas"]
        assert "note" in data["roas"]
    
    def test_dashboard_has_consumption_metrics(self, brand_token):
        """Dashboard has verified consumption, redemptions, unique consumers"""
        response = requests.get(
            f"{BASE_URL}/api/brand/dashboard",
            headers={"Authorization": f"Bearer {brand_token}"}
        )
        assert response.status_code == 200
        
        metrics = response.json()["demand_metrics"]
        assert "total_redemptions" in metrics
        assert "verified_consumption_value" in metrics
        assert "unique_consumers_reached" in metrics
    
    def test_dashboard_no_impressions_or_cpm(self, brand_token):
        """GUARDRAIL: Dashboard does NOT have impressions or CPM metrics"""
        response = requests.get(
            f"{BASE_URL}/api/brand/dashboard",
            headers={"Authorization": f"Bearer {brand_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        data_str = str(data).lower()
        
        # Should NOT contain impression/CPM language
        assert "impression" not in data_str, "Dashboard should NOT have 'impression' metrics"
        assert "cpm" not in data_str, "Dashboard should NOT have 'CPM' metrics"
        assert "cpc" not in data_str, "Dashboard should NOT have 'CPC' metrics"
        assert "click" not in data_str or "clock" in data_str, "Dashboard should NOT have 'click' metrics"
    
    def test_dashboard_recent_activity(self, brand_token):
        """Dashboard has recent activity metrics"""
        response = requests.get(
            f"{BASE_URL}/api/brand/dashboard",
            headers={"Authorization": f"Bearer {brand_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "recent_activity" in data
        assert "last_7_days_redemptions" in data["recent_activity"]
        assert "last_30_days_redemptions" in data["recent_activity"]
    
    def test_dashboard_requires_brand_auth(self):
        """Dashboard requires brand authentication"""
        response = requests.get(f"{BASE_URL}/api/brand/dashboard")
        assert response.status_code in [401, 403]


class TestBrandCampaigns:
    """Test brand campaign management"""
    
    @pytest.fixture
    def brand_token(self):
        """Get brand token"""
        response = requests.post(
            f"{BASE_URL}/api/brand/auth/login",
            json={"email": BRAND_EMAIL, "password": BRAND_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Brand login failed")
    
    def test_get_campaigns(self, brand_token):
        """GET /api/brand/campaigns returns campaign list"""
        response = requests.get(
            f"{BASE_URL}/api/brand/campaigns",
            headers={"Authorization": f"Bearer {brand_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "campaigns" in data
        assert isinstance(data["campaigns"], list)
    
    def test_create_campaign(self, brand_token):
        """POST /api/brand/campaigns creates a campaign"""
        response = requests.post(
            f"{BASE_URL}/api/brand/campaigns",
            json={
                "name": "TEST_Phase3 Test Campaign",
                "description": "Automated test campaign",
                "objective": "demand_creation",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31"
            },
            headers={"Authorization": f"Bearer {brand_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "campaign_id" in data


class TestBrandProducts:
    """Test brand product management"""
    
    @pytest.fixture
    def brand_token(self):
        """Get brand token"""
        response = requests.post(
            f"{BASE_URL}/api/brand/auth/login",
            json={"email": BRAND_EMAIL, "password": BRAND_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Brand login failed")
    
    def test_get_products(self, brand_token):
        """GET /api/brand/products returns product list"""
        response = requests.get(
            f"{BASE_URL}/api/brand/products",
            headers={"Authorization": f"Bearer {brand_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        assert isinstance(data["products"], list)
    
    def test_create_product(self, brand_token):
        """POST /api/brand/products creates a product"""
        response = requests.post(
            f"{BASE_URL}/api/brand/products",
            json={
                "name": "TEST_Amazon Gift Card ₹100",
                "description": "Test product for Phase 3",
                "category": "gift_cards",
                "cost_in_coins": 1000,
                "value_in_inr": 100,
                "total_inventory": 10
            },
            headers={"Authorization": f"Bearer {brand_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "product_id" in data


# Run with: pytest /app/backend/tests/test_phase3_automation.py -v --junitxml=/app/test_reports/pytest/phase3_results.xml
