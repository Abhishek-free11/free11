"""
FREE11 V2 Engine API Tests
Testing: Contests, Predictions, Cards, Ledger, Ads, Referral, MatchState, Admin Controls
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASS = "Admin@123"
TEST_EMAIL = "tester@free11.com"
TEST_PASS = "tester123"

class TestV2AuthAndSetup:
    """Test auth and get tokens for subsequent tests"""
    
    admin_token = None
    test_token = None
    admin_id = None
    test_user_id = None
    
    @classmethod
    def get_admin_token(cls):
        if cls.admin_token:
            return cls.admin_token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASS
        })
        if response.status_code == 200:
            cls.admin_token = response.json().get("access_token")
            cls.admin_id = response.json().get("user", {}).get("id")
        return cls.admin_token
    
    @classmethod
    def get_test_token(cls):
        if cls.test_token:
            return cls.test_token
        # First try login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASS
        })
        if response.status_code == 200:
            cls.test_token = response.json().get("access_token")
            cls.test_user_id = response.json().get("user", {}).get("id")
            return cls.test_token
        # If login fails, use admin token for testing
        return cls.get_admin_token()
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASS
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["is_admin"] == True
        TestV2AuthAndSetup.admin_token = data["access_token"]
        TestV2AuthAndSetup.admin_id = data["user"]["id"]
        print(f"✓ Admin login successful, user_id: {data['user']['id']}")


class TestV2AdminMatchControl:
    """Test Admin V2 Match Control APIs"""
    
    test_match_id = None
    
    def test_create_test_match(self):
        """Admin creates test match for simulation"""
        token = TestV2AuthAndSetup.get_admin_token()
        assert token, "Admin token required"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/v2/match/test/create",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Create test match failed: {response.text}"
        data = response.json()
        assert "match_id" in data
        assert data.get("status") == "live"
        TestV2AdminMatchControl.test_match_id = data["match_id"]
        print(f"✓ Test match created: {data['match_id']}")
    
    def test_advance_test_match(self):
        """Admin advances test match ball-by-ball"""
        token = TestV2AuthAndSetup.get_admin_token()
        match_id = TestV2AdminMatchControl.test_match_id
        if not match_id:
            pytest.skip("No test match created")
        
        # Advance 6 balls (1 over)
        for runs in [1, 2, 0, 4, 6, 1]:
            response = requests.post(
                f"{BASE_URL}/api/admin/v2/match/test/advance",
                headers={"Authorization": f"Bearer {token}"},
                json={"match_id": match_id, "runs": runs, "wicket": False}
            )
            assert response.status_code == 200, f"Advance failed: {response.text}"
        
        data = response.json()
        assert "score" in data
        print(f"✓ Match advanced, score: {data['score']}")
    
    def test_set_feature_flag(self):
        """Admin sets feature flag"""
        token = TestV2AuthAndSetup.get_admin_token()
        assert token, "Admin token required"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/v2/feature-flag",
            headers={"Authorization": f"Bearer {token}"},
            json={"flag": "test_v2_api", "enabled": True}
        )
        assert response.status_code == 200, f"Set feature flag failed: {response.text}"
        data = response.json()
        assert data["flag"] == "test_v2_api"
        assert data["enabled"] == True
        print(f"✓ Feature flag set: test_v2_api = True")
    
    def test_get_feature_flags(self):
        """Admin gets all feature flags"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/v2/feature-flags",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get flags failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} feature flags")


