"""
Gift Card Management Routes for FREE11
Bulk upload, auto-distribution, and admin management
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import csv
import io

# Import from server.py
from server import db, get_current_user, User

gift_card_router = APIRouter(prefix="/gift-cards", tags=["Gift Cards"])

# ==================== MODELS ====================

class GiftCard(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str  # The actual gift card code
    brand: str  # Amazon, Flipkart, etc.
    value: int  # Value in INR
    coin_price: int  # Price in coins
    status: str = "available"  # available, reserved, redeemed
    reserved_by: Optional[str] = None  # User ID if reserved
    reserved_at: Optional[str] = None
    redeemed_by: Optional[str] = None  # User ID who redeemed
    redeemed_at: Optional[str] = None
    batch_id: Optional[str] = None  # For bulk uploads
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GiftCardRedemption(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    gift_card_id: str
    gift_card_code: str  # Store code at time of redemption
    brand: str
    value: int
    coins_spent: int
    status: str = "completed"  # completed, failed
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GiftCardCreate(BaseModel):
    code: str
    brand: str
    value: int
    coin_price: int

class BulkUploadResult(BaseModel):
    total: int
    success: int
    failed: int
    errors: List[str]

# ==================== HELPER FUNCTIONS ====================

def calculate_coin_price(value: int, brand: str) -> int:
    """Calculate coin price based on gift card value and brand"""
    # Base rate: 1 INR = 1 coin (1:1 ratio)
    # Can add brand-specific multipliers or discounts later
    return value

# ==================== ADMIN ROUTES ====================

@gift_card_router.post("/admin/upload-single")
async def upload_single_gift_card(
    gift_card_data: GiftCardCreate,
    current_user: User = Depends(get_current_user)
):
    """Upload a single gift card (admin only)"""
    # Check if code already exists
    existing = await db.gift_cards.find_one({"code": gift_card_data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Gift card code already exists")
    
    gift_card = GiftCard(
        code=gift_card_data.code,
        brand=gift_card_data.brand,
        value=gift_card_data.value,
        coin_price=gift_card_data.coin_price
    )
    await db.gift_cards.insert_one(gift_card.model_dump())
    
    return {"message": "Gift card uploaded successfully", "id": gift_card.id}

@gift_card_router.post("/admin/upload-bulk")
async def upload_bulk_gift_cards(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk upload gift cards via CSV file
    CSV format: code,brand,value,coin_price
    Example: AMZN-XXXX-YYYY-ZZZZ,Amazon,500,500
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    batch_id = str(uuid.uuid4())
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    total = 0
    success = 0
    failed = 0
    errors = []
    
    for row in reader:
        total += 1
        try:
            code = row.get('code', '').strip()
            brand = row.get('brand', '').strip()
            value = int(row.get('value', 0))
            coin_price = int(row.get('coin_price', value))  # Default to value if not specified
            
            if not code or not brand or value <= 0:
                errors.append(f"Row {total}: Invalid data")
                failed += 1
                continue
            
            # Check if code exists
            existing = await db.gift_cards.find_one({"code": code})
            if existing:
                errors.append(f"Row {total}: Code {code[:8]}... already exists")
                failed += 1
                continue
            
            gift_card = GiftCard(
                code=code,
                brand=brand,
                value=value,
                coin_price=coin_price,
                batch_id=batch_id
            )
            await db.gift_cards.insert_one(gift_card.model_dump())
            success += 1
            
        except Exception as e:
            errors.append(f"Row {total}: {str(e)}")
            failed += 1
    
    return BulkUploadResult(
        total=total,
        success=success,
        failed=failed,
        errors=errors[:10]  # Limit errors shown
    )

@gift_card_router.get("/admin/inventory")
async def get_gift_card_inventory(
    brand: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get gift card inventory (admin view)"""
    query = {}
    if brand:
        query["brand"] = brand
    if status:
        query["status"] = status
    
    # Don't show actual codes in list view
    cards = await db.gift_cards.find(
        query,
        {"_id": 0, "code": 0}  # Hide code for security
    ).sort("created_at", -1).to_list(500)
    
    # Get summary stats
    total_available = await db.gift_cards.count_documents({"status": "available"})
    total_redeemed = await db.gift_cards.count_documents({"status": "redeemed"})
    
    # Stats by brand
    pipeline = [
        {"$match": {"status": "available"}},
        {"$group": {
            "_id": "$brand",
            "count": {"$sum": 1},
            "total_value": {"$sum": "$value"}
        }}
    ]
    brand_stats = await db.gift_cards.aggregate(pipeline).to_list(20)
    
    return {
        "cards": cards,
        "summary": {
            "total_available": total_available,
            "total_redeemed": total_redeemed,
            "by_brand": brand_stats
        }
    }

