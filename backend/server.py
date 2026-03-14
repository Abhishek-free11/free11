from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query, status
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
import sentry_sdk
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize Sentry for crash monitoring
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.05,  # Reduced from 0.1 to minimize overhead
            environment=os.environ.get('FREE11_ENV', 'production'),
            enable_tracing=False,  # Disabled to prevent startup hangs in Kubernetes
            _experiments={
                "continuous_profiling_auto_start": False,
            },
        )
        logging.info("Sentry initialized for backend crash monitoring")
    except Exception as e:
        logging.warning(f"Sentry init skipped (non-fatal): {e}")

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
# For Atlas (mongodb+srv://) connections, append authSource=admin to avoid SCRAM-SHA-1 auth failures
if 'mongodb+srv://' in mongo_url and 'authSource' not in mongo_url:
    separator = '&' if '?' in mongo_url else '?'
    mongo_url = mongo_url + separator + 'authSource=admin'
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    date_of_birth: Optional[str] = None  # YYYY-MM-DD for 18+ verification
    is_admin: bool = False
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
    date_of_birth: str  # Required: YYYY-MM-DD format for 18+ validation
    invite_code: Optional[str] = None  # Beta invite code

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
    """Verify password using bcrypt directly to avoid passlib/bcrypt 4.x compatibility issues"""
    import bcrypt
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password):
    """Hash password using bcrypt directly"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
    """Spend coins from user balance - atomic to prevent race condition / negative balance"""
    result = await db.users.find_one_and_update(
        {"id": user_id, "coins_balance": {"$gte": amount}},
        {"$inc": {"coins_balance": -amount, "total_redeemed": amount}},
        projection={"_id": 0, "coins_balance": 1}
    )
    if result is None:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    
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
async def register(user_data: UserCreate, request: Request):
    # Check beta registration status
    from beta_routes import check_beta_registration_allowed, use_invite_code
    
    # Validate 18+ age requirement
    try:
        dob = datetime.strptime(user_data.date_of_birth, "%Y-%m-%d")
        today = datetime.now(timezone.utc)
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        if age < 18:
            raise HTTPException(
                status_code=403, 
                detail={
                    "error": "age_restricted",
                    "message": "You must be 18 years or older to use FREE11."
                }
            )
        
        if age > 120:
            raise HTTPException(
                status_code=400,
                detail="Invalid date of birth"
            )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date of birth format. Use YYYY-MM-DD."
        )
    
    # Open registration — no invite code required
    # (Beta gate removed for public launch)
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if email was OTP-verified (skip in dev mode if no email provider)
    email_lower = user_data.email.strip().lower()
    otp_record = await db.otp_codes.find_one(
        {"email": email_lower, "purpose": "registration", "verified": True},
        sort=[("created_at", -1)]
    )
    email_verified = otp_record is not None
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        date_of_birth=user_data.date_of_birth,
        coins_balance=50  # Welcome bonus
    )
    
    user_dict = user.model_dump()
    user_dict["email_verified"] = email_verified
    if email_verified:
        user_dict["email_verified_at"] = datetime.now(timezone.utc).isoformat()
    
    # Track invite code if used
    if user_data.invite_code:
        user_dict["beta_invite_code"] = user_data.invite_code.upper().strip()
        await use_invite_code(user_data.invite_code, user.id, user.email)
    
    await db.users.insert_one(user_dict)
    
    # Create welcome transaction
    await add_coins(user.id, 50, "bonus", "Welcome bonus")
    
    # Record device fingerprint
    try:
        ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.client.host if request.client else ""))
        ua = request.headers.get("User-Agent", "")
        await fraud.record_login(user.id, ip.split(",")[0].strip(), ua)
        await analytics.track("registration", user.id)
    except Exception:
        pass
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    # Remove sensitive/internal fields from response
    user_dict.pop('password_hash', None)
    user_dict.pop('_id', None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_dict
    }

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin, request: Request):
    email = user_data.email.strip().lower()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.get("banned"):
        raise HTTPException(status_code=403, detail="Account suspended")

    if not verify_password(user_data.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user['id']})

    # Record login for fraud detection
    try:
        ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.client.host if request.client else ""))
        ua = request.headers.get("User-Agent", "")
        al = request.headers.get("Accept-Language", "")
        await fraud.record_login(user['id'], ip.split(",")[0].strip(), ua, al)
        await analytics.track("login", user['id'], {"ip": ip.split(",")[0].strip()})
    except Exception:
        pass
    
    user.pop('password_hash', None)
    user.pop('hashed_password', None)
    
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

# ==================== OTP EMAIL VERIFICATION ====================

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

@api_router.post("/auth/send-otp")
async def send_otp(req: OTPRequest):
    """Send OTP to email for verification"""
    result = await otp_engine.send_otp(req.email.strip().lower())
    # Only block on rate-limit/cooldown errors — delivery failures still return 200
    if result.get("error"):
        raise HTTPException(status_code=429, detail=result["error"])
    return result


# ── Section 12: Google OAuth (Emergent-managed) ──────────────────────────────
@api_router.post("/auth/google-oauth")
async def google_oauth_callback(session_id: str = Query(...)):
    """
    Exchange Emergent Auth session_id for FREE11 JWT token.
    Creates user on first login, finds existing user on subsequent logins.
    """
    import httpx
    _oauth_url = os.environ.get("OAUTH_CALLBACK_URL", "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data")
    logger.info(f"[Google OAuth] Processing session_id: {session_id[:20]}...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                _oauth_url,
                headers={"X-Session-ID": session_id}
            )
        logger.info(f"[Google OAuth] Emergent Auth response status: {res.status_code}")
        if res.status_code != 200:
            logger.error(f"[Google OAuth] Emergent Auth error: {res.text[:200]}")
            raise HTTPException(401, "Invalid or expired session")
    except httpx.TimeoutException:
        logger.error("[Google OAuth] Timeout connecting to Emergent Auth")
        raise HTTPException(504, "Authentication service timeout")
    except Exception as e:
        logger.error(f"[Google OAuth] Error: {str(e)}")
        raise HTTPException(500, f"Authentication error: {str(e)}")

    gdata = res.json()
    email = gdata.get("email", "").lower()
    name = gdata.get("name") or email.split("@")[0]
    picture = gdata.get("picture", "")

    if not email:
        raise HTTPException(400, "No email in OAuth response")

    # Find or create user
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["id"]
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "profile_image": picture,
                "last_activity": datetime.now(timezone.utc).isoformat(),
            }}
        )
    else:
        user_id = str(uuid.uuid4())
        coin_expiry = (datetime.now(timezone.utc) + timedelta(days=180)).isoformat()
        new_user = {
            "id": user_id, "email": email, "name": name,
            "hashed_password": None,
            "coins_balance": 50, "xp": 0, "level": 1,
            "streak_days": 0, "total_earned": 50, "total_spent": 0,
            "correct_predictions": 0, "total_predictions": 0,
            "prediction_streak": 0, "is_admin": False,
            "is_verified": True, "profile_image": picture,
            "auth_provider": "google",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "coin_expiry_date": coin_expiry,
        }
        await db.users.insert_one(new_user)
        await db.coin_transactions.insert_one({
            "user_id": user_id, "amount": 50, "type": "welcome_bonus",
            "description": "Welcome to FREE11! Google sign-up bonus.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    token = create_access_token({"sub": user_id})
    safe_user = {k: v for k, v in user.items() if k not in ("hashed_password", "coin_expiry_date")}
    return {"token": token, "user": safe_user}

@api_router.post("/auth/verify-otp")
async def verify_otp(req: OTPVerifyRequest):
    """Verify OTP code"""
    result = await otp_engine.verify_otp(req.email.strip().lower(), req.otp)
    if not result.get("verified"):
        raise HTTPException(status_code=400, detail=result.get("error", "Verification failed"))
    # Mark email as verified in DB if user exists
    await otp_engine.mark_email_verified(req.email.strip().lower())
    return result

class OTPRegisterRequest(BaseModel):
    email: EmailStr
    otp: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD, required for new users

@api_router.post("/auth/verify-otp-register")
async def verify_otp_register(req: OTPRegisterRequest):
    """
    Magic-link registration/login:
    - Verifies OTP
    - If user exists → returns JWT (magic link signin for existing users)
    - If user doesn't exist → creates account then returns JWT (requires 18+ DOB)
    """
    email = req.email.strip().lower()
    phone = req.phone_number.strip() if req.phone_number else None
    if phone and not phone.startswith('+'):
        phone = f"+91{phone.replace(' ', '').replace('-', '')}"

    # 1. Verify OTP
    result = await otp_engine.verify_otp(email, req.otp)
    if not result.get("verified"):
        raise HTTPException(status_code=400, detail=result.get("error", "Incorrect OTP code"))

    # 2. Find existing user (login flow — no age check needed)
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["id"]
        update_fields = {"last_activity": datetime.now(timezone.utc).isoformat(), "email_verified": True}
        if phone and not existing.get("phone"):
            update_fields["phone"] = phone
            update_fields["phone_verified"] = False
        await db.users.update_one({"id": user_id}, {"$set": update_fields})
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        token = create_access_token({"sub": user_id})
        safe_user = {k: v for k, v in user_doc.items() if k not in ("password_hash", "hashed_password", "coin_expiry_date")}
        return {"access_token": token, "token_type": "bearer", "user": safe_user}

    # 3. New user — validate 18+ age before creating account
    if not req.date_of_birth:
        raise HTTPException(status_code=400, detail="Date of birth is required for registration.")
    try:
        dob = datetime.strptime(req.date_of_birth, "%Y-%m-%d")
        today = datetime.now(timezone.utc)
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise HTTPException(
                status_code=403,
                detail={"error": "age_restricted", "message": "You must be 18 years or older to use FREE11."}
            )
        if age > 120:
            raise HTTPException(status_code=400, detail="Invalid date of birth.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date of birth format. Use YYYY-MM-DD.")

    # 4. Auto-create account
    name_raw = email.split("@")[0].replace(".", " ").replace("_", " ").replace("-", " ")
    name = " ".join(w.capitalize() for w in name_raw.split())

    user_id = str(uuid.uuid4())
    coin_expiry = (datetime.now(timezone.utc) + timedelta(days=180)).isoformat()
    new_user_doc = {
        "id": user_id,
        "email": email,
        "phone": phone,
        "phone_verified": False if phone else None,
        "name": name,
        "date_of_birth": req.date_of_birth,
        "password_hash": None,
        "google_id": None,
        "is_admin": False,
        "coins_balance": 50,
        "xp": 0,
        "level": 1,
        "streak_days": 0,
        "total_earned": 50,
        "total_redeemed": 0,
        "prediction_streak": 0,
        "total_predictions": 0,
        "correct_predictions": 0,
        "badges": [],
        "email_verified": True,
        "email_verified_at": datetime.now(timezone.utc).isoformat(),
        "auth_type": "otp_magic_link",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_activity": datetime.now(timezone.utc).isoformat(),
        "coin_expiry_date": coin_expiry,
    }
    await db.users.insert_one(new_user_doc)
    await add_coins(user_id, 50, "bonus", "Welcome bonus")

    token = create_access_token({"sub": user_id})
    safe_user = {k: v for k, v in new_user_doc.items() if k not in ("password_hash", "coin_expiry_date", "_id")}
    return {"access_token": token, "token_type": "bearer", "user": safe_user}


# ─── Phone Firebase Auth ────────────────────────────────────────────────────

class PhoneFirebaseRequest(BaseModel):
    firebase_id_token: str
    name: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD, required for new users

FIREBASE_WEB_API_KEY = os.environ.get("REACT_APP_FIREBASE_API_KEY", "AIzaSyBMRjuuazsPK8YXaKuI93v6yTE96k3Z0Gg")

async def _verify_firebase_phone_token(id_token: str) -> dict:
    """Verify Firebase ID token via REST and return user data with phone number."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_WEB_API_KEY}",
            json={"idToken": id_token}
        )
    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=f"Firebase token invalid: {data['error']['message']}")
    users = data.get("users", [])
    if not users:
        raise HTTPException(status_code=400, detail="No user found for this token")
    return users[0]