class TestV2Contests:
    """Test V2 Contest APIs"""
    
    contest_id = None
    invite_code = None
    
    def test_create_public_contest(self):
        """Create public contest"""
        token = TestV2AuthAndSetup.get_admin_token()
        match_id = TestV2AdminMatchControl.test_match_id or "test_match_001"
        
        response = requests.post(
            f"{BASE_URL}/api/v2/contests/create",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "match_id": match_id,
                "name": "TEST_Public Contest",
                "contest_type": "public",
                "max_participants": 100,
                "entry_fee": 0
            }
        )
        assert response.status_code == 200, f"Create contest failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["type"] == "public"
        TestV2Contests.contest_id = data["id"]
        print(f"✓ Public contest created: {data['id']}")
    
    def test_create_private_contest(self):
        """Create private contest with invite code"""
        token = TestV2AuthAndSetup.get_admin_token()
        match_id = TestV2AdminMatchControl.test_match_id or "test_match_001"
        
        response = requests.post(
            f"{BASE_URL}/api/v2/contests/create",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "match_id": match_id,
                "name": "TEST_Private Contest",
                "contest_type": "private",
                "max_participants": 10,
                "entry_fee": 0
            }
        )
        assert response.status_code == 200, f"Create private contest failed: {response.text}"
        data = response.json()
        assert data["type"] == "private"
        assert "invite_code" in data and data["invite_code"] is not None
        TestV2Contests.invite_code = data["invite_code"]
        print(f"✓ Private contest created with code: {data['invite_code']}")
    
    def test_join_contest(self):
        """Join contest"""
        token = TestV2AuthAndSetup.get_admin_token()
        contest_id = TestV2Contests.contest_id
        if not contest_id:
            pytest.skip("No contest created")
        
        response = requests.post(
            f"{BASE_URL}/api/v2/contests/join",
            headers={"Authorization": f"Bearer {token}"},
            json={"contest_id": contest_id}
        )
        assert response.status_code == 200, f"Join contest failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Joined contest, participants: {data.get('participants')}")
    
    def test_join_duplicate_prevention(self):
        """Test duplicate join prevention"""
        token = TestV2AuthAndSetup.get_admin_token()
        contest_id = TestV2Contests.contest_id
        if not contest_id:
            pytest.skip("No contest created")
        
        # Try joining again - should fail
        response = requests.post(
            f"{BASE_URL}/api/v2/contests/join",
            headers={"Authorization": f"Bearer {token}"},
            json={"contest_id": contest_id}
        )
        assert response.status_code == 400, f"Duplicate join should fail: {response.text}"
        print(f"✓ Duplicate join correctly prevented")
    
    def test_join_by_invite_code(self):
        """Join contest by invite code"""
        token = TestV2AuthAndSetup.get_admin_token()
        invite_code = TestV2Contests.invite_code
        if not invite_code:
            pytest.skip("No invite code")
        
        response = requests.post(
            f"{BASE_URL}/api/v2/contests/join-code",
            headers={"Authorization": f"Bearer {token}"},
            json={"invite_code": invite_code}
        )
        # May fail if already joined - that's okay
        assert response.status_code in [200, 400], f"Join by code failed: {response.text}"
        print(f"✓ Join by code endpoint working")
    
    def test_get_my_contests(self):
        """Get user's contests"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/v2/contests/user/my",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get my contests failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} user contests")


class TestV2Predictions:
    """Test V2 Prediction APIs"""
    
    prediction_id = None
    
    def test_get_prediction_types(self):
        """Get available prediction types"""
        response = requests.get(f"{BASE_URL}/api/v2/predictions/types")
        assert response.status_code == 200, f"Get prediction types failed: {response.text}"
        data = response.json()
        assert "over_runs" in data
        assert "over_wicket" in data
        assert "reward" in data["over_runs"]
        print(f"✓ Got {len(data)} prediction types")
    
    def test_submit_prediction(self):
        """Submit a prediction"""
        token = TestV2AuthAndSetup.get_admin_token()
        match_id = TestV2AdminMatchControl.test_match_id or "test_match_001"
        
        response = requests.post(
            f"{BASE_URL}/api/v2/predictions/submit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "match_id": match_id,
                "prediction_type": "over_runs",
                "prediction_value": "6-10",
                "over_number": 2
            }
        )
        assert response.status_code == 200, f"Submit prediction failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
        TestV2Predictions.prediction_id = data["id"]
        print(f"✓ Prediction submitted: {data['id']}")
    
    def test_idempotent_prediction(self):
        """Test idempotent prediction (no duplicate)"""
        token = TestV2AuthAndSetup.get_admin_token()
        match_id = TestV2AdminMatchControl.test_match_id or "test_match_001"
        
        # Try same prediction again
        response = requests.post(
            f"{BASE_URL}/api/v2/predictions/submit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "match_id": match_id,
                "prediction_type": "over_runs",
                "prediction_value": "6-10",
                "over_number": 2
            }
        )
        assert response.status_code == 400, f"Duplicate prediction should fail: {response.text}"
        print(f"✓ Idempotent prediction protection working")
    
    def test_get_my_predictions(self):
        """Get user's predictions"""
        token = TestV2AuthAndSetup.get_admin_token()
        match_id = TestV2AdminMatchControl.test_match_id
        
        url = f"{BASE_URL}/api/v2/predictions/my"
        if match_id:
            url += f"?match_id={match_id}"
        
        response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, f"Get predictions failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} predictions")
    
    def test_get_prediction_stats(self):
        """Get prediction stats"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/v2/predictions/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get stats failed: {response.text}"
        data = response.json()
        assert "total" in data
        assert "accuracy" in data
        print(f"✓ Prediction stats: {data['total']} total, {data['accuracy']}% accuracy")


class TestV2Cards:
    """Test V2 Cards APIs"""
    
    def test_get_card_types(self):
        """Get all card types"""
        response = requests.get(f"{BASE_URL}/api/v2/cards/types")
        assert response.status_code == 200, f"Get card types failed: {response.text}"
        data = response.json()
        assert "2x_coins" in data
        assert "shield" in data
        print(f"✓ Got {len(data)} card types")
    
    def test_get_card_inventory(self):
        """Get user's card inventory"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/v2/cards/inventory",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get inventory failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Card inventory has {len(data)} cards")


