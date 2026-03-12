"""
Reloadly Router Provider for FREE11 Smart Commerce Router.
Wraps the ReloadlyProvider (main API client) as a pluggable BaseProvider.
Covered states = [] → all-India digital delivery.
"""

import uuid
import os
from typing import List, Dict
from .base_provider import BaseProvider

ROUTER_MODE = os.environ.get("ROUTER_MODE", "mock")


class ReloadlyRouterProvider(BaseProvider):
    """
    Router-compatible wrapper for Reloadly Gift Cards.
    SKUs mirror Xoxoday's naming so the router can compare both providers.
    Actual Reloadly product IDs are resolved at order time via catalog lookup.
    """

    name = "Reloadly"
    provider_id = "reloadly"
    covered_states = []  # All-India digital delivery

    # SKU map with REAL Reloadly production product IDs + USD sender denominations
    # Only includes products with real INR pricing (Flipkart, Uber, Steam)
    # Gaming vouchers (PUBG/Razer/Free Fire) are USD-priced globally — kept separate
    _SKUS: Dict[str, Dict] = {
        # LIVE - Global Prepaid Cards via Swype (USD range, works worldwide incl. India)
        # These are CONFIRMED LIVE on this Reloadly account (tested March 2026)
        "swype_mc_5":   {"name": "Prepaid Mastercard $5",   "brand": "Mastercard", "product_id": 20312, "usd": 5.0,   "sender_usd": 5.0,   "coins":  420, "category": "prepaid",  "margin": 0.02, "denom_type": "range", "country_code": "US"},
        "swype_mc_10":  {"name": "Prepaid Mastercard $10",  "brand": "Mastercard", "product_id": 20312, "usd": 10.0,  "sender_usd": 10.0,  "coins":  840, "category": "prepaid",  "margin": 0.02, "denom_type": "range", "country_code": "US"},
        "swype_mc_25":  {"name": "Prepaid Mastercard $25",  "brand": "Mastercard", "product_id": 20312, "usd": 25.0,  "sender_usd": 25.0,  "coins": 2100, "category": "prepaid",  "margin": 0.02, "denom_type": "range", "country_code": "US"},
        "swype_mc_50":  {"name": "Prepaid Mastercard $50",  "brand": "Mastercard", "product_id": 20312, "usd": 50.0,  "sender_usd": 50.0,  "coins": 4200, "category": "prepaid",  "margin": 0.02, "denom_type": "range", "country_code": "US"},
        "swype_visa_5": {"name": "Prepaid Visa $5",         "brand": "Visa",       "product_id": 20491, "usd": 5.0,   "sender_usd": 5.0,   "coins":  420, "category": "prepaid",  "margin": 0.02, "denom_type": "range", "country_code": "IN"},
        "swype_visa_10":{"name": "Prepaid Visa $10",        "brand": "Visa",       "product_id": 20491, "usd": 10.0,  "sender_usd": 10.0,  "coins":  840, "category": "prepaid",  "margin": 0.02, "denom_type": "range", "country_code": "IN"},
        # Gaming — Razer Gold (USD, CONFIRMED active in IN catalogue)
        "razer_5":      {"name": "Razer Gold $5",           "brand": "Razer Gold", "product_id": 10222, "usd": 5.0,   "sender_usd": 5.0,   "coins":  420, "category": "gaming",   "margin": 0.05, "denom_type": "fixed", "country_code": "IN"},
        "razer_10":     {"name": "Razer Gold $10",          "brand": "Razer Gold", "product_id": 10222, "usd": 10.0,  "sender_usd": 10.0,  "coins":  840, "category": "gaming",   "margin": 0.05, "denom_type": "fixed", "country_code": "IN"},
        "razer_20":     {"name": "Razer Gold $20",          "brand": "Razer Gold", "product_id": 10222, "usd": 20.0,  "sender_usd": 20.0,  "coins": 1680, "category": "gaming",   "margin": 0.05, "denom_type": "fixed", "country_code": "IN"},
        # Shopping — Flipkart INR (pending Reloadly brand permission — falls back to mock)
        "flipkart_gc_50":   {"name": "Flipkart Gift Card ₹50",  "brand": "Flipkart", "product_id": 18678, "inr": 50.0,   "sender_usd": 0.60,  "coins":  55, "category": "vouchers",   "margin": 0.07, "denom_type": "fixed", "country_code": "IN"},
        "flipkart_gc_100":  {"name": "Flipkart Gift Card ₹100", "brand": "Flipkart", "product_id": 18678, "inr": 100.0,  "sender_usd": 1.21,  "coins": 110, "category": "vouchers",   "margin": 0.07, "denom_type": "fixed", "country_code": "IN"},
        "flipkart_gc_250":  {"name": "Flipkart Gift Card ₹250", "brand": "Flipkart", "product_id": 18678, "inr": 250.0,  "sender_usd": 3.02,  "coins": 270, "category": "vouchers",   "margin": 0.07, "denom_type": "fixed", "country_code": "IN"},
        "flipkart_gc_500":  {"name": "Flipkart Gift Card ₹500", "brand": "Flipkart", "product_id": 18678, "inr": 500.0,  "sender_usd": 6.05,  "coins": 540, "category": "vouchers",   "margin": 0.07, "denom_type": "fixed", "country_code": "IN"},
        # Transport — Uber INR (pending Reloadly brand permission — falls back to mock)
        "uber_100":         {"name": "Uber Voucher ₹100",       "brand": "Uber",     "product_id": 18677, "inr": 100.0,  "sender_usd": 1.21,  "coins": 108, "category": "transport",  "margin": 0.08, "denom_type": "fixed", "country_code": "IN"},
        "uber_250":         {"name": "Uber Voucher ₹250",       "brand": "Uber",     "product_id": 18677, "inr": 250.0,  "sender_usd": 3.02,  "coins": 265, "category": "transport",  "margin": 0.08, "denom_type": "fixed", "country_code": "IN"},
        "uber_500":         {"name": "Uber Voucher ₹500",       "brand": "Uber",     "product_id": 18677, "inr": 500.0,  "sender_usd": 6.05,  "coins": 530, "category": "transport",  "margin": 0.08, "denom_type": "fixed", "country_code": "IN"},
        # Gaming — Steam INR (pending Reloadly brand permission — falls back to mock)
        "steam_150":        {"name": "Steam Wallet ₹150",       "brand": "Steam",    "product_id": 15714, "inr": 150.0,  "sender_usd": 1.81,  "coins": 160, "category": "gaming",     "margin": 0.05, "denom_type": "fixed", "country_code": "IN"},
        "steam_250":        {"name": "Steam Wallet ₹250",       "brand": "Steam",    "product_id": 15714, "inr": 250.0,  "sender_usd": 3.02,  "coins": 265, "category": "gaming",     "margin": 0.05, "denom_type": "fixed", "country_code": "IN"},
        "steam_500":        {"name": "Steam Wallet ₹500",       "brand": "Steam",    "product_id": 15714, "inr": 500.0,  "sender_usd": 6.05,  "coins": 530, "category": "gaming",     "margin": 0.05, "denom_type": "fixed", "country_code": "IN"},
    }

    # Convenience aliases used by the legacy Xoxoday SKU set
    _SKU_ALIASES = {
        "amazon_gc_100":   "flipkart_gc_100",
        "amazon_gc_250":   "flipkart_gc_250",
        "amazon_gc_500":   "flipkart_gc_500",
        "flipkart_gc_100": "flipkart_gc_100",
        "flipkart_gc_500": "flipkart_gc_500",
    }

    def get_skus(self) -> List[Dict]:
        result = []
        for k, v in self._SKUS.items():
            # Swype USD cards: show dollar price; INR cards: show rupee price
            if v.get("denom_type") == "range":
                display_price = v.get("usd", 0)
                display_label = f"${display_price:.0f}"
            else:
                display_price = v.get("inr", 0)
                display_label = f"₹{display_price:.0f}"
            result.append({
                "sku":           k,
                "name":          v["name"],
                "coins":         v["coins"],
                "category":      v["category"],
                "provider":      self.provider_id,
                "display_price": display_price,
                "display_label": display_label,
                "image":         f"https://placehold.co/120x120/1B1E23/C6A052?text={v['brand']}",
            })
        return result

    def supports_sku(self, sku: str) -> bool:
        return sku in self._SKUS or sku in self._SKU_ALIASES

    def _resolve_sku(self, sku: str) -> Dict:
        resolved = self._SKU_ALIASES.get(sku, sku)
        return self._SKUS.get(resolved, {})

    def get_price(self, sku: str) -> int:
        return self._resolve_sku(sku).get("coins", 0)

    def get_real_price(self, sku: str) -> float:
        info = self._resolve_sku(sku)
        return info.get("usd", info.get("inr", 0.0))

    def get_eta(self, sku: str, geo_state: str) -> float:
        return 0.0

    def get_margin(self, sku: str) -> float:
        return self._resolve_sku(sku).get("margin", 0.07)

    async def redeem(self, sku: str, coins_used: int, user_id: str, **kwargs) -> Dict:
        """
        Place order via Reloadly.
        - USD range products (Swype cards): send sender_usd directly
        - INR fixed products (Flipkart, Uber, Steam): fetch live sender_usd from catalog
        """
        from reloadly_provider import reloadly

        info         = self._resolve_sku(sku)
        brand        = info.get("brand", "Reloadly")
        product_id   = info.get("product_id", 20312)
        country_code = info.get("country_code", "IN")
        denom_type   = info.get("denom_type", "fixed")
        user_email   = kwargs.get("user_email", "rewards@free11.com")
        custom_id    = f"free11-{user_id[:8]}-{uuid.uuid4().hex[:6]}"

        if denom_type == "range":
            # USD range products — use usd value directly as unitPrice
            sender_usd = info.get("usd", 5.0)
            display_value = f"${sender_usd:.0f}"
        else:
            # INR fixed products — fetch live sender_usd from catalog
            inr_value = info.get("inr", 100.0)
            display_value = f"₹{inr_value:.0f}"
            sender_usd = await reloadly.get_sender_usd(product_id, inr_value)
            if sender_usd is None:
                sender_usd = info.get("sender_usd", 1.21)
                logger.warning("Reloadly: could not resolve live sender_usd for %s, using fallback %s", sku, sender_usd)

        result = await reloadly.place_order(
            product_id=product_id,
            unit_price=sender_usd,
            recipient_email=user_email,
            sender_name="FREE11 Rewards",
            custom_identifier=custom_id,
            country=country_code,
        )

        # Build user-friendly instructions
        if denom_type == "range":
            instructions = (
                f"Your ${info.get('usd', 0):.0f} prepaid {brand} card has been delivered to {user_email}. "
                "Activate via the link in your email. Works anywhere Mastercard/Visa is accepted."
            )
        else:
            instructions = f"Use code during {brand} checkout. Valid 90 days."

        return {
            "status":       result.get("status", "failed"),
            "voucher_code": result.get("voucher_code", ""),
            "voucher_pin":  result.get("voucher_pin"),
            "sku":          sku,
            "sku_name":     info.get("name", sku),
            "provider":     self.name,
            "provider_id":  self.provider_id,
            "real_value":   display_value,
            "brand":        brand,
            "mock":         result.get("mock", False),
            "instructions": instructions,
        }
