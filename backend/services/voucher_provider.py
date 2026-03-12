"""
Mock Voucher Provider for FREE11
Plug-replaceable: swap MockVoucherProvider with real Xoxoday/Gyftr later
"""
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict


class VoucherProvider:
    """Interface for voucher providers"""
    async def create_voucher(self, user_id: str, product_id: str, amount: int) -> Dict:
        raise NotImplementedError

    async def check_status(self, voucher_id: str) -> Dict:
        raise NotImplementedError

    async def cancel_voucher(self, voucher_id: str) -> Dict:
        raise NotImplementedError


class MockVoucherProvider(VoucherProvider):
    """Mock implementation that simulates full voucher lifecycle"""

    def __init__(self, db):
        self.db = db

    async def create_voucher(self, user_id: str, product_id: str, amount: int) -> Dict:
        voucher_id = str(uuid.uuid4())
        voucher_code = f"FREE11-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        voucher = {
            "id": voucher_id,
            "user_id": user_id,
            "product_id": product_id,
            "amount": amount,
            "code": voucher_code,
            "status": "processing",
            "provider": "mock",
            "created_at": now,
            "updated_at": now,
            "delivered_at": None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }
        await self.db.vouchers.insert_one(voucher)

        # Schedule auto-complete after 5 seconds (simulates processing)
        asyncio.create_task(self._auto_complete(voucher_id))
        return {"id": voucher_id, "code": voucher_code, "status": "processing"}

    async def _auto_complete(self, voucher_id: str):
        await asyncio.sleep(5)
        now = datetime.now(timezone.utc).isoformat()
        await self.db.vouchers.update_one(
            {"id": voucher_id, "status": "processing"},
            {"$set": {"status": "delivered", "delivered_at": now, "updated_at": now}}
        )

    async def check_status(self, voucher_id: str) -> Dict:
        v = await self.db.vouchers.find_one({"id": voucher_id}, {"_id": 0})
        if not v:
            return {"error": "not_found"}
        return v

    async def cancel_voucher(self, voucher_id: str) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        result = await self.db.vouchers.update_one(
            {"id": voucher_id, "status": {"$in": ["processing"]}},
            {"$set": {"status": "cancelled", "updated_at": now}}
        )
        return {"success": result.modified_count > 0}

    async def force_complete(self, voucher_id: str) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        result = await self.db.vouchers.update_one(
            {"id": voucher_id},
            {"$set": {"status": "delivered", "delivered_at": now, "updated_at": now}}
        )
        return {"success": result.modified_count > 0}

    async def force_fail(self, voucher_id: str) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        result = await self.db.vouchers.update_one(
            {"id": voucher_id},
            {"$set": {"status": "failed", "updated_at": now}}
        )
        return {"success": result.modified_count > 0}
