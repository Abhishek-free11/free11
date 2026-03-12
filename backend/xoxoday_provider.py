"""
Xoxoday (Plum) Voucher Integration for FREE11
Pluggable — works when XOXODAY_CLIENT_ID and XOXODAY_CLIENT_SECRET are set.
Falls back to mock voucher delivery when not configured.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

XOXODAY_CLIENT_ID = os.environ.get("XOXODAY_CLIENT_ID", "")
XOXODAY_CLIENT_SECRET = os.environ.get("XOXODAY_CLIENT_SECRET", "")
XOXODAY_API_URL = os.environ.get("XOXODAY_API_URL", "https://accounts.xoxoday.com/chef")
XOXODAY_ENABLED = bool(XOXODAY_CLIENT_ID and XOXODAY_CLIENT_SECRET)


class XoxodayProvider:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._token = None
        self._token_expiry = None

    async def _get_token(self) -> Optional[str]:
        if not XOXODAY_ENABLED:
            return None
        if self._token and self._token_expiry and datetime.now(timezone.utc).timestamp() < self._token_expiry:
            return self._token
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{XOXODAY_API_URL}/v1/oauth/token", json={
                    "grant_type": "client_credentials",
                    "client_id": XOXODAY_CLIENT_ID,
                    "client_secret": XOXODAY_CLIENT_SECRET,
                })
                if r.status_code == 200:
                    data = r.json()
                    self._token = data.get("access_token")
                    self._token_expiry = datetime.now(timezone.utc).timestamp() + data.get("expires_in", 3600) - 60
                    return self._token
        except Exception as e:
            logger.error(f"Xoxoday token error: {e}")
        return None

    async def get_catalog(self, category: str = "", limit: int = 50) -> List[Dict]:
        if not XOXODAY_ENABLED:
            return self._mock_catalog()
        token = await self._get_token()
        if not token:
            return self._mock_catalog()
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{XOXODAY_API_URL}/v1/oauth/api", headers={"Authorization": f"Bearer {token}"}, json={
                    "query": "plumProAPI.mutation.getVouchers",
                    "tag": "plumProAPI",
                    "variables": {"data": {"limit": limit, "page": 1, "country": "IN", "category": category}},
                })
                if r.status_code == 200:
                    data = r.json()
                    vouchers = data.get("data", {}).get("getVouchers", {}).get("data", [])
                    return [{"id": v.get("productId"), "name": v.get("name"), "description": v.get("description", ""),
                             "denomination": v.get("denomination", []), "image": v.get("imageUrl", ""), "brand": v.get("brandName", "")}
                            for v in vouchers]
        except Exception as e:
            logger.error(f"Xoxoday catalog error: {e}")
        return self._mock_catalog()

    async def place_order(self, user_id: str, product_id: str, denomination: int, email: str, mobile: str = "") -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        order = {
            "user_id": user_id, "product_id": product_id, "denomination": denomination,
            "email": email, "mobile": mobile, "status": "processing", "created_at": now,
        }

        if not XOXODAY_ENABLED:
            order["status"] = "delivered"
            order["voucher_code"] = f"FREE11-MOCK-{denomination}-{''.join(__import__('random').choices('ABCDEF0123456789', k=8))}"
            order["delivery_method"] = "mock"
            await self.db.voucher_orders.insert_one(order)
            return {"status": "delivered", "voucher_code": order["voucher_code"], "delivery": "mock"}

        token = await self._get_token()
        if not token:
            order["status"] = "failed"
            order["error"] = "Token acquisition failed"
            await self.db.voucher_orders.insert_one(order)
            return {"status": "failed", "error": "Payment provider unavailable"}

        import httpx
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{XOXODAY_API_URL}/v1/oauth/api", headers={"Authorization": f"Bearer {token}"}, json={
                    "query": "plumProAPI.mutation.placeOrder",
                    "tag": "plumProAPI",
                    "variables": {"data": {
                        "productId": product_id, "quantity": 1, "denomination": denomination,
                        "email": email, "contact": mobile,
                        "tag": f"free11_{user_id[:8]}",
                    }},
                })
                if r.status_code == 200:
                    data = r.json()
                    result = data.get("data", {}).get("placeOrder", {})
                    if result.get("status") == 200:
                        order["status"] = "delivered"
                        order["xoxoday_order_id"] = result.get("orderId", "")
                        order["voucher_code"] = result.get("vouchers", [{}])[0].get("voucherCode", "")
                        order["delivery_method"] = "xoxoday"
                    else:
                        order["status"] = "failed"
                        order["error"] = result.get("message", "Unknown error")
        except Exception as e:
            order["status"] = "failed"
            order["error"] = str(e)

        await self.db.voucher_orders.insert_one(order)
        return {"status": order["status"], "voucher_code": order.get("voucher_code", ""), "delivery": order.get("delivery_method", "")}

    def _mock_catalog(self) -> List[Dict]:
        return [
            {"id": "mock_amazon_50", "name": "Amazon Gift Card", "brand": "Amazon", "denomination": [50, 100, 250, 500], "image": "https://via.placeholder.com/100?text=Amazon"},
            {"id": "mock_flipkart_50", "name": "Flipkart Gift Card", "brand": "Flipkart", "denomination": [50, 100, 250, 500], "image": "https://via.placeholder.com/100?text=Flipkart"},
            {"id": "mock_swiggy_50", "name": "Swiggy Voucher", "brand": "Swiggy", "denomination": [50, 100, 200], "image": "https://via.placeholder.com/100?text=Swiggy"},
            {"id": "mock_zomato_50", "name": "Zomato Voucher", "brand": "Zomato", "denomination": [50, 100, 200], "image": "https://via.placeholder.com/100?text=Zomato"},
            {"id": "mock_myntra_100", "name": "Myntra Gift Card", "brand": "Myntra", "denomination": [100, 250, 500], "image": "https://via.placeholder.com/100?text=Myntra"},
        ]

    @staticmethod
    def is_enabled() -> bool:
        return XOXODAY_ENABLED
