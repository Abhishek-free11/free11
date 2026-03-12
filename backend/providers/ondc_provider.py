"""
ONDC Provider — Grocery / Ration fulfilment via ONDC Network.
Metro ETA: ~45 min.  Tier-2/3: 1 day.
Real APIs: ONDC BAP integration (swap in when credentials available).
"""
import os
import uuid
from typing import List, Dict
from .base_provider import BaseProvider

ROUTER_MODE = os.environ.get("ROUTER_MODE", "mock")


class ONDCProvider(BaseProvider):
    name = "ONDC Network"
    provider_id = "ondc"
    covered_states = ["MH", "DL", "KA", "TN", "GJ", "WB", "UP", "AP", "RJ", "PB", "HR", "MP"]

    _SKUS: Dict[str, Dict] = {
        "atta_5kg": {
            "name": "Premium Wheat Flour 5kg",
            "coins": 265, "real_price": 265.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=200",
        },
        "rice_5kg": {
            "name": "Premium Basmati Rice 5kg",
            "coins": 320, "real_price": 320.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=200",
        },
        "cola_2l": {
            "name": "Cola Drink 2L Bottle",
            "coins": 95, "real_price": 95.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=200",
        },
        "biscuits_pack": {
            "name": "Glucose Biscuits 400g Pack",
            "coins": 50, "real_price": 50.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=200",
        },
        "oil_1l": {
            "name": "Refined Sunflower Oil 1L",
            "coins": 145, "real_price": 145.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=200",
        },
        "daal_1kg": {
            "name": "Yellow Toor Dal 1kg",
            "coins": 110, "real_price": 110.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1595436169199-3cd70c98af1e?w=200",
        },
        "sugar_1kg": {
            "name": "Refined Sugar 1kg",
            "coins": 45, "real_price": 45.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1548247416-ec66f4900b2e?w=200",
        },
        "salt_pack": {
            "name": "Iodised Salt 1kg",
            "coins": 25, "real_price": 25.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1583339793403-3d9b001b6008?w=200",
        },
        "chips_pack": {
            "name": "Masala Potato Chips 50g",
            "coins": 20, "real_price": 20.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=200",
        },
        "chocolate": {
            "name": "Milk Chocolate Bar 40g",
            "coins": 30, "real_price": 30.0, "category": "groceries",
            "image": "https://images.unsplash.com/photo-1481391319762-47dff72954d9?w=200",
        },
    }

    # ── Metro states where 45-min delivery is available ──
    _METRO_STATES = {"MH", "DL", "KA", "TN"}

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
        gs = (geo_state or "").upper()
        if gs in self._METRO_STATES:
            return 0.031  # ~45 minutes
        if gs in self.covered_states:
            return 1.0    # next-day delivery
        return 2.0        # 2 days for uncovered states (fallback)

    def get_margin(self, sku: str) -> float:
        return 0.12  # 12% commission from ONDC network sellers

    async def redeem(self, sku: str, coins_used: int, user_id: str, **kwargs) -> Dict:
        if ROUTER_MODE == "live":
            # TODO: Replace with real ONDC BAP order placement
            pass  # fall through to mock

        order_id = f"ONDC-{str(uuid.uuid4())[:8].upper()}"
        sku_info = self._SKUS.get(sku, {})
        return {
            "status": "placed",
            "order_id": order_id,
            "sku": sku,
            "sku_name": sku_info.get("name", sku),
            "provider": self.name,
            "provider_id": self.provider_id,
            "delivery_note": "Delivering via ONDC network. ETA: 45 min (metro) / 1 day (others).",
            "tracking_url": f"https://free11.com/orders/{order_id}",
            "mock": ROUTER_MODE == "mock",
        }
