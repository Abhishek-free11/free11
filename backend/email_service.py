"""
Email Service for FREE11
Provider abstraction layer supporting Resend (primary)
Transactional emails only - no marketing
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import uuid
import os
import logging
import httpx

logger = logging.getLogger(__name__)

# ==================== ENUMS ====================

class EmailType(str, Enum):
    VOUCHER_DELIVERED = "voucher_delivered"
    VOUCHER_FAILED = "voucher_failed"
    VOUCHER_RETRY = "voucher_retry"
    ORDER_CONFIRMATION = "order_confirmation"
    SUPPORT_TICKET_CREATED = "support_ticket_created"
    SUPPORT_TICKET_UPDATED = "support_ticket_updated"

class EmailStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"

# ==================== MODELS ====================

class EmailLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Recipient
    to_email: str
    to_name: Optional[str] = None
    
    # Email content
    email_type: EmailType
    subject: str
    template_data: Dict[str, Any] = {}
    
    # Delivery info
    status: EmailStatus = EmailStatus.PENDING
    provider: str = "resend"
    provider_message_id: Optional[str] = None
    
    # Tracking
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    failed_at: Optional[str] = None
    failure_reason: Optional[str] = None
    
    # Context
    user_id: Optional[str] = None
    order_id: Optional[str] = None
    fulfillment_id: Optional[str] = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ==================== EMAIL TEMPLATES ====================

EMAIL_TEMPLATES = {
    EmailType.VOUCHER_DELIVERED: {
        "subject": "Your FREE11 voucher is ready!",
        "body": """
Hi {user_name},

Great news! Your voucher has been delivered.

**Product:** {product_name}
**Voucher Code:** {voucher_code}
{voucher_pin_line}
**Expiry Date:** {expiry_date}

{redemption_instructions}

Order ID: {order_id}
Delivered: {delivered_at}

If you have any issues redeeming this voucher, please contact our support team.

Happy redeeming!
Team FREE11

---
This is a transactional email. You received this because you redeemed a reward on FREE11.
"""
    },
    EmailType.VOUCHER_FAILED: {
        "subject": "Action needed: Your FREE11 voucher delivery failed",
        "body": """
Hi {user_name},

We encountered an issue delivering your voucher.

**Product:** {product_name}
**Order ID:** {order_id}
**Status:** Delivery Failed

Don't worry - we're automatically retrying the delivery. If the issue persists, our support team will reach out.

You can also check your order status anytime in the FREE11 app under Help & Support > My Vouchers.

Team FREE11

---
This is a transactional email regarding your FREE11 order.
"""
    },
    EmailType.VOUCHER_RETRY: {
        "subject": "We're retrying your FREE11 voucher delivery",
        "body": """
Hi {user_name},

We're retrying the delivery of your voucher.

**Product:** {product_name}
**Order ID:** {order_id}
**Attempt:** {attempt_number} of 3

You'll receive another email once the voucher is successfully delivered.

Team FREE11

---
This is a transactional email regarding your FREE11 order.
"""
    }
}

# ==================== ABSTRACT PROVIDER ====================

class EmailProviderBase(ABC):
    """Base class for email providers"""
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email and return provider response"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name"""
        pass

# ==================== RESEND PROVIDER ====================