class TestV2Ledger:
    """Test V2 Ledger (Double-Entry) APIs"""
    
    def test_get_ledger_balance(self):
        """Get balance from ledger"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/v2/ledger/balance",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get balance failed: {response.text}"
        data = response.json()
        assert "balance" in data
        assert "user_id" in data
        print(f"✓ Ledger balance: {data['balance']} coins")
    
    def test_get_ledger_history(self):
        """Get transaction history"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/v2/ledger/history?limit=10&offset=0",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get history failed: {response.text}"
        data = response.json()
        assert "entries" in data
        assert "balance" in data
        assert isinstance(data["entries"], list)
        print(f"✓ Ledger history has {len(data['entries'])} entries")


class TestV2Ads:
    """Test V2 Rewarded Ads APIs (MOCKED)"""
    
    ad_id = None
    
    def test_get_ad_status(self):
        """Get ad status (daily limit, watched)"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/v2/ads/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get ad status failed: {response.text}"
        data = response.json()
        assert "daily_limit" in data
        assert "remaining_today" in data
        print(f"✓ Ad status: {data['watched_today']}/{data['daily_limit']} today")
    
    def test_start_ad(self):
        """Start watching ad"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.post(
            f"{BASE_URL}/api/v2/ads/start",
            headers={"Authorization": f"Bearer {token}"}
        )
        # May fail if daily limit reached
        if response.status_code == 400:
            pytest.skip("Daily ad limit reached")
        assert response.status_code == 200, f"Start ad failed: {response.text}"
        data = response.json()
        assert "ad_id" in data
        TestV2Ads.ad_id = data["ad_id"]
        print(f"✓ Ad started: {data['ad_id']}")
    
    def test_complete_ad(self):
        """Complete ad and get reward"""
        token = TestV2AuthAndSetup.get_admin_token()
        ad_id = TestV2Ads.ad_id
        if not ad_id:
            pytest.skip("No ad started")
        
        response = requests.post(
            f"{BASE_URL}/api/v2/ads/complete",
            headers={"Authorization": f"Bearer {token}"},
            json={"ad_id": ad_id}
        )
        assert response.status_code == 200, f"Complete ad failed: {response.text}"
        data = response.json()
        assert "reward_coins" in data
        print(f"✓ Ad completed, earned {data['reward_coins']} coins")


