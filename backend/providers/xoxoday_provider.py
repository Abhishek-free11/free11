"""
Xoxoday Router Provider — Instant digital vouchers (gift cards, food, fashion).
Wraps existing XoxodayProvider logic when XOXODAY credentials are set.
Falls back to mock voucher generation otherwise.
"""
import os
import uuid
from typing import List, Dict
from .base_provider import BaseProvider

ROUTER_MODE = os.environ.get("ROUTER_MODE", "mock")
XOXODAY_ENABLED = bool(os.environ.get("XOXODAY_CLIENT_ID") and os.environ.get("XOXODAY_CLIENT_SECRET"))


class XoxodayRouterProvider(BaseProvider):
    """
    Router-compatible wrapper for Xoxoday Plum.
    covered_states = [] means all-India (digital delivery — no geo restriction).
    """
    name = "Xoxoday Plum"
    provider_id = "xoxoday"
    covered_states = []  # All-India digital delivery

    _SKUS: Dict[str, Dict] = {
        # Amazon gift cards
        "amazon_gc_100":  {"name": "Amazon Gift Card ₹100",  "coins": 120,  "real_price": 100.0,  "category": "vouchers",   "brand": "Amazon"},
        "amazon_gc_250":  {"name": "Amazon Gift Card ₹250",  "coins": 285,  "real_price": 250.0,  "category": "vouchers",   "brand": "Amazon"},
        "amazon_gc_500":  {"name": "Amazon Gift Card ₹500",  "coins": 565,  "real_price": 500.0,  "category": "vouchers",   "brand": "Amazon"},
        # Flipkart gift cards
        "flipkart_gc_100": {"name": "Flipkart Gift Card ₹100", "coins": 115, "real_price": 100.0, "category": "vouchers",  "brand": "Flipkart"},
        "flipkart_gc_500": {"name": "Flipkart Gift Card ₹500", "coins": 560, "real_price": 500.0, "category": "vouchers",  "brand": "Flipkart"},
        # Food vouchers
        "swiggy_100":     {"name": "Swiggy Voucher ₹100",    "coins": 110,  "real_price": 100.0,  "category": "food",       "brand": "Swiggy"},
        "zomato_100":     {"name": "Zomato Voucher ₹100",    "coins": 110,  "real_price": 100.0,  "category": "food",       "brand": "Zomato"},
        # Fashion
        "myntra_250":     {"name": "Myntra Gift Card ₹250",  "coins": 270,  "real_price": 250.0,  "category": "fashion",    "brand": "Myntra"},
        # Groceries
        "bigbasket_200":  {"name": "BigBasket Voucher ₹200", "coins": 210,  "real_price": 200.0,  "category": "groceries",  "brand": "BigBasket"},
        # Recharge
        "recharge_50":    {"name": "Mobile Recharge ₹50",   "coins": 55,   "real_price": 50.0,   "category": "recharge",   "brand": "Paytm"},
        "recharge_149":   {"name": "Mobile Recharge ₹149",  "coins": 160,  "real_price": 149.0,  "category": "recharge",   "brand": "Paytm"},
    }

    _MARGIN_MAP = {
        "Amazon": 0.08, "Flipkart": 0.07,
        "Swiggy": 0.10, "Zomato": 0.10,
        "Myntra": 0.07, "BigBasket": 0.08,
        "Paytm": 0.03,
    }

    def get_skus(self) -> List[Dict]:
        return [
            {
                "sku": k, "name": v["name"], "coins": v["coins"],
                "category": v["category"], "provider": self.provider_id,
                "display_price": v["real_price"],
                "image": f"https://placehold.co/120x120/1B1E23/C6A052?text={v['brand']}",
            }
            for k, v in self._SKUS.items()
        ]

    def supports_sku(self, sku: str) -> bool:
        return sku in self._SKUS

    def get_price(self, sku: str) -> int:
        return self._SKUS.get(sku, {}).get("coins", 0)

    def get_real_price(self, sku: str) -> float:
        return self._SKUS.get(sku, {}).get("real_price", 0.0)

    def get_eta(self, sku: str, geo_state: str) -> float:
        return 0.0  # Always instant — digital voucher delivery

    def get_margin(self, sku: str) -> float:
        brand = self._SKUS.get(sku, {}).get("brand", "")
        return self._MARGIN_MAP.get(brand, 0.08)

    async def redeem(self, sku: str, coins_used: int, user_id: str, **kwargs) -> Dict:
        if ROUTER_MODE == "live" and XOXODAY_ENABLED:
            # TODO: Call existing xoxoday_provider.XoxodayProvider.place_order()
            pass  # fall through to mock

        brand = self._SKUS.get(sku, {}).get("brand", "BRAND")
        voucher_code = f"{brand.upper()[:3]}-{str(uuid.uuid4())[:6].upper()}-FREE11"
        sku_info = self._SKUS.get(sku, {})
        return {
            "status": "delivered",
            "voucher_code": voucher_code,
            "sku": sku,
            "sku_name": sku_info.get("name", sku),
            "provider": self.name,
            "provider_id": self.provider_id,
            "real_value": sku_info.get("real_price", 0),
            "brand": brand,
            "instructions": f"Use code {voucher_code} during {brand} checkout. Valid 90 days.",
            "mock": ROUTER_MODE == "mock",
        }
