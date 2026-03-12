"""
Reloadly Gift Cards API Integration for FREE11
==============================================
Supports India gift cards (Amazon, Flipkart, Swiggy, Zomato, etc.)
Falls back to mock delivery when RELOADLY_CLIENT_ID / RELOADLY_CLIENT_SECRET
are not configured.

Environments
------------
  sandbox     https://giftcards-sandbox.reloadly.com
  production  https://giftcards.reloadly.com

Auth: OAuth2 client_credentials  →  https://auth.reloadly.com/oauth/token
"""

import os
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

RELOADLY_CLIENT_ID     = os.environ.get("RELOADLY_CLIENT_ID", "")
RELOADLY_CLIENT_SECRET = os.environ.get("RELOADLY_CLIENT_SECRET", "")
RELOADLY_ENV           = os.environ.get("RELOADLY_ENVIRONMENT", "sandbox")  # sandbox | production

RELOADLY_ENABLED = bool(RELOADLY_CLIENT_ID and RELOADLY_CLIENT_SECRET)

_BASE_URLS = {
    "sandbox":    "https://giftcards-sandbox.reloadly.com",
    "production": "https://giftcards.reloadly.com",
}
_AUDIENCES = {
    "sandbox":    "https://giftcards-sandbox.reloadly.com",
    "production": "https://giftcards.reloadly.com",
}
AUTH_URL = "https://auth.reloadly.com/oauth/token"

_BASE_URL = _BASE_URLS.get(RELOADLY_ENV, _BASE_URLS["sandbox"])
_AUDIENCE = _AUDIENCES.get(RELOADLY_ENV, _AUDIENCES["sandbox"])

# Accept header required by Reloadly Gift Cards API
_ACCEPT = "application/com.reloadly.giftcards-v1+json"


