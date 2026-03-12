"""
Sponsored Pools — Brand-funded contest pools
Admin creates pool (brand name, SKU tie, prize), users join.
Platform takes 20% cut on finalization.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from server import db, get_current_user, User

logger = logging.getLogger(__name__)
sponsored_router = APIRouter(prefix="/api/v2/sponsored", tags=["Sponsored Pools"])

PLATFORM_CUT_PCT = 0.20  # 20% platform cut

# ── Sample seed data for 3 sponsored pools ─────────────────────────────────────
SEED_POOLS = [
    {
        "id": str(uuid.uuid4()),
        "brand_name": "CoolDrink Co.",
        "brand_logo": "cooldrink",
        "title": "CoolDrink Season Boost Pool",
        "description": "A top beverage brand is rewarding cricket predictors! Win coins and unlock a cold drink voucher.",
        "sku_tie": "cola_2l",
        "sku_name": "Cola Drink 2L Bottle",
        "prize_pool": 2000,
        "platform_cut": 400,
        "net_prize_pool": 1600,
        "max_participants": 200,
        "current_participants": 0,
        "participants": [],
        "prize_distribution": {"1": 800, "2": 400, "3": 200, "4": 100, "5": 100},
        "status": "open",
        "finalized": False,
        "match_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
        "banner_color": "#1a3a6b",
        "accent": "#00a0e9",
        "badge": "SEASON BOOST",
        "is_sponsored": True,
    },
    {
        "id": str(uuid.uuid4()),
        "brand_name": "Biscuit Brand",
        "brand_logo": "biscuits",
        "title": "Cricket Champions Biscuit Pool",
        "description": "A leading snack brand is backing cricket fans. Win coins + redeem free biscuit pack!",
        "sku_tie": "biscuits_pack",
        "sku_name": "Glucose Biscuits 400g Pack",
        "prize_pool": 1500,
        "platform_cut": 300,
        "net_prize_pool": 1200,
        "max_participants": 150,
        "current_participants": 0,
        "participants": [],
        "prize_distribution": {"1": 600, "2": 300, "3": 200, "4": 60, "5": 40},
        "status": "open",
        "finalized": False,
        "match_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
        "banner_color": "#1a0a00",
        "accent": "#C6A052",
        "badge": "CRICKET CHAMPS",
        "is_sponsored": True,
    },
    {
        "id": str(uuid.uuid4()),
        "brand_name": "Fortune Foods",
        "brand_logo": "fortune",
        "title": "Fortune Atta Predict & Win",
        "description": "Fortune is fuelling your predictions! Top predictors win Fortune Atta.",
        "sku_tie": "atta_5kg",
        "sku_name": "Aashirvaad Atta 5kg",
        "prize_pool": 3000,
        "platform_cut": 600,
        "net_prize_pool": 2400,
        "max_participants": 300,
        "current_participants": 0,
        "participants": [],
        "prize_distribution": {"1": 1200, "2": 600, "3": 300, "4": 150, "5": 150},
        "status": "open",
        "finalized": False,
        "match_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
        "banner_color": "#0a1a00",
        "accent": "#4ade80",
        "badge": "FORTUNE",
        "is_sponsored": True,
    },
]


# ── Request Models ──────────────────────────────────────────────────────────────

class CreateSponsoredPoolReq(BaseModel):
    brand_name: str
    title: str
    description: str
    sku_tie: Optional[str] = None
    prize_pool: int
    max_participants: int = 200
    match_id: Optional[str] = None
    banner_color: str = "#1B1E23"
    accent: str = "#C6A052"
    badge: str = "SPONSORED"


class JoinSponsoredPoolReq(BaseModel):
    pool_id: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@sponsored_router.get("")
async def get_sponsored_pools(status: Optional[str] = "open"):
    query = {"is_sponsored": True}
    if status:
        query["status"] = status
    pools = await db.sponsored_pools.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return pools


@sponsored_router.get("/{pool_id}")
async def get_pool_detail(pool_id: str):
    pool = await db.sponsored_pools.find_one({"id": pool_id}, {"_id": 0})
    if not pool:
        raise HTTPException(404, "Pool not found")
    return pool


@sponsored_router.post("/join")
async def join_sponsored_pool(req: JoinSponsoredPoolReq, user: User = Depends(get_current_user)):
    pool = await db.sponsored_pools.find_one({"id": req.pool_id}, {"_id": 0})
    if not pool:
        raise HTTPException(404, "Pool not found")
    if pool["status"] != "open":
        raise HTTPException(400, f"Pool is {pool['status']}")
    if user.id in pool.get("participants", []):
        raise HTTPException(400, "Already joined")
    if pool["current_participants"] >= pool["max_participants"]:
        raise HTTPException(400, "Pool is full")

    result = await db.sponsored_pools.update_one(
        {"id": req.pool_id, "status": "open", "participants": {"$ne": user.id}},
        {
            "$push": {"participants": user.id},
            "$inc": {"current_participants": 1},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        }
    )
    if result.modified_count == 0:
        raise HTTPException(400, "Could not join pool")

    logger.info(f"SPONSORED POOL JOIN: user={user.id} pool={req.pool_id}")
    return {"success": True, "pool_id": req.pool_id}


@sponsored_router.get("/{pool_id}/leaderboard")
async def get_pool_leaderboard(pool_id: str):
    pool = await db.sponsored_pools.find_one({"id": pool_id}, {"_id": 0})
    if not pool:
        raise HTTPException(404, "Pool not found")

    entries = await db.sponsored_entries.find(
        {"pool_id": pool_id}, {"_id": 0}
    ).sort([("points", -1), ("joined_at", 1)]).to_list(200)

    user_ids = [e["user_id"] for e in entries]
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(len(user_ids))
    user_map = {u["id"]: u["name"] for u in users}

    dist = pool.get("prize_distribution", {})
    for i, entry in enumerate(entries):
        rank = i + 1
        entry["rank"] = rank
        entry["user_name"] = user_map.get(entry["user_id"], "Unknown")
        entry["prize_coins"] = dist.get(str(rank), 0)

    return {"pool": pool, "leaderboard": entries}


@sponsored_router.post("/create")
async def create_sponsored_pool(req: CreateSponsoredPoolReq, user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")

    platform_cut = round(req.prize_pool * PLATFORM_CUT_PCT)
    net_prize = req.prize_pool - platform_cut

    # Auto-generate distribution
    tiers = [0.50, 0.25, 0.15, 0.06, 0.04]
    dist = {}
    for i, pct in enumerate(tiers):
        coins = round(net_prize * pct)
        if coins > 0:
            dist[str(i + 1)] = coins

    pool = {
        "id": str(uuid.uuid4()),
        "brand_name": req.brand_name,
        "brand_logo": req.brand_name.lower().replace(" ", "_"),
        "title": req.title,
        "description": req.description,
        "sku_tie": req.sku_tie,
        "prize_pool": req.prize_pool,
        "platform_cut": platform_cut,
        "net_prize_pool": net_prize,
        "prize_distribution": dist,
        "max_participants": req.max_participants,
        "current_participants": 0,
        "participants": [],
        "status": "open",
        "finalized": False,
        "match_id": req.match_id,
        "banner_color": req.banner_color,
        "accent": req.accent,
        "badge": req.badge,
        "is_sponsored": True,
        "created_by": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.sponsored_pools.insert_one(pool)
    return {k: v for k, v in pool.items() if k != "_id"}


@sponsored_router.post("/{pool_id}/finalize")
async def finalize_sponsored_pool(pool_id: str, user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")

    pool = await db.sponsored_pools.find_one({"id": pool_id}, {"_id": 0})
    if not pool:
        raise HTTPException(404, "Pool not found")
    if pool.get("finalized"):
        return {"already_finalized": True}

    entries = await db.sponsored_entries.find(
        {"pool_id": pool_id}, {"_id": 0}
    ).sort([("points", -1), ("joined_at", 1)]).to_list(200)

    dist = pool.get("prize_distribution", {})
    payouts = []
    now = datetime.now(timezone.utc).isoformat()

    for i, entry in enumerate(entries):
        rank = i + 1
        reward = dist.get(str(rank), 0)
        if reward <= 0:
            continue

        unique_id = f"sponsored_payout_{pool_id}_{entry['user_id']}"
        try:
            await db.coin_transactions.insert_one({
                "unique_payout_id": unique_id,
                "user_id": entry["user_id"],
                "amount": reward,
                "type": "sponsored_prize",
                "description": f"Sponsored Pool Prize: Rank #{rank} — {pool['title']}",
                "pool_id": pool_id,
                "timestamp": now,
            })
            await db.users.update_one(
                {"id": entry["user_id"]},
                {"$inc": {"coins_balance": reward, "total_earned": reward}}
            )
            payouts.append({"user_id": entry["user_id"], "rank": rank, "coins": reward})
        except Exception:
            pass  # Duplicate → already paid

    await db.sponsored_pools.update_one(
        {"id": pool_id},
        {"$set": {"status": "completed", "finalized": True, "updated_at": now}}
    )
    return {"finalized": True, "payouts": payouts, "total_paid": sum(p["coins"] for p in payouts)}


# ── Seed helper (called once at startup) ──────────────────────────────────────

async def seed_sponsored_pools():
    existing = await db.sponsored_pools.count_documents({"is_sponsored": True})
    if existing > 0:
        return
    for pool in SEED_POOLS:
        await db.sponsored_pools.insert_one({**pool})
    logger.info(f"SPONSORED POOLS SEEDED: {len(SEED_POOLS)} pools")