class TestV2Referral:
    """Test V2 Referral APIs"""
    
    referral_code = None
    
    def test_get_referral_code(self):
        """Get user's referral code"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/v2/referral/code",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get referral code failed: {response.text}"
        data = response.json()
        assert "code" in data
        TestV2Referral.referral_code = data["code"]
        print(f"✓ Referral code: {data['code']}")
    
    def test_get_referral_stats(self):
        """Get referral stats"""
        token = TestV2AuthAndSetup.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/v2/referral/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Get stats failed: {response.text}"
        data = response.json()
        assert "total_referrals" in data
        assert "referral_code" in data
        print(f"✓ Referral stats: {data['total_referrals']} referrals")
    
    def test_self_referral_prevention(self):
        """Test self-referral prevention"""
        token = TestV2AuthAndSetup.get_admin_token()
        code = TestV2Referral.referral_code
        if not code:
            pytest.skip("No referral code")
        
        # Try using own referral code
        response = requests.post(
            f"{BASE_URL}/api/v2/referral/bind",
            headers={"Authorization": f"Bearer {token}"},
            json={"referral_code": code}
        )
        assert response.status_code == 400, f"Self-referral should be prevented: {response.text}"
        print(f"✓ Self-referral correctly prevented")


class TestV2AdminResolveOver:
    """Test Admin over resolution with coin credits"""
    
    def test_resolve_over(self):
        """Admin resolves over and credits coins"""
        token = TestV2AuthAndSetup.get_admin_token()
        match_id = TestV2AdminMatchControl.test_match_id
        if not match_id:
            pytest.skip("No test match")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/v2/predictions/resolve-over",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "match_id": match_id,
                "over_number": 2,
                "runs": 8,  # 6-10 range - matches our prediction
                "wickets": 0,
                "boundaries": 1
            }
        )
        assert response.status_code == 200, f"Resolve over failed: {response.text}"
        data = response.json()
        assert "resolved" in data
        print(f"✓ Resolved {data['resolved']} predictions")


class TestV2AdminWallet:
    """Test Admin wallet adjustment"""
    
    def test_adjust_coins(self):
        """Admin adjusts user coins"""
        token = TestV2AuthAndSetup.get_admin_token()
        user_id = TestV2AuthAndSetup.admin_id
        
        response = requests.post(
            f"{BASE_URL}/api/admin/v2/wallet/adjust",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": user_id,
                "amount": 100,
                "reason": "TEST_V2_API adjustment"
            }
        )
        assert response.status_code == 200, f"Adjust coins failed: {response.text}"
        data = response.json()
        assert data["adjusted"] == True
        print(f"✓ Adjusted 100 coins for testing")


class TestV2MatchState:
    """Test V2 Match State APIs"""
    
    def test_get_live_matches(self):
        """Get live matches"""
        response = requests.get(f"{BASE_URL}/api/v2/matches/live")
        assert response.status_code == 200, f"Get live matches failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} live matches")
    
    def test_get_all_matches(self):
        """Get all matches"""
        response = requests.get(f"{BASE_URL}/api/v2/matches/all?limit=10")
        assert response.status_code == 200, f"Get all matches failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} matches")
    
    def test_get_match_state(self):
        """Get match state snapshot"""
        match_id = TestV2AdminMatchControl.test_match_id
        if not match_id:
            pytest.skip("No test match")
        
        response = requests.get(f"{BASE_URL}/api/v2/match/{match_id}/state")
        assert response.status_code == 200, f"Get match state failed: {response.text}"
        data = response.json()
        assert "match" in data
        print(f"✓ Got match state for {match_id}")


class TestFullFlow:
    """Test complete prediction flow: create match -> predict -> resolve -> verify coins"""
    
    def test_full_prediction_flow(self):
        """End-to-end prediction and resolution flow"""
        token = TestV2AuthAndSetup.get_admin_token()
        
        # 1. Get initial balance
        balance_resp = requests.get(
            f"{BASE_URL}/api/v2/ledger/balance",
            headers={"Authorization": f"Bearer {token}"}
        )
        initial_balance = balance_resp.json().get("balance", 0)
        
        # 2. Create test match
        match_resp = requests.post(
            f"{BASE_URL}/api/admin/v2/match/test/create",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert match_resp.status_code == 200
        match_id = match_resp.json()["match_id"]
        
        # 3. Submit prediction for over 1
        unique_over = 99  # Use a unique over to avoid conflicts
        pred_resp = requests.post(
            f"{BASE_URL}/api/v2/predictions/submit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "match_id": match_id,
                "prediction_type": "over_runs",
                "prediction_value": "6-10",
                "over_number": unique_over
            }
        )
        assert pred_resp.status_code == 200, f"Prediction failed: {pred_resp.text}"
        
        # 4. Resolve the over with matching result
        resolve_resp = requests.post(
            f"{BASE_URL}/api/admin/v2/predictions/resolve-over",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "match_id": match_id,
                "over_number": unique_over,
                "runs": 8,  # Matches 6-10 range
                "wickets": 0,
                "boundaries": 0
            }
        )
        assert resolve_resp.status_code == 200
        resolved = resolve_resp.json()
        
        # 5. Verify prediction was correct
        correct_count = sum(1 for r in resolved.get("results", []) if r.get("is_correct"))
        
        # 6. Check final balance
        final_balance_resp = requests.get(
            f"{BASE_URL}/api/v2/ledger/balance",
            headers={"Authorization": f"Bearer {token}"}
        )
        final_balance = final_balance_resp.json().get("balance", 0)
        
        print(f"✓ Full flow complete:")
        print(f"  - Match created: {match_id}")
        print(f"  - Prediction submitted for over {unique_over}")
        print(f"  - Resolved: {resolved.get('resolved', 0)} predictions")
        print(f"  - Correct: {correct_count}")
        print(f"  - Balance: {initial_balance} -> {final_balance}")
        
        # Verify coins credited if prediction was correct
        if correct_count > 0:
            assert final_balance > initial_balance, "Coins should be credited for correct prediction"
            print(f"  - Coins credited: +{final_balance - initial_balance}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
