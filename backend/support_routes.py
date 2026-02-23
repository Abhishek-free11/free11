"""
Support Chatbot for FREE11
Deterministic FAQ + Order Status + Ticket System
NO AI for now - rule-based responses
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import re

# Import from server.py
from server import db, get_current_user, User

support_router = APIRouter(prefix="/support", tags=["Support"])

# ==================== ENUMS ====================

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketCategory(str, Enum):
    ORDER = "order"
    REDEMPTION = "redemption"
    ACCOUNT = "account"
    TECHNICAL = "technical"
    FEEDBACK = "feedback"
    OTHER = "other"

# ==================== MODELS ====================

class SupportTicket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    user_name: str
    
    subject: str
    description: str
    category: TicketCategory = TicketCategory.OTHER
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    
    related_order_id: Optional[str] = None
    
    messages: List[Dict[str, Any]] = []
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None  # For order lookups, etc.

class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []
    action: Optional[str] = None  # e.g., "create_ticket", "show_order"
    data: Optional[Dict[str, Any]] = None

# ==================== FAQ DATABASE ====================

FAQ_DATABASE = {
    "coins": {
        "what are coins": {
            "response": "FREE11 Coins are non-withdrawable reward tokens that you earn by making accurate cricket predictions. You can redeem them for real products and vouchers from our brand partners!",
            "keywords": ["what", "coins", "free11 coins", "earn"]
        },
        "withdraw coins": {
            "response": "FREE11 Coins cannot be withdrawn as cash. They are reward tokens redeemable only for goods and services. No cash. No betting. Brand-funded rewards only.",
            "keywords": ["withdraw", "cash out", "convert", "money"]
        },
        "expire": {
            "response": "Coins remain active as long as you maintain regular activity. Extended inactivity (60+ days) may result in expiry warnings. Keep predicting to keep your coins safe!",
            "keywords": ["expire", "expiry", "lose", "disappear"]
        }
    },
    "orders": {
        "order status": {
            "response": "I can help you check your order status! Please provide your order ID, or I can look up your recent orders for you.",
            "keywords": ["order", "status", "track", "where"]
        },
        "voucher not received": {
            "response": "I'm sorry your voucher hasn't arrived yet. Let me help:\n\n1. **Check email spam folder** - Vouchers are sent to your registered email\n2. **Allow up to 24 hours** - Some vouchers take time to process\n3. **Check 'My Vouchers' tab** - Your voucher code may already be there\n\nIf still missing after 24 hours, please share your **Order ID** and I'll create a support ticket for immediate investigation.",
            "keywords": ["voucher", "not received", "missing", "didn't get", "haven't received", "where is my voucher", "no voucher"]
        },
        "redeemed but not received": {
            "response": "I understand you redeemed but didn't receive your voucher. This can happen due to:\n\n• **Processing delay** - Allow 15-30 minutes\n• **Email delivery** - Check spam/promotions folder\n• **System error** - Our team can investigate\n\n**To help you faster, please provide:**\n1. Your Order ID or Redemption ID\n2. Product name you redeemed\n3. When you made the redemption\n\nI'll look up your delivery status right away.",
            "keywords": ["redeemed", "not received", "no code", "didn't arrive", "waiting"]
        },
        "how to redeem": {
            "response": "To redeem your coins: 1) Go to the Redeem section 2) Browse available rewards 3) Select a product you can afford 4) Click 'Redeem' and confirm. Your voucher will be delivered to your email!",
            "keywords": ["how", "redeem", "use coins", "get rewards"]
        },
        "voucher code not working": {
            "response": "If your voucher code isn't working:\n\n1. **Check expiry date** - Codes expire, check the date in 'My Vouchers'\n2. **Copy correctly** - Some codes are case-sensitive\n3. **Minimum purchase** - Some vouchers have minimum order requirements\n4. **Already used** - Each code works only once\n\nIf none of these apply, share your Order ID and I'll investigate.",
            "keywords": ["code not working", "invalid code", "voucher error", "can't use"]
        }
    },
    "account": {
        "delete account": {
            "response": "To delete your account, please create a support ticket and our team will process your request within 48 hours. Note: This action is irreversible and all coins will be forfeited.",
            "keywords": ["delete", "remove", "close account"]
        },
        "change email": {
            "response": "To change your email address, please create a support ticket with your current and new email addresses. We'll verify and update within 24 hours.",
            "keywords": ["change", "email", "update email"]
        }
    },
    "predictions": {
        "how predictions work": {
            "response": "During live cricket matches, predict the outcome of each ball (runs, wicket, etc.). Correct predictions earn you coins based on difficulty. Higher accuracy = more rewards!",
            "keywords": ["how", "predictions", "work", "predict"]
        },
        "leaderboard ranking": {
            "response": "Our leaderboards rank users by SKILL (prediction accuracy and streaks), not by total coins. This ensures the best predictors rise to the top!",
            "keywords": ["leaderboard", "rank", "ranking", "position"]
        }
    },
    "clans": {
        "join clan": {
            "response": "To join a clan: Go to Clans section → Browse available clans → Click 'Join'. To create your own clan, you need to be Level 2 (Amateur) or higher.",
            "keywords": ["join", "clan", "team", "group"]
        },
        "clan benefits": {
            "response": "Clans let you compete together! Benefits include: Clan vs Clan challenges, group leaderboards, exclusive badges, and bragging rights. Remember: Clans compete on SKILL, not coins!",
            "keywords": ["clan", "benefit", "why", "advantage"]
        }
    }
}

# ==================== CHATBOT ENGINE ====================

class ChatbotEngine:
    """Rule-based chatbot with FAQ, order lookup, and ticket creation"""
    
    @staticmethod
    def extract_order_id(message: str) -> Optional[str]:
        """Extract order ID from message if present"""
        # Pattern for UUID
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        match = re.search(uuid_pattern, message.lower())
        return match.group(0) if match else None
    
    @staticmethod
    def find_best_faq_match(message: str) -> Optional[Dict[str, Any]]:
        """Find the best matching FAQ response"""
        message_lower = message.lower()
        best_match = None
        best_score = 0
        
        for category, faqs in FAQ_DATABASE.items():
            for faq_key, faq_data in faqs.items():
                score = 0
                for keyword in faq_data.get("keywords", []):
                    if keyword in message_lower:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = faq_data
        
        return best_match if best_score >= 2 else None
    
    @staticmethod
    async def lookup_order(order_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Look up order status"""
        # Check fulfillments
        fulfillment = await db.fulfillments.find_one(
            {"order_id": order_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if fulfillment:
            return {
                "order_id": order_id,
                "product": fulfillment.get("product_name"),
                "status": fulfillment.get("status"),
                "voucher_code": fulfillment.get("voucher_code") if fulfillment.get("status") == "delivered" else None,
                "created_at": fulfillment.get("created_at")
            }
        
        # Check orders collection
        order = await db.orders.find_one(
            {"id": order_id, "user_id": user_id},
            {"_id": 0}
        )
        
        return order
    
    @staticmethod
    async def get_recent_orders(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get user's recent orders"""
        orders = await db.fulfillments.find(
            {"user_id": user_id},
            {"_id": 0, "id": 1, "order_id": 1, "product_name": 1, "status": 1, "created_at": 1}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return orders
    
    @classmethod
    async def process_message(cls, message: str, user: User) -> ChatResponse:
        """Process a chat message and return appropriate response"""
        message_lower = message.lower()
        
        # Check for order ID in message
        order_id = cls.extract_order_id(message)
        if order_id:
            order = await cls.lookup_order(order_id, user.id)
            if order:
                status_emoji = {
                    "pending": "⏳",
                    "processing": "🔄",
                    "delivered": "✅",
                    "failed": "❌"
                }.get(order.get("status", ""), "❓")
                
                response = f"Found your order!\n\n**Order:** {order.get('product', 'Unknown')}\n**Status:** {status_emoji} {order.get('status', 'Unknown').title()}"
                
                if order.get("voucher_code"):
                    response += f"\n**Voucher Code:** `{order['voucher_code']}`"
                
                return ChatResponse(
                    response=response,
                    suggestions=["Check another order", "I have an issue with this order", "Talk to support"],
                    action="show_order",
                    data=order
                )
            else:
                return ChatResponse(
                    response=f"I couldn't find order {order_id} in your account. Please check the order ID and try again.",
                    suggestions=["Show my recent orders", "Talk to support"]
                )
        
        # Check for recent orders request
        if any(phrase in message_lower for phrase in ["recent orders", "my orders", "show orders", "order history"]):
            orders = await cls.get_recent_orders(user.id)
            if orders:
                order_list = "\n".join([
                    f"• **{o.get('product_name', 'Unknown')}** - {o.get('status', 'Unknown')}"
                    for o in orders
                ])
                return ChatResponse(
                    response=f"Here are your recent orders:\n\n{order_list}",
                    suggestions=["Check specific order status", "I have an issue", "Talk to support"],
                    data={"orders": orders}
                )
            else:
                return ChatResponse(
                    response="You don't have any orders yet. Head to the Redeem section to use your coins!",
                    suggestions=["How do I redeem coins?", "How do I earn coins?"]
                )
        
        # Check for support/ticket request
        if any(phrase in message_lower for phrase in ["talk to support", "human", "agent", "create ticket", "help me", "issue", "problem", "complaint"]):
            return ChatResponse(
                response="I'll connect you with our support team. Please describe your issue and I'll create a ticket for you.",
                suggestions=["Order issue", "Account issue", "Technical problem", "Feedback"],
                action="create_ticket"
            )
        
        # FAQ matching
        faq_match = cls.find_best_faq_match(message)
        if faq_match:
            return ChatResponse(
                response=faq_match["response"],
                suggestions=["This helped!", "I need more help", "Talk to support"]
            )
        
        # Default response
        return ChatResponse(
            response="I'm here to help! Here are some things I can assist with:\n\n• Check your order status\n• Answer questions about coins and rewards\n• Help with clan and leaderboard questions\n• Create a support ticket",
            suggestions=["Show my recent orders", "How do coins work?", "How do I redeem?", "Talk to support"]
        )

# ==================== API ROUTES ====================

@support_router.post("/chat")
async def chat(
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """Send a message to the support chatbot"""
    return await ChatbotEngine.process_message(chat_message.message, current_user)

@support_router.get("/chat/suggestions")
async def get_chat_suggestions():
    """Get initial chat suggestions"""
    return {
        "greeting": "Hi! I'm your FREE11 support assistant. How can I help you today?",
        "suggestions": [
            "Check my order status",
            "I redeemed but didn't receive my voucher",
            "How do coins work?",
            "How do I redeem rewards?",
            "Talk to support"
        ]
    }

# ==================== TICKET ROUTES ====================

class CreateTicketRequest(BaseModel):
    subject: str
    description: str
    category: TicketCategory = TicketCategory.OTHER
    related_order_id: Optional[str] = None

@support_router.post("/tickets")
async def create_ticket(
    ticket_data: CreateTicketRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new support ticket"""
    ticket = SupportTicket(
        user_id=current_user.id,
        user_email=current_user.email,
        user_name=current_user.name,
        subject=ticket_data.subject,
        description=ticket_data.description,
        category=ticket_data.category,
        related_order_id=ticket_data.related_order_id,
        messages=[{
            "sender": "user",
            "message": ticket_data.description,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    )
    
    # Auto-assign priority based on category
    if ticket_data.category == TicketCategory.ORDER:
        ticket.priority = TicketPriority.HIGH
    
    await db.support_tickets.insert_one(ticket.model_dump())
    
    return {
        "message": "Support ticket created successfully!",
        "ticket_id": ticket.id,
        "expected_response": "Within 24-48 hours"
    }

@support_router.get("/tickets")
async def get_my_tickets(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None
):
    """Get user's support tickets"""
    query = {"user_id": current_user.id}
    if status:
        query["status"] = status
    
    tickets = await db.support_tickets.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return {"tickets": tickets}

@support_router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific ticket"""
    ticket = await db.support_tickets.find_one(
        {"id": ticket_id, "user_id": current_user.id},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket

@support_router.post("/tickets/{ticket_id}/reply")
async def reply_to_ticket(
    ticket_id: str,
    message: str,
    current_user: User = Depends(get_current_user)
):
    """Add a reply to a ticket"""
    ticket = await db.support_tickets.find_one(
        {"id": ticket_id, "user_id": current_user.id}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket["status"] == TicketStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Cannot reply to a closed ticket")
    
    new_message = {
        "sender": "user",
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"messages": new_message},
            "$set": {
                "status": TicketStatus.OPEN,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Reply added successfully"}

# ==================== ADMIN TICKET ROUTES ====================

@support_router.get("/admin/tickets")
async def admin_get_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all tickets (admin only)"""
    query = {}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    
    tickets = await db.support_tickets.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(100).to_list(100)
    
    # Stats
    open_count = await db.support_tickets.count_documents({"status": TicketStatus.OPEN})
    in_progress = await db.support_tickets.count_documents({"status": TicketStatus.IN_PROGRESS})
    
    return {
        "tickets": tickets,
        "stats": {
            "open": open_count,
            "in_progress": in_progress,
            "total": len(tickets)
        }
    }

@support_router.post("/admin/tickets/{ticket_id}/reply")
async def admin_reply_to_ticket(
    ticket_id: str,
    message: str,
    current_user: User = Depends(get_current_user)
):
    """Admin reply to a ticket"""
    ticket = await db.support_tickets.find_one({"id": ticket_id})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    new_message = {
        "sender": "support",
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": current_user.id
    }
    
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"messages": new_message},
            "$set": {
                "status": TicketStatus.WAITING_USER,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Reply sent to user"}

@support_router.post("/admin/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    resolution_message: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Resolve a ticket"""
    update = {
        "status": TicketStatus.RESOLVED,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if resolution_message:
        await db.support_tickets.update_one(
            {"id": ticket_id},
            {
                "$push": {"messages": {
                    "sender": "support",
                    "message": resolution_message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "is_resolution": True
                }},
                "$set": update
            }
        )
    else:
        await db.support_tickets.update_one({"id": ticket_id}, {"$set": update})
    
    return {"message": "Ticket resolved"}


# ==================== ADMIN SUPPORT VIEW WITH DELIVERY DETAILS ====================

@support_router.get("/admin/tickets/{ticket_id}/delivery-details")
async def get_ticket_delivery_details(
    ticket_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get delivery details for a ticket with related order
    Shows: delivery timeline, provider used, last failure reason, retry option
    """
    ticket = await db.support_tickets.find_one({"id": ticket_id}, {"_id": 0})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get related order/fulfillment if any
    fulfillment = None
    if ticket.get("related_order_id"):
        fulfillment = await db.fulfillments.find_one(
            {"order_id": ticket["related_order_id"]},
            {"_id": 0, "provider_response": 0}
        )
    
    # If no direct order link, try to find from user's recent orders
    user_fulfillments = []
    if not fulfillment:
        user_fulfillments = await db.fulfillments.find(
            {"user_id": ticket["user_id"]},
            {"_id": 0, "provider_response": 0}
        ).sort("created_at", -1).limit(5).to_list(5)
    
    # Build delivery timeline if fulfillment exists
    delivery_timeline = None
    if fulfillment:
        delivery_timeline = {
            "order_id": fulfillment["order_id"],
            "product_name": fulfillment["product_name"],
            "current_status": fulfillment["status"],
            "provider_used": fulfillment.get("provider"),
            "delivery_provider_id": fulfillment.get("delivery_provider_id"),
            "delivery_attempts": fulfillment.get("delivery_attempt_count", 0),
            "max_retries": 3,
            "last_failure_reason": fulfillment.get("last_failure_reason"),
            "last_failure_code": fulfillment.get("last_failure_code"),
            "delivery_history": fulfillment.get("delivery_history", []),
            "timestamps": {
                "created_at": fulfillment.get("created_at"),
                "last_attempt": fulfillment.get("updated_at"),
                "delivered_at": fulfillment.get("delivered_at")
            },
            "voucher_delivered": fulfillment["status"] == "delivered",
            "voucher_code": fulfillment.get("voucher_code") if fulfillment["status"] == "delivered" else None,
            "can_retry": fulfillment["status"] in ["failed", "pending", "retry_scheduled"] and fulfillment.get("delivery_attempt_count", 0) < 3,
            "can_force_retry": fulfillment["status"] == "failed"
        }
    
    return {
        "ticket": ticket,
        "delivery_timeline": delivery_timeline,
        "user_recent_orders": user_fulfillments if not fulfillment else [],
        "resolution_guidance": {
            "voucher_not_received": [
                "1. Check delivery_timeline.current_status",
                "2. If 'failed', check last_failure_reason",
                "3. If retries remain, use admin retry endpoint",
                "4. If max retries reached, use manual fulfillment"
            ]
        }
    }

@support_router.post("/admin/tickets/{ticket_id}/retry-delivery")
async def admin_retry_ticket_delivery(
    ticket_id: str,
    force: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Admin retry delivery for a ticket's related order"""
    ticket = await db.support_tickets.find_one({"id": ticket_id})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not ticket.get("related_order_id"):
        raise HTTPException(status_code=400, detail="No order linked to this ticket")
    
    fulfillment = await db.fulfillments.find_one({"order_id": ticket["related_order_id"]})
    
    if not fulfillment:
        raise HTTPException(status_code=404, detail="Fulfillment not found")
    
    if fulfillment["status"] == "delivered":
        raise HTTPException(status_code=400, detail="Voucher already delivered")
    
    # Check retry eligibility
    attempts = fulfillment.get("delivery_attempt_count", 0)
    if attempts >= 3 and not force:
        raise HTTPException(
            status_code=400, 
            detail="Max retries reached. Use force=true to override"
        )
    
    # Reset attempts if forcing
    if force and attempts >= 3:
        await db.fulfillments.update_one(
            {"id": fulfillment["id"]},
            {"$set": {
                "delivery_attempt_count": 0,
                "admin_override_used": True,
                "admin_override_by": current_user.id,
                "admin_override_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    # Trigger retry via fulfillment service
    from fulfillment_routes import FulfillmentService
    result = await FulfillmentService.execute_fulfillment(fulfillment["id"], is_retry=True)
    
    # Add note to ticket
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"messages": {
                "sender": "system",
                "message": f"Admin triggered delivery retry. Result: {'Success' if result.get('success') else 'Failed - ' + result.get('error', 'Unknown')}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": current_user.id
            }},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {
        "message": "Retry triggered",
        "result": result,
        "ticket_updated": True
    }

@support_router.get("/admin/voucher-issues")
async def get_voucher_issue_tickets(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None
):
    """Get all tickets related to voucher/order issues for quick triage"""
    query = {
        "$or": [
            {"category": "order"},
            {"category": "redemption"},
            {"subject": {"$regex": "voucher", "$options": "i"}},
            {"description": {"$regex": "not received", "$options": "i"}}
        ]
    }
    
    if status:
        query["status"] = status
    
    tickets = await db.support_tickets.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    # Enrich with fulfillment data
    enriched_tickets = []
    for ticket in tickets:
        fulfillment = None
        if ticket.get("related_order_id"):
            fulfillment = await db.fulfillments.find_one(
                {"order_id": ticket["related_order_id"]},
                {"_id": 0, "id": 1, "status": 1, "delivery_attempt_count": 1, "last_failure_reason": 1}
            )
        
        enriched_tickets.append({
            **ticket,
            "fulfillment_status": fulfillment.get("status") if fulfillment else None,
            "delivery_attempts": fulfillment.get("delivery_attempt_count", 0) if fulfillment else None,
            "last_failure": fulfillment.get("last_failure_reason") if fulfillment else None,
            "needs_attention": (
                fulfillment and 
                fulfillment.get("status") == "failed" and 
                fulfillment.get("delivery_attempt_count", 0) >= 3
            ) if fulfillment else False
        })
    
    return {
        "tickets": enriched_tickets,
        "count": len(enriched_tickets),
        "needs_attention_count": len([t for t in enriched_tickets if t.get("needs_attention")])
    }
