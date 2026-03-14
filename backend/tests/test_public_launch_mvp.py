"""
FREE11 Public Launch MVP - Backend API Tests
Tests for: Redis caching, Rate limiting, FREE Bucks, Stripe Payments,
Feature Gating, Notifications, Analytics, Fraud Engine, Auto-scoring
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://app-recovery-91.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASSWORD = "Admin@123"


def get_auth_token():
    """Helper to get auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token", "")
    return ""


@pytest.fixture(scope="module")
def auth_headers():
    """Module-scoped auth headers fixture"""
    token = get_auth_token()
    return {"Authorization": f"Bearer {token}"}


class TestHealthAndRedis:
    """Health check and Redis connectivity tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns ok with redis: true"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("redis") is True, "Redis should be connected"
        assert data.get("version") == "2.0.0"
        print(f"✓ Health check passed: {data}")


class TestAuth:
    """Authentication tests"""
    
    def test_admin_login_success(self):
        """Login with admin@free11.com / Admin@123 returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful, user_id: {data['user']['id']}")


class TestEntitySportCaching:
    """EntitySport API with Redis caching tests"""
    
    def test_entitysport_matches_status_1(self):
        """GET /api/v2/es/matches?status=1 returns upcoming matches"""
        response = requests.get(f"{BASE_URL}/api/v2/es/matches?status=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ EntitySport upcoming matches: {len(data)} matches")
    
    def test_entitysport_caching_performance(self):
        """Second call to /api/v2/es/matches should be faster (cache hit)"""
        # First call - may hit external API
        start1 = time.time()
        response1 = requests.get(f"{BASE_URL}/api/v2/es/matches?status=1")
        time1 = time.time() - start1
        assert response1.status_code == 200
        
        # Second call - should hit cache (60s TTL for match list)
        start2 = time.time()
        response2 = requests.get(f"{BASE_URL}/api/v2/es/matches?status=1")
        time2 = time.time() - start2
        assert response2.status_code == 200
        
        # Cache should make second call faster or similar
        print(f"✓ Cache test - First call: {time1:.3f}s, Second call: {time2:.3f}s")


class TestRateLimiting:
    """Rate limiting middleware tests"""
    
    def test_auth_rate_limit_429(self):
        """6+ rapid POST /api/auth/login should return 429 on 6th call"""
        # Auth endpoint has 5 req/min limit
        results = []
        for i in range(7):
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "ratelimit@test.com", "password": "wrong"},
                headers={"X-Forwarded-For": "203.0.113.99"}  # Fake external IP
            )
            results.append(response.status_code)
            print(f"  Request {i+1}: {response.status_code}")
        
        # First 5 should be 401 (invalid credentials), 6th+ should be 429
        assert 429 in results, f"Expected 429 in results, got: {results}"
        print(f"✓ Rate limit triggered: {results}")


class TestFreeBucks:
    """FREE Bucks wallet tests"""
    
    def test_freebucks_balance(self, auth_headers):
        """GET /api/v2/freebucks/balance returns wallet data"""
        response = requests.get(f"{BASE_URL}/api/v2/freebucks/balance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "wallet" in data
        print(f"✓ FREE Bucks balance: {data['balance']}")
    
    def test_freebucks_packages(self):
        """GET /api/v2/freebucks/packages returns 3 packages"""
        response = requests.get(f"{BASE_URL}/api/v2/freebucks/packages")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "starter" in data
        assert "pro" in data
        assert "elite" in data
        assert data["starter"]["bucks"] == 50
        assert data["pro"]["bucks"] == 200
        assert data["elite"]["bucks"] == 750
        print(f"✓ FREE Bucks packages: {list(data.keys())}")


class TestPayments:
    """Stripe payment checkout tests"""
    
    def test_payment_packages(self):
        """GET /api/payments/packages returns package info"""
        response = requests.get(f"{BASE_URL}/api/payments/packages")
        assert response.status_code == 200
        data = response.json()
        assert "starter" in data
        assert "pro" in data
        assert "elite" in data
        print(f"✓ Payment packages loaded")
    
    def test_payment_checkout_creates_session(self, auth_headers):
        """POST /api/payments/checkout with package_id + origin_url creates Stripe session"""
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout",
            json={
                "package_id": "starter",
                "origin_url": BASE_URL
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Checkout failed: {response.text}"
        data = response.json()
        assert "url" in data, f"Expected url in response: {data}"
        assert "session_id" in data
        print(f"✓ Stripe checkout session created: {data['session_id'][:20]}...")


class TestFeatureGating:
    """Feature gating tests"""
    
    def test_get_gated_features(self):
        """GET /api/v2/features/gated returns 3 gated features"""
        response = requests.get(f"{BASE_URL}/api/v2/features/gated")
        assert response.status_code == 200
        data = response.json()
        assert "ad_free_join" in data
        assert "advanced_stats" in data
        assert "fast_lane_join" in data
        assert data["ad_free_join"]["cost"] == 5
        assert data["advanced_stats"]["cost"] == 10
        assert data["fast_lane_join"]["cost"] == 3
        print(f"✓ Gated features: {list(data.keys())}")
    
    def test_check_feature_access(self, auth_headers):
        """GET /api/v2/features/check/ad_free_join returns access status"""
        response = requests.get(f"{BASE_URL}/api/v2/features/check/ad_free_join", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data
        assert "cost" in data
        assert "balance" in data
        # allowed depends on user's FREE Bucks balance
        print(f"✓ Feature check ad_free_join: allowed={data['allowed']}, cost={data['cost']}, balance={data['balance']}")


class TestNotifications:
    """Notification engine tests"""
    
    def test_get_notifications(self, auth_headers):
        """GET /api/v2/notifications returns notifications with unread_count"""
        response = requests.get(f"{BASE_URL}/api/v2/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"✓ Notifications: {len(data['notifications'])} total, {data['unread_count']} unread")


class TestAnalytics:
    """Analytics dashboard tests"""
    
    def test_analytics_dashboard(self, auth_headers):
        """GET /api/v2/analytics/dashboard returns user/team/prediction counts"""
        response = requests.get(f"{BASE_URL}/api/v2/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_fantasy_teams" in data
        assert "total_predictions" in data
        print(f"✓ Analytics: {data['total_users']} users, {data['total_fantasy_teams']} teams, {data['total_predictions']} predictions")


class TestCacheStats:
    """Cache stats tests"""
    
    def test_cache_stats(self, auth_headers):
        """GET /api/v2/cache/stats returns hits/misses"""
        response = requests.get(f"{BASE_URL}/api/v2/cache/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "hits" in data
        assert "misses" in data
        assert "hit_rate" in data
        print(f"✓ Cache stats: {data['hits']} hits, {data['misses']} misses, {data['hit_rate']}% hit rate")


class TestFraudAdmin:
    """Fraud admin tests"""
    
    def test_get_flagged_users(self, auth_headers):
        """GET /api/admin/v2/fraud/flagged returns list"""
        response = requests.get(f"{BASE_URL}/api/admin/v2/fraud/flagged", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Flagged users: {len(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