class ResendEmailProvider(EmailProviderBase):
    """Resend.com email provider"""
    
    def __init__(self):
        self.api_key = os.environ.get("RESEND_API_KEY")
        self.default_from = os.environ.get("RESEND_FROM_EMAIL", "FREE11 <noreply@free11.app>")
        self.api_url = "https://api.resend.com/emails"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("RESEND_API_KEY not configured - email will be logged but not sent")
            return {
                "success": False,
                "error": "Email provider not configured",
                "mock": True
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": from_email or self.default_from,
                        "to": [to_email],
                        "subject": subject,
                        "text": body
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "message_id": data.get("id"),
                        "provider": "resend"
                    }
                else:
                    return {
                        "success": False,
                        "error": response.text,
                        "status_code": response.status_code
                    }
        except Exception as e:
            logger.error(f"Resend email failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_provider_name(self) -> str:
        return "Resend"

# ==================== MOCK PROVIDER (For testing) ====================

class MockEmailProvider(EmailProviderBase):
    """Mock email provider for testing"""
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
        return {
            "success": True,
            "message_id": f"mock-{uuid.uuid4().hex[:12]}",
            "provider": "mock",
            "mock": True
        }
    
    def get_provider_name(self) -> str:
        return "Mock"

# ==================== EMAIL SERVICE ====================

class EmailService:
    """Main email service with provider abstraction"""
    
    _instance = None
    _provider: EmailProviderBase = None
    _db = None
    
    @classmethod
    def initialize(cls, db, use_mock: bool = False):
        """Initialize the email service with database and provider"""
        cls._db = db
        
        if use_mock or not os.environ.get("RESEND_API_KEY"):
            cls._provider = MockEmailProvider()
            logger.info("Email service initialized with MOCK provider")
        else:
            cls._provider = ResendEmailProvider()
            logger.info("Email service initialized with Resend provider")
    
    @classmethod
    async def send_voucher_delivered(
        cls,
        user_email: str,
        user_name: str,
        user_id: str,
        order_id: str,
        fulfillment_id: str,
        product_name: str,
        voucher_code: str,
        voucher_pin: Optional[str],
        expiry_date: str
    ) -> Dict[str, Any]:
        """Send voucher delivered email"""
        
        template = EMAIL_TEMPLATES[EmailType.VOUCHER_DELIVERED]
        
        # Build redemption instructions based on product
        instructions = "Visit the retailer website to redeem your voucher."
        if "amazon" in product_name.lower():
            instructions = "Go to amazon.in/gc/redeem to apply your gift card code."
        elif "swiggy" in product_name.lower():
            instructions = "Open Swiggy app > Wallet > Add Gift Card to redeem."
        
        body = template["body"].format(
            user_name=user_name or "User",
            product_name=product_name,
            voucher_code=voucher_code,
            voucher_pin_line=f"**PIN:** {voucher_pin}" if voucher_pin else "",
            expiry_date=expiry_date or "See voucher terms",
            redemption_instructions=instructions,
            order_id=order_id[:8] + "...",
            delivered_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        )
        
        return await cls._send_and_log(
            to_email=user_email,
            to_name=user_name,
            email_type=EmailType.VOUCHER_DELIVERED,
            subject=template["subject"],
            body=body,
            user_id=user_id,
            order_id=order_id,
            fulfillment_id=fulfillment_id,
            template_data={
                "product_name": product_name,
                "voucher_code": voucher_code[:4] + "****"  # Masked in log
            }
        )
    
    @classmethod
    async def send_voucher_failed(
        cls,
        user_email: str,
        user_name: str,
        user_id: str,
        order_id: str,
        fulfillment_id: str,
        product_name: str
    ) -> Dict[str, Any]:
        """Send voucher delivery failed email"""
        
        template = EMAIL_TEMPLATES[EmailType.VOUCHER_FAILED]
        
        body = template["body"].format(
            user_name=user_name or "User",
            product_name=product_name,
            order_id=order_id[:8] + "..."
        )
        
        return await cls._send_and_log(
            to_email=user_email,
            to_name=user_name,
            email_type=EmailType.VOUCHER_FAILED,
            subject=template["subject"],
            body=body,
            user_id=user_id,
            order_id=order_id,
            fulfillment_id=fulfillment_id,
            template_data={"product_name": product_name}
        )
    
    @classmethod
    async def send_voucher_retry(
        cls,
        user_email: str,
        user_name: str,
        user_id: str,
        order_id: str,
        fulfillment_id: str,
        product_name: str,
        attempt_number: int
    ) -> Dict[str, Any]:
        """Send voucher retry notification"""
        
        template = EMAIL_TEMPLATES[EmailType.VOUCHER_RETRY]
        
        body = template["body"].format(
            user_name=user_name or "User",
            product_name=product_name,
            order_id=order_id[:8] + "...",
            attempt_number=attempt_number
        )
        
        return await cls._send_and_log(
            to_email=user_email,
            to_name=user_name,
            email_type=EmailType.VOUCHER_RETRY,
            subject=template["subject"],
            body=body,
            user_id=user_id,
            order_id=order_id,
            fulfillment_id=fulfillment_id,
            template_data={
                "product_name": product_name,
                "attempt_number": attempt_number
            }
        )
    
    @classmethod
    async def _send_and_log(
        cls,
        to_email: str,
        to_name: Optional[str],
        email_type: EmailType,
        subject: str,
        body: str,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        fulfillment_id: Optional[str] = None,
        template_data: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """Send email and log to database"""
        
        # Create log entry
        log = EmailLog(
            to_email=to_email,
            to_name=to_name,
            email_type=email_type,
            subject=subject,
            template_data=template_data,
            user_id=user_id,
            order_id=order_id,
            fulfillment_id=fulfillment_id
        )
        
        # Send email
        if cls._provider:
            result = await cls._provider.send_email(
                to_email=to_email,
                subject=subject,
                body=body
            )
            
            if result.get("success"):
                log.status = EmailStatus.SENT
                log.sent_at = datetime.now(timezone.utc).isoformat()
                log.provider_message_id = result.get("message_id")
            else:
                log.status = EmailStatus.FAILED
                log.failed_at = datetime.now(timezone.utc).isoformat()
                log.failure_reason = result.get("error")
        else:
            log.status = EmailStatus.FAILED
            log.failure_reason = "Email service not initialized"
        
        # Save log to database
        if cls._db:
            await cls._db.email_logs.insert_one(log.model_dump())
        
        return {
            "success": log.status == EmailStatus.SENT,
            "email_log_id": log.id,
            "status": log.status,
            "provider_message_id": log.provider_message_id,
            "failure_reason": log.failure_reason
        }
    
    @classmethod
    async def get_email_logs(
        cls,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get email logs for audit"""
        if not cls._db:
            return []
        
        query = {}
        if user_id:
            query["user_id"] = user_id
        if order_id:
            query["order_id"] = order_id
        
        logs = await cls._db.email_logs.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return logs