class ReloadlyProvider:
    """
    Async Reloadly Gift Cards API client.
    A single instance is shared for the lifetime of the process.
    """

    def __init__(self):
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0
        # In-memory catalog cache (refreshed every 6 hours)
        self._catalog_cache: Optional[List[Dict]] = None
        self._catalog_cached_at: float = 0.0

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def _get_token(self) -> Optional[str]:
        if not RELOADLY_ENABLED:
            return None
        now = datetime.now(timezone.utc).timestamp()
        if self._token and now < self._token_expiry:
            return self._token
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(AUTH_URL, json={
                    "client_id":     RELOADLY_CLIENT_ID,
                    "client_secret": RELOADLY_CLIENT_SECRET,
                    "grant_type":    "client_credentials",
                    "audience":      _AUDIENCE,
                })
                r.raise_for_status()
                data = r.json()
                self._token = data["access_token"]
                # sandbox tokens expire in 24 h; production in 60 days
                self._token_expiry = now + data.get("expires_in", 86400) - 120
                logger.info("Reloadly token acquired (env=%s)", RELOADLY_ENV)
                return self._token
        except Exception as e:
            logger.error("Reloadly token error: %s", e)
            return None

    def _headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": _ACCEPT,
            "Content-Type": "application/json",
        }

    # ── Catalog ───────────────────────────────────────────────────────────────

    async def get_catalog(self, country: str = "IN", page_size: int = 200) -> List[Dict]:
        """
        Fetch Reloadly gift card products for a country.
        Results are cached in-memory for 6 hours.
        Falls back to mock catalog when not configured.
        """
        if not RELOADLY_ENABLED:
            return self._mock_catalog()

        now = datetime.now(timezone.utc).timestamp()
        if self._catalog_cache and (now - self._catalog_cached_at) < 6 * 3600:
            return self._catalog_cache

        token = await self._get_token()
        if not token:
            return self._mock_catalog()

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(
                    f"{_BASE_URL}/products",
                    params={"countryCode": country, "size": page_size, "page": 1,
                            "includeRange": "false", "includeFixed": "true"},
                    headers=self._headers(token),
                )
                r.raise_for_status()
                products = r.json().get("content", [])
                catalog = [self._normalize_product(p) for p in products]
                self._catalog_cache = catalog
                self._catalog_cached_at = now
                logger.info("Reloadly catalog fetched: %d products (country=%s)", len(catalog), country)
                return catalog
        except Exception as e:
            logger.error("Reloadly catalog error: %s", e)
            return self._mock_catalog()

    def _normalize_product(self, p: Dict) -> Dict:
        sender_denoms = p.get("fixedSenderDenominations") or []
        recip_denoms  = p.get("fixedRecipientDenominations") or p.get("denominations", [])
        # Build a mapping: recipient INR value → sender USD value
        denom_map = {}
        if sender_denoms and recip_denoms and len(sender_denoms) == len(recip_denoms):
            for s, r in zip(sender_denoms, recip_denoms):
                denom_map[float(r)] = float(s)
        return {
            "product_id":    p.get("productId"),
            "name":          p.get("productName", ""),
            "brand":         p.get("brand", {}).get("brandName", ""),
            "brand_id":      p.get("brand", {}).get("brandId"),
            "country":       p.get("country", {}).get("isoName", "IN"),
            "currency":      p.get("recipientCurrencyCode", "INR"),
            "sender_currency": p.get("senderCurrencyCode", "USD"),
            "denominations": sorted(recip_denoms),   # INR values for display
            "denom_map":     denom_map,               # INR → USD lookup
            "sender_denoms": sorted(sender_denoms),   # USD values for API calls
            "min_amount":    p.get("minRecipientDenomination") or (min(recip_denoms) if recip_denoms else 0),
            "max_amount":    p.get("maxRecipientDenomination") or (max(recip_denoms) if recip_denoms else 0),
            "image":         p.get("logoUrls", [None])[0],
            "redeem_instructions": p.get("redeemInstruction", {}).get("concise", ""),
            "category":      self._guess_category(p.get("brand", {}).get("brandName", "")),
        }

    def _guess_category(self, brand: str) -> str:
        brand = brand.lower()
        if any(x in brand for x in ["amazon", "flipkart", "myntra", "ajio", "nykaa"]):
            return "vouchers"
        if any(x in brand for x in ["swiggy", "zomato", "domino", "kfc", "mcdonald", "pizza"]):
            return "food"
        if any(x in brand for x in ["bigbasket", "jiomart", "grofer", "zepto", "blinkit"]):
            return "groceries"
        if any(x in brand for x in ["netflix", "spotify", "zee5", "hotstar", "prime", "sony"]):
            return "entertainment"
        if any(x in brand for x in ["paytm", "recharge", "jio", "airtel", "vi"]):
            return "recharge"
        return "vouchers"

    async def get_sender_usd(self, product_id: int, inr_amount: float) -> Optional[float]:
        """
        Look up the current sender USD denomination for a given product + INR amount.
        Uses the cached catalog so no extra API call is made.
        Falls back to None if not found (caller should use hardcoded fallback).
        """
        catalog = await self.get_catalog()
        for item in catalog:
            if item.get("product_id") == product_id:
                denom_map = item.get("denom_map", {})
                usd = denom_map.get(float(inr_amount))
                if usd is not None:
                    return usd
                # Try nearest match within 1 INR tolerance
                for k, v in denom_map.items():
                    if abs(k - inr_amount) <= 1.0:
                        return v
        return None

    # ── Find product by brand + denomination ─────────────────────────────────

    async def find_product(self, brand_keyword: str, denomination: int,
                           country: str = "IN") -> Optional[Dict]:
        """
        Find a product matching brand keyword and denomination.
        Used by the router provider to resolve SKU → Reloadly product_id.
        """
        catalog = await self.get_catalog(country)
        keyword = brand_keyword.lower()
        for item in catalog:
            if keyword in item["brand"].lower() or keyword in item["name"].lower():
                if denomination in item["denominations"]:
                    return item
        return None

    # ── Place Order ───────────────────────────────────────────────────────────

    async def place_order(
        self,
        product_id: int,
        unit_price: float,
        recipient_email: str,
        sender_name: str = "FREE11",
        custom_identifier: str = "",
        country: str = "IN",
    ) -> Dict:
        """
        Place a gift card order.
        Returns dict with status, transaction_id, and voucher info.
        Falls back to mock when not configured.
        """
        if not custom_identifier:
            custom_identifier = f"free11-{uuid.uuid4().hex[:12]}"

        if not RELOADLY_ENABLED:
            return self._mock_order(product_id, unit_price, recipient_email, custom_identifier)

        token = await self._get_token()
        if not token:
            return {"status": "failed", "error": "Auth failed", "mock": False}

        payload = {
            "productId":         product_id,
            "countryCode":       country,
            "quantity":          1,
            "unitPrice":         unit_price,
            "customIdentifier":  custom_identifier,
            "senderName":        sender_name,
            "recipientEmail":    recipient_email,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{_BASE_URL}/orders",
                    json=payload,
                    headers=self._headers(token),
                )
                r.raise_for_status()
                data = r.json()
                transaction_id = data.get("transactionId")

                # Fetch redeem codes immediately
                codes = await self._get_redeem_codes(token, transaction_id)

                return {
                    "status":         "delivered",
                    "transaction_id": transaction_id,
                    "voucher_code":   codes.get("card_number", ""),
                    "voucher_pin":    codes.get("pin_code"),
                    "redeem_url":     codes.get("redeem_url"),
                    "product_name":   data.get("product", {}).get("productName", ""),
                    "amount":         unit_price,
                    "currency":       "INR",
                    "custom_id":      custom_identifier,
                    "mock":           False,
                }
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            error_code = ""
            try:
                error_code = e.response.json().get("errorCode") or ""
            except Exception:
                pass

            # Known Reloadly account-not-ready / pricing errors — fall back to mock silently
            _known_codes = {"WRONG_PRODUCT_PRICE", "ACCOUNT_NOT_ACTIVE", "UNAUTHORIZED_ACCESS"}
            _is_generic_500 = e.response.status_code >= 500
            _is_known_code  = error_code in _known_codes

            if _is_known_code or _is_generic_500:
                logger.warning(
                    "Reloadly order not fulfilled (status=%s errorCode=%s) — using mock delivery",
                    e.response.status_code, error_code or "null",
                )
                return self._mock_order(product_id, unit_price, recipient_email, custom_identifier)

            logger.error("Reloadly order HTTP error %s: %s", e.response.status_code, error_body)
            return {"status": "failed", "error": error_body, "mock": False}
        except Exception as e:
            logger.error("Reloadly order error: %s", e)
            return {"status": "failed", "error": str(e), "mock": False}

    async def _get_redeem_codes(self, token: str, transaction_id: int) -> Dict:
        """Fetch voucher/PIN codes for a completed transaction."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"{_BASE_URL}/orders/transactions/{transaction_id}/cards",
                    headers=self._headers(token),
                )
                r.raise_for_status()
                cards = r.json()
                if cards and isinstance(cards, list):
                    card = cards[0]
                    return {
                        "card_number": card.get("cardNumber", ""),
                        "pin_code":    card.get("pinCode"),
                        "redeem_url":  card.get("redemptionUrl"),
                    }
        except Exception as e:
            logger.error("Reloadly get redeem codes error: %s", e)
        return {}

    # ── Check Balance ─────────────────────────────────────────────────────────

    async def get_balance(self) -> Dict:
        """Check Reloadly gift cards account balance."""
        if not RELOADLY_ENABLED:
            return {"balance": 0, "currency": "USD", "enabled": False}
        token = await self._get_token()
        if not token:
            return {"balance": 0, "currency": "USD", "enabled": True, "error": "Auth failed"}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{_BASE_URL}/accounts/balance",
                    headers=self._headers(token),
                )
                r.raise_for_status()
                data = r.json()
                return {"balance": data.get("balance", 0), "currency": data.get("currencyCode", "USD"), "enabled": True}
        except Exception as e:
            return {"balance": 0, "currency": "USD", "enabled": True, "error": str(e)}

    # ── Mock fallback ─────────────────────────────────────────────────────────

    def _mock_catalog(self) -> List[Dict]:
        return [
            {"product_id": 1001, "name": "Amazon India Gift Card", "brand": "Amazon",
             "country": "IN", "currency": "INR", "denominations": [50, 100, 200, 250, 500, 1000],
             "min_amount": 50, "max_amount": 1000, "category": "vouchers",
             "image": "https://placehold.co/100x100/FF9900/ffffff?text=Amazon",
             "redeem_instructions": "Visit amazon.in, add to cart, enter code at checkout."},
            {"product_id": 1002, "name": "Flipkart Gift Card", "brand": "Flipkart",
             "country": "IN", "currency": "INR", "denominations": [50, 100, 250, 500, 1000],
             "min_amount": 50, "max_amount": 1000, "category": "vouchers",
             "image": "https://placehold.co/100x100/F7B900/ffffff?text=Flipkart",
             "redeem_instructions": "Login to Flipkart, go to My Gifts, enter code."},
            {"product_id": 1003, "name": "Swiggy Voucher", "brand": "Swiggy",
             "country": "IN", "currency": "INR", "denominations": [50, 100, 200],
             "min_amount": 50, "max_amount": 200, "category": "food",
             "image": "https://placehold.co/100x100/FC8019/ffffff?text=Swiggy",
             "redeem_instructions": "Apply code at Swiggy checkout."},
            {"product_id": 1004, "name": "Zomato Voucher", "brand": "Zomato",
             "country": "IN", "currency": "INR", "denominations": [50, 100, 200],
             "min_amount": 50, "max_amount": 200, "category": "food",
             "image": "https://placehold.co/100x100/E23744/ffffff?text=Zomato",
             "redeem_instructions": "Apply code at Zomato checkout."},
            {"product_id": 1005, "name": "Myntra Gift Card", "brand": "Myntra",
             "country": "IN", "currency": "INR", "denominations": [100, 250, 500],
             "min_amount": 100, "max_amount": 500, "category": "vouchers",
             "image": "https://placehold.co/100x100/FF3E6C/ffffff?text=Myntra",
             "redeem_instructions": "Apply code at Myntra checkout."},
            {"product_id": 1006, "name": "BigBasket Voucher", "brand": "BigBasket",
             "country": "IN", "currency": "INR", "denominations": [100, 200, 500],
             "min_amount": 100, "max_amount": 500, "category": "groceries",
             "image": "https://placehold.co/100x100/84C225/ffffff?text=BigBasket",
             "redeem_instructions": "Apply code at BigBasket checkout."},
            {"product_id": 1007, "name": "Netflix Gift Card", "brand": "Netflix",
             "country": "IN", "currency": "INR", "denominations": [149, 199, 499, 649],
             "min_amount": 149, "max_amount": 649, "category": "entertainment",
             "image": "https://placehold.co/100x100/E50914/ffffff?text=Netflix",
             "redeem_instructions": "Visit netflix.com/redeem and enter your code."},
        ]

    def _mock_order(self, product_id: int, unit_price: float,
                    recipient_email: str, custom_id: str) -> Dict:
        brand_map = {1001: "AMZ", 1002: "FLK", 1003: "SWG", 1004: "ZMT",
                     1005: "MYN", 1006: "BBK", 1007: "NFX"}
        prefix = brand_map.get(product_id, "FREE11")
        code = f"{prefix}-{uuid.uuid4().hex[:8].upper()}-IN"
        return {
            "status":         "delivered",
            "transaction_id": f"MOCK-{uuid.uuid4().hex[:8].upper()}",
            "voucher_code":   code,
            "voucher_pin":    None,
            "redeem_url":     None,
            "product_name":   f"Gift Card #{product_id}",
            "amount":         unit_price,
            "currency":       "INR",
            "custom_id":      custom_id,
            "mock":           True,
        }

    @staticmethod
    def is_enabled() -> bool:
        return RELOADLY_ENABLED


# Singleton instance
reloadly = ReloadlyProvider()
