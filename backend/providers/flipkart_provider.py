"""
Flipkart Affiliate Provider — Fashion & Electronics.
Redeem = generate affiliate deep-link, user redirects to Flipkart.
Real API: Flipkart Affiliate API (swap in with affiliate_id + token).
"""
import os
from typing import List, Dict
from .base_provider import BaseProvider

ROUTER_MODE = os.environ.get("ROUTER_MODE", "mock")
FLIPKART_AFFILIATE_ID = os.environ.get("FLIPKART_AFFILIATE_ID", "free11")


class FlipkartProvider(BaseProvider):
    name = "Flipkart"
    provider_id = "flipkart"
    covered_states = []  # All-India (redirect / digital)

    _SKUS: Dict[str, Dict] = {
        "tshirt_basic": {
            "name": "Premium Cotton T-Shirt",
            "coins": 499, "real_price": 499.0, "category": "fashion",
            "pid": "TSHGXF73GVKBDPKX",
            "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=200",
        },
        "jeans_basic": {
            "name": "Classic Slim Fit Jeans",
            "coins": 899, "real_price": 899.0, "category": "fashion",
            "pid": "JNSFXP4GZZHQYDQN",
            "image": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=200",
        },
        "sport_shoes": {
            "name": "Professional Running Shoes",
            "coins": 1199, "real_price": 1199.0, "category": "fashion",
            "pid": "SHOGH9ZFTXDQNQCC",
            "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200",
        },
        "smartwatch": {
            "name": "Smart Fitness Watch",
            "coins": 2499, "real_price": 2499.0, "category": "electronics",
            "pid": "SMWGXGAEYTZGYQDB",
            "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=200",
        },
        "headphones": {
            "name": "Wireless Over-Ear Headphones",
            "coins": 1499, "real_price": 1499.0, "category": "electronics",
            "pid": "HPHMG2BKBXRJPZQE",
            "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=200",
        },
        "cricket_bat": {
            "name": "Professional Cricket Bat",
            "coins": 1299, "real_price": 1299.0, "category": "lifestyle",
            "pid": "BATGSF3KBNHQZPLT",
            "image": "https://images.unsplash.com/photo-1540747913346-19212a4b32a6?w=200",
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
        return 0.06  # ~6% Flipkart affiliate commission

    async def redeem(self, sku: str, coins_used: int, user_id: str, **kwargs) -> Dict:
        sku_info = self._SKUS.get(sku, {})
        pid = sku_info.get("pid", "")
        aff_id = FLIPKART_AFFILIATE_ID

        if ROUTER_MODE == "live" and pid:
            redirect_url = f"https://www.flipkart.com/product/p/item?pid={pid}&affid={aff_id}"
        else:
            redirect_url = (
                f"https://www.flipkart.com/product/p/item?pid={pid}&affid={aff_id}_mock"
                if pid else f"https://www.flipkart.com/?affid={aff_id}"
            )

        return {
            "status": "redirect",
            "redirect_url": redirect_url,
            "sku": sku,
            "sku_name": sku_info.get("name", sku),
            "provider": self.name,
            "provider_id": self.provider_id,
            "note": "You'll be redirected to Flipkart. FREE11 earns a small affiliate commission — no extra cost to you.",
            "mock": ROUTER_MODE == "mock",
        }