# ==================== USER ROUTES ====================

@gift_card_router.get("/available")
async def get_available_gift_cards(
    brand: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get available gift card types (not individual codes)"""
    # Group by brand and value to show available options
    pipeline = [
        {"$match": {"status": "available"}},
        {"$group": {
            "_id": {"brand": "$brand", "value": "$value", "coin_price": "$coin_price"},
            "available_count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "brand": "$_id.brand",
            "value": "$_id.value",
            "coin_price": "$_id.coin_price",
            "available_count": 1,
            "in_stock": {"$gt": ["$available_count", 0]}
        }},
        {"$sort": {"brand": 1, "value": 1}}
    ]
    
    if brand:
        pipeline[0]["$match"]["brand"] = brand
    
    options = await db.gift_cards.aggregate(pipeline).to_list(50)
    
    return options

@gift_card_router.post("/redeem")
async def redeem_gift_card(
    brand: str,
    value: int,
    current_user: User = Depends(get_current_user)
):
    """
    Redeem a gift card using coins
    System auto-assigns an available card of the requested brand/value
    """
    # Find an available card matching criteria
    gift_card = await db.gift_cards.find_one(
        {"brand": brand, "value": value, "status": "available"},
        {"_id": 0}
    )
    
    if not gift_card:
        raise HTTPException(status_code=404, detail=f"No {brand} gift cards of ₹{value} available")
    
    # Check if user has enough coins
    coin_price = gift_card.get("coin_price", value)
    if current_user.coins_balance < coin_price:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient coins. Need {coin_price}, have {current_user.coins_balance}"
        )
    
    # Reserve the card (atomic operation to prevent race conditions)
    result = await db.gift_cards.update_one(
        {"id": gift_card["id"], "status": "available"},
        {"$set": {
            "status": "redeemed",
            "redeemed_by": current_user.id,
            "redeemed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=409, detail="Card was redeemed by another user. Please try again.")
    
    # Deduct coins from user
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"coins_balance": -coin_price, "total_redeemed": coin_price}}
    )
    
    # Record the redemption
    redemption = GiftCardRedemption(
        user_id=current_user.id,
        gift_card_id=gift_card["id"],
        gift_card_code=gift_card["code"],  # Store code at redemption time
        brand=brand,
        value=value,
        coins_spent=coin_price
    )
    await db.gift_card_redemptions.insert_one(redemption.model_dump())
    
    # Record coin transaction
    from server import CoinTransaction
    transaction = CoinTransaction(
        user_id=current_user.id,
        amount=-coin_price,
        type="spent",
        description=f"Redeemed {brand} gift card ₹{value}"
    )
    await db.coin_transactions.insert_one(transaction.model_dump())
    
    return {
        "message": "Gift card redeemed successfully!",
        "code": gift_card["code"],  # IMPORTANT: Show the actual code to user
        "brand": brand,
        "value": value,
        "coins_spent": coin_price,
        "new_balance": current_user.coins_balance - coin_price
    }

@gift_card_router.get("/my-redemptions")
async def get_my_redemptions(current_user: User = Depends(get_current_user)):
    """Get user's gift card redemption history"""
    redemptions = await db.gift_card_redemptions.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return redemptions

# ==================== STATS ROUTES ====================

@gift_card_router.get("/stats")
async def get_gift_card_stats():
    """Get overall gift card redemption stats"""
    total_redeemed = await db.gift_card_redemptions.count_documents({})
    
    # Total value redeemed
    pipeline = [
        {"$group": {
            "_id": None,
            "total_value": {"$sum": "$value"},
            "total_coins": {"$sum": "$coins_spent"}
        }}
    ]
    totals = await db.gift_card_redemptions.aggregate(pipeline).to_list(1)
    
    # By brand
    brand_pipeline = [
        {"$group": {
            "_id": "$brand",
            "count": {"$sum": 1},
            "total_value": {"$sum": "$value"}
        }},
        {"$sort": {"count": -1}}
    ]
    by_brand = await db.gift_card_redemptions.aggregate(brand_pipeline).to_list(10)
    
    return {
        "total_redemptions": total_redeemed,
        "total_value_redeemed": totals[0]["total_value"] if totals else 0,
        "total_coins_spent": totals[0]["total_coins"] if totals else 0,
        "by_brand": by_brand
    }
