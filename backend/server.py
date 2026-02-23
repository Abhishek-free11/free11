from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import random
import sys

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'free11_db')]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Create the main app
app = FastAPI(title="FREE11 API")
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

# User Rank Tiers (Progression System)
USER_RANKS = {
    1: {"name": "Rookie", "min_xp": 0, "color": "#94a3b8"},
    2: {"name": "Amateur", "min_xp": 100, "color": "#22c55e"},
    3: {"name": "Pro", "min_xp": 500, "color": "#3b82f6"},
    4: {"name": "Expert", "min_xp": 1500, "color": "#a855f7"},
    5: {"name": "Legend", "min_xp": 5000, "color": "#eab308"},
}

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    password_hash: Optional[str] = None
    google_id: Optional[str] = None
    coins_balance: int = 0
    level: int = 1
    xp: int = 0
    streak_days: int = 0
    last_checkin: Optional[str] = None
    total_earned: int = 0
    total_redeemed: int = 0
    # Progression System
    prediction_streak: int = 0  # Consecutive correct predictions
    total_predictions: int = 0
    correct_predictions: int = 0
    consumption_unlocked: int = 0  # Total value in paise of goods redeemed
    badges: List[str] = Field(default_factory=list)  # List of badge IDs
    last_activity: Optional[str] = None  # For coin expiry warning
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict

class CoinTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: int
    type: str  # earned, spent, bonus
    description: str
    source: str = "skill"  # skill, booster, bonus (for categorization)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Badge definitions
BADGES = {
    "first_prediction": {"title": "First Prediction", "description": "Made your first cricket prediction", "icon": "🎯"},
    "prediction_pro": {"title": "Prediction Pro", "description": "Reached 50% prediction accuracy", "icon": "🏆"},
    "streak_7": {"title": "7-Day Streak", "description": "Maintained a 7-day check-in streak", "icon": "🔥"},
    "streak_30": {"title": "Monthly Master", "description": "Maintained a 30-day check-in streak", "icon": "⚡"},
    "first_redemption": {"title": "First Redemption", "description": "Redeemed your first reward", "icon": "🎁"},
    "level_pro": {"title": "Pro Player", "description": "Reached Pro level", "icon": "⭐"},
    "level_expert": {"title": "Expert Predictor", "description": "Reached Expert level", "icon": "💎"},
    "level_legend": {"title": "Legendary", "description": "Reached Legend level", "icon": "👑"},
    "hot_streak": {"title": "Hot Streak", "description": "5 correct predictions in a row", "icon": "🎯"},
    "consumption_100": {"title": "First ₹100", "description": "Unlocked ₹100 worth of goods", "icon": "💰"},
    "consumption_500": {"title": "Power Consumer", "description": "Unlocked ₹500 worth of goods", "icon": "🛒"},
}

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str
    coin_price: int
    base_coin_price: Optional[int] = None  # For dynamic pricing
    image_url: str
    stock: int
    brand: str
    # Brand-funded fields (Demand Rail)
    brand_id: str = "default_brand"
    campaign_id: Optional[str] = None
    funded_by_brand: bool = True
    # Fulfillment abstraction (ONDC/Q-Comm ready)
    fulfillment_type: str = "direct"  # direct, ondc_bap, qcomm, d2c
    # Economy controls
    min_level_required: int = 1  # Shop tier unlock
    is_limited_drop: bool = False
    drop_expires_at: Optional[str] = None
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    coin_price: int
    image_url: str
    stock: int
    brand: str
    brand_id: Optional[str] = "default_brand"
    campaign_id: Optional[str] = None
    funded_by_brand: bool = True
    fulfillment_type: str = "direct"
    min_level_required: int = 1
    is_limited_drop: bool = False