@api_router.post("/auth/phone-verify")
async def phone_firebase_verify(req: PhoneFirebaseRequest):
    """Sign in or register a user via Firebase Phone Auth OTP."""
    firebase_user = await _verify_firebase_phone_token(req.firebase_id_token)
    phone_number = firebase_user.get("phoneNumber")
    if not phone_number:
        raise HTTPException(status_code=400, detail="No phone number in Firebase token")

    # Find existing user by phone
    existing = await db.users.find_one({"phone": phone_number}, {"_id": 0})
    if existing:
        update_fields = {"last_activity": datetime.now(timezone.utc).isoformat(), "phone_verified": True}
        # Save email if provided and not already set
        if req.email and not existing.get("email"):
            conflict = await db.users.find_one({"email": req.email.strip().lower()}, {"_id": 0})
            if not conflict:
                update_fields["email"] = req.email.strip().lower()
        await db.users.update_one({"id": existing["id"]}, {"$set": update_fields})
        user_doc = await db.users.find_one({"id": existing["id"]}, {"_id": 0})
        token = create_access_token({"sub": existing["id"]})
        safe = {k: v for k, v in user_doc.items() if k not in ("password_hash", "hashed_password", "coin_expiry_date")}
        return {"access_token": token, "token_type": "bearer", "user": safe, "is_new_user": False}

    # New user — validate 18+ before creating
    if not req.date_of_birth:
        raise HTTPException(status_code=400, detail={"error": "dob_required", "message": "Date of birth is required for new accounts."})
    try:
        dob = datetime.strptime(req.date_of_birth, "%Y-%m-%d")
        today = datetime.now(timezone.utc)
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise HTTPException(status_code=403, detail={"error": "age_restricted", "message": "You must be 18 years or older to use FREE11."})
        if age > 120:
            raise HTTPException(status_code=400, detail="Invalid date of birth.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date of birth format.")

    user_id = str(uuid.uuid4())
    display_name = req.name or f"Player{phone_number[-4:]}"
    email_val = req.email.strip().lower() if req.email else None
    if email_val:
        conflict = await db.users.find_one({"email": email_val}, {"_id": 0})
        if conflict:
            email_val = None
    now = datetime.now(timezone.utc).isoformat()
    new_user = {
        "id": user_id, "name": display_name, "email": email_val,
        "phone": phone_number, "phone_verified": True,
        "date_of_birth": req.date_of_birth,
        "hashed_password": None, "coins_balance": 50,
        "total_earned": 50, "total_redeemed": 0,
        "level": 1, "xp": 0, "prediction_streak": 0,
        "total_predictions": 0, "correct_predictions": 0,
        "email_verified": True, "created_at": now, "last_activity": now,
        "is_admin": False, "is_seed": False,
        "referral_code": user_id[:8].upper(),
        "referred_by": None, "referred_users": [],
        "achievements": [], "notification_preferences": {
            "match_start": True, "prediction_result": True,
            "rewards": True, "leaderboard": True
        }
    }
    await db.users.insert_one(new_user)
    await db.coin_transactions.insert_one({
        "user_id": user_id, "amount": 50, "type": "welcome_bonus",
        "description": "Welcome to FREE11! Phone sign-up bonus.",
        "timestamp": now,
    })
    token = create_access_token({"sub": user_id})
    new_user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    safe = {k: v for k, v in new_user_doc.items() if k not in ("password_hash", "hashed_password", "coin_expiry_date")}
    return {"access_token": token, "token_type": "bearer", "user": safe, "is_new_user": True}


class UpdateContactRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None

@api_router.post("/auth/update-contact")
async def update_contact(req: UpdateContactRequest, current_user: User = Depends(get_current_user)):
    """Add or update email/phone for an existing user (e.g. phone-only users adding email)."""
    update_fields = {}
    if req.email:
        email_val = req.email.strip().lower()
        conflict = await db.users.find_one({"email": email_val, "id": {"$ne": current_user.id}}, {"_id": 0})
        if conflict:
            raise HTTPException(status_code=400, detail="This email is already linked to another account.")
        update_fields["email"] = email_val
    if req.phone:
        phone_val = req.phone.strip()
        if not phone_val.startswith('+'):
            phone_val = f"+91{phone_val.replace(' ', '').replace('-', '')}"
        conflict = await db.users.find_one({"phone": phone_val, "id": {"$ne": current_user.id}}, {"_id": 0})
        if conflict:
            raise HTTPException(status_code=400, detail="This phone is already linked to another account.")
        update_fields["phone"] = phone_val
    if not update_fields:
        raise HTTPException(status_code=400, detail="Provide email or phone to update.")
    await db.users.update_one({"id": current_user.id}, {"$set": update_fields})
    user_doc = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    safe = {k: v for k, v in user_doc.items() if k not in ("password_hash", "hashed_password", "coin_expiry_date")}
    return {"success": True, "user": safe}


@api_router.get("/auth/email-status")
async def email_verification_status(current_user: User = Depends(get_current_user)):
    """Check if current user's email is verified"""
    verified = await otp_engine.is_email_verified(current_user.email)
    return {"email": current_user.email, "verified": verified}

@api_router.post("/auth/resend-verification")
async def resend_verification(current_user: User = Depends(get_current_user)):
    """Resend verification OTP for currently logged-in user"""
    result = await otp_engine.send_otp(current_user.email, purpose="verification")
    if not result.get("sent"):
        raise HTTPException(status_code=429, detail=result.get("error", "Failed"))
    return result

# ==================== FCM PUSH NOTIFICATIONS ====================

class FCMTokenRequest(BaseModel):
    token: str
    device_type: str = "web"

class NotifPrefsRequest(BaseModel):
    match_starting: Optional[bool] = None
    contest_closing: Optional[bool] = None
    match_completed: Optional[bool] = None
    leaderboard_update: Optional[bool] = None
    payment_success: Optional[bool] = None
    daily_reminder: Optional[bool] = None

@api_router.post("/push/register")
async def register_push_token(req: FCMTokenRequest, current_user: User = Depends(get_current_user)):
    """Register FCM push token for the current user"""
    return await fcm.register_token(current_user.id, req.token, req.device_type)

@api_router.post("/push/unregister")
async def unregister_push_token(req: FCMTokenRequest, current_user: User = Depends(get_current_user)):
    """Unregister push token"""
    await fcm.unregister_token(current_user.id, req.device_type)
    return {"ok": True}

@api_router.get("/push/preferences")
async def get_push_preferences(current_user: User = Depends(get_current_user)):
    return await fcm.get_notification_preferences(current_user.id)

@api_router.post("/push/preferences")
async def update_push_preferences(req: NotifPrefsRequest, current_user: User = Depends(get_current_user)):
    prefs = {k: v for k, v in req.model_dump().items() if v is not None}
    return await fcm.update_preferences(current_user.id, prefs)

# ==================== USER PROFILE UPDATE ====================

class UpdateMobileReq(BaseModel):
    mobile: str
    state: Optional[str] = None

@api_router.post("/user/update-mobile")
async def update_mobile(req: UpdateMobileReq, current_user: User = Depends(get_current_user)):
    update = {"mobile": req.mobile.strip()}
    if req.state:
        update["state"] = req.state
    await db.users.update_one({"id": current_user.id}, {"$set": update})
    return {"ok": True}

# ==================== TUTORIAL ROUTES ====================

@api_router.get("/user/tutorial-status")
async def get_tutorial_status(current_user: User = Depends(get_current_user)):
    """Check if user has completed the first-time tutorial"""
    user = await db.users.find_one({"id": current_user.id}, {"_id": 0, "tutorial_completed": 1})
    return {"tutorial_completed": user.get("tutorial_completed", False) if user else False}

@api_router.post("/user/complete-tutorial")
async def complete_tutorial(current_user: User = Depends(get_current_user)):
    """Mark the first-time tutorial as completed"""
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"tutorial_completed": True, "tutorial_completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True, "message": "Tutorial marked as completed"}

