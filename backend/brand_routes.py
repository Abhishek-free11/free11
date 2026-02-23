"""
Brand Portal for FREE11
Dedicated /brand portal with brand-specific logins
Focus: Verified consumption & ROAS tracking
NO impression/CPM language - brands fund demand creation
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
import uuid
import os

# Import from server.py
from server import db

brand_router = APIRouter(prefix="/brand", tags=["Brand Portal"])

# ==================== AUTH CONFIG ====================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("JWT_SECRET", "free11-brand-secret-key-change-in-production")
ALGORITHM = "HS256"
security = HTTPBearer()

# ==================== MODELS ====================

class BrandAccount(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    company_name: str
    contact_name: str
    phone: Optional[str] = None
    
    # Brand identity
    brand_name: str
    brand_logo_url: Optional[str] = None
    website: Optional[str] = None
    category: str = "general"  # fmcg, electronics, lifestyle, food, entertainment
    
    # Status
    is_active: bool = True
    is_verified: bool = False
    
    # Funding commitment (not displayed publicly)
    total_budget_committed: int = 0  # In INR
    budget_utilized: int = 0
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None

class Campaign(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand_id: str
    brand_name: str
    
    name: str
    description: Optional[str] = None
    objective: str = "demand_creation"  # demand_creation, brand_awareness, product_trial
    
    # Products linked to this campaign
    product_ids: List[str] = []
    
    # Budget (internal, not public)
    budget_allocated: int = 0
    budget_consumed: int = 0
    
    # Timeline
    start_date: str
    end_date: str
    is_active: bool = True
    
    # ROAS Metrics (verified consumption only)
    total_redemptions: int = 0
    total_value_delivered: int = 0  # In INR - actual goods delivered
    unique_users_reached: int = 0
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BrandProduct(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand_id: str
    campaign_id: Optional[str] = None
    
    name: str
    description: str
    category: str
    
    # Pricing
    cost_in_coins: int
    value_in_inr: int  # Actual retail value
    
    # Inventory
    total_inventory: int = 0
    redeemed_count: int = 0
    
    # Settings
    is_active: bool = True
    requires_level: int = 1
    is_limited_drop: bool = False
    
    image_url: Optional[str] = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ==================== AUTH HELPERS ====================

def create_brand_token(brand_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": brand_id,
        "email": email,
        "type": "brand",
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_brand(credentials: HTTPAuthorizationCredentials = Depends(security)) -> BrandAccount:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "brand":
            raise HTTPException(status_code=403, detail="Invalid token type")
        
        brand = await db.brand_accounts.find_one({"id": payload["sub"]})
        if not brand:
            raise HTTPException(status_code=404, detail="Brand account not found")
        
        if not brand.get("is_active"):
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        return BrandAccount(**brand)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTH ROUTES ====================

class BrandRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    contact_name: str
    brand_name: str
    phone: Optional[str] = None
    website: Optional[str] = None
    category: str = "general"

class BrandLoginRequest(BaseModel):
    email: EmailStr
    password: str

@brand_router.post("/auth/register")
async def register_brand(data: BrandRegisterRequest):
    """Register a new brand account"""
    # Check if email exists
    existing = await db.brand_accounts.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create account
    brand = BrandAccount(
        email=data.email,
        password_hash=pwd_context.hash(data.password),
        company_name=data.company_name,
        contact_name=data.contact_name,
        brand_name=data.brand_name,
        phone=data.phone,
        website=data.website,
        category=data.category
    )
    
    await db.brand_accounts.insert_one(brand.model_dump())
    
    return {
        "message": "Brand account created successfully!",
        "brand_id": brand.id,
        "note": "Your account is pending verification. You'll receive access within 24-48 hours."
    }

import logging
logger = logging.getLogger(__name__)

@brand_router.post("/auth/login")
async def login_brand(data: BrandLoginRequest):
    """Brand portal login"""
    logger.info(f"Brand login attempt for: {data.email}")
    brand = await db.brand_accounts.find_one({"email": data.email})
    
    if not brand:
        logger.warning(f"Brand not found: {data.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    logger.info(f"Brand found: {brand.get('brand_name')}, checking password...")
    try:
        is_valid = pwd_context.verify(data.password, brand["password_hash"])
        logger.info(f"Password verification result: {is_valid}")
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        is_valid = False
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not brand.get("is_active"):
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    # Update last login
    await db.brand_accounts.update_one(
        {"id": brand["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    token = create_brand_token(brand["id"], brand["email"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "brand": {
            "id": brand["id"],
            "brand_name": brand["brand_name"],
            "company_name": brand["company_name"],
            "is_verified": brand.get("is_verified", False)
        }
    }

@brand_router.get("/auth/me")
async def get_brand_profile(brand: BrandAccount = Depends(get_current_brand)):
    """Get current brand profile"""
    return {
        "id": brand.id,
        "email": brand.email,
        "brand_name": brand.brand_name,
        "company_name": brand.company_name,
        "contact_name": brand.contact_name,
        "category": brand.category,
        "is_verified": brand.is_verified
    }

# ==================== DASHBOARD / ROAS ====================

# Environment mode detection
import os
IS_SANDBOX_MODE = os.environ.get("FREE11_ENV", "sandbox") != "production"

@brand_router.get("/dashboard")
async def get_brand_dashboard(brand: BrandAccount = Depends(get_current_brand)):
    """
    Get brand dashboard with ROAS metrics
    Focus: Verified consumption & demand creation
    NO impression/CPM metrics
    
    ATTRIBUTION: ROAS computed from actual redemptions ONLY
    NOT from: tasks, views, impressions, engagement
    """
    # Get campaigns
    campaigns = await db.brand_campaigns.find(
        {"brand_id": brand.id},
        {"_id": 0}
    ).to_list(100)
    
    # Get products
    products = await db.brand_products.find(
        {"brand_id": brand.id},
        {"_id": 0}
    ).to_list(100)
    
    # Aggregate redemption data
    total_redemptions = sum(p.get("redeemed_count", 0) for p in products)
    total_value_delivered = sum(
        p.get("redeemed_count", 0) * p.get("value_in_inr", 0) 
        for p in products
    )
    
    # Get unique users who redeemed
    unique_users = await db.fulfillments.distinct(
        "user_id",
        {"brand_id": brand.id, "status": "delivered"}
    )
    
    # Calculate ROAS (Return on Ad Spend -> Return on Demand Creation Spend)
    budget_utilized = brand.budget_utilized or 1  # Avoid division by zero
    roas = round(total_value_delivered / budget_utilized, 2) if budget_utilized > 0 else 0
    
    # Sandbox mode labeling
    consumption_label = "Test Consumption" if IS_SANDBOX_MODE else "Verified Consumption"
    
    return {
        "brand": {
            "name": brand.brand_name,
            "is_verified": brand.is_verified
        },
        # SANDBOX MODE INDICATOR
        "environment": {
            "mode": "sandbox" if IS_SANDBOX_MODE else "production",
            "is_sandbox": IS_SANDBOX_MODE,
            "data_label": "TEST DATA" if IS_SANDBOX_MODE else "LIVE DATA"
        },
        "demand_metrics": {
            "total_redemptions": total_redemptions,
            "verified_consumption_value": total_value_delivered,  # INR worth of goods delivered
            "consumption_label": consumption_label,
            "unique_consumers_reached": len(unique_users),
            "active_campaigns": len([c for c in campaigns if c.get("is_active")]),
            "active_products": len([p for p in products if p.get("is_active")])
        },
        "roas": {
            "value": roas if not IS_SANDBOX_MODE else None,  # Hide in sandbox
            "display_value": f"{roas}x" if not IS_SANDBOX_MODE else "N/A (Sandbox)",
            "description": "For every ₹1 invested in demand creation, ₹{} of verified consumption was unlocked".format(roas) if not IS_SANDBOX_MODE else "ROAS hidden in sandbox mode",
            "note": "ROAS = Total Value of Goods Consumed / Budget Invested",
            "sandbox_hidden": IS_SANDBOX_MODE
        },
        "recent_activity": {
            "last_7_days_redemptions": await db.fulfillments.count_documents({
                "brand_id": brand.id,
                "status": "delivered",
                "delivered_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()}
            }),
            "last_30_days_redemptions": await db.fulfillments.count_documents({
                "brand_id": brand.id,
                "status": "delivered",
                "delivered_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}
            })
        },
        # ATTRIBUTION INTEGRITY - explicit declaration
        "attribution_integrity": {
            "computation_basis": "verified_redemptions_only",
            "not_based_on": ["tasks", "views", "impressions", "engagement", "clicks"],
            "explanation": "All metrics are computed from actual goods delivered to users, not from ad impressions or task completions"
        }
    }

@brand_router.get("/analytics")
async def get_detailed_analytics(
    brand: BrandAccount = Depends(get_current_brand),
    days: int = 30
):
    """
    Detailed analytics for brand
    Focus: Verified consumption metrics
    
    Includes: ROAS by campaign, ROAS by SKU, ROAS by day
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Redemptions by campaign with ROAS
    campaigns = await db.brand_campaigns.find(
        {"brand_id": brand.id},
        {"_id": 0, "id": 1, "name": 1, "budget_allocated": 1}
    ).to_list(100)
    
    campaign_stats = []
    for campaign in campaigns:
        redemptions = await db.fulfillments.count_documents({
            "campaign_id": campaign["id"],
            "status": "delivered",
            "delivered_at": {"$gte": cutoff}
        })
        
        value_agg = await db.fulfillments.aggregate([
            {"$match": {
                "campaign_id": campaign["id"],
                "status": "delivered",
                "delivered_at": {"$gte": cutoff}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        value_delivered = value_agg[0]["total"] if value_agg else 0
        budget = campaign.get("budget_allocated", 1) or 1
        campaign_roas = round(value_delivered / budget, 2) if budget > 0 else 0
        
        campaign_stats.append({
            "campaign_id": campaign["id"],
            "campaign_name": campaign["name"],
            "redemptions": redemptions,
            "value_delivered": value_delivered,
            "budget_allocated": budget,
            "roas": campaign_roas if not IS_SANDBOX_MODE else None,
            "roas_display": f"{campaign_roas}x" if not IS_SANDBOX_MODE else "N/A"
        })
    
    # Product performance with ROAS by SKU
    products = await db.brand_products.find(
        {"brand_id": brand.id},
        {"_id": 0, "id": 1, "name": 1, "redeemed_count": 1, "value_in_inr": 1, "cost_in_coins": 1}
    ).sort("redeemed_count", -1).limit(20).to_list(20)
    
    product_stats = []
    for p in products:
        total_value = p.get("redeemed_count", 0) * p.get("value_in_inr", 0)
        product_stats.append({
            "product_id": p["id"],
            "product_name": p["name"],
            "redemptions": p.get("redeemed_count", 0),
            "value_per_unit": p.get("value_in_inr", 0),
            "total_value_delivered": total_value,
            "cost_per_redemption": p.get("value_in_inr", 0)
        })
    
    # ROAS by day (last N days)
    daily_stats = []
    for i in range(min(days, 30)):
        day_start = (datetime.now(timezone.utc) - timedelta(days=i)).replace(hour=0, minute=0, second=0)
        day_end = day_start + timedelta(days=1)
        
        day_redemptions = await db.fulfillments.count_documents({
            "brand_id": brand.id,
            "status": "delivered",
            "delivered_at": {
                "$gte": day_start.isoformat(),
                "$lt": day_end.isoformat()
            }
        })
        
        day_value_agg = await db.fulfillments.aggregate([
            {"$match": {
                "brand_id": brand.id,
                "status": "delivered",
                "delivered_at": {
                    "$gte": day_start.isoformat(),
                    "$lt": day_end.isoformat()
                }
            }},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        day_value = day_value_agg[0]["total"] if day_value_agg else 0
        
        daily_stats.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "redemptions": day_redemptions,
            "value_delivered": day_value
        })
    
    # User demographics (anonymized)
    user_levels = await db.fulfillments.aggregate([
        {"$match": {"brand_id": brand.id, "status": "delivered"}},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "id",
            "as": "user"
        }},
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {"$group": {"_id": "$user.level", "count": {"$sum": 1}}}
    ]).to_list(10)
    
    return {
        "period": f"Last {days} days",
        # SANDBOX INDICATOR
        "environment": {
            "mode": "sandbox" if IS_SANDBOX_MODE else "production",
            "is_sandbox": IS_SANDBOX_MODE,
            "data_label": "TEST DATA" if IS_SANDBOX_MODE else "LIVE DATA"
        },
        # ROAS by Campaign
        "roas_by_campaign": campaign_stats,
        # ROAS by SKU (product)
        "roas_by_sku": product_stats,
        # ROAS by Day
        "roas_by_day": daily_stats[:14],  # Last 14 days
        # Legacy fields
        "campaigns": campaign_stats,
        "top_products": product_stats,
        "consumer_segments": [
            {"level": segment["_id"] or 1, "consumers": segment["count"]}
            for segment in user_levels
        ],
        # Attribution integrity
        "attribution_note": "All metrics computed from verified redemptions (actual goods delivered), not from tasks/views/impressions"
    }

# ==================== CAMPAIGN MANAGEMENT ====================

class CreateCampaignRequest(BaseModel):
    name: str
    description: Optional[str] = None
    objective: str = "demand_creation"
    start_date: str
    end_date: str
    budget_allocated: int = 0

@brand_router.post("/campaigns")
async def create_campaign(
    data: CreateCampaignRequest,
    brand: BrandAccount = Depends(get_current_brand)
):
    """Create a new campaign"""
    campaign = Campaign(
        brand_id=brand.id,
        brand_name=brand.brand_name,
        name=data.name,
        description=data.description,
        objective=data.objective,
        start_date=data.start_date,
        end_date=data.end_date,
        budget_allocated=data.budget_allocated
    )
    
    await db.brand_campaigns.insert_one(campaign.model_dump())
    
    return {
        "message": "Campaign created successfully!",
        "campaign_id": campaign.id
    }

@brand_router.get("/campaigns")
async def get_campaigns(brand: BrandAccount = Depends(get_current_brand)):
    """Get all brand campaigns"""
    campaigns = await db.brand_campaigns.find(
        {"brand_id": brand.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"campaigns": campaigns}

@brand_router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    brand: BrandAccount = Depends(get_current_brand)
):
    """Get campaign details with ROAS"""
    campaign = await db.brand_campaigns.find_one(
        {"id": campaign_id, "brand_id": brand.id},
        {"_id": 0}
    )
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get linked products
    products = await db.brand_products.find(
        {"campaign_id": campaign_id},
        {"_id": 0}
    ).to_list(100)
    
    # Calculate campaign ROAS
    total_redemptions = sum(p.get("redeemed_count", 0) for p in products)
    total_value = sum(
        p.get("redeemed_count", 0) * p.get("value_in_inr", 0)
        for p in products
    )
    
    budget = campaign.get("budget_allocated", 1)
    roas = round(total_value / budget, 2) if budget > 0 else 0
    
    return {
        "campaign": campaign,
        "products": products,
        "performance": {
            "total_redemptions": total_redemptions,
            "value_delivered": total_value,
            "roas": roas
        }
    }

@brand_router.patch("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    is_active: Optional[bool] = None,
    brand: BrandAccount = Depends(get_current_brand)
):
    """Update campaign status"""
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if is_active is not None:
        update["is_active"] = is_active
    
    result = await db.brand_campaigns.update_one(
        {"id": campaign_id, "brand_id": brand.id},
        {"$set": update}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {"message": "Campaign updated"}

# ==================== PRODUCT MANAGEMENT ====================

class CreateProductRequest(BaseModel):
    name: str
    description: str
    category: str
    cost_in_coins: int
    value_in_inr: int
    total_inventory: int = 0
    campaign_id: Optional[str] = None
    requires_level: int = 1
    is_limited_drop: bool = False
    image_url: Optional[str] = None

class BulkProductUpload(BaseModel):
    products: List[CreateProductRequest]
    campaign_id: Optional[str] = None

@brand_router.post("/products")
async def create_product(
    data: CreateProductRequest,
    brand: BrandAccount = Depends(get_current_brand)
):
    """Create a new product"""
    product = BrandProduct(
        brand_id=brand.id,
        campaign_id=data.campaign_id,
        name=data.name,
        description=data.description,
        category=data.category,
        cost_in_coins=data.cost_in_coins,
        value_in_inr=data.value_in_inr,
        total_inventory=data.total_inventory,
        requires_level=data.requires_level,
        is_limited_drop=data.is_limited_drop,
        image_url=data.image_url
    )
    
    await db.brand_products.insert_one(product.model_dump())
    
    # Link to campaign if specified
    if data.campaign_id:
        await db.brand_campaigns.update_one(
            {"id": data.campaign_id},
            {"$push": {"product_ids": product.id}}
        )
    
    return {
        "message": "Product created successfully!",
        "product_id": product.id
    }

@brand_router.post("/products/bulk")
async def bulk_upload_products(
    data: BulkProductUpload,
    brand: BrandAccount = Depends(get_current_brand)
):
    """Bulk upload products (CSV-ready)"""
    created_ids = []
    
    for product_data in data.products:
        product = BrandProduct(
            brand_id=brand.id,
            campaign_id=data.campaign_id or product_data.campaign_id,
            name=product_data.name,
            description=product_data.description,
            category=product_data.category,
            cost_in_coins=product_data.cost_in_coins,
            value_in_inr=product_data.value_in_inr,
            total_inventory=product_data.total_inventory,
            requires_level=product_data.requires_level,
            is_limited_drop=product_data.is_limited_drop,
            image_url=product_data.image_url
        )
        
        await db.brand_products.insert_one(product.model_dump())
        created_ids.append(product.id)
    
    return {
        "message": f"Successfully created {len(created_ids)} products",
        "product_ids": created_ids
    }

@brand_router.get("/products")
async def get_products(
    brand: BrandAccount = Depends(get_current_brand),
    campaign_id: Optional[str] = None
):
    """Get all brand products"""
    query = {"brand_id": brand.id}
    if campaign_id:
        query["campaign_id"] = campaign_id
    
    products = await db.brand_products.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    return {"products": products}

@brand_router.patch("/products/{product_id}")
async def update_product(
    product_id: str,
    is_active: Optional[bool] = None,
    cost_in_coins: Optional[int] = None,
    total_inventory: Optional[int] = None,
    brand: BrandAccount = Depends(get_current_brand)
):
    """Update product settings"""
    update = {}
    if is_active is not None:
        update["is_active"] = is_active
    if cost_in_coins is not None:
        update["cost_in_coins"] = cost_in_coins
    if total_inventory is not None:
        update["total_inventory"] = total_inventory
    
    if not update:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = await db.brand_products.update_one(
        {"id": product_id, "brand_id": brand.id},
        {"$set": update}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product updated"}

# ==================== REDEMPTION TRACKING ====================

@brand_router.get("/redemptions")
async def get_redemptions(
    brand: BrandAccount = Depends(get_current_brand),
    campaign_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get redemptions for brand products"""
    query = {"brand_id": brand.id}
    if campaign_id:
        query["campaign_id"] = campaign_id
    if status:
        query["status"] = status
    
    redemptions = await db.fulfillments.find(
        query,
        {"_id": 0, "voucher_code": 0, "voucher_pin": 0}  # Don't expose voucher details
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"redemptions": redemptions, "count": len(redemptions)}

# ==================== EXPORT ====================

@brand_router.get("/export/redemptions")
async def export_redemptions(
    brand: BrandAccount = Depends(get_current_brand),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export redemptions data (CSV-ready JSON)"""
    query = {"brand_id": brand.id, "status": "delivered"}
    
    if start_date:
        query["delivered_at"] = {"$gte": start_date}
    if end_date:
        if "delivered_at" in query:
            query["delivered_at"]["$lte"] = end_date
        else:
            query["delivered_at"] = {"$lte": end_date}
    
    redemptions = await db.fulfillments.find(
        query,
        {"_id": 0, "voucher_code": 0, "voucher_pin": 0, "provider_response": 0}
    ).to_list(10000)
    
    return {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "brand": brand.brand_name,
        "total_records": len(redemptions),
        "data": redemptions
    }