class Redemption(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str
    product_name: str
    coins_spent: int
    status: str = "pending"  # pending, confirmed, shipped, delivered
    order_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    delivery_address: Optional[str] = None
    # Brand attribution (Demand Rail)
    brand_id: Optional[str] = None
    campaign_id: Optional[str] = None
    fulfillment_type: str = "direct"
    # For ROAS tracking
    sku: Optional[str] = None
    brand_cost: Optional[int] = None  # Cost to brand in paise

class RedemptionCreate(BaseModel):
    product_id: str
    delivery_address: Optional[str] = None

class Activity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    activity_type: str  # checkin, task, quiz, spin, scratch
    coins_earned: int
    details: Optional[Dict] = None
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Achievement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    achievement_type: str
    title: str
    description: str
    earned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class QuizSubmission(BaseModel):
    answers: List[int]  # List of selected answer indices

class TaskComplete(BaseModel):
    task_id: str

# ==================== HELPER FUNCTIONS ====================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise credentials_exception
    return User(**user)

async def add_coins(user_id: str, amount: int, transaction_type: str, description: str):
    """Add coins to user balance and record transaction"""
    # Update user balance
    await db.users.update_one(
        {"id": user_id},
        {
            "$inc": {"coins_balance": amount, "total_earned": amount, "xp": amount},
            "$set": {"level": calculate_level(await get_user_xp(user_id) + amount)}
        }
    )
    
    # Record transaction
    transaction = CoinTransaction(
        user_id=user_id,
        amount=amount,
        type=transaction_type,
        description=description
    )
    await db.coin_transactions.insert_one(transaction.model_dump())
    
    return transaction

async def spend_coins(user_id: str, amount: int, description: str):
    """Spend coins from user balance"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user['coins_balance'] < amount:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"coins_balance": -amount, "total_redeemed": amount}}
    )
    
    transaction = CoinTransaction(
        user_id=user_id,
        amount=-amount,
        type="spent",
        description=description
    )
    await db.coin_transactions.insert_one(transaction.model_dump())

async def get_user_xp(user_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return user.get('xp', 0) if user else 0

def calculate_level(xp: int):
    """Calculate user level based on XP"""
    if xp < 100:
        return 1
    elif xp < 500:
        return 2
    elif xp < 1500:
        return 3
    elif xp < 5000:
        return 4
    else:
        return 5

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        coins_balance=50  # Welcome bonus
    )
    
    await db.users.insert_one(user.model_dump())
    
    # Create welcome transaction
    await add_coins(user.id, 50, "bonus", "Welcome bonus")
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    user_dict = user.model_dump()
    user_dict.pop('password_hash', None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_dict
    }

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user or not verify_password(user_data.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user['id']})
    
    user.pop('password_hash', None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    user_dict = current_user.model_dump()
    user_dict.pop('password_hash', None)
    return user_dict

# ==================== COINS ROUTES ====================

@api_router.get("/coins/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    return {"coins_balance": current_user.coins_balance}

@api_router.get("/coins/transactions")
async def get_transactions(current_user: User = Depends(get_current_user)):
    transactions = await db.coin_transactions.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(50).to_list(50)
    return transactions

@api_router.post("/coins/checkin")
async def daily_checkin(current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    
    if current_user.last_checkin == today:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Calculate streak
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    new_streak = current_user.streak_days + 1 if current_user.last_checkin == yesterday else 1
    
    # Calculate reward (increases with streak)
    base_reward = 10
    streak_bonus = min(new_streak * 5, 50)  # Max 50 bonus
    total_reward = base_reward + streak_bonus
    
    # Update user
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"last_checkin": today, "streak_days": new_streak}}
    )
    
    # Add coins
    transaction = await add_coins(
        current_user.id,
        total_reward,
        "earned",
        f"Daily check-in (Day {new_streak})"
    )
    
    # Record activity
    activity = Activity(
        user_id=current_user.id,
        activity_type="checkin",
        coins_earned=total_reward,
        details={"streak": new_streak}
    )
    await db.activities.insert_one(activity.model_dump())
    
    return {
        "message": "Check-in successful!",
        "coins_earned": total_reward,
        "streak_days": new_streak,
        "new_balance": current_user.coins_balance + total_reward
    }

# ==================== GAME ROUTES ====================

@api_router.post("/games/quiz")
async def play_quiz(submission: QuizSubmission, current_user: User = Depends(get_current_user)):
    # Quiz questions (hardcoded for POC)
    correct_answers = [0, 2, 1, 3, 0]  # Correct answer indices
    
    # Calculate score
    correct_count = sum(1 for i, ans in enumerate(submission.answers) if i < len(correct_answers) and ans == correct_answers[i])
    total_questions = len(correct_answers)
    score_percentage = (correct_count / total_questions) * 100
    
    # Calculate reward based on score
    coins_earned = int(correct_count * 10)
    
    if coins_earned > 0:
        transaction = await add_coins(
            current_user.id,
            coins_earned,
            "earned",
            f"Quiz completed ({correct_count}/{total_questions} correct)"
        )
        
        activity = Activity(
            user_id=current_user.id,
            activity_type="quiz",
            coins_earned=coins_earned,
            details={"score": score_percentage, "correct": correct_count, "total": total_questions}
        )
        await db.activities.insert_one(activity.model_dump())
    
    return {
        "correct_count": correct_count,
        "total_questions": total_questions,
        "score_percentage": score_percentage,
        "coins_earned": coins_earned,
        "new_balance": current_user.coins_balance + coins_earned
    }

@api_router.post("/games/spin")
async def spin_wheel(current_user: User = Depends(get_current_user)):
    # Check if already played today
    today = datetime.now(timezone.utc).date().isoformat()
    last_spin = await db.activities.find_one(
        {"user_id": current_user.id, "activity_type": "spin"},
        {"_id": 0},
        sort=[("completed_at", -1)]
    )
    
    if last_spin:
        last_spin_date = datetime.fromisoformat(last_spin['completed_at']).date().isoformat()
        if last_spin_date == today:
            raise HTTPException(status_code=400, detail="Already spun today! Come back tomorrow.")
    
    # Random reward (weighted)
    rewards = [5, 10, 15, 20, 25, 50, 100, 0]
    weights = [25, 30, 20, 15, 5, 3, 1, 1]  # % probability
    coins_earned = random.choices(rewards, weights=weights)[0]
    
    if coins_earned > 0:
        transaction = await add_coins(
            current_user.id,
            coins_earned,
            "earned",
            f"Spin the wheel"
        )
    
    activity = Activity(
        user_id=current_user.id,
        activity_type="spin",
        coins_earned=coins_earned,
        details={"reward": coins_earned}
    )
    await db.activities.insert_one(activity.model_dump())
    
    return {
        "coins_earned": coins_earned,
        "new_balance": current_user.coins_balance + coins_earned,
        "message": "Better luck next time!" if coins_earned == 0 else f"Congratulations! You won {coins_earned} coins!"
    }

@api_router.post("/games/scratch")
async def scratch_card(current_user: User = Depends(get_current_user)):
    # Check daily limit
    today = datetime.now(timezone.utc).date().isoformat()
    scratch_count = await db.activities.count_documents({
        "user_id": current_user.id,
        "activity_type": "scratch",
        "completed_at": {"$gte": today}
    })
    
    if scratch_count >= 3:
        raise HTTPException(status_code=400, detail="Daily scratch card limit reached (3/day)")
    
    # Random reward
    rewards = [0, 5, 10, 15, 20, 50]
    weights = [40, 30, 15, 10, 4, 1]
    coins_earned = random.choices(rewards, weights=weights)[0]
    
    if coins_earned > 0:
        await add_coins(
            current_user.id,
            coins_earned,
            "earned",
            f"Scratch card"
        )
    
    activity = Activity(
        user_id=current_user.id,
        activity_type="scratch",
        coins_earned=coins_earned,
        details={"reward": coins_earned, "attempt": scratch_count + 1}
    )
    await db.activities.insert_one(activity.model_dump())
    
    return {
        "coins_earned": coins_earned,
        "new_balance": current_user.coins_balance + coins_earned,
        "attempts_left": 2 - scratch_count
    }

# ==================== TASKS ROUTES ====================

@api_router.get("/tasks")
async def get_tasks(current_user: User = Depends(get_current_user)):
    # Get completed tasks today
    today = datetime.now(timezone.utc).date().isoformat()
    completed_tasks = await db.activities.find({
        "user_id": current_user.id,
        "activity_type": "task",
        "completed_at": {"$gte": today}
    }, {"_id": 0}).to_list(100)
    
    completed_task_ids = [task['details']['task_id'] for task in completed_tasks if task.get('details')]
    
    # Available tasks
    tasks = [
        {"id": "task_1", "title": "Watch Brand Video", "description": "Watch a 30-second brand video", "coins": 5, "type": "video"},
        {"id": "task_2", "title": "Complete Survey", "description": "Share your opinion (2 mins)", "coins": 15, "type": "survey"},
        {"id": "task_3", "title": "Share FREE11", "description": "Share FREE11 on social media", "coins": 20, "type": "share"},
        {"id": "task_4", "title": "Browse Products", "description": "Browse at least 5 products", "coins": 10, "type": "browse"},
        {"id": "task_5", "title": "Update Profile", "description": "Complete your profile information", "coins": 25, "type": "profile"},
    ]
    
    for task in tasks:
        task['completed'] = task['id'] in completed_task_ids
    
    return tasks

@api_router.post("/tasks/complete")
async def complete_task(task_data: TaskComplete, current_user: User = Depends(get_current_user)):
    # Check if already completed today
    today = datetime.now(timezone.utc).date().isoformat()
    existing = await db.activities.find_one({
        "user_id": current_user.id,
        "activity_type": "task",
        "details.task_id": task_data.task_id,
        "completed_at": {"$gte": today}
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Task already completed today")
    
    # Task rewards
    task_rewards = {
        "task_1": 5,
        "task_2": 15,
        "task_3": 20,
        "task_4": 10,
        "task_5": 25
    }
    
    coins_earned = task_rewards.get(task_data.task_id, 0)
    
    if coins_earned > 0:
        await add_coins(
            current_user.id,
            coins_earned,
            "earned",
            f"Task completed: {task_data.task_id}"
        )
        
        activity = Activity(
            user_id=current_user.id,
            activity_type="task",
            coins_earned=coins_earned,
            details={"task_id": task_data.task_id}
        )
        await db.activities.insert_one(activity.model_dump())
    
    return {
        "message": "Task completed!",
        "coins_earned": coins_earned,
        "new_balance": current_user.coins_balance + coins_earned
    }

# ==================== PRODUCTS ROUTES ====================

@api_router.get("/products")
async def get_products(category: Optional[str] = None):
    query = {"active": True}
    if category and category != "all":
        query["category"] = category
    
    products = await db.products.find(query, {"_id": 0}).to_list(100)
    return products

@api_router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.post("/products", response_model=Product)
async def create_product(product: ProductCreate, current_user: User = Depends(get_current_user)):
    # Simple admin check (in production, use proper role-based access)
    product_obj = Product(**product.model_dump())
    await db.products.insert_one(product_obj.model_dump())
    return product_obj

# ==================== REDEMPTIONS ROUTES ====================

@api_router.post("/redemptions")
async def create_redemption(redemption_data: RedemptionCreate, current_user: User = Depends(get_current_user)):
    # Get product
    product = await db.products.find_one({"id": redemption_data.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user has enough coins
    if current_user.coins_balance < product['coin_price']:
        raise HTTPException(status_code=400, detail=f"Insufficient coins. Need {product['coin_price']}, have {current_user.coins_balance}")
    
    # Check stock
    if product['stock'] <= 0:
        raise HTTPException(status_code=400, detail="Product out of stock")
    
    # Spend coins
    await spend_coins(current_user.id, product['coin_price'], f"Redeemed: {product['name']}")
    
    # Update stock
    await db.products.update_one(
        {"id": redemption_data.product_id},
        {"$inc": {"stock": -1}}
    )
    
    # Create redemption
    redemption = Redemption(
        user_id=current_user.id,
        product_id=product['id'],
        product_name=product['name'],
        coins_spent=product['coin_price'],
        delivery_address=redemption_data.delivery_address
    )
    await db.redemptions.insert_one(redemption.model_dump())
    
    # Check for first redemption achievement
    redemption_count = await db.redemptions.count_documents({"user_id": current_user.id})
    if redemption_count == 1:
        achievement = Achievement(
            user_id=current_user.id,
            achievement_type="first_redemption",
            title="First Purchase!",
            description="Completed your first redemption"
        )
        await db.achievements.insert_one(achievement.model_dump())
    
    return {
        "message": "Redemption successful!",
        "redemption": redemption.model_dump(),
        "new_balance": current_user.coins_balance - product['coin_price']
    }

@api_router.get("/redemptions")
async def get_redemptions(current_user: User = Depends(get_current_user)):
    redemptions = await db.redemptions.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("order_date", -1).to_list(100)
    return redemptions

@api_router.get("/redemptions/all")
async def get_all_redemptions():
    """Admin endpoint to get all redemptions"""
    redemptions = await db.redemptions.find({}, {"_id": 0}).sort("order_date", -1).to_list(1000)
    return redemptions

# ==================== USER ROUTES ====================

@api_router.get("/user/stats")
async def get_user_stats(current_user: User = Depends(get_current_user)):
    activities_count = await db.activities.count_documents({"user_id": current_user.id})
    redemptions_count = await db.redemptions.count_documents({"user_id": current_user.id})
    achievements = await db.achievements.find({"user_id": current_user.id}, {"_id": 0}).to_list(100)
    
    return {
        "user": current_user.model_dump(),
        "activities_count": activities_count,
        "redemptions_count": redemptions_count,
        "achievements": achievements
    }

@api_router.get("/user/demand-progress")
async def get_demand_progress(current_user: User = Depends(get_current_user)):
    """
    Get user's progress in the Demand Rail
    Shows: next reachable reward, prediction accuracy, consumption unlocked
    """
    user_data = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    
    # Get cheapest available product user can reach
    products = await db.products.find(
        {"active": True, "stock": {"$gt": 0}, "min_level_required": {"$lte": current_user.level}},
        {"_id": 0}
    ).sort("coin_price", 1).to_list(100)
    
    next_reward = None
    for p in products:
        if p["coin_price"] > current_user.coins_balance:
            next_reward = p
            break
    
    # If user has enough for all shown, get the cheapest one
    if not next_reward and products:
        next_reward = products[0]
    
    # Calculate prediction accuracy
    total_predictions = user_data.get("total_predictions", 0)
    correct_predictions = user_data.get("correct_predictions", 0)
    accuracy = round((correct_predictions / total_predictions * 100), 1) if total_predictions > 0 else 0
    
    # Get consumption unlocked (from redemptions)
    consumption_pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {"_id": None, "total": {"$sum": "$coins_spent"}}}
    ]
    consumption_result = await db.redemptions.aggregate(consumption_pipeline).to_list(1)
    consumption_unlocked = consumption_result[0]["total"] if consumption_result else 0
    
    # Get rank info
    level = current_user.level
    rank_info = USER_RANKS.get(level, USER_RANKS[1])
    next_rank = USER_RANKS.get(level + 1) if level < 5 else None
    
    return {
        "coins_balance": current_user.coins_balance,
        "next_reward": {
            "name": next_reward["name"] if next_reward else None,
            "coin_price": next_reward["coin_price"] if next_reward else 0,
            "progress": round((current_user.coins_balance / next_reward["coin_price"]) * 100, 1) if next_reward and next_reward["coin_price"] > 0 else 100,
            "coins_needed": max(0, next_reward["coin_price"] - current_user.coins_balance) if next_reward else 0,
            "image_url": next_reward.get("image_url") if next_reward else None
        } if next_reward else None,
        "prediction_stats": {
            "total": total_predictions,
            "correct": correct_predictions,
            "accuracy": accuracy,
            "streak": user_data.get("prediction_streak", 0)
        },
        "consumption_unlocked": consumption_unlocked,
        "rank": {
            "level": level,
            "name": rank_info["name"],
            "color": rank_info["color"],
            "xp": current_user.xp,
            "next_rank": next_rank["name"] if next_rank else None,
            "xp_to_next": next_rank["min_xp"] - current_user.xp if next_rank else 0
        },
        "badges": user_data.get("badges", [])
    }

@api_router.get("/user/badges")
async def get_user_badges(current_user: User = Depends(get_current_user)):
    """Get user's earned badges and available badges"""
    user_data = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    earned_badges = user_data.get("badges", [])
    
    all_badges = []
    for badge_id, badge_info in BADGES.items():
        all_badges.append({
            "id": badge_id,
            "title": badge_info["title"],
            "description": badge_info["description"],
            "icon": badge_info["icon"],
            "earned": badge_id in earned_badges
        })
    
    return {
        "earned_count": len(earned_badges),
        "total_count": len(BADGES),
        "badges": all_badges
    }

@api_router.get("/leaderboard")
async def get_leaderboard():
    """Get leaderboard based on SKILL (prediction accuracy), not coins"""
    # Aggregate from ball predictions for skill-based leaderboard
    pipeline = [
        {"$group": {
            "_id": "$user_id",
            "total_predictions": {"$sum": 1},
            "correct_predictions": {"$sum": {"$cond": ["$is_correct", 1, 0]}}
        }},
        {"$match": {"total_predictions": {"$gte": 5}}},  # Min 5 predictions to qualify
        {"$addFields": {
            "accuracy": {"$multiply": [{"$divide": ["$correct_predictions", "$total_predictions"]}, 100]}
        }},
        {"$sort": {"accuracy": -1, "correct_predictions": -1}},
        {"$limit": 10}
    ]
    
    leaderboard_data = await db.ball_predictions.aggregate(pipeline).to_list(10)
    
    # Enrich with user data
    result = []
    for entry in leaderboard_data:
        user = await db.users.find_one({"id": entry["_id"]}, {"_id": 0, "name": 1, "level": 1})
        if user:
            result.append({
                "id": entry["_id"],
                "name": user.get("name", "Anonymous"),
                "level": user.get("level", 1),
                "accuracy": round(entry["accuracy"], 1),
                "total_predictions": entry["total_predictions"],
                "correct_predictions": entry["correct_predictions"]
            })
    
    # Fallback to old leaderboard if no predictions yet
    if not result:
        users = await db.users.find(
            {},
            {"_id": 0, "id": 1, "name": 1, "total_earned": 1, "level": 1}
        ).sort("total_earned", -1).limit(10).to_list(10)
        return users
    
    return result

# ==================== FAQ ROUTES ====================

@api_router.get("/faq")
async def get_faq():
    """
    Get FAQ items for the platform
    Includes PRORGA-compliant coin policy information
    """
    faq_items = [
        {
            "id": "coin-policy",
            "question": "What are FREE11 Coins and can I withdraw them?",
            "answer": "FREE11 Coins are non-withdrawable reward tokens redeemable only for goods/services. No cash. No betting. Brand-funded rewards.",
            "category": "coins",
            "priority": 1
        },
        {
            "id": "how-to-earn",
            "question": "How do I earn FREE11 Coins?",
            "answer": "You earn coins primarily through cricket predictions. Make accurate predictions to earn more coins! You can also boost your earnings with daily check-ins, mini-games, and completing tasks.",
            "category": "earning",
            "priority": 2
        },
        {
            "id": "redemption",
            "question": "How do I redeem my coins?",
            "answer": "Visit the Redeem section to browse available rewards. Select a product, confirm your order, and we'll process your redemption. All rewards are brand-funded and delivered digitally or physically based on the product.",
            "category": "redemption",
            "priority": 3
        },
        {
            "id": "skill-levels",
            "question": "What are skill levels and how do I progress?",
            "answer": "Your skill level (Rookie → Amateur → Pro → Expert → Legend) reflects your prediction accuracy and engagement. Higher levels unlock premium rewards and exclusive drops!",
            "category": "progression",
            "priority": 4
        },
        {
            "id": "brand-funded",
            "question": "What does 'Brand-funded' mean?",
            "answer": "All rewards on FREE11 are funded by our brand partners. This means you're getting real products and vouchers from brands like Amazon, Swiggy, Netflix, and more - at no cost to you!",
            "category": "rewards",
            "priority": 5
        },
        {
            "id": "coin-expiry",
            "question": "Do my coins expire?",
            "answer": "Coins remain active as long as you maintain regular activity on the platform. Extended inactivity (60+ days) may result in coin expiry warnings. Stay active and keep predicting!",
            "category": "coins",
            "priority": 6
        },
        {
            "id": "leaderboard",
            "question": "How is the leaderboard ranked?",
            "answer": "Our leaderboard ranks users by prediction SKILL (accuracy and streaks), not by total coins. This ensures the best predictors rise to the top!",
            "category": "progression",
            "priority": 7
        },
        {
            "id": "legal-safe",
            "question": "Is FREE11 legal and safe?",
            "answer": "Yes! FREE11 is a skill-based rewards platform, not a gambling app. Our coin system is fully compliant with Indian regulations - coins cannot be purchased, withdrawn, or transferred. It's 100% safe and legal.",
            "category": "legal",
            "priority": 8
        }
    ]
    
    return {
        "items": faq_items,
        "disclaimer": "FREE11 Coins are non-withdrawable reward tokens redeemable only for goods/services. No cash. No betting. Brand-funded rewards."
    }

# ==================== ADMIN ROUTES ====================

@api_router.get("/admin/analytics")
async def get_analytics():
    total_users = await db.users.count_documents({})
    total_redemptions = await db.redemptions.count_documents({})
    total_products = await db.products.count_documents({"active": True})
    
    # Total coins in circulation
    pipeline = [
        {"$group": {"_id": None, "total_coins": {"$sum": "$coins_balance"}}}
    ]
    result = await db.users.aggregate(pipeline).to_list(1)
    total_coins = result[0]['total_coins'] if result else 0
    
    return {
        "total_users": total_users,
        "total_redemptions": total_redemptions,
        "total_products": total_products,
        "total_coins_in_circulation": total_coins
    }

@api_router.get("/admin/brand-roas")
async def get_brand_roas():
    """
    Placeholder Brand ROAS Dashboard
    Shows redemption attribution by brand for partner reporting
    """
    # Aggregate redemptions by brand
    pipeline = [
        {"$group": {
            "_id": "$brand_id",
            "total_redemptions": {"$sum": 1},
            "total_coins_spent": {"$sum": "$coins_spent"},
            "unique_users": {"$addToSet": "$user_id"}
        }},
        {"$addFields": {
            "unique_user_count": {"$size": "$unique_users"}
        }},
        {"$project": {"unique_users": 0}},
        {"$sort": {"total_redemptions": -1}}
    ]
    
    brand_data = await db.redemptions.aggregate(pipeline).to_list(50)
    
    return {
        "message": "Brand ROAS Dashboard (Placeholder)",
        "note": "Full attribution tracking will be enabled with live brand integrations",
        "brand_performance": brand_data,
        "total_demand_created": sum(b.get("total_coins_spent", 0) for b in brand_data)
    }

# ==================== SEED DATA ====================

@api_router.post("/seed-products")
async def seed_products():
    """Seed database with brand-funded products including impulse rewards"""
    # Clear existing products for fresh seed
    await db.products.delete_many({})
    
    sample_products = [
        # ============ IMPULSE REWARDS (₹10-₹50) - Entry tier ============
        {
            "name": "Mobile Recharge ₹10",
            "description": "Instant mobile recharge for any operator",
            "category": "recharge",
            "coin_price": 10,
            "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400",
            "stock": 1000,
            "brand": "Jio/Airtel",
            "brand_id": "telecom_partner",
            "campaign_id": "ipl2026_recharge",
            "funded_by_brand": True,
            "fulfillment_type": "direct",
            "min_level_required": 1
        },
        {
            "name": "Mobile Recharge ₹20",
            "description": "Instant mobile recharge for any operator",
            "category": "recharge",
            "coin_price": 20,
            "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400",
            "stock": 1000,
            "brand": "Jio/Airtel",
            "brand_id": "telecom_partner",
            "campaign_id": "ipl2026_recharge",
            "funded_by_brand": True,
            "fulfillment_type": "direct",
            "min_level_required": 1
        },
        {
            "name": "Mobile Recharge ₹50",
            "description": "Instant mobile recharge for any operator",
            "category": "recharge",
            "coin_price": 50,
            "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400",
            "stock": 500,
            "brand": "Jio/Airtel",
            "brand_id": "telecom_partner",
            "campaign_id": "ipl2026_recharge",
            "funded_by_brand": True,
            "fulfillment_type": "direct",
            "min_level_required": 1
        },
        {
            "name": "Cafe Coffee Day ₹50",
            "description": "Coffee or snack at any CCD outlet",
            "category": "food",
            "coin_price": 50,
            "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400",
            "stock": 200,
            "brand": "CCD",
            "brand_id": "ccd_india",
            "campaign_id": "ipl2026_ccd",
            "funded_by_brand": True,
            "fulfillment_type": "direct",
            "min_level_required": 1
        },
        {
            "name": "Netflix 1-Week Trial",
            "description": "Stream unlimited shows for 7 days",
            "category": "ott",
            "coin_price": 30,
            "image_url": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400",
            "stock": 300,
            "brand": "Netflix",
            "brand_id": "netflix_india",
            "campaign_id": "ipl2026_ott",
            "funded_by_brand": True,
            "fulfillment_type": "direct",
            "min_level_required": 1
        },
        {
            "name": "Hotstar 3-Day Pass",
            "description": "Watch IPL matches live!",
            "category": "ott",
            "coin_price": 25,
            "image_url": "https://images.unsplash.com/photo-1522869635100-9f4c5e86aa37?w=400",
            "stock": 500,
            "brand": "Disney+ Hotstar",
            "brand_id": "hotstar_india",
            "campaign_id": "ipl2026_hotstar",
            "funded_by_brand": True,
            "fulfillment_type": "direct",
            "min_level_required": 1,
            "is_limited_drop": True
        },
        # ============ MID-TIER REWARDS (₹100-₹500) ============
        {
            "name": "Swiggy Voucher ₹100",
            "description": "Order your favorite food",
            "category": "food",
            "coin_price": 100,
            "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400",
            "stock": 300,
            "brand": "Swiggy",
            "brand_id": "swiggy_india",
            "campaign_id": "ipl2026_food",
            "funded_by_brand": True,
            "fulfillment_type": "qcomm",
            "min_level_required": 1
        },
        {
            "name": "Swiggy Voucher ₹200",
            "description": "Order your favorite food",
            "category": "food",
            "coin_price": 200,
            "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400",
            "stock": 200,
            "brand": "Swiggy",
            "brand_id": "swiggy_india",
            "campaign_id": "ipl2026_food",
            "funded_by_brand": True,
            "fulfillment_type": "qcomm",
            "min_level_required": 2
        },
        {
            "name": "Amazon Gift Card ₹100",
            "description": "Shop anything on Amazon",
            "category": "vouchers",
            "coin_price": 100,
            "image_url": "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?w=400",
            "stock": 200,
            "brand": "Amazon",
            "brand_id": "amazon_india",
            "campaign_id": "ipl2026_amazon",
            "funded_by_brand": True,
            "fulfillment_type": "direct",
            "min_level_required": 1
        },
        {
            "name": "Amazon Gift Card ₹500",
            "description": "Shop anything on Amazon",
            "category": "vouchers",
            "coin_price": 500,
            "image_url": "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?w=400",
            "stock": 100,
            "brand": "Amazon",
            "brand_id": "amazon_india",
            "campaign_id": "ipl2026_amazon",
            "funded_by_brand": True,
            "fulfillment_type": "direct",
            "min_level_required": 2
        },
        {
            "name": "Grocery Bundle ₹200",
            "description": "Essential groceries delivered home",
            "category": "groceries",
            "coin_price": 200,
            "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400",
            "stock": 300,
            "brand": "BigBasket",
            "brand_id": "bigbasket_india",
            "campaign_id": "ipl2026_grocery",
            "funded_by_brand": True,
            "fulfillment_type": "qcomm",
            "min_level_required": 2
        },
        # ============ PREMIUM REWARDS (₹1000+) - Higher tiers ============
        {
            "name": "Flipkart Voucher ₹1000",
            "description": "Shop electronics, fashion & more",
            "category": "vouchers",
            "coin_price": 1000,
            "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400",
            "stock": 50,
            "brand": "Flipkart",
            "brand_id": "flipkart_india",
            "campaign_id": "ipl2026_flipkart",
            "funded_by_brand": True,
            "fulfillment_type": "ondc_bap",
            "min_level_required": 3
        },
        {
            "name": "Nike Running Shoes",
            "description": "Premium athletic footwear",
            "category": "fashion",
            "coin_price": 5000,
            "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
            "stock": 30,
            "brand": "Nike",
            "brand_id": "nike_india",
            "campaign_id": "ipl2026_sports",
            "funded_by_brand": True,
            "fulfillment_type": "d2c",
            "min_level_required": 4
        },
        {
            "name": "Sony WH-1000XM5",
            "description": "Industry-leading noise cancellation",
            "category": "electronics",
            "coin_price": 15000,
            "image_url": "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400",
            "stock": 10,
            "brand": "Sony",
            "brand_id": "sony_india",
            "campaign_id": "ipl2026_electronics",
            "funded_by_brand": True,
            "fulfillment_type": "d2c",
            "min_level_required": 4
        },
        {
            "name": "Samsung Galaxy S24",
            "description": "Flagship Android smartphone",
            "category": "electronics",
            "coin_price": 35000,
            "image_url": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400",
            "stock": 5,
            "brand": "Samsung",
            "brand_id": "samsung_india",
            "campaign_id": "ipl2026_electronics",
            "funded_by_brand": True,
            "fulfillment_type": "d2c",
            "min_level_required": 5,
            "is_limited_drop": True
        },
        {
            "name": "iPhone 15 Pro",
            "description": "Latest Apple iPhone with A17 Pro chip",
            "category": "electronics",
            "coin_price": 50000,
            "image_url": "https://images.unsplash.com/photo-1696446702281-1af638e15d2e?w=400",
            "stock": 3,
            "brand": "Apple",
            "brand_id": "apple_india",
            "campaign_id": "ipl2026_electronics",
            "funded_by_brand": True,
            "fulfillment_type": "d2c",
            "min_level_required": 5,
            "is_limited_drop": True
        }
    ]
    
    for product_data in sample_products:
        product = Product(**product_data)
        await db.products.insert_one(product.model_dump())
    
    return {"message": f"Seeded {len(sample_products)} brand-funded products with impulse rewards"}

# ==================== ROOT ====================

@api_router.get("/")
async def root():
    return {"message": "FREE11 API - Everything here is free, except your time! 🪙"}

# Include router
app.include_router(api_router)

# Import and include additional routers
# Add backend directory to path for imports
sys.path.insert(0, str(ROOT_DIR))

from cricket_routes import cricket_router
from gift_card_routes import gift_card_router
from ads_routes import ads_router

# Include additional routers under /api prefix
app.include_router(cricket_router, prefix="/api")
app.include_router(gift_card_router, prefix="/api")
app.include_router(ads_router, prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
