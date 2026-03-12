"""
Test Wallet History Feature (FREE11 Transaction History)
Tests: GET /api/v2/payments/history - returns free_bucks_purchases and coin_transactions
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@free11.com"
ADMIN_PASSWORD = "Admin@123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("token") or data.get("access_token")
        print(f"Auth token obtained for {ADMIN_EMAIL}")
        return token
    pytest.skip(f"Authentication failed with status {response.status_code}: {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Authorization headers with Bearer token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestWalletHistoryAuth:
    """Test authentication requirements for wallet history endpoint"""

    def test_wallet_history_requires_auth(self):
        """GET /api/v2/payments/history should return 401 without auth token"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history")
        assert response.status_code == 401, (
            f"Expected 401 without auth, got {response.status_code}: {response.text}"
        )
        print(f"PASS: /api/v2/payments/history returns 401 without auth token")

    def test_wallet_history_with_invalid_token(self):
        """GET /api/v2/payments/history should return 401 with invalid token"""
        response = requests.get(
            f"{BASE_URL}/api/v2/payments/history",
            headers={"Authorization": "Bearer invalidtoken123"}
        )
        assert response.status_code == 401, (
            f"Expected 401 with invalid token, got {response.status_code}"
        )
        print("PASS: /api/v2/payments/history returns 401 with invalid token")


class TestWalletHistoryResponse:
    """Test the response structure of wallet history endpoint"""

    def test_wallet_history_returns_200(self, auth_headers):
        """GET /api/v2/payments/history should return 200 with valid auth"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        print("PASS: /api/v2/payments/history returns 200 with valid auth")

    def test_wallet_history_returns_both_arrays(self, auth_headers):
        """GET /api/v2/payments/history should return free_bucks_purchases and coin_transactions"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert "free_bucks_purchases" in data, (
            f"Response missing 'free_bucks_purchases' key. Keys: {list(data.keys())}"
        )
        assert "coin_transactions" in data, (
            f"Response missing 'coin_transactions' key. Keys: {list(data.keys())}"
        )
        print(f"PASS: Response contains both arrays - "
              f"free_bucks_purchases: {len(data['free_bucks_purchases'])}, "
              f"coin_transactions: {len(data['coin_transactions'])}")

    def test_free_bucks_purchases_is_list(self, auth_headers):
        """free_bucks_purchases should be a list (even if empty)"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        assert isinstance(data["free_bucks_purchases"], list), (
            f"free_bucks_purchases should be a list, got {type(data['free_bucks_purchases'])}"
        )
        print(f"PASS: free_bucks_purchases is a list with {len(data['free_bucks_purchases'])} items")

    def test_coin_transactions_is_list(self, auth_headers):
        """coin_transactions should be a list (even if empty)"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        assert isinstance(data["coin_transactions"], list), (
            f"coin_transactions should be a list, got {type(data['coin_transactions'])}"
        )
        print(f"PASS: coin_transactions is a list with {len(data['coin_transactions'])} items")

    def test_no_mongodb_id_in_response(self, auth_headers):
        """Response should not contain MongoDB _id fields"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()

        for purchase in data.get("free_bucks_purchases", []):
            assert "_id" not in purchase, f"Purchase contains _id: {purchase}"

        for txn in data.get("coin_transactions", []):
            assert "_id" not in txn, f"Coin transaction contains _id: {txn}"

        print("PASS: No MongoDB _id fields in response")


class TestWalletHistoryPurchaseStructure:
    """Test the structure of free_bucks_purchases entries"""

    def test_purchase_fields_when_present(self, auth_headers):
        """If purchases exist, validate their field structure"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        purchases = data.get("free_bucks_purchases", [])

        if not purchases:
            pytest.skip("No purchase records to validate (user has no purchases)")

        for i, p in enumerate(purchases[:3]):  # Check first 3 entries
            # These fields should be projected in the query
            assert "amount" in p, f"Purchase[{i}] missing 'amount'"
            assert "payment_status" in p, f"Purchase[{i}] missing 'payment_status'"
            print(f"PASS: Purchase[{i}] has valid structure: amount={p.get('amount')}, status={p.get('payment_status')}")

    def test_purchase_payment_status_values(self, auth_headers):
        """Payment status should be 'paid', 'pending', or similar"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        purchases = data.get("free_bucks_purchases", [])

        if not purchases:
            pytest.skip("No purchase records to validate (user has no purchases)")

        valid_statuses = {'paid', 'pending', 'failed', 'refunded', 'created', 'initiated'}
        for p in purchases:
            status = p.get("payment_status", "").lower()
            assert status in valid_statuses, f"Unexpected payment_status: {status}"
        print(f"PASS: All purchase payment_status values are valid")


class TestWalletHistoryCoinTxnStructure:
    """Test the structure of coin_transactions entries"""

    def test_coin_txn_fields_when_present(self, auth_headers):
        """If coin transactions exist, validate their field structure"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        coin_txns = data.get("coin_transactions", [])

        if not coin_txns:
            pytest.skip("No coin transaction records to validate")

        for i, txn in enumerate(coin_txns[:3]):  # Check first 3 entries
            # At least one of: credit/debit, amount, or description should be present
            has_amount_info = (
                txn.get("credit") is not None or
                txn.get("debit") is not None or
                txn.get("amount") is not None or
                txn.get("description") is not None
            )
            assert has_amount_info, f"Coin txn[{i}] has no amount info: {txn}"
            print(f"PASS: Coin txn[{i}] has amount info - "
                  f"credit={txn.get('credit')}, debit={txn.get('debit')}, amount={txn.get('amount')}")

    def test_coin_txn_has_type_or_description(self, auth_headers):
        """Coin transactions should have type or description for display"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        coin_txns = data.get("coin_transactions", [])

        if not coin_txns:
            pytest.skip("No coin transaction records to validate")

        for i, txn in enumerate(coin_txns[:5]):
            has_label = txn.get("type") or txn.get("description")
            assert has_label, f"Coin txn[{i}] has no type or description: {txn}"
        print("PASS: All coin transactions have type or description")

    def test_coin_txn_has_timestamp(self, auth_headers):
        """Coin transactions should have timestamps"""
        response = requests.get(f"{BASE_URL}/api/v2/payments/history", headers=auth_headers)
        data = response.json()
        coin_txns = data.get("coin_transactions", [])

        if not coin_txns:
            pytest.skip("No coin transaction records to validate")

        for i, txn in enumerate(coin_txns[:3]):
            assert "timestamp" in txn, f"Coin txn[{i}] missing 'timestamp': {txn}"
        print("PASS: All coin transactions have timestamps")
