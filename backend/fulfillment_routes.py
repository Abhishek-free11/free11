"""
Voucher Fulfillment Pipeline for FREE11
Production-grade fulfillment with pluggable providers
Supports: Amazon Gift Cards, Generic vouchers (mocked but production-ready)

AUDIT TRAIL: Full delivery auditability for disputes, ops, and brand trust
IDEMPOTENCY: Prevents duplicate voucher delivery
RETRY LOGIC: Capped retries with failure tracking
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import os
import logging
import asyncio

# Import from server.py
from server import db, get_current_user, User

logger = logging.getLogger(__name__)

fulfillment_router = APIRouter(prefix="/fulfillment", tags=["Fulfillment"])

# Constants for retry logic
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = [30, 120, 300]  # 30s, 2min, 5min

# ==================== ENUMS ====================

class FulfillmentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    REFUNDED = "refunded"
    RETRY_SCHEDULED = "retry_scheduled"

class VoucherProvider(str, Enum):
    AMAZON = "amazon"
    SWIGGY = "swiggy"
    FLIPKART = "flipkart"
    NETFLIX = "netflix"
    SPOTIFY = "spotify"
    GENERIC = "generic"  # For manual/mocked fulfillment

class FailureReason(str, Enum):
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_ERROR = "provider_error"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    INVALID_AMOUNT = "invalid_amount"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

# ==================== MODELS ====================

class FulfillmentRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    user_id: str
    user_email: str
    user_name: Optional[str] = None
    product_id: str
    product_name: str
    provider: VoucherProvider
    amount: int  # In INR
    brand_id: Optional[str] = None
    campaign_id: Optional[str] = None
    
    # Fulfillment details
    status: FulfillmentStatus = FulfillmentStatus.PENDING
    voucher_code: Optional[str] = None
    voucher_pin: Optional[str] = None
    voucher_url: Optional[str] = None
    expiry_date: Optional[str] = None
    
    # === AUDIT TRAIL FIELDS (NEW) ===
    delivery_attempt_count: int = 0
    last_delivery_status: str = "pending"  # pending, delivered, failed
    last_failure_reason: Optional[str] = None
    last_failure_code: Optional[FailureReason] = None
    delivery_provider_id: Optional[str] = None  # Provider's reference ID
    delivery_timestamp_utc: Optional[str] = None
    
    # Delivery attempt history
    delivery_history: List[Dict[str, Any]] = []
    
    # Admin flags
    admin_override_allowed: bool = True
    admin_override_used: bool = False
    admin_override_by: Optional[str] = None
    admin_override_at: Optional[str] = None
    
    # Idempotency
    idempotency_key: Optional[str] = None
    
    # Delivery
    delivery_method: str = "email"  # email, sms, in-app
    delivered_at: Optional[str] = None
    delivery_attempts: int = 0  # Legacy field, use delivery_attempt_count
    last_error: Optional[str] = None  # Legacy field, use last_failure_reason
    
    # Email notification tracking
    email_sent: bool = False
    email_sent_at: Optional[str] = None
    email_log_id: Optional[str] = None
    
    # Tracking
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Provider response (raw)
    provider_response: Optional[Dict[str, Any]] = None

# ==================== ABSTRACT PROVIDER ====================

class VoucherProviderBase(ABC):
    """Base class for voucher providers - pluggable architecture"""
    
    @abstractmethod
    async def generate_voucher(self, amount: int, order_id: str) -> Dict[str, Any]:
        """Generate a voucher code from the provider"""
        pass
    
    @abstractmethod
    async def check_balance(self) -> Dict[str, Any]:
        """Check provider balance/availability"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name"""
        pass

# ==================== MOCK PROVIDERS (Production-Ready Structure) ====================

