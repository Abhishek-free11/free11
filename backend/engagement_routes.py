"""
FREE11 Engagement & Retention API Routes
Progression, Missions, Streak, Spin, Leaderboards, Economy, Surprise Rewards.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict

from server import db, get_current_user, User

from progression_engine import ProgressionEngine
from missions_engine import MissionsEngine
from spin_wheel_engine import SpinWheelEngine
from economy_engine import EconomyEngine
from streak_leaderboard_engine import StreakEngine, LeaderboardEngine
from cards_engine import CardsEngine
from notification_engine import NotificationEngine

engage_router = APIRouter(prefix="/v2/engage", tags=["engagement"])

progression = ProgressionEngine(db)
missions = MissionsEngine(db)
spin = SpinWheelEngine(db)
economy = EconomyEngine(db)
streak = StreakEngine(db)
leaderboards = LeaderboardEngine(db)
cards = CardsEngine(db)
notif = NotificationEngine(db)


# ══════════════════════ PROGRESSION ══════════════════════

@engage_router.get("/progression")
async def get_progression(user: User = Depends(get_current_user)):
    return await progression.get_progression(user.id)


@engage_router.get("/tiers")
async def get_tiers():
    return {"tiers": ProgressionEngine.get_tiers(), "xp_rules": ProgressionEngine.get_xp_rules()}


# ══════════════════════ MISSIONS ══════════════════════

@engage_router.get("/missions")
async def get_missions(user: User = Depends(get_current_user)):
    m = await missions.get_daily_missions(user.id)
    return {"missions": m, "date": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")}


class ClaimMissionReq(BaseModel):
    mission_id: str


@engage_router.post("/missions/claim")
async def claim_mission(req: ClaimMissionReq, user: User = Depends(get_current_user)):
    try:
        reward = await missions.claim_reward(user.id, req.mission_id)
        # Credit coins
        if reward["coins"] > 0:
            await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": reward["coins"]}})
            await db.coin_transactions.insert_one({
                "user_id": user.id, "amount": reward["coins"], "type": "mission_reward",
                "description": f"Mission completed: {req.mission_id}",
                "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            })
        # Add XP
        if reward["xp"] > 0:
            await progression.add_xp(user.id, "mission_completed", reward["xp"])
        await notif.send(user.id, "daily_reminder", f"Mission complete! +{reward['coins']} coins, +{reward['xp']} XP")
        return reward
    except ValueError as e:
        raise HTTPException(400, str(e))


# ══════════════════════ STREAK ══════════════════════

@engage_router.get("/streak")
async def get_streak(user: User = Depends(get_current_user)):
    return await streak.get_streak(user.id)


@engage_router.post("/streak/checkin")
async def streak_checkin(user: User = Depends(get_current_user)):
    try:
        result = await streak.checkin(user.id)
        # Credit coins
        if result["coins_earned"] > 0:
            await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": result["coins_earned"]}})
            await db.coin_transactions.insert_one({
                "user_id": user.id, "amount": result["coins_earned"], "type": "streak_reward",
                "description": f"Login streak day {result['streak_days']}",
                "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            })
        # Add XP
        await progression.add_xp(user.id, "daily_login", result.get("xp_earned", 5))
        # Grant booster card if applicable
        if result.get("booster"):
            try:
                await cards.grant_card(user.id, result["booster"], "streak_reward")
            except Exception:
                pass
        # Update missions
        await missions.update_progress(user.id, "checkins", 1)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


# ══════════════════════ SPIN WHEEL ══════════════════════

@engage_router.get("/spin/status")
async def spin_status(user: User = Depends(get_current_user)):
    return await spin.can_spin(user.id)


@engage_router.post("/spin")
async def do_spin(user: User = Depends(get_current_user)):
    try:
        result = await spin.spin(user.id)
        reward = result["reward"]
        # Process reward
        if reward["type"] == "coins" and reward["value"] > 0:
            await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": reward["value"]}})
            await db.coin_transactions.insert_one({
                "user_id": user.id, "amount": reward["value"], "type": "spin_reward",
                "description": f"Spin wheel: {reward['label']}",
                "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            })
        elif reward["type"] == "booster":
            try:
                await cards.grant_card(user.id, str(reward["value"]), "spin_reward")
            except Exception:
                pass
        elif reward["type"] == "xp" and reward["value"] > 0:
            await progression.add_xp(user.id, "spin_reward", reward["value"])
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@engage_router.get("/spin/history")
async def spin_history(user: User = Depends(get_current_user)):
    return await spin.get_history(user.id)


# ══════════════════════ LEADERBOARDS ══════════════════════

@engage_router.get("/leaderboard/{period}")
async def get_leaderboard(period: str, limit: int = 50):
    if period not in ("daily", "weekly", "seasonal"):
        raise HTTPException(400, "Period must be daily, weekly, or seasonal")
    return await leaderboards.get_leaderboard(period, limit)


# ══════════════════════ ECONOMY ══════════════════════

@engage_router.get("/economy/status")
async def economy_status(user: User = Depends(get_current_user)):
    cap = await economy.check_daily_cap(user.id)
    redeem = await economy.check_redeem_limit(user.id)
    return {**cap, **redeem}


@engage_router.get("/economy/stats")
async def economy_stats(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return await economy.get_economy_stats()


# ══════════════════════ SURPRISE REWARDS ══════════════════════

@engage_router.post("/surprise/{trigger}")
async def check_surprise(trigger: str, user: User = Depends(get_current_user)):
    result = await economy.try_surprise_reward(user.id, trigger)
    if result:
        if result["type"] == "coins":
            await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": result["amount"]}})
        elif result["type"] == "xp":
            await progression.add_xp(user.id, "surprise", result["amount"])
        await notif.send(user.id, "daily_reminder", f"Surprise! You won {result.get('amount', '')} {result['type']}!")
    return {"surprise": result}


# ══════════════════════ REWARD STORE TIERS ══════════════════════

STORE_TIERS = {
    1: {"name": "Bronze Store", "min_tier": "Bronze", "vouchers": [50]},
    2: {"name": "Silver Store", "min_tier": "Silver", "vouchers": [50, 100]},
    3: {"name": "Gold Store", "min_tier": "Gold", "vouchers": [50, 100, 250]},
    4: {"name": "Platinum Store", "min_tier": "Platinum", "vouchers": [50, 100, 250, 500]},
    5: {"name": "Diamond Store", "min_tier": "Diamond", "vouchers": [50, 100, 250, 500, 1000]},
}


@engage_router.get("/store/tiers")
async def get_store_tiers(user: User = Depends(get_current_user)):
    prog = await progression.get_progression(user.id)
    user_store_level = prog["tier"]["store_level"]
    tiers = []
    for level, info in STORE_TIERS.items():
        tiers.append({
            **info,
            "level": level,
            "unlocked": level <= user_store_level,
        })
    return {"user_store_level": user_store_level, "tiers": tiers}
