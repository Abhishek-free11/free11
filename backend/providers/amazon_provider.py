"""
Amazon Affiliate Provider — Electronics & Lifestyle.
Redeem = generate affiliate deep-link, user redirects to Amazon.
Real API: Amazon Associates / Creators API (swap in with tag + secret).
"""
import os
import uuid
from typing import List, Dict
from .base_provider import BaseProvider

ROUTER_MODE = os.environ.get("ROUTER_MODE", "mock")
AMAZON_AFFILIATE_TAG = os.environ.get("AMAZON_AFFILIATE_TAG", "free11-21")


class AmazonProvider(BaseProvider):
    name = "Amazon"
    provider_id = "amazon"
    covered_states = []  # All-India (redirect / digital)

    _SKUS: Dict[str, Dict] = {
        "earbuds_basic": {
            "name": "True Wireless Earbuds",
            "coins": 799, "real_price": 799.0, "category": "electronics",
            "asin": "B08B3S2L1Q",
            "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200",
        },
        "usb_cable": {
            "name": "USB-C Braided Cable 6ft",
            "coins": 599, "real_price": 599.0, "category": "electronics",
            "asin": "B07D3BFN2R",
            "image": "https://images.unsplash.com/photo-1588591795084-1770cb3be374?w=200",
        },
        "phone_case": {
            "name": "Premium Slim Phone Case",
            "coins": 349, "real_price": 349.0, "category": "electronics",
            "asin": "B09NCBZRGF",
            "image": "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=200",
        },
        "water_bottle": {
            "name": "Stainless Steel Water Bottle 750ml",
            "coins": 499, "real_price": 499.0, "category": "lifestyle",
            "asin": "B076SXYK6P",
            "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=200",
        },
        "yoga_mat": {
            "name": "Premium Yoga Mat 6mm",
            "coins": 699, "real_price": 699.0, "category": "lifestyle",
            "asin": "B07WL5WHFK",
            "image": "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=200",
        },
        "ipl_jersey": {
            "name": "Cricket Team Fan Jersey",
            "coins": 899, "real_price": 899.0, "category": "fashion",
            "asin": "B09D6RCDHG",
            "image": "https://images.unsplash.com/photo-1620280767577-29c5b0e2ad30?w=200",
        },
    }

    def get_skus(self) -> List[Dict]:
        return [
            {
                "sku": k, "name": v["name"], "coins": v["coins"],
                "category": v["category"], "provider": self.provider_id,
                "display_price": v["real_price"], "image": v.get("image", ""),
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
        return 0.0  # Instant affiliate redirect

    def get_margin(self, sku: str) -> float:
        return 0.05  # ~5% Amazon affiliate commission

    async def redeem(self, sku: str, coins_used: int, user_id: str, **kwargs) -> Dict:
        sku_info = self._SKUS.get(sku, {})
        asin = sku_info.get("asin", "")
        tag = AMAZON_AFFILIATE_TAG

        if ROUTER_MODE == "live" and asin:
            # TODO: Optionally use Amazon PA-API to fetch live price + generate link
            redirect_url = f"https://www.amazon.in/dp/{asin}?tag={tag}&ref=free11"
        else:
            redirect_url = (
                f"https://www.amazon.in/dp/{asin}?tag={tag}&ref=free11_mock"
                if asin else f"https://www.amazon.in/?tag={tag}"
            )

        return {
            "status": "redirect",
            "redirect_url": redirect_url,
            "sku": sku,
            "sku_name": sku_info.get("name", sku),
            "provider": self.name,
            "provider_id": self.provider_id,
            "note": "You'll be redirected to Amazon. FREE11 earns a small affiliate commission — no extra cost to you.",
            "mock": ROUTER_MODE == "mock",
        }