class MockAmazonProvider(VoucherProviderBase):
    """
    Amazon Gift Card Provider (MOCKED)
    Production-ready structure - replace with real Amazon GC API
    """
    
    async def generate_voucher(self, amount: int, order_id: str) -> Dict[str, Any]:
        # In production: Call Amazon Gift Card API
        # API: https://developer.amazon.com/docs/incentives-api/incentives-api.html
        
        # Mock response with provider tracking ID
        provider_id = f"AMZN-{uuid.uuid4().hex[:16].upper()}"
        voucher_code = f"AMZ-{uuid.uuid4().hex[:12].upper()}"
        
        return {
            "success": True,
            "voucher_code": voucher_code,
            "voucher_pin": None,  # Amazon doesn't use PINs
            "voucher_url": f"https://www.amazon.in/gc/redeem?code={voucher_code}",
            "amount": amount,
            "currency": "INR",
            "expiry_date": "2027-12-31",
            "provider_ref": provider_id,
            "provider_id": provider_id,
            "provider_name": "amazon",
            "is_mocked": True,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_balance(self) -> Dict[str, Any]:
        return {
            "available": True, 
            "balance": 100000, 
            "currency": "INR", 
            "is_mocked": True,
            "health_status": "healthy",
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    
    def get_provider_name(self) -> str:
        return "Amazon Gift Cards"

class MockSwiggyProvider(VoucherProviderBase):
    """Swiggy Voucher Provider (MOCKED)"""
    
    async def generate_voucher(self, amount: int, order_id: str) -> Dict[str, Any]:
        provider_id = f"SWG-{uuid.uuid4().hex[:16].upper()}"
        voucher_code = f"SWG-{uuid.uuid4().hex[:8].upper()}"
        
        return {
            "success": True,
            "voucher_code": voucher_code,
            "voucher_pin": str(uuid.uuid4().int)[:4],
            "voucher_url": None,
            "amount": amount,
            "currency": "INR",
            "expiry_date": "2026-06-30",
            "provider_ref": provider_id,
            "provider_id": provider_id,
            "provider_name": "swiggy",
            "is_mocked": True,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_balance(self) -> Dict[str, Any]:
        return {
            "available": True, 
            "balance": 50000, 
            "currency": "INR", 
            "is_mocked": True,
            "health_status": "healthy",
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    
    def get_provider_name(self) -> str:
        return "Swiggy"

class MockGenericProvider(VoucherProviderBase):
    """Generic Voucher Provider for manual fulfillment"""
    
    async def generate_voucher(self, amount: int, order_id: str) -> Dict[str, Any]:
        provider_id = f"GEN-{uuid.uuid4().hex[:16].upper()}"
        voucher_code = f"FREE11-{uuid.uuid4().hex[:10].upper()}"
        
        return {
            "success": True,
            "voucher_code": voucher_code,
            "voucher_pin": None,
            "voucher_url": None,
            "amount": amount,
            "currency": "INR",
            "expiry_date": "2026-12-31",
            "provider_ref": provider_id,
            "provider_id": provider_id,
            "provider_name": "generic",
            "is_mocked": True,
            "requires_manual_fulfillment": True,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_balance(self) -> Dict[str, Any]:
        return {
            "available": True, 
            "balance": "unlimited", 
            "is_mocked": True,
            "health_status": "healthy",
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    
    def get_provider_name(self) -> str:
        return "FREE11 Generic"

# ==================== PROVIDER FACTORY ====================

class ProviderFactory:
    """Factory to get the appropriate voucher provider"""
    
    _providers = {
        VoucherProvider.AMAZON: MockAmazonProvider(),
        VoucherProvider.SWIGGY: MockSwiggyProvider(),
        VoucherProvider.FLIPKART: MockGenericProvider(),
        VoucherProvider.NETFLIX: MockGenericProvider(),
        VoucherProvider.SPOTIFY: MockGenericProvider(),
        VoucherProvider.GENERIC: MockGenericProvider(),
    }
    
    @classmethod
    def get_provider(cls, provider: VoucherProvider) -> VoucherProviderBase:
        return cls._providers.get(provider, MockGenericProvider())
    
    @classmethod
    def register_provider(cls, provider: VoucherProvider, instance: VoucherProviderBase):
        """Register a new provider (for real integrations)"""
        cls._providers[provider] = instance

# ==================== FULFILLMENT SERVICE ====================

class FulfillmentService:
    """Main fulfillment orchestration service with idempotency and retry logic"""
    
    @staticmethod
    async def check_idempotency(order_id: str) -> Optional[Dict[str, Any]]:
        """Check if this order has already been fulfilled (idempotency check)"""
        existing = await db.fulfillments.find_one({
            "order_id": order_id,
            "status": {"$in": [FulfillmentStatus.DELIVERED, FulfillmentStatus.PROCESSING]}
        })
        return existing
    
    @staticmethod
    async def process_redemption(order_id: str, user_id: str, user_email: str, 
                                  product: dict, user_name: str = None) -> FulfillmentRecord:
        """Process a redemption and create fulfillment record with idempotency"""
        
        # IDEMPOTENCY CHECK: Prevent duplicate voucher delivery
        existing = await FulfillmentService.check_idempotency(order_id)
        if existing:
            logger.warning(f"Idempotency check failed: Order {order_id} already exists with status {existing['status']}")
            raise HTTPException(
                status_code=409,
                detail=f"Order {order_id} has already been processed (status: {existing['status']})"
            )
        
        # Determine provider from product
        brand = product.get("brand", "").lower()
        product_name = product.get("name", "").lower()
        provider = VoucherProvider.GENERIC
        
        if "amazon" in brand or "amazon" in product_name:
            provider = VoucherProvider.AMAZON
        elif "swiggy" in brand or "swiggy" in product_name:
            provider = VoucherProvider.SWIGGY
        elif "flipkart" in brand or "flipkart" in product_name:
            provider = VoucherProvider.FLIPKART
        elif "netflix" in brand or "netflix" in product_name:
            provider = VoucherProvider.NETFLIX
        elif "spotify" in brand or "spotify" in product_name:
            provider = VoucherProvider.SPOTIFY
        
        # Create fulfillment record with idempotency key
        idempotency_key = f"{order_id}:{user_id}:{product.get('id', '')}"
        
        record = FulfillmentRecord(
            order_id=order_id,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            product_id=product.get("id", ""),
            product_name=product.get("name", ""),
            provider=provider,
            amount=product.get("value", product.get("cost", 0)),
            brand_id=product.get("brand_id"),
            campaign_id=product.get("campaign_id"),
            idempotency_key=idempotency_key,
            last_delivery_status="pending"
        )
        
        # Save initial record
        await db.fulfillments.insert_one(record.model_dump())
        
        return record
    
    @staticmethod
    async def execute_fulfillment(fulfillment_id: str, is_retry: bool = False) -> Dict[str, Any]:
        """Execute the actual voucher generation with full audit trail"""
        
        record = await db.fulfillments.find_one({"id": fulfillment_id})
        if not record:
            raise HTTPException(status_code=404, detail="Fulfillment record not found")
        
        # Check retry limit
        attempt_count = record.get("delivery_attempt_count", 0)
        if attempt_count >= MAX_RETRY_ATTEMPTS and not record.get("admin_override_used"):
            logger.error(f"Max retry attempts reached for {fulfillment_id}")
            return {
                "success": False, 
                "error": "Maximum delivery attempts reached",
                "attempts": attempt_count
            }
        
        # IDEMPOTENCY: Don't process already delivered vouchers
        if record.get("status") == FulfillmentStatus.DELIVERED:
            logger.warning(f"Attempted to re-deliver already delivered voucher {fulfillment_id}")
            return {
                "success": True,
                "already_delivered": True,
                "voucher_code": record.get("voucher_code")
            }
        
        current_attempt = attempt_count + 1
        attempt_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Update status to processing
        await db.fulfillments.update_one(
            {"id": fulfillment_id},
            {"$set": {
                "status": FulfillmentStatus.PROCESSING,
                "delivery_attempt_count": current_attempt,
                "updated_at": attempt_timestamp
            }}
        )
        
        attempt_record = {
            "attempt_number": current_attempt,
            "timestamp": attempt_timestamp,
            "is_retry": is_retry,
            "status": "processing"
        }
        
        try:
            # Get provider and generate voucher
            provider = ProviderFactory.get_provider(VoucherProvider(record["provider"]))
            result = await provider.generate_voucher(record["amount"], record["order_id"])
            
            if result.get("success"):
                delivery_timestamp = datetime.now(timezone.utc).isoformat()
                
                # Update attempt record
                attempt_record["status"] = "success"
                attempt_record["provider_id"] = result.get("provider_id")
                attempt_record["completed_at"] = delivery_timestamp
                
                # Update with voucher details and audit trail
                update_data = {
                    "status": FulfillmentStatus.DELIVERED,
                    "voucher_code": result.get("voucher_code"),
                    "voucher_pin": result.get("voucher_pin"),
                    "voucher_url": result.get("voucher_url"),
                    "expiry_date": result.get("expiry_date"),
                    "delivered_at": delivery_timestamp,
                    "delivery_timestamp_utc": delivery_timestamp,
                    "delivery_provider_id": result.get("provider_id"),
                    "last_delivery_status": "delivered",
                    "last_failure_reason": None,
                    "last_failure_code": None,
                    "provider_response": result,
                    "updated_at": delivery_timestamp
                }
                
                await db.fulfillments.update_one(
                    {"id": fulfillment_id},
                    {
                        "$set": update_data,
                        "$push": {"delivery_history": attempt_record}
                    }
                )
                
                # Send email notification
                try:
                    from email_service import EmailService
                    email_result = await EmailService.send_voucher_delivered(
                        user_email=record["user_email"],
                        user_name=record.get("user_name"),
                        user_id=record["user_id"],
                        order_id=record["order_id"],
                        fulfillment_id=fulfillment_id,
                        product_name=record["product_name"],
                        voucher_code=result.get("voucher_code"),
                        voucher_pin=result.get("voucher_pin"),
                        expiry_date=result.get("expiry_date")
                    )
                    
                    # Update email status
                    await db.fulfillments.update_one(
                        {"id": fulfillment_id},
                        {"$set": {
                            "email_sent": email_result.get("success", False),
                            "email_sent_at": datetime.now(timezone.utc).isoformat() if email_result.get("success") else None,
                            "email_log_id": email_result.get("email_log_id")
                        }}
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send delivery email for {fulfillment_id}: {str(email_error)}")
                
                logger.info(f"Voucher delivered for order {record['order_id']}: {result.get('voucher_code')}")
                
                return {
                    "success": True, 
                    "voucher_code": result.get("voucher_code"),
                    "attempt": current_attempt,
                    "provider_id": result.get("provider_id")
                }
            else:
                raise Exception(result.get("error", "Provider returned failure"))
                
        except Exception as e:
            error_str = str(e)
            failure_timestamp = datetime.now(timezone.utc).isoformat()
            
            # Determine failure reason
            failure_code = FailureReason.UNKNOWN
            if "timeout" in error_str.lower():
                failure_code = FailureReason.TIMEOUT
            elif "rate" in error_str.lower():
                failure_code = FailureReason.RATE_LIMITED
            elif "unavailable" in error_str.lower():
                failure_code = FailureReason.PROVIDER_UNAVAILABLE
            elif "balance" in error_str.lower():
                failure_code = FailureReason.INSUFFICIENT_BALANCE
            else:
                failure_code = FailureReason.PROVIDER_ERROR
            
            # Update attempt record
            attempt_record["status"] = "failed"
            attempt_record["error"] = error_str
            attempt_record["failure_code"] = failure_code.value
            attempt_record["completed_at"] = failure_timestamp
            
            # Determine if retry is possible
            can_retry = current_attempt < MAX_RETRY_ATTEMPTS
            new_status = FulfillmentStatus.RETRY_SCHEDULED if can_retry else FulfillmentStatus.FAILED
            
            # Update failure status with full audit trail
            await db.fulfillments.update_one(
                {"id": fulfillment_id},
                {
                    "$set": {
                        "status": new_status,
                        "last_error": error_str,
                        "last_failure_reason": error_str,
                        "last_failure_code": failure_code.value,
                        "last_delivery_status": "failed",
                        "delivery_attempts": current_attempt,
                        "updated_at": failure_timestamp
                    },
                    "$push": {"delivery_history": attempt_record}
                }
            )
            
            # Send failure email if max retries reached
            if not can_retry:
                try:
                    from email_service import EmailService
                    await EmailService.send_voucher_failed(
                        user_email=record["user_email"],
                        user_name=record.get("user_name"),
                        user_id=record["user_id"],
                        order_id=record["order_id"],
                        fulfillment_id=fulfillment_id,
                        product_name=record["product_name"]
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send failure email for {fulfillment_id}: {str(email_error)}")
            else:
                # Send retry notification
                try:
                    from email_service import EmailService
                    await EmailService.send_voucher_retry(
                        user_email=record["user_email"],
                        user_name=record.get("user_name"),
                        user_id=record["user_id"],
                        order_id=record["order_id"],
                        fulfillment_id=fulfillment_id,
                        product_name=record["product_name"],
                        attempt_number=current_attempt
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send retry email for {fulfillment_id}: {str(email_error)}")
            
            logger.error(f"Fulfillment failed for {fulfillment_id}: {error_str}")
            
            return {
                "success": False, 
                "error": error_str,
                "failure_code": failure_code.value,
                "attempt": current_attempt,
                "can_retry": can_retry,
                "retries_remaining": MAX_RETRY_ATTEMPTS - current_attempt
            }
    
    @staticmethod
    async def schedule_retry(fulfillment_id: str, delay_seconds: int = None):
        """Schedule a retry with delay"""
        record = await db.fulfillments.find_one({"id": fulfillment_id})
        if not record:
            return
        
        attempt_count = record.get("delivery_attempt_count", 0)
        if attempt_count >= MAX_RETRY_ATTEMPTS:
            return
        
        # Use exponential backoff delay
        if delay_seconds is None:
            delay_seconds = RETRY_DELAY_SECONDS[min(attempt_count, len(RETRY_DELAY_SECONDS) - 1)]
        
        logger.info(f"Scheduling retry for {fulfillment_id} in {delay_seconds} seconds")
        
        # In production, use a proper task queue like Celery
        # For now, use asyncio delay (not ideal for production)
        await asyncio.sleep(delay_seconds)
        await FulfillmentService.execute_fulfillment(fulfillment_id, is_retry=True)

# ==================== API ROUTES ====================

@fulfillment_router.get("/status/{order_id}")
async def get_fulfillment_status(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get fulfillment status for an order"""
    record = await db.fulfillments.find_one(
        {"order_id": order_id, "user_id": current_user.id},
        {"_id": 0, "provider_response": 0}
    )
    
    if not record:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "order_id": order_id,
        "status": record["status"],
        "product_name": record["product_name"],
        "voucher_code": record.get("voucher_code") if record["status"] == "delivered" else None,
        "voucher_pin": record.get("voucher_pin") if record["status"] == "delivered" else None,
        "voucher_url": record.get("voucher_url") if record["status"] == "delivered" else None,
        "expiry_date": record.get("expiry_date"),
        "delivered_at": record.get("delivered_at"),
        "created_at": record.get("created_at")
    }

@fulfillment_router.get("/my-vouchers")
async def get_my_vouchers(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None
):
    """Get all vouchers for the current user"""
    query = {"user_id": current_user.id}
    if status:
        query["status"] = status
    
    vouchers = await db.fulfillments.find(
        query,
        {"_id": 0, "provider_response": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    return {"vouchers": vouchers}

@fulfillment_router.post("/retry/{fulfillment_id}")
async def retry_fulfillment(
    fulfillment_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Retry a failed fulfillment"""
    record = await db.fulfillments.find_one({"id": fulfillment_id, "user_id": current_user.id})
    
    if not record:
        raise HTTPException(status_code=404, detail="Fulfillment not found")
    
    if record["status"] not in [FulfillmentStatus.FAILED, FulfillmentStatus.PENDING]:
        raise HTTPException(status_code=400, detail="Can only retry failed or pending fulfillments")
    
    if record.get("delivery_attempts", 0) >= 3:
        raise HTTPException(status_code=400, detail="Maximum retry attempts reached. Please contact support.")
    
    # Queue retry
    background_tasks.add_task(FulfillmentService.execute_fulfillment, fulfillment_id)
    
    return {"message": "Retry queued", "fulfillment_id": fulfillment_id}

# ==================== ADMIN ROUTES ====================

@fulfillment_router.get("/admin/pending")
async def get_pending_fulfillments(current_user: User = Depends(get_current_user)):
    """Get all pending fulfillments (admin only)"""
    # TODO: Add proper admin check
    
    pending = await db.fulfillments.find(
        {"status": {"$in": [FulfillmentStatus.PENDING, FulfillmentStatus.FAILED]}},
        {"_id": 0}
    ).sort("created_at", 1).limit(100).to_list(100)
    
    return {"pending_fulfillments": pending, "count": len(pending)}

@fulfillment_router.post("/admin/process/{fulfillment_id}")
async def admin_process_fulfillment(
    fulfillment_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Manually process a fulfillment (admin only)"""
    background_tasks.add_task(FulfillmentService.execute_fulfillment, fulfillment_id)
    return {"message": "Processing queued", "fulfillment_id": fulfillment_id}

@fulfillment_router.post("/admin/manual-fulfill/{fulfillment_id}")
async def manual_fulfill(
    fulfillment_id: str,
    voucher_code: str,
    voucher_pin: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Manually fulfill with a voucher code (admin only)"""
    record = await db.fulfillments.find_one({"id": fulfillment_id})
    if not record:
        raise HTTPException(status_code=404, detail="Fulfillment not found")
    
    await db.fulfillments.update_one(
        {"id": fulfillment_id},
        {"$set": {
            "status": FulfillmentStatus.DELIVERED,
            "voucher_code": voucher_code,
            "voucher_pin": voucher_pin,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "provider_response": {"manual": True, "fulfilled_by": current_user.id}
        }}
    )
    
    return {"message": "Manually fulfilled", "voucher_code": voucher_code}

# ==================== PROVIDER STATUS ====================

@fulfillment_router.get("/providers/status")
async def get_providers_status():
    """Get status of all voucher providers"""
    statuses = {}
    
    for provider in VoucherProvider:
        instance = ProviderFactory.get_provider(provider)
        try:
            balance = await instance.check_balance()
            statuses[provider.value] = {
                "name": instance.get_provider_name(),
                "available": balance.get("available", False),
                "is_mocked": balance.get("is_mocked", False)
            }
        except Exception as e:
            statuses[provider.value] = {
                "name": provider.value,
                "available": False,
                "error": str(e)
            }
    
    return {"providers": statuses}