@api_router.post("/user/reset-tutorial")
async def reset_tutorial(current_user: User = Depends(get_current_user)):
    """Reset the tutorial so it shows again (for replay from Profile → Help)"""
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"tutorial_completed": False}}
    )
    return {"success": True, "message": "Tutorial reset - will show on next dashboard visit"}

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
    # Ensure every entry has a unique id for frontend key prop
    for i, tx in enumerate(transactions):
        if not tx.get("id"):
            import uuid as _uuid
            tx["id"] = str(_uuid.uuid4())
    return transactions

@api_router.post("/coins/checkin")
async def daily_checkin(current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Calculate streak based on current user data
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    new_streak = current_user.streak_days + 1 if current_user.last_checkin == yesterday else 1
    
    # Calculate reward (increases with streak)
    base_reward = 10
    streak_bonus = min(new_streak * 5, 50)  # Max 50 bonus
    total_reward = base_reward + streak_bonus
    
    # ATOMIC check: only update if last_checkin != today (prevents race condition)
    result = await db.users.find_one_and_update(
        {"id": current_user.id, "last_checkin": {"$ne": today}},
        {"$set": {"last_checkin": today, "streak_days": new_streak}},
        projection={"_id": 0, "id": 1}
    )
    if result is None:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
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
            "Spin the wheel"
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
            "Scratch card"
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
    cache_key = f"products:{category or 'all'}"
    try:
        from redis_cache import get_redis
        import json as _json
        r = get_redis()
        if r is not None:
            cached = r.get(cache_key)
            if cached:
                return _json.loads(cached)
    except Exception:
        r = None

    query = {"active": True}
    if category and category != "all":
        query["category"] = category
    products = await db.products.find(query, {"_id": 0}).to_list(100)

    try:
        if r is not None:
            import json as _json
            r.set(cache_key, _json.dumps(products, default=str), ex=300)
    except Exception:
        pass
    return products

@api_router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.post("/products", response_model=Product)
async def create_product(product: ProductCreate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required to create products")
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
    
    coin_price = product['coin_price']
    
    # ATOMIC stock check + decrement to prevent race conditions on limited stock
    stock_result = await db.products.find_one_and_update(
        {"id": redemption_data.product_id, "stock": {"$gt": 0}},
        {"$inc": {"stock": -1}},
        projection={"_id": 0, "stock": 1}
    )
    if stock_result is None:
        raise HTTPException(status_code=400, detail="Product out of stock")
    
    # ATOMIC coin deduction (spend_coins already uses find_one_and_update with balance check)
    try:
        await spend_coins(current_user.id, coin_price, f"Redeemed: {product['name']}")
    except HTTPException:
        # Rollback stock if coin deduction fails
        await db.products.update_one({"id": redemption_data.product_id}, {"$inc": {"stock": 1}})
        raise HTTPException(status_code=400, detail=f"Insufficient coins. Need {coin_price} coins.")
    
    # Create redemption
    redemption = Redemption(
        user_id=current_user.id,
        product_id=product['id'],
        product_name=product['name'],
        coins_spent=coin_price,
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
        "new_balance": current_user.coins_balance - coin_price
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
        user = await db.users.find_one(
            {"id": entry["_id"], "is_admin": {"$ne": True}, "is_seed": {"$ne": True}},
            {"_id": 0, "name": 1, "level": 1}
        )
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
            {"is_admin": {"$ne": True}, "is_seed": {"$ne": True}},
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
            "question": "What are Free Coins and can I withdraw them?",
            "answer": "Free Coins are non-withdrawable reward tokens redeemable only for goods/services. No cash. No prediction. Brand-funded rewards.",
            "category": "coins",
            "priority": 1
        },
        {
            "id": "how-to-earn",
            "question": "How do I earn Free Coins?",
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
            "answer": "Yes! FREE11 is a skill-based rewards platform, not a predictions app. Our coin system is fully compliant with Indian regulations - coins cannot be purchased, withdrawn, or transferred. It's 100% safe and legal.",
            "category": "legal",
            "priority": 8
        }
    ]
    
    return {
        "items": faq_items,
        "disclaimer": "Free Coins are non-withdrawable reward tokens redeemable only for goods/services. No cash. No prediction. Brand-funded rewards."
    }

# ==================== ADMIN ROUTES ====================

@api_router.get("/admin/analytics")
async def get_analytics(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
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

@api_router.get("/admin/beta-metrics")
async def get_beta_metrics(current_user: User = Depends(get_current_user)):
    """Comprehensive Beta Metrics Dashboard"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # === USER METRICS ===
    total_users = await db.users.count_documents({})
    admin_users = await db.users.count_documents({"is_admin": True})
    beta_users = total_users - admin_users
    
    # Users with tutorial completed
    tutorial_completed = await db.users.count_documents({"tutorial_completed": True})
    tutorial_rate = round((tutorial_completed / beta_users * 100), 1) if beta_users > 0 else 0
    
    # === INVITE METRICS ===
    total_invites = await db.beta_invites.count_documents({"source": "wave1_simple"})
    used_invites = await db.beta_invites.count_documents({"source": "wave1_simple", "current_uses": {"$gt": 0}})
    unused_invites = total_invites - used_invites
    invite_conversion = round((used_invites / total_invites * 100), 1) if total_invites > 0 else 0
    
    # === PREDICTION METRICS ===
    total_predictions = await db.predictions.count_documents({})
    correct_predictions = await db.predictions.count_documents({"is_correct": True})
    prediction_accuracy = round((correct_predictions / total_predictions * 100), 1) if total_predictions > 0 else 0
    
    # Users who made at least 1 prediction
    users_with_predictions = await db.predictions.distinct("user_id")
    prediction_adoption = round((len(users_with_predictions) / beta_users * 100), 1) if beta_users > 0 else 0
    
    # Predictions per user
    predictions_per_user = round(total_predictions / len(users_with_predictions), 1) if users_with_predictions else 0
    
    # === REDEMPTION METRICS ===
    total_redemptions = await db.redemptions.count_documents({})
    successful_redemptions = await db.redemptions.count_documents({"status": {"$in": ["completed", "delivered", "processing"]}})
    failed_redemptions = await db.redemptions.count_documents({"status": "failed"})
    
    # Users who redeemed at least once
    users_with_redemptions = await db.redemptions.distinct("user_id")
    redemption_adoption = round((len(users_with_redemptions) / beta_users * 100), 1) if beta_users > 0 else 0
    
    # === COIN ECONOMY ===
    coin_pipeline = [
        {"$group": {
            "_id": None, 
            "total_balance": {"$sum": "$coins_balance"},
            "total_earned": {"$sum": "$total_earned"},
            "total_redeemed": {"$sum": "$total_redeemed"}
        }}
    ]
    coin_result = await db.users.aggregate(coin_pipeline).to_list(1)
    coin_data = coin_result[0] if coin_result else {"total_balance": 0, "total_earned": 0, "total_redeemed": 0}
    
    # === ENGAGEMENT METRICS ===
    # Active users (made prediction or redemption in last 24h)
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    
    # === TOP USERS ===
    top_predictors = await db.users.find(
        {"is_admin": {"$ne": True}},
        {"_id": 0, "name": 1, "email": 1, "correct_predictions": 1, "total_predictions": 1, "coins_balance": 1}
    ).sort("correct_predictions", -1).limit(5).to_list(5)
    
    # === PRODUCT PERFORMANCE ===
    product_pipeline = [
        {"$group": {
            "_id": "$product_id",
            "redemption_count": {"$sum": 1}
        }},
        {"$sort": {"redemption_count": -1}},
        {"$limit": 5}
    ]
    top_products = await db.redemptions.aggregate(product_pipeline).to_list(5)
    
    # Enrich with product names — bulk fetch to avoid N+1 queries
    product_ids = [p["_id"] for p in top_products]
    product_docs = await db.products.find(
        {"id": {"$in": product_ids}}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(len(product_ids))
    product_name_map = {doc["id"]: doc["name"] for doc in product_docs}
    for p in top_products:
        p["name"] = product_name_map.get(p["_id"], "Unknown")
    
    # === FULL LOOP COMPLETION ===
    # Users who: registered -> predicted -> redeemed (core loop)
    users_completed_loop = len(set(users_with_predictions) & set(users_with_redemptions))
    loop_completion_rate = round((users_completed_loop / beta_users * 100), 1) if beta_users > 0 else 0
    
    # === SUPPORT METRICS ===
    total_tickets = await db.support_tickets.count_documents({})
    open_tickets = await db.support_tickets.count_documents({"status": "open"})
    
    # === CARD GAME METRICS ===
    total_game_rooms = await db.game_rooms.count_documents({})
    active_game_rooms = await db.game_rooms.count_documents({"status": {"$in": ["waiting", "playing"]}})
    completed_games = await db.game_results.count_documents({})
    
    # Game type breakdown
    rummy_games = await db.game_results.count_documents({"game_type": "rummy"})
    teen_patti_games = await db.game_results.count_documents({"game_type": "teen_patti"})
    poker_games = await db.game_results.count_documents({"game_type": "poker"})
    
    # Unique game players
    game_players = await db.game_stats.distinct("user_id")
    game_adoption = round((len(game_players) / beta_users * 100), 1) if beta_users > 0 else 0
    
    # Total coins earned from games
    game_coins_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$total_coins_earned"}}}
    ]
    game_coins_result = await db.game_stats.aggregate(game_coins_pipeline).to_list(1)
    total_game_coins = game_coins_result[0]["total"] if game_coins_result else 0
    
    # === CLAN METRICS ===
    total_clans = await db.clans.count_documents({})
    active_clans = await db.clans.count_documents({"member_count": {"$gte": 2}})
    
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "beta_users": beta_users,
            "loop_completion_rate": f"{loop_completion_rate}%",
            "health": "🟢 Good" if loop_completion_rate >= 20 else "🟡 Monitor" if loop_completion_rate >= 10 else "🔴 Needs Work"
        },
        "users": {
            "total_beta_users": beta_users,
            "tutorial_completed": tutorial_completed,
            "tutorial_completion_rate": f"{tutorial_rate}%",
            "users_completed_full_loop": users_completed_loop
        },
        "invites": {
            "total_generated": total_invites,
            "used": used_invites,
            "unused": unused_invites,
            "conversion_rate": f"{invite_conversion}%"
        },
        "predictions": {
            "total": total_predictions,
            "correct": correct_predictions,
            "accuracy_rate": f"{prediction_accuracy}%",
            "users_who_predicted": len(users_with_predictions),
            "adoption_rate": f"{prediction_adoption}%",
            "avg_per_user": predictions_per_user
        },
        "redemptions": {
            "total": total_redemptions,
            "successful": successful_redemptions,
            "failed": failed_redemptions,
            "users_who_redeemed": len(users_with_redemptions),
            "adoption_rate": f"{redemption_adoption}%"
        },
        "coins": {
            "total_in_circulation": coin_data.get("total_balance", 0),
            "total_earned_all_time": coin_data.get("total_earned", 0),
            "total_redeemed_all_time": coin_data.get("total_redeemed", 0)
        },
        "support": {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets
        },
        "card_games": {
            "total_rooms_created": total_game_rooms,
            "active_rooms": active_game_rooms,
            "completed_games": completed_games,
            "by_type": {
                "rummy": rummy_games,
                "teen_patti": teen_patti_games,
                "poker": poker_games
            },
            "unique_players": len(game_players),
            "adoption_rate": f"{game_adoption}%",
            "total_coins_distributed": total_game_coins
        },
        "clans": {
            "total": total_clans,
            "active": active_clans
        },
        "leaderboard": {
            "top_predictors": top_predictors
        },
        "top_products": top_products
    }

@api_router.get("/admin/brand-roas")
async def get_brand_roas(current_user: User = Depends(get_current_user)):
    """
    Placeholder Brand ROAS Dashboard
    Shows redemption attribution by brand for partner reporting
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
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
    """Seed database with 50 brand-funded products: 30 grocery/rations + 20 lifestyle."""
    await db.products.delete_many({})

    sample_products = [
        # ══════════════════════════════════════════
        # RATIONS — 30 SKUs (₹20–₹500) Entry/Staples
        # ══════════════════════════════════════════
        {"name": "Glucose Biscuits 400g", "description": "India's favourite biscuit snack pack", "category": "rations", "coin_price": 20, "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400", "stock": 2000, "brand": "Snack Partner", "brand_id": "snack_partner", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Cola Drink 2L Bottle", "description": "Chilled cola — perfect for match day", "category": "rations", "coin_price": 50, "image_url": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400", "stock": 1500, "brand": "Beverage Partner", "brand_id": "beverage_partner", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "qcomm", "min_level_required": 1},
        {"name": "Aashirvaad Atta 5kg", "description": "Whole wheat atta — home essentials", "category": "rations", "coin_price": 150, "image_url": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400", "stock": 800, "brand": "ITC Aashirvaad", "brand_id": "itc_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "India Gate Rice 5kg", "description": "Premium basmati rice", "category": "rations", "coin_price": 200, "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400", "stock": 600, "brand": "KRBL", "brand_id": "krbl_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Fortune Sunflower Oil 1L", "description": "Healthy cooking oil", "category": "rations", "coin_price": 100, "image_url": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400", "stock": 1000, "brand": "Fortune", "brand_id": "adani_foods", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Tata Sampann Daal 1kg", "description": "Protein-rich toor daal", "category": "rations", "coin_price": 80, "image_url": "https://images.unsplash.com/photo-1595436169199-3cd70c98af1e?w=400", "stock": 1200, "brand": "Tata Consumer", "brand_id": "tata_consumer", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Tata Salt 1kg", "description": "Iodized salt — daily essential", "category": "rations", "coin_price": 15, "image_url": "https://images.unsplash.com/photo-1583339793403-3d9b001b6008?w=400", "stock": 3000, "brand": "Tata Consumer", "brand_id": "tata_consumer", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Uttam Sugar 1kg", "description": "Fine white sugar", "category": "rations", "coin_price": 25, "image_url": "https://images.unsplash.com/photo-1548247416-ec66f4900b2e?w=400", "stock": 2500, "brand": "Uttam Sugar", "brand_id": "uttam_sugar", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Surf Excel 1kg Detergent", "description": "Tough stain remover for clothes", "category": "rations", "coin_price": 90, "image_url": "https://images.unsplash.com/photo-1585421514738-01798e348b17?w=400", "stock": 900, "brand": "Unilever", "brand_id": "hul_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Salted Potato Chips 50g", "description": "Classic salted chips — match snack", "category": "rations", "coin_price": 10, "image_url": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400", "stock": 5000, "brand": "Snack Partner", "brand_id": "snack_partner", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "qcomm", "min_level_required": 1},
        {"name": "Cadbury Dairy Milk 40g", "description": "Silky smooth chocolate bar", "category": "rations", "coin_price": 20, "image_url": "https://images.unsplash.com/photo-1481391319762-47dff72954d9?w=400", "stock": 3000, "brand": "Cadbury", "brand_id": "mondelez_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "qcomm", "min_level_required": 1},
        {"name": "Premium Dairy Butter 500g", "description": "Fresh pasteurized butter, 500g pack", "category": "rations", "coin_price": 120, "image_url": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400", "stock": 700, "brand": "Dairy Fresh", "brand_id": "dairy_fresh", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "qcomm", "min_level_required": 1},
        {"name": "Nescafe Classic Coffee 50g", "description": "Rich instant coffee", "category": "rations", "coin_price": 60, "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400", "stock": 1000, "brand": "Nestle", "brand_id": "nestle_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Lipton Green Tea 25 bags", "description": "Refreshing green tea", "category": "rations", "coin_price": 45, "image_url": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400", "stock": 1500, "brand": "Unilever", "brand_id": "hul_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Maggi Noodles 12-pack", "description": "2-minute noodles — matchday snack", "category": "rations", "coin_price": 70, "image_url": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=400", "stock": 1200, "brand": "Nestle", "brand_id": "nestle_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Dabur Honey 500g", "description": "Pure natural honey", "category": "rations", "coin_price": 130, "image_url": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400", "stock": 600, "brand": "Dabur", "brand_id": "dabur_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Horlicks 500g", "description": "Nutrition drink for the family", "category": "rations", "coin_price": 110, "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400", "stock": 800, "brand": "GSK", "brand_id": "gsk_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "MDH Garam Masala 100g", "description": "Aromatic spice blend", "category": "rations", "coin_price": 35, "image_url": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400", "stock": 2000, "brand": "MDH", "brand_id": "mdh_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Dettol Soap 4-pack", "description": "Antibacterial protection soap", "category": "rations", "coin_price": 65, "image_url": "https://images.unsplash.com/photo-1584305574647-0cc949a2bb9f?w=400", "stock": 1500, "brand": "Reckitt", "brand_id": "reckitt_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Colgate Max Fresh Toothpaste", "description": "Cooling crystals toothpaste 150g", "category": "rations", "coin_price": 55, "image_url": "https://images.unsplash.com/photo-1607613009820-a29f7bb81c04?w=400", "stock": 1800, "brand": "Colgate", "brand_id": "colgate_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Boost Health Drink 200g", "description": "Energy-boosting malted drink", "category": "rations", "coin_price": 75, "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400", "stock": 900, "brand": "GSK", "brand_id": "gsk_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "BigBasket Ration Bundle ₹200", "description": "Atta + Rice + Oil + Daal combo", "category": "rations", "coin_price": 200, "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400", "stock": 400, "brand": "BigBasket", "brand_id": "bigbasket_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "qcomm", "min_level_required": 1},
        {"name": "Zepto Snack Bundle ₹100", "description": "Chips + Biscuits + Chocolate combo (10-min delivery)", "category": "rations", "coin_price": 100, "image_url": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400", "stock": 800, "brand": "Zepto", "brand_id": "zepto_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "qcomm", "min_level_required": 1},
        {"name": "ONDC Grocery Voucher ₹150", "description": "Redeem at any ONDC merchant near you", "category": "rations", "coin_price": 150, "image_url": "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?w=400", "stock": 500, "brand": "ONDC", "brand_id": "ondc_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Flipkart Grocery ₹250", "description": "Shop staples on Flipkart Grocery", "category": "rations", "coin_price": 250, "image_url": "https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?w=400", "stock": 300, "brand": "Flipkart", "brand_id": "flipkart_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 2},
        {"name": "Lemon-Lime Soda 2L", "description": "Crisp lemon-lime soda", "category": "rations", "coin_price": 45, "image_url": "https://images.unsplash.com/photo-1625772299848-391b6a87d7b3?w=400", "stock": 1500, "brand": "Snack Partner", "brand_id": "snack_partner", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "qcomm", "min_level_required": 1},
        {"name": "Haldiram's Namkeen 200g", "description": "Mixed namkeen for match snacking", "category": "rations", "coin_price": 35, "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400", "stock": 2000, "brand": "Haldiram's", "brand_id": "haldirams_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Milkmaid Condensed Milk 400g", "description": "Perfect for desserts", "category": "rations", "coin_price": 85, "image_url": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400", "stock": 700, "brand": "Nestle", "brand_id": "nestle_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 1},
        {"name": "Saffola Gold Oil 2L", "description": "Heart-friendly blended oil", "category": "rations", "coin_price": 250, "image_url": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400", "stock": 500, "brand": "Marico", "brand_id": "marico_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 2},
        {"name": "Ration Mega Bundle ₹500", "description": "Complete monthly ration pack via ONDC", "category": "rations", "coin_price": 500, "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400", "stock": 200, "brand": "ONDC Partner", "brand_id": "ondc_india", "campaign_id": "t20_2026_rations", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 2},

        # ══════════════════════════════════════════
        # LIFESTYLE — 20 SKUs (₹10–₹50000)
        # ══════════════════════════════════════════
        {"name": "Mobile Recharge ₹10", "description": "Instant recharge any operator", "category": "recharge", "coin_price": 10, "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400", "stock": 5000, "brand": "Jio/Airtel", "brand_id": "telecom", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "direct", "min_level_required": 1},
        {"name": "Mobile Recharge ₹50", "description": "Instant recharge any operator", "category": "recharge", "coin_price": 50, "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400", "stock": 2000, "brand": "Jio/Airtel", "brand_id": "telecom", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "direct", "min_level_required": 1},
        {"name": "Hotstar 3-Day Pass", "description": "Watch live cricket — limited offer!", "category": "ott", "coin_price": 25, "image_url": "https://images.unsplash.com/photo-1522869635100-9f4c5e86aa37?w=400", "stock": 500, "brand": "Disney+ Hotstar", "brand_id": "hotstar_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "direct", "min_level_required": 1, "is_limited_drop": True},
        {"name": "Netflix 1-Week Trial", "description": "Stream unlimited shows for 7 days", "category": "ott", "coin_price": 30, "image_url": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400", "stock": 300, "brand": "Netflix", "brand_id": "netflix_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "direct", "min_level_required": 1},
        {"name": "Swiggy Voucher ₹100", "description": "Order your favourite food", "category": "food", "coin_price": 100, "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400", "stock": 400, "brand": "Swiggy", "brand_id": "swiggy_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "qcomm", "min_level_required": 1},
        {"name": "Amazon Gift Card ₹100", "description": "Shop anything on Amazon", "category": "vouchers", "coin_price": 100, "image_url": "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?w=400", "stock": 300, "brand": "Amazon", "brand_id": "amazon_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "direct", "min_level_required": 1},
        {"name": "Amazon Gift Card ₹500", "description": "Shop electronics, fashion & more", "category": "vouchers", "coin_price": 500, "image_url": "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?w=400", "stock": 150, "brand": "Amazon", "brand_id": "amazon_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "direct", "min_level_required": 2},
        {"name": "boAt Bassheads 100 Earphones", "description": "Wired earphones — deep bass", "category": "electronics", "coin_price": 200, "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400", "stock": 200, "brand": "boAt", "brand_id": "boat_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "d2c", "min_level_required": 2},
        {"name": "Noise ColorFit Pulse 2 Watch", "description": "Fitness smartwatch with SpO2", "category": "electronics", "coin_price": 1500, "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400", "stock": 100, "brand": "Noise", "brand_id": "noise_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "d2c", "min_level_required": 3},
        {"name": "Puma Cricket T-Shirt", "description": "Cricket edition branded jersey", "category": "fashion", "coin_price": 500, "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400", "stock": 150, "brand": "Puma", "brand_id": "puma_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "d2c", "min_level_required": 2},
        {"name": "Flipkart Voucher ₹1000", "description": "Shop electronics, fashion & more", "category": "vouchers", "coin_price": 1000, "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400", "stock": 80, "brand": "Flipkart", "brand_id": "flipkart_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "ondc_bap", "min_level_required": 3},
        {"name": "Cafe Coffee Day ₹50", "description": "Coffee or snack at any CCD outlet", "category": "food", "coin_price": 50, "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400", "stock": 300, "brand": "CCD", "brand_id": "ccd_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "direct", "min_level_required": 1},
        {"name": "Zomato Gold 1-Month", "description": "Free delivery + exclusive discounts", "category": "food", "coin_price": 300, "image_url": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=400", "stock": 200, "brand": "Zomato", "brand_id": "zomato_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "direct", "min_level_required": 2},
        {"name": "Myntra Fashion Voucher ₹500", "description": "Shop trending fashion and apparel", "category": "fashion", "coin_price": 500, "image_url": "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=400", "stock": 100, "brand": "Myntra", "brand_id": "myntra_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "direct", "min_level_required": 2},
        {"name": "Nike Running Shoes", "description": "Premium athletic footwear", "category": "fashion", "coin_price": 5000, "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400", "stock": 30, "brand": "Nike", "brand_id": "nike_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "d2c", "min_level_required": 4},
        {"name": "boAt Airdopes 141 TWS", "description": "True wireless earbuds — 42hr battery", "category": "electronics", "coin_price": 800, "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400", "stock": 120, "brand": "boAt", "brand_id": "boat_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "d2c", "min_level_required": 3},
        {"name": "Sony WH-1000XM5 Headphones", "description": "Industry-leading noise cancellation", "category": "electronics", "coin_price": 15000, "image_url": "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400", "stock": 10, "brand": "Sony", "brand_id": "sony_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "d2c", "min_level_required": 4},
        {"name": "Samsung Galaxy S24", "description": "Flagship Android smartphone", "category": "electronics", "coin_price": 35000, "image_url": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400", "stock": 5, "brand": "Samsung", "brand_id": "samsung_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "d2c", "min_level_required": 5, "is_limited_drop": True},
        {"name": "iPhone 15 Pro", "description": "Latest Apple iPhone with A17 Pro chip", "category": "electronics", "coin_price": 50000, "image_url": "https://images.unsplash.com/photo-1696446702281-1af638e15d2e?w=400", "stock": 3, "brand": "Apple", "brand_id": "apple_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "d2c", "min_level_required": 5, "is_limited_drop": True},
        {"name": "Swiggy Instamart Bundle ₹200", "description": "Snacks + drinks — 15-min delivery", "category": "food", "coin_price": 200, "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400", "stock": 300, "brand": "Swiggy", "brand_id": "swiggy_india", "campaign_id": "t20_2026_life", "funded_by_brand": True, "fulfillment_type": "qcomm", "min_level_required": 1},
    ]

    for product_data in sample_products:
        product = Product(**product_data)
        await db.products.insert_one(product.model_dump())

    return {"message": f"Seeded {len(sample_products)} brand-funded products (30 rations + 20 lifestyle)"}

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
from clans_routes import clans_router
from leaderboards_routes import leaderboards_router
from fulfillment_routes import fulfillment_router
from support_routes import support_router
from brand_routes import brand_router
from beta_routes import beta_router
from reports_routes import reports_router
from feature_routes import feature_router
from fantasy_routes import fantasy_router
from leagues_routes import leagues_router
from games_routes import games_router
from v2_routes import v2_router
from admin_v2_routes import admin_v2_router
from reloadly_routes import reloadly_router
from cashfree_routes import cashfree_router
from airtime_routes import airtime_router
from email_service import EmailService
from geo_fence_middleware import GeoFenceMiddleware
from rate_limiter import RateLimitMiddleware
from payment_routes import payment_router, init_payment
from fraud_engine import FraudEngine
from freebucks_engine import FreeBucksEngine
from feature_gate import FeatureGate
from notification_engine import NotificationEngine
from analytics_engine import AnalyticsEngine
from scheduler_service import AutoScorer
from redis_cache import get_cache_stats
from entitysport_service import EntitySportService
from fantasy_engine import FantasyEngine
from otp_engine import OTPEngine
from fcm_service import FCMService

# Initialize new engines
entitysport = EntitySportService(db)
fantasy = FantasyEngine(db)
fraud = FraudEngine(db)
freebucks = FreeBucksEngine(db)
notif_engine = NotificationEngine(db)
analytics = AnalyticsEngine(db)
feature_gating = FeatureGate(db, freebucks)
auto_scorer = AutoScorer(db, fantasy, entitysport, notif_engine)
otp_engine = OTPEngine(db)
fcm = FCMService(db)

# Init payment module
init_payment(db, freebucks, notif_engine, analytics)

# Initialize email service
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    EmailService.initialize(db, use_mock=not os.environ.get("RESEND_API_KEY"))
    # Inject contest engine into AutoScorer for auto-finalization
    from v2_routes import contests as contest_engine_instance
    auto_scorer.set_contest_engine(contest_engine_instance)
    auto_scorer.set_fcm_service(fcm)
    auto_scorer.start()
    # Create unique index on coin_transactions.unique_payout_id for payout idempotency
    try:
        await db.coin_transactions.create_index(
            "unique_payout_id", unique=True, sparse=True,
            name="unique_payout_idempotency"
        )
    except Exception as e:
        logger.info(f"Unique payout index: {e}")
    # Critical performance indexes for scale (300k users)
    try:
        await db.users.create_index("email", unique=True, sparse=True, name="users_email_unique")
        await db.users.create_index("id", unique=True, name="users_id_unique")
        await db.coin_transactions.create_index("user_id", name="txn_user_id")
        await db.coin_transactions.create_index([("user_id", 1), ("timestamp", -1)], name="txn_user_time")
        await db.predictions.create_index("user_id", name="pred_user_id")
        await db.predictions.create_index([("user_id", 1), ("match_id", 1)], name="pred_user_match")
        await db.redemptions.create_index("user_id", name="redempt_user_id")
        await db.redemptions.create_index([("user_id", 1), ("order_date", -1)], name="redempt_user_date")
        await db.missions.create_index([("user_id", 1), ("type", 1)], name="mission_user_type")
        await db.router_orders.create_index("user_id", name="router_user_id")
        logger.info("DB indexes created/verified")
    except Exception as e:
        logger.warning(f"Index creation (non-fatal): {e}")
    # Feature 4: Pre-generate today's AI puzzle on startup (warm cache, non-blocking)
    # Note: Wrapped in try-except to prevent startup failures in production
    try:
        import asyncio as _asyncio
        from v2_routes import puzzle_engine as puzzle_eng
        _asyncio.create_task(puzzle_eng.generate_today())
    except Exception as e:
        logger.warning(f"AI puzzle pre-generation skipped: {e}")
    # Seed sponsored pools (idempotent) - wrapped to prevent startup failures
    try:
        await seed_sponsored_pools()
    except Exception as e:
        logger.warning(f"Sponsored pools seeding skipped: {e}")
    logger.info("Startup complete: Email service, AutoScorer, payout index, AI puzzle task, sponsored pools")

# Include additional routers under /api prefix
app.include_router(cricket_router, prefix="/api")
app.include_router(gift_card_router, prefix="/api")
app.include_router(clans_router, prefix="/api")
app.include_router(leaderboards_router, prefix="/api")
app.include_router(fulfillment_router, prefix="/api")
app.include_router(support_router, prefix="/api")
app.include_router(brand_router, prefix="/api")
app.include_router(feature_router, prefix="/api")
app.include_router(fantasy_router, prefix="/api")
app.include_router(leagues_router, prefix="/api")
app.include_router(games_router, prefix="/api")
app.include_router(v2_router, prefix="/api")
app.include_router(admin_v2_router, prefix="/api")
app.include_router(reloadly_router, prefix="/api")
app.include_router(cashfree_router, prefix="/api")
app.include_router(airtime_router)
app.include_router(payment_router)
from engagement_routes import engage_router
app.include_router(engage_router, prefix="/api")
from razorpay_routes import razorpay_router, init_razorpay
app.include_router(razorpay_router)
init_razorpay(db, freebucks, notif_engine)
app.include_router(beta_router)  # Beta routes already have /api prefix
app.include_router(reports_router)  # Reports routes already have /api prefix

# New phase: Sponsored Pools, KPI, Router
from sponsored_routes import sponsored_router, seed_sponsored_pools
from kpi_routes import kpi_router
app.include_router(sponsored_router)
app.include_router(kpi_router)

# Push campaigns + Google OAuth
from push_routes import push_router
app.include_router(push_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# Geo-Fencing Middleware (India-only + restricted states)
app.add_middleware(GeoFenceMiddleware)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    auto_scorer.stop()
    client.close()

# ══════════════════════ HEALTH CHECK ══════════════════════

@app.get("/api/health")
async def health():
    from redis_cache import get_redis
    redis_ok = False
    try:
        r = get_redis()
        if r:
            redis_ok = r.ping()
    except Exception:
        pass

    # EntitySport status check
    es_ok = False
    try:
        es_test = await entitysport.get_matches(status="1", per_page=1)
        es_ok = es_test is not None
    except Exception:
        pass

    # DB status check
    db_ok = False
    try:
        await db.command("ping")
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "version": "2.0.0",
        "env": os.environ.get("FREE11_ENV", "production"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_status": "connected" if db_ok else "disconnected",
        "redis_status": "connected" if redis_ok else "unavailable",
        "entitysport_status": "connected" if es_ok else "unavailable",
        "integrations": {
            "razorpay": "active" if os.environ.get("RAZORPAY_KEY_ID") else "stubbed",
            "resend": "active" if os.environ.get("RESEND_API_KEY") else "mock",
            "firebase": "active" if os.environ.get("FIREBASE_CREDENTIALS_PATH") else "stubbed",
            "admob": "active" if os.environ.get("ADMOB_APP_ID") else "stubbed",
        }
    }


# ── Root health endpoint — Kubernetes liveness/readiness probe hits /health directly ──
@app.get("/health")
async def health_root():
    """Lightweight root health check for Kubernetes probes. No external calls."""
    # Quick DB check with timeout
    db_ok = False
    try:
        import asyncio
        await asyncio.wait_for(db.command("ping"), timeout=2.0)
        db_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "2.0.0",
        "database": "connected" if db_ok else "disconnected",
    }


# ── Section 12: assetlinks.json served with correct Content-Type ────────────
from fastapi.responses import FileResponse

@app.get("/.well-known/assetlinks.json")
async def serve_assetlinks():
    return FileResponse(
        "/app/frontend/build/.well-known/assetlinks.json",
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=3600"},
    )

