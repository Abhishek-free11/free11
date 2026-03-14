"""
routes/v2_earn.py — Earn, Games, Ads, Referral, Quest, Cards routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, date

from server import db, get_current_user, User
from v2_engines import ads_provider, referrals, quest_engine, cards, ledger

router = APIRouter()

# ── Request Models ─────────────────────────────────────────────────────────────

class CompleteAdReq(BaseModel):
    ad_id: str

class BindReferralReq(BaseModel):
    referral_code: str
    device_fingerprint: Optional[str] = None

class ActivateCardReq(BaseModel):
    card_id: str
    prediction_id: str

class QuestDismissReq(BaseModel):
    quest_id: str

# ── Cards ──────────────────────────────────────────────────────────────────────

@router.get("/cards/inventory")
async def get_card_inventory(user: User = Depends(get_current_user)):
    return await cards.get_inventory(user.id)

@router.get("/cards/types")
async def get_card_types():
    return await cards.get_card_types()

@router.post("/cards/activate")
async def activate_card(req: ActivateCardReq, user: User = Depends(get_current_user)):
    try:
        return await cards.activate_card(req.card_id, req.prediction_id, user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))

# ── Ads ────────────────────────────────────────────────────────────────────────

@router.get("/ads/status")
async def get_ad_status(user: User = Depends(get_current_user)):
    return await ads_provider.get_ad_status(user.id)

@router.post("/ads/start")
async def start_ad(req: CompleteAdReq, user: User = Depends(get_current_user)):
    return await ads_provider.start_ad(user.id, req.ad_id)

@router.post("/ads/complete")
async def complete_ad(req: CompleteAdReq, user: User = Depends(get_current_user)):
    return await ads_provider.complete_ad(user.id, req.ad_id)

@router.post("/ads/reward")
async def reward_ad_view(req: CompleteAdReq, user: User = Depends(get_current_user)):
    ad_status = await ads_provider.get_ad_status(user.id)
    today = datetime.now(timezone.utc).date().isoformat()
    ad_views_today = ad_status.get("views_today", 0)
    if ad_views_today >= 5:
        raise HTTPException(400, "Maximum 5 ad rewards per day reached")
    try:
        result = await ads_provider.reward_ad(user.id, req.ad_id)
        coins = result.get("coins_earned", 20)
        await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": coins}})
        await db.coin_transactions.insert_one({
            "user_id": user.id, "amount": coins, "type": "ad_reward",
            "description": "Rewarded video ad view",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        updated = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
        return {"success": True, "coins_earned": coins, "new_balance": updated.get("coins_balance", 0)}
    except ValueError as e:
        raise HTTPException(400, str(e))

# ── Referral ───────────────────────────────────────────────────────────────────

@router.get("/referral/code")
async def get_referral_code(user: User = Depends(get_current_user)):
    code = await referrals.generate_referral_code(user.id)
    return {"code": code}

@router.get("/referral/stats")
async def get_referral_stats(user: User = Depends(get_current_user)):
    return await referrals.get_referral_stats(user.id)

@router.post("/referral/bind")
async def bind_referral(req: BindReferralReq, user: User = Depends(get_current_user)):
    try:
        result = await referrals.bind_referral(user.id, req.referral_code, req.device_fingerprint)
        return {
            "success": True,
            "status": result["status"],
            "message": result.get("message", "Referral applied. Complete activity to unlock reward."),
            "pending_reward": result["referee_reward"],
        }
    except ValueError as e:
        raise HTTPException(400, str(e))

# ── Card Game Earn Endpoints ────────────────────────────────────────────────────

async def _daily_game_reward(user_id: str, game_type: str, coins: int, description: str):
    """Shared helper: award daily game reward with idempotency via reference_id."""
    from datetime import date as _date
    today = str(_date.today())
    key = f"{game_type}_{user_id}_{today}"
    if await db.coin_transactions.find_one({"reference_id": key}, {"_id": 0}):
        raise HTTPException(400, f"{description} coins already claimed today. Come back tomorrow!")
    await db.users.update_one({"id": user_id}, {"$inc": {"coins_balance": coins}})
    await db.coin_transactions.insert_one({
        "user_id": user_id, "amount": coins, "type": game_type,
        "description": description, "reference_id": key, "created_at": today,
    })
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "coins_balance": 1})
    return {"success": True, "coins_earned": coins, "new_balance": updated.get("coins_balance", 0)}


@router.post("/earn/teen-patti-win")
async def teen_patti_win(user: User = Depends(get_current_user)):
    return await _daily_game_reward(user.id, "teen_patti_win", 40, "Teen Patti game win vs AI")

@router.post("/earn/solitaire-win")
async def solitaire_win(user: User = Depends(get_current_user)):
    return await _daily_game_reward(user.id, "solitaire_win", 25, "Solitaire game win")

@router.post("/earn/rummy-win")
async def rummy_win(user: User = Depends(get_current_user)):
    return await _daily_game_reward(user.id, "rummy_win", 50, "Rummy game win vs AI")

@router.post("/earn/poker-win")
async def poker_win(user: User = Depends(get_current_user)):
    return await _daily_game_reward(user.id, "poker_win", 60, "Poker game win vs AI")

@router.post("/earn/app-share")
async def app_share_reward(user: User = Depends(get_current_user)):
    key = f"app_share_{user.id}"
    if await db.coin_transactions.find_one({"reference_id": key}, {"_id": 0}):
        raise HTTPException(400, "Share bonus already claimed!")
    coins = 50
    today = str(date.today())
    await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": coins}})
    await db.coin_transactions.insert_one({
        "user_id": user.id, "amount": coins, "type": "app_share",
        "description": "Shared FREE11 app with friends",
        "reference_id": key, "created_at": today,
    })
    updated = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
    return {"success": True, "coins_earned": coins, "new_balance": updated.get("coins_balance", 0)}

# ── Card Game Leaderboard + Streak ────────────────────────────────────────────

@router.get("/games/card-leaderboard")
async def card_game_leaderboard():
    from datetime import date as _date, timedelta
    week_ago = str(_date.today() - timedelta(days=7))
    pipeline = [
        {"$match": {"type": {"$in": ["teen_patti_win", "solitaire_win", "rummy_win", "poker_win"]}, "created_at": {"$gte": week_ago}}},
        {"$group": {"_id": "$user_id", "total_coins": {"$sum": "$amount"}, "wins": {"$sum": 1}}},
        {"$sort": {"total_coins": -1}}, {"$limit": 10},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "id", "as": "u"}},
        {"$project": {"_id": 0, "user_id": "$_id", "total_coins": 1, "wins": 1, "name": {"$arrayElemAt": ["$u.name", 0]}}},
    ]
    return {"leaderboard": await db.coin_transactions.aggregate(pipeline).to_list(10)}


@router.get("/games/card-streak")
async def get_card_streak(user: User = Depends(get_current_user)):
    from datetime import date as _date, timedelta
    today = _date.today()
    CARD_GAME_TYPES = ["teen_patti_win", "solitaire_win", "rummy_win", "poker_win"]
    streak, check_date = 0, today
    while streak < 30:
        played = await db.coin_transactions.find_one(
            {"user_id": user.id, "type": {"$in": CARD_GAME_TYPES}, "created_at": str(check_date)}, {"_id": 0}
        )
        if not played:
            break
        streak += 1
        check_date -= timedelta(days=1)
    played_today = await db.coin_transactions.find_one(
        {"user_id": user.id, "type": {"$in": CARD_GAME_TYPES}, "created_at": str(today)}, {"_id": 0}
    )
    return {"streak": streak, "played_today": bool(played_today)}

# ── Quest Engine ───────────────────────────────────────────────────────────────

@router.get("/quest/status")
async def quest_status(user: User = Depends(get_current_user)):
    return await quest_engine.check_eligibility(user.id)

@router.post("/quest/offer")
async def offer_quest(user: User = Depends(get_current_user)):
    eligibility = await quest_engine.check_eligibility(user.id)
    session = await quest_engine.offer_quest(user.id)
    return {**session, "streak": eligibility.get("streak", 0)}

@router.post("/quest/claim-ad")
async def quest_claim_ad(req: QuestDismissReq, user: User = Depends(get_current_user)):
    try:
        return await quest_engine.claim_ad_reward(user.id, req.quest_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/quest/ration-viewed")
async def quest_ration_viewed(req: QuestDismissReq, user: User = Depends(get_current_user)):
    return await quest_engine.mark_ration_viewed(user.id, req.quest_id)

@router.post("/quest/dismiss")
async def quest_dismiss(req: QuestDismissReq, user: User = Depends(get_current_user)):
    return await quest_engine.dismiss_quest(user.id, req.quest_id)

@router.get("/quest/history")
async def quest_history(user: User = Depends(get_current_user)):
    return await quest_engine.get_history(user.id)
