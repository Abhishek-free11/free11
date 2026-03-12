"""
FREE11 V2 API Routes
Unified routes for: Contests, Predictions, Cards, Ledger, Ads, Vouchers, Referral, MatchState
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone, date
import uuid

from server import db, get_current_user, User
from fcm_service import FCMService as _FCMService

# Lazy FCM accessor — avoids circular imports with server.py
def _get_fcm():
    from server import fcm as _fcm
    return _fcm

# Engine imports
from ledger_engine import LedgerEngine
from contest_engine import ContestEngine
from predict_engine import PredictEngine
from cards_engine import CardsEngine
from matchstate_engine import MatchStateEngine
from referral_engine import ReferralEngine
from services.voucher_provider import MockVoucherProvider
from services.ads_provider import MockAdsProvider
from entitysport_service import EntitySportService
from fantasy_engine import FantasyEngine
from engagement_engine import CrowdMeterEngine, PuzzleEngine, WeeklyReportEngine

# Initialize engines
ledger = LedgerEngine(db)
contests = ContestEngine(db)
predictions = PredictEngine(db)
cards = CardsEngine(db)
matchstate = MatchStateEngine(db)
referrals = ReferralEngine(db)
voucher_provider = MockVoucherProvider(db)
ads_provider = MockAdsProvider(db)
entitysport = EntitySportService(db)
fantasy = FantasyEngine(db)
crowd_meter = CrowdMeterEngine(db)
puzzle_engine = PuzzleEngine(db)
report_engine = WeeklyReportEngine(db)

v2_router = APIRouter(prefix="/v2", tags=["V2"])

# ══════════════════════ REQUEST MODELS ══════════════════════

class CreateContestReq(BaseModel):
    match_id: str
    name: str
    contest_type: str = "public"
    max_participants: int = 100
    entry_fee: int = 0

class JoinContestReq(BaseModel):
    contest_id: str
    team: Optional[Dict] = None

class JoinByCodeReq(BaseModel):
    invite_code: str
    team: Optional[Dict] = None

class SubmitPredictionReq(BaseModel):
    match_id: str
    prediction_type: str
    prediction_value: str
    over_number: Optional[int] = None

class ActivateCardReq(BaseModel):
    card_id: str
    prediction_id: str

class RedeemReq(BaseModel):
    product_id: str

class CompleteAdReq(BaseModel):
    ad_id: str

class BindReferralReq(BaseModel):
    referral_code: str
    device_fingerprint: Optional[str] = None

class PinWishlistReq(BaseModel):
    product_id: str

# ══════════════════════ CONTEST ROUTES ══════════════════════

@v2_router.post("/contests/create")
async def create_contest(req: CreateContestReq, user: User = Depends(get_current_user)):
    try:
        contest = await contests.create_contest(
            match_id=req.match_id,
            creator_id=user.id,
            name=req.name,
            contest_type=req.contest_type,
            max_participants=req.max_participants,
            entry_fee=req.entry_fee,
        )
        return contest
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@v2_router.post("/contests/join")
async def join_contest(req: JoinContestReq, user: User = Depends(get_current_user)):
    try:
        contest = await contests.get_contest(req.contest_id)
        if not contest:
            raise HTTPException(status_code=404, detail="Contest not found")
        if contest.get("entry_fee", 0) > 0:
            await ledger.debit(user.id, contest["entry_fee"], "contest_entry", req.contest_id, f"Contest entry: {contest['name']}")

        result = await contests.join_contest(req.contest_id, user.id, req.team)
        # Section 5: check referral activity gate after joining
        try:
            await referrals.check_and_complete_referral(user.id)
        except Exception:
            pass
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@v2_router.post("/contests/join-code")
async def join_by_invite_code(req: JoinByCodeReq, user: User = Depends(get_current_user)):
    try:
        result = await contests.join_by_invite_code(req.invite_code, user.id, req.team)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@v2_router.get("/contests/match/{match_id}")
async def get_match_contests(match_id: str, contest_type: Optional[str] = None):
    return await contests.get_contests_for_match(match_id, contest_type)

@v2_router.get("/contests/{contest_id}")
async def get_contest_detail(contest_id: str):
    contest = await contests.get_contest(contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    return contest

@v2_router.get("/contests/{contest_id}/leaderboard")
async def get_contest_leaderboard(contest_id: str):
    return await contests.get_leaderboard(contest_id)

@v2_router.get("/contests/user/my")
async def get_my_contests(user: User = Depends(get_current_user)):
    return await contests.get_user_contests(user.id)


@v2_router.post("/contests/seed/{match_id}")
async def seed_match_contests(match_id: str, user: User = Depends(get_current_user)):
    """Seed platform contests for a match (admin or auto-called on match load)."""
    # Allow any logged-in user to trigger seeding (idempotent — won't duplicate)
    match = await db.matches.find_one({"match_id": match_id}, {"_id": 0, "series": 1})
    series = match.get("series", "") if match else ""
    created = await contests.seed_platform_contests(match_id, series)
    return {"seeded": len(created), "contests": created}


@v2_router.post("/contests/{contest_id}/finalize")
async def finalize_contest(contest_id: str, user: User = Depends(get_current_user)):
    """Finalize contest and distribute coin prizes to winners. Admin only."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        return await contests.finalize_contest(contest_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ══════════════════════ PREDICTION ROUTES ══════════════════════

@v2_router.post("/predictions/submit")
async def submit_prediction(req: SubmitPredictionReq, user: User = Depends(get_current_user)):
    # Section 6: enforce max predictions per match per user
    prediction_count = await db.predictions_v2.count_documents(
        {"user_id": user.id, "match_id": req.match_id}
    )
    if prediction_count >= MAX_PREDICTIONS_PER_MATCH:
        raise HTTPException(429, f"Maximum {MAX_PREDICTIONS_PER_MATCH} predictions per match reached")

    try:
        prediction = await predictions.submit_prediction(
            user_id=user.id,
            match_id=req.match_id,
            prediction_type=req.prediction_type,
            prediction_value=req.prediction_value,
            over_number=req.over_number,
        )
        # Section 5: check if this prediction completes a pending referral activity gate
        try:
            await referrals.check_and_complete_referral(user.id)
        except Exception:
            pass  # Non-blocking
        return prediction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@v2_router.get("/predictions/my")
async def get_my_predictions(
    match_id: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    return await predictions.get_user_predictions(user.id, match_id)

@v2_router.get("/predictions/stats")
async def get_prediction_stats(user: User = Depends(get_current_user)):
    return await predictions.get_prediction_stats(user.id)

@v2_router.get("/predictions/types")
async def get_prediction_types():
    from predict_engine import PREDICTION_TYPES, PREDICTION_REWARDS
    result = {}
    for key, val in PREDICTION_TYPES.items():
        result[key] = {**val, "reward": PREDICTION_REWARDS.get(key, 0)}
    return result

# ══════════════════════ CARDS ROUTES ══════════════════════

@v2_router.get("/cards/inventory")
async def get_card_inventory(user: User = Depends(get_current_user)):
    return await cards.get_inventory(user.id)

@v2_router.get("/cards/types")
async def get_card_types():
    return cards.get_card_types()

@v2_router.post("/cards/activate")
async def activate_card(req: ActivateCardReq, user: User = Depends(get_current_user)):
    try:
        result = await cards.activate_card(user.id, req.card_id, req.prediction_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ══════════════════════ LEDGER ROUTES ══════════════════════

@v2_router.get("/ledger/balance")
async def get_ledger_balance(user: User = Depends(get_current_user)):
    balance = await ledger.get_balance(user.id)
    return {"balance": balance, "user_id": user.id}

@v2_router.get("/ledger/history")
async def get_ledger_history(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
):
    entries = await ledger.get_history(user.id, limit, offset)
    balance = await ledger.get_balance(user.id)
    return {"entries": entries, "balance": balance, "count": len(entries)}

@v2_router.post("/ledger/reconcile")
async def reconcile_ledger(user: User = Depends(get_current_user)):
    result = await ledger.reconcile(user.id)
    return result

# ══════════════════════ REDEMPTION (MOCK VOUCHER) ROUTES ══════════════════════

@v2_router.post("/redeem")
async def redeem_product(req: RedeemReq, user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": req.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.get("stock", 0) <= 0:
        raise HTTPException(status_code=400, detail="Out of stock")

    try:
        # Debit coins via ledger
        await ledger.debit(user.id, product["coin_price"], "redemption", req.product_id, f"Redeemed: {product['name']}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Decrement stock
    await db.products.update_one({"id": req.product_id}, {"$inc": {"stock": -1}})

    # Create mock voucher
    voucher = await voucher_provider.create_voucher(user.id, req.product_id, product["coin_price"])

    return {
        "success": True,
        "voucher": voucher,
        "product_name": product["name"],
        "coins_spent": product["coin_price"],
    }

@v2_router.get("/redeem/status/{voucher_id}")
async def get_voucher_status(voucher_id: str, user: User = Depends(get_current_user)):
    status = await voucher_provider.check_status(voucher_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail="Voucher not found")
    return status

@v2_router.get("/redeem/my")
async def get_my_vouchers(user: User = Depends(get_current_user)):
    vouchers = await db.vouchers.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return vouchers

# ══════════════════════ PUSH NOTIFICATION ROUTES (v2) ══════════════════════

class PushRegisterReq(BaseModel):
    device_token: str
    device_type: str = "android"

class PushSendReq(BaseModel):
    title: str
    body: str
    user_id: Optional[str] = None
    deep_link: Optional[str] = None
    topic: Optional[str] = None

@v2_router.post("/push/register")
async def register_device_v2(req: PushRegisterReq, user: User = Depends(get_current_user)):
    """Register device FCM token — stores in user_devices and fcm_tokens collections."""
    now = datetime.now(timezone.utc).isoformat()
    # Upsert into user_devices (per spec)
    await db.user_devices.update_one(
        {"user_id": user.id, "device_type": req.device_type},
        {"$set": {
            "device_token": req.device_token,
            "device_type": req.device_type,
            "updated_at": now,
            "active": True,
        }, "$setOnInsert": {"user_id": user.id, "created_at": now}},
        upsert=True,
    )
    # Also register in fcm_tokens for backwards compat
    await _get_fcm().register_token(user.id, req.device_token, req.device_type)
    return {"registered": True, "device_type": req.device_type}


@v2_router.post("/push/send")
async def send_push_notification(req: PushSendReq, user: User = Depends(get_current_user)):
    """Send push notification. Admin use-case or self-notification."""
    target_user_id = req.user_id if req.user_id else user.id
    data = {}
    if req.deep_link:
        data["deep_link"] = req.deep_link
    sent = await _get_fcm().send_push(target_user_id, req.title, req.body, data)
    return {"sent": sent, "target_user_id": target_user_id}


# ══════════════════════ ADS (MOCK) ROUTES ══════════════════════

@v2_router.get("/ads/status")
async def get_ad_status(user: User = Depends(get_current_user)):
    return await ads_provider.get_ad_status(user.id)

@v2_router.post("/ads/start")
async def start_ad(user: User = Depends(get_current_user)):
    result = await ads_provider.start_ad(user.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@v2_router.post("/ads/complete")
async def complete_ad(req: CompleteAdReq, user: User = Depends(get_current_user)):
    result = await ads_provider.complete_ad(user.id, req.ad_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Credit coins via ledger
    await ledger.credit(
        user.id,
        result["reward_coins"],
        "ad_reward",
        req.ad_id,
        "Watched rewarded ad"
    )
    return result


# ══════════════════════ ADMOB REWARDED AD ENDPOINT ══════════════════════

ADMOB_DAILY_LIMIT = 5
ADMOB_REWARD_COINS = 20

class AdRewardReq(BaseModel):
    reward_type: str = "ad_watch"

@v2_router.post("/ads/reward")
async def claim_admob_reward(req: AdRewardReq, user: User = Depends(get_current_user)):
    """Called by the web app after a real AdMob rewarded ad completes on Android TWA."""
    today = date.today().isoformat()

    # Check daily limit (shared with mock events collection)
    watched_today = await db.ad_events.count_documents({
        "user_id": user.id,
        "date": today,
        "status": "completed",
    })
    if watched_today >= ADMOB_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail="Daily ad limit reached (5/day)")

    ad_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.ad_events.insert_one({
        "id": ad_id,
        "user_id": user.id,
        "status": "completed",
        "date": today,
        "started_at": now,
        "completed_at": now,
        "reward_coins": ADMOB_REWARD_COINS,
        "provider": "admob",
        "reward_type": req.reward_type,
    })

    await ledger.credit(
        user.id,
        ADMOB_REWARD_COINS,
        "ad_reward",
        ad_id,
        "AdMob rewarded ad watched",
    )

    remaining = max(0, ADMOB_DAILY_LIMIT - watched_today - 1)
    return {
        "success": True,
        "reward_coins": ADMOB_REWARD_COINS,
        "watched_today": watched_today + 1,
        "remaining_today": remaining,
        "daily_limit": ADMOB_DAILY_LIMIT,
    }

# ══════════════════════ REFERRAL ROUTES ══════════════════════

@v2_router.get("/referral/code")
async def get_referral_code(user: User = Depends(get_current_user)):
    code = await referrals.generate_referral_code(user.id)
    return {"code": code}

@v2_router.get("/referral/stats")
async def get_referral_stats(user: User = Depends(get_current_user)):
    return await referrals.get_referral_stats(user.id)

@v2_router.post("/referral/bind")
async def bind_referral(req: BindReferralReq, user: User = Depends(get_current_user)):
    try:
        result = await referrals.bind_referral(user.id, req.referral_code, req.device_fingerprint)
        # Section 5: referral rewards are ONLY credited after activity gate is met (via check_and_complete_referral)
        # Do NOT credit here — status is always 'pending' at bind time. Double-payout prevention.
        return {
            "success": True,
            "status": result["status"],
            "message": result.get("message", "Referral applied. Complete activity to unlock reward."),
            "pending_reward": result["referee_reward"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ══════════════════════ MATCH STATE ROUTES ══════════════════════

@v2_router.get("/match/{match_id}/state")
async def get_match_state(match_id: str):
    snapshot = await matchstate.get_latest_snapshot(match_id)
    match = await db.matches.find_one({"match_id": match_id}, {"_id": 0})

    # If match has stale TBA team names, refresh from EntitySport
    if match and (match.get("team1", "TBA") == "TBA" or match.get("team2", "TBA") == "TBA"):
        try:
            fresh = await entitysport.get_match_info(match_id)
            if fresh and fresh.get("team1", "TBA") != "TBA":
                await db.matches.update_one(
                    {"match_id": match_id},
                    {"$set": {k: v for k, v in fresh.items() if k not in ("_id",)}}
                )
                match = {**match, **fresh}
        except Exception:
            pass

    return {
        "match": match,
        "snapshot": snapshot,
        "frozen": matchstate.is_frozen(match_id),
    }

@v2_router.get("/matches/live")
async def get_live_matches():
    matches = await db.matches.find(
        {"status": {"$in": ["live", "upcoming"]}},
        {"_id": 0}
    ).sort("match_date", 1).to_list(50)
    return matches

@v2_router.get("/matches/all")
async def get_all_matches(status: Optional[str] = None, limit: int = 20):
    query = {}
    if status:
        query["status"] = status
    matches = await db.matches.find(query, {"_id": 0}).sort("match_date", -1).limit(limit).to_list(limit)
    return matches


# ══════════════════════ ENTITYSPORT LIVE DATA ══════════════════════

@v2_router.get("/es/matches")
async def es_get_matches(status: str = "3", per_page: int = 20):
    """Get matches from EntitySport (1=upcoming, 2=completed, 3=live)"""
    return await entitysport.get_matches(status=status, per_page=per_page)

@v2_router.get("/es/match/{match_id}/info")
async def es_get_match_info(match_id: str):
    data = await entitysport.get_match_info(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="Match not found")
    return data

@v2_router.get("/es/match/{match_id}/live")
async def es_get_match_live(match_id: str):
    data = await entitysport.get_match_live(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="No live data")
    return data

@v2_router.get("/es/match/{match_id}/scorecard")
async def es_get_scorecard(match_id: str):
    data = await entitysport.get_match_scorecard(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="No scorecard")
    return data

@v2_router.get("/es/match/{match_id}/squads")
async def es_get_squads(match_id: str):
    """Get match squads with player details, roles, credits for fantasy team building"""
    data = await entitysport.get_match_squads(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="No squad data")
    return data

@v2_router.post("/es/sync")
async def es_sync_matches(user: User = Depends(get_current_user)):
    """Sync live + upcoming matches from EntitySport to local DB, then seed platform contests."""
    count = await entitysport.sync_matches()
    # Auto-seed platform contests for any new matches
    matches_list = await db.matches.find(
        {"status": {"$in": ["live", "upcoming"]}}, {"_id": 0, "match_id": 1, "series": 1}
    ).to_list(50)
    seeded_total = 0
    for m in matches_list:
        created = await contests.seed_platform_contests(m["match_id"], m.get("series", ""))
        seeded_total += len(created)
    return {"synced": count, "contests_seeded": seeded_total}

@v2_router.get("/es/competitions")
async def es_get_competitions():
    return await entitysport.get_competitions()

# ══════════════════════ FANTASY TEAM ROUTES ══════════════════════

class CreateFantasyTeamReq(BaseModel):
    match_id: str
    players: List[Dict]
    captain_id: str
    vc_id: str

class CompareTeamsReq(BaseModel):
    team_id_1: str
    team_id_2: str

@v2_router.post("/fantasy/create-team")
async def create_fantasy_team(req: CreateFantasyTeamReq, user: User = Depends(get_current_user)):
    try:
        team = await fantasy.create_team(
            user_id=user.id,
            match_id=req.match_id,
            players=req.players,
            captain_id=req.captain_id,
            vc_id=req.vc_id,
        )
        return team
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@v2_router.get("/fantasy/my-teams")
async def get_my_fantasy_teams(match_id: Optional[str] = None, user: User = Depends(get_current_user)):
    return await fantasy.get_user_teams(user.id, match_id)

@v2_router.get("/fantasy/team/{team_id}")
async def get_fantasy_team(team_id: str):
    team = await fantasy.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@v2_router.get("/fantasy/rankings/{match_id}")
async def get_fantasy_rankings(match_id: str):
    return await fantasy.get_match_rankings(match_id)

@v2_router.post("/fantasy/compare")
async def compare_fantasy_teams(req: CompareTeamsReq, user: User = Depends(get_current_user)):
    try:
        return await fantasy.compare_teams(req.team_id_1, req.team_id_2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@v2_router.get("/fantasy/points-system")
async def get_points_system():
    from fantasy_engine import POINTS, ROLE_CONSTRAINTS
    return {"points": POINTS, "constraints": ROLE_CONSTRAINTS, "team_size": 11, "max_credits": 100.0, "max_per_team": 7}


# ══════════════════════ FREE BUCKS ROUTES ══════════════════════

from freebucks_engine import FreeBucksEngine
from feature_gate import FeatureGate
from notification_engine import NotificationEngine
from analytics_engine import AnalyticsEngine
from redis_cache import get_cache_stats

_freebucks = FreeBucksEngine(db)
_feature_gate = FeatureGate(db, _freebucks)
_notif = NotificationEngine(db)
_analytics = AnalyticsEngine(db)


@v2_router.get("/freebucks/balance")
async def freebucks_balance(user: User = Depends(get_current_user)):
    balance = await _freebucks.get_balance(user.id)
    wallet = await _freebucks.get_wallet(user.id)
    return {"balance": balance, "wallet": wallet}


@v2_router.get("/freebucks/history")
async def freebucks_history(limit: int = 50, user: User = Depends(get_current_user)):
    return await _freebucks.get_history(user.id, limit)


@v2_router.get("/freebucks/packages")
async def freebucks_packages():
    return FreeBucksEngine.get_packages()


@v2_router.get("/payments/history")
async def get_wallet_history(user: User = Depends(get_current_user)):
    """Combined wallet history: Razorpay purchases + coin transactions."""
    purchases = await db.payment_transactions.find(
        {"user_id": user.id},
        {"_id": 0, "order_id": 1, "razorpay_payment_id": 1, "amount": 1,
         "bucks": 1, "payment_status": 1, "created_at": 1, "paid_at": 1, "package_id": 1},
    ).sort("created_at", -1).limit(100).to_list(100)

    coin_txns = await db.coin_transactions.find(
        {"user_id": user.id},
        {"_id": 0, "id": 1, "type": 1, "credit": 1, "debit": 1, "amount": 1,
         "description": 1, "timestamp": 1, "reference_id": 1},
    ).sort("timestamp", -1).limit(100).to_list(100)

    return {"free_bucks_purchases": purchases, "coin_transactions": coin_txns}


# ══════════════════════ FEATURE GATING ROUTES ══════════════════════

@v2_router.get("/features/gated")
async def get_gated_features():
    return FeatureGate.get_gated_features()


@v2_router.get("/features/check/{feature}")
async def check_feature_access(feature: str, user: User = Depends(get_current_user)):
    return await _feature_gate.check_access(user.id, feature)


class UseFeatureReq(BaseModel):
    feature: str
    reference_id: str = ""


@v2_router.post("/features/use")
async def use_feature(req: UseFeatureReq, user: User = Depends(get_current_user)):
    try:
        return await _feature_gate.consume_feature(user.id, req.feature, req.reference_id)
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))


# ══════════════════════ NOTIFICATION ROUTES ══════════════════════

@v2_router.get("/notifications")
async def get_notifications(limit: int = 50, unread_only: bool = False, user: User = Depends(get_current_user)):
    notifs = await _notif.get_notifications(user.id, limit, unread_only)
    unread = await _notif.get_unread_count(user.id)
    return {"notifications": notifs, "unread_count": unread}


@v2_router.post("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, user: User = Depends(get_current_user)):
    await _notif.mark_read(user.id, notif_id)
    return {"ok": True}


@v2_router.post("/notifications/read-all")
async def mark_all_notifications_read(user: User = Depends(get_current_user)):
    await _notif.mark_all_read(user.id)
    return {"ok": True}


# ══════════════════════ ANALYTICS & HEALTH ROUTES ══════════════════════

@v2_router.post("/analytics/event")
async def track_ui_event(request: Request, current_user: User = Depends(get_current_user)):
    """Track any frontend button/icon click for analytics."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    event = body.get("event", "unknown")
    properties = body.get("properties", {})
    await _analytics.track(event, str(current_user.id), properties)
    return {"ok": True}

@v2_router.post("/analytics/event/anon")
async def track_anon_event(request: Request):
    """Track anonymous events (pre-login screens)."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    event = body.get("event", "unknown")
    properties = body.get("properties", {})
    await _analytics.track(event, "anon", properties)
    return {"ok": True}

@v2_router.get("/analytics/dashboard")
async def analytics_dashboard(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return await _analytics.get_dashboard()


@v2_router.get("/cache/stats")
async def cache_stats(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    return get_cache_stats()


@v2_router.get("/health")
async def health_check():
    from redis_cache import get_redis
    redis_ok = False
    try:
        r = get_redis()
        if r:
            redis_ok = r.ping()
    except Exception:
        pass
    return {
        "status": "ok",
        "redis": redis_ok,
        "version": "2.0.0",
        "env": __import__("os").environ.get("FREE11_ENV", "unknown"),
    }


# ══════════════════════ XOXODAY VOUCHER ROUTES ══════════════════════

from xoxoday_provider import XoxodayProvider

_xoxoday = XoxodayProvider(db)


@v2_router.get("/vouchers/catalog")
async def voucher_catalog(category: str = ""):
    return await _xoxoday.get_catalog(category)


@v2_router.get("/vouchers/status")
async def voucher_status():
    return {"provider": "xoxoday" if XoxodayProvider.is_enabled() else "mock", "enabled": XoxodayProvider.is_enabled()}


class RedeemVoucherReq(BaseModel):
    product_id: str
    denomination: int
    mobile: str = ""


@v2_router.post("/vouchers/redeem")
async def redeem_voucher(req: RedeemVoucherReq, user: User = Depends(get_current_user)):
    # Check coin balance
    user_data = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1, "email": 1, "mobile": 1})
    coin_cost = req.denomination * 100  # 100 coins per ₹1 value
    if user_data.get("coins_balance", 0) < coin_cost:
        raise HTTPException(400, f"Need {coin_cost} Free Coins. You have {user_data.get('coins_balance', 0)}.")

    # Deduct coins
    await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": -coin_cost}})
    await db.coin_transactions.insert_one({
        "user_id": user.id, "amount": -coin_cost, "type": "voucher_redeem",
        "description": f"Redeemed ₹{req.denomination} voucher ({req.product_id})",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Place order
    email = user_data.get("email", "")
    mobile = req.mobile or user_data.get("mobile", "")
    result = await _xoxoday.place_order(user.id, req.product_id, req.denomination, email, mobile)

    if result.get("status") == "failed":
        # Refund coins on failure
        await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": coin_cost}})
        await db.coin_transactions.insert_one({
            "user_id": user.id, "amount": coin_cost, "type": "voucher_refund",
            "description": "Refund: voucher order failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        raise HTTPException(500, "Voucher order failed. Coins refunded.")

    return {
        "status": result["status"],
        "voucher_code": result.get("voucher_code", ""),
        "delivery": result.get("delivery", ""),
        "coins_spent": coin_cost,
        "new_balance": user_data.get("coins_balance", 0) - coin_cost,
    }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 10 — Admin Operations: Bulk Contest Finalization
# SECTION 6  — Coin Economy: Prediction Limits
# ════════════════════════════════════════════════════════════════════════════

MAX_PREDICTIONS_PER_MATCH = 10       # Section 6: max predictions per user per match
MAX_SPIN_PER_DAY         = 1         # Already enforced; documented here
MAX_MISSION_REWARDS_PER_DAY = 5      # Max distinct mission completions per day


@v2_router.post("/admin/finalize-match/{match_id}")
async def admin_finalize_match(match_id: str, user: User = Depends(get_current_user)):
    """Finalize all unfinalized contests for a completed match. Admin only."""
    if not user.is_admin:
        raise HTTPException(403, "Admin only")

    open_contests = await db.contests.find(
        {"match_id": match_id, "finalized": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(50)

    if not open_contests:
        return {"message": "No contests to finalize", "match_id": match_id}

    results = []
    for c in open_contests:
        try:
            result = await contests.finalize_contest(c["id"])
            results.append({"contest_id": c["id"], "name": c["name"], "result": result})
        except Exception as e:
            results.append({"contest_id": c["id"], "name": c["name"], "error": str(e)})

    total_paid = sum(r["result"].get("total_paid", 0) for r in results if "result" in r)
    return {"match_id": match_id, "finalized_count": len(results), "total_paid": total_paid, "results": results}


@v2_router.get("/predictions/match/{match_id}/count")
async def get_user_prediction_count(match_id: str, user: User = Depends(get_current_user)):
    """Return how many predictions the user has made for this match."""
    count = await db.predictions_v2.count_documents({"user_id": user.id, "match_id": match_id})
    return {"count": count, "limit": MAX_PREDICTIONS_PER_MATCH, "remaining": max(0, MAX_PREDICTIONS_PER_MATCH - count)}


# ════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — Wish List Progress Tracker
# ════════════════════════════════════════════════════════════════════════════

@v2_router.post("/wishlist/pin")
async def pin_wishlist(req: PinWishlistReq, user: User = Depends(get_current_user)):
    """Pin a product as the user's savings goal. One goal at a time."""
    product = await db.products.find_one({"id": req.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(404, "Product not found")
    await db.user_wishlist.update_one(
        {"user_id": user.id},
        {"$set": {"user_id": user.id, "product_id": req.product_id, "pinned_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"pinned": True, "product_id": req.product_id}

@v2_router.delete("/wishlist/unpin")
async def unpin_wishlist(user: User = Depends(get_current_user)):
    """Remove the user's pinned wishlist goal."""
    await db.user_wishlist.delete_one({"user_id": user.id})
    return {"unpinned": True}

@v2_router.get("/wishlist")
async def get_wishlist(user: User = Depends(get_current_user)):
    """Get user's pinned reward goal with live progress calculation."""
    doc = await db.user_wishlist.find_one({"user_id": user.id}, {"_id": 0})
    if not doc:
        return {"pinned": False, "product": None}

    product = await db.products.find_one({"id": doc["product_id"]}, {"_id": 0})
    if not product:
        await db.user_wishlist.delete_one({"user_id": user.id})
        return {"pinned": False, "product": None}

    u_data = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
    coins_balance = (u_data or {}).get("coins_balance", 0)
    coin_price = product.get("coin_price", 0)
    progress = round(min(100, (coins_balance / coin_price) * 100), 1) if coin_price > 0 else 100
    coins_needed = max(0, coin_price - coins_balance)

    return {
        "pinned": True,
        "product": product,
        "progress": progress,
        "coins_needed": coins_needed,
        "coins_balance": coins_balance,
        "pinned_at": doc["pinned_at"],
    }

# ════════════════════════════════════════════════════════════════════════════
# FEATURE 2 — Streak / Hot Hand: expose current streak via stats
# ════════════════════════════════════════════════════════════════════════════

@v2_router.get("/predictions/streak")
async def get_prediction_streak(user: User = Depends(get_current_user)):
    """Return the user's current consecutive correct prediction streak and multiplier."""
    u_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "prediction_streak": 1})
    streak = (u_doc or {}).get("prediction_streak", 0)
    if streak >= 7:
        multiplier = 4
    elif streak >= 5:
        multiplier = 3
    elif streak >= 3:
        multiplier = 2
    else:
        multiplier = 1
    return {"streak": streak, "multiplier": multiplier, "hot_hand": streak >= 3}



# ════════════════════════════════════════════════════════════════════════════
# FEATURE 3 — Live Crowd Meter
# ════════════════════════════════════════════════════════════════════════════

@v2_router.get("/crowd-meter/{match_id}")
async def get_crowd_meter(match_id: str):
    """Anonymously aggregate prediction distribution for a match."""
    return await crowd_meter.get_meter(match_id)


# ════════════════════════════════════════════════════════════════════════════
# FEATURE 4 — Daily Cricket Puzzle
# ════════════════════════════════════════════════════════════════════════════

class PuzzleAnswerReq(BaseModel):
    answer: str

@v2_router.get("/puzzle/today")
async def get_today_puzzle(user: User = Depends(get_current_user)):
    """Get today's puzzle. Includes `already_answered` flag."""
    puzzle = await puzzle_engine.get_today()
    if not puzzle:
        raise HTTPException(404, "No puzzle available today")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    completion = await db.puzzle_completions.find_one(
        {"user_id": user.id, "puzzle_date": today}, {"_id": 0}
    )
    return {
        **puzzle,
        "already_answered": completion is not None,
        "previous_answer": completion.get("answer") if completion else None,
        "previous_result": {
            "is_correct": completion.get("is_correct"),
            "coins_earned": completion.get("coins_earned"),
            "correct_answer": completion.get("correct_answer"),
            "explanation": completion.get("explanation"),
        } if completion else None,
        "first_100_reward": 25,
        "late_reward": 5,
    }

@v2_router.post("/puzzle/answer")
async def answer_puzzle(req: PuzzleAnswerReq, user: User = Depends(get_current_user)):
    """Submit an answer for today's puzzle. Idempotent."""
    return await puzzle_engine.submit_answer(user.id, req.answer, ledger)


@v2_router.post("/earn/teen-patti-win")
async def teen_patti_win(user: User = Depends(get_current_user)):
    """Award 40 coins for winning Teen Patti vs AI. Once per day."""
    from datetime import date as _date
    today = str(_date.today())
    key = f"teen_patti_win_{user.id}_{today}"

    already = await db.coin_transactions.find_one({"reference_id": key}, {"_id": 0})
    if already:
        raise HTTPException(400, "Teen Patti win coins already claimed today. Come back tomorrow!")

    coins = 40
    await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": coins}})
    await db.coin_transactions.insert_one({
        "user_id": user.id,
        "amount": coins,
        "type": "teen_patti_win",
        "description": "Teen Patti game win vs AI",
        "reference_id": key,
        "created_at": today,
    })
    updated = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
    return {"success": True, "coins_earned": coins, "new_balance": updated.get("coins_balance", 0)}


@v2_router.post("/earn/solitaire-win")
async def solitaire_win(user: User = Depends(get_current_user)):
    """Award 25 coins for winning Solitaire. Once per day."""
    from datetime import date as _date
    today = str(_date.today())
    key = f"solitaire_win_{user.id}_{today}"

    already = await db.coin_transactions.find_one({"reference_id": key}, {"_id": 0})
    if already:
        raise HTTPException(400, "Solitaire win coins already claimed today. Come back tomorrow!")

    coins = 25
    await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": coins}})
    await db.coin_transactions.insert_one({
        "user_id": user.id,
        "amount": coins,
        "type": "solitaire_win",
        "description": "Solitaire game win",
        "reference_id": key,
        "created_at": today,
    })
    updated = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
    return {"success": True, "coins_earned": coins, "new_balance": updated.get("coins_balance", 0)}


@v2_router.post("/earn/rummy-win")
async def rummy_win(user: User = Depends(get_current_user)):
    """Award 50 coins for winning Rummy vs AI. Once per day."""
    from datetime import date as _date
    today = str(_date.today())
    key = f"rummy_win_{user.id}_{today}"
    if await db.coin_transactions.find_one({"reference_id": key}, {"_id": 0}):
        raise HTTPException(400, "Rummy win coins already claimed today. Come back tomorrow!")
    coins = 50
    await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": coins}})
    await db.coin_transactions.insert_one({
        "user_id": user.id, "amount": coins, "type": "rummy_win",
        "description": "Rummy game win vs AI", "reference_id": key, "created_at": today,
    })
    updated = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
    return {"success": True, "coins_earned": coins, "new_balance": updated.get("coins_balance", 0)}


@v2_router.post("/earn/poker-win")
async def poker_win(user: User = Depends(get_current_user)):
    """Award 60 coins for winning Poker vs AI. Once per day."""
    from datetime import date as _date
    today = str(_date.today())
    key = f"poker_win_{user.id}_{today}"
    if await db.coin_transactions.find_one({"reference_id": key}, {"_id": 0}):
        raise HTTPException(400, "Poker win coins already claimed today. Come back tomorrow!")
    coins = 60
    await db.users.update_one({"id": user.id}, {"$inc": {"coins_balance": coins}})
    await db.coin_transactions.insert_one({
        "user_id": user.id, "amount": coins, "type": "poker_win",
        "description": "Poker game win vs AI", "reference_id": key, "created_at": today,
    })
    updated = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
    return {"success": True, "coins_earned": coins, "new_balance": updated.get("coins_balance", 0)}


@v2_router.get("/games/card-leaderboard")
async def card_game_leaderboard():
    """Top 10 card game coin earners this week."""
    from datetime import date as _date, timedelta
    week_ago = str(_date.today() - timedelta(days=7))
    pipeline = [
        {"$match": {
            "type": {"$in": ["teen_patti_win", "solitaire_win", "rummy_win", "poker_win"]},
            "created_at": {"$gte": week_ago},
        }},
        {"$group": {"_id": "$user_id", "total_coins": {"$sum": "$amount"}, "wins": {"$sum": 1}}},
        {"$sort": {"total_coins": -1}},
        {"$limit": 10},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "id", "as": "u"}},
        {"$project": {"_id": 0, "user_id": "$_id", "total_coins": 1, "wins": 1, "name": {"$arrayElemAt": ["$u.name", 0]}}},
    ]
    results = await db.coin_transactions.aggregate(pipeline).to_list(10)
    return {"leaderboard": results}


@v2_router.get("/games/card-streak")
async def get_card_streak(user: User = Depends(get_current_user)):
    """Get user's consecutive card game playing streak."""
    from datetime import date as _date, timedelta
    today = _date.today()
    CARD_GAME_TYPES = ["teen_patti_win", "solitaire_win", "rummy_win", "poker_win"]
    streak = 0
    check_date = today
    while streak < 30:
        played = await db.coin_transactions.find_one({
            "user_id": user.id, "type": {"$in": CARD_GAME_TYPES}, "created_at": str(check_date)
        }, {"_id": 0})
        if not played:
            break
        streak += 1
        check_date -= timedelta(days=1)
    played_today = await db.coin_transactions.find_one({
        "user_id": user.id, "type": {"$in": CARD_GAME_TYPES}, "created_at": str(today)
    }, {"_id": 0})
    return {"streak": streak, "played_today": bool(played_today)}


# ════════════════════════════════════════════════════════════════════════════
# FEATURE 5 — Weekly Report Card
# ════════════════════════════════════════════════════════════════════════════

@v2_router.get("/report-card/weekly")
async def get_weekly_report(user: User = Depends(get_current_user)):
    """Get (or generate) the current week's report card for the user."""
    report = await report_engine.get_latest(user.id)
    is_new = not report.get("viewed", False)
    return {**report, "is_new": is_new}

@v2_router.post("/report-card/dismiss")
async def dismiss_weekly_report(user: User = Depends(get_current_user)):
    """Mark the current week's report card as viewed."""
    await report_engine.mark_viewed(user.id)
    return {"dismissed": True}


# ════════════════════════════════════════════════════════════════════════════
# FEATURE 6 — Rebound Quest Engine
# ════════════════════════════════════════════════════════════════════════════

from quest_engine import QuestEngine

_quest_engine = QuestEngine(db)


class QuestDismissReq(BaseModel):
    quest_id: str


@v2_router.get("/quest/status")
async def quest_status(user: User = Depends(get_current_user)):
    """Check if a rebound quest should be offered to this user."""
    return await _quest_engine.check_eligibility(user.id)


@v2_router.post("/quest/offer")
async def offer_quest(user: User = Depends(get_current_user)):
    """Create (or return existing) quest session for today."""
    eligibility = await _quest_engine.check_eligibility(user.id)
    session = await _quest_engine.offer_quest(user.id)
    return {**session, "streak": eligibility.get("streak", 0)}


@v2_router.post("/quest/claim-ad")
async def quest_claim_ad(req: QuestDismissReq, user: User = Depends(get_current_user)):
    """Path A: Watch ad → +20 coins."""
    try:
        return await _quest_engine.claim_ad_reward(user.id, req.quest_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@v2_router.post("/quest/ration-viewed")
async def quest_ration_viewed(req: QuestDismissReq, user: User = Depends(get_current_user)):
    """Path B: User clicked to see ration tease — mark as engaged."""
    return await _quest_engine.mark_ration_viewed(user.id, req.quest_id)


@v2_router.post("/quest/dismiss")
async def quest_dismiss(req: QuestDismissReq, user: User = Depends(get_current_user)):
    """User dismissed quest modal."""
    return await _quest_engine.dismiss_quest(user.id, req.quest_id)


@v2_router.get("/quest/history")
async def quest_history(user: User = Depends(get_current_user)):
    return await _quest_engine.get_history(user.id)


# ════════════════════════════════════════════════════════════════════════════
# FEATURE 7 — Smart Commerce Router v2
# Providers: ONDC (groceries), Xoxoday (vouchers), Amazon, Flipkart (affiliates)
# ════════════════════════════════════════════════════════════════════════════

from router_service import (
    get_router_tease, settle_router_order, get_aggregated_skus,
    get_ration_categories, get_dynamic_coin_price, get_demand_factor,
)

ROUTER_SETTLE_LIMIT = 5  # max 5 settle requests per user per minute (Redis-based)


class RouterSettleReq(BaseModel):
    sku: str
    coins_used: int = 0
    geo_state: str = "MH"


@v2_router.get("/router/skus")
async def router_sku_catalog():
    """
    Return aggregated SKU catalog from all providers.
    Includes coin_price, real_price, category, provider, ETA hint.
    """
    from router_service import get_aggregated_skus, get_demand_factor, get_dynamic_coin_price
    skus = get_aggregated_skus()
    for item in skus:
        try:
            demand = await get_demand_factor(item["sku"], db)
        except Exception:
            demand = 1.0
        item["demand_factor"] = round(demand, 2)
        item["dynamic_coin_price"] = get_dynamic_coin_price(item.get("coins", 100), demand)
    return skus


@v2_router.get("/router/tease")
async def router_tease(sku: str = "cola_2l", geo_state: str = "MH"):
    """
    Score all providers for a SKU × geo_state.
    Returns ranked options with best provider highlighted.
    Redis-cached 600 s.
    """
    return await get_router_tease(sku, geo_state)


@v2_router.post("/router/settle")
async def router_settle(req: RouterSettleReq, user: User = Depends(get_current_user)):
    """
    Auto-select best provider, debit coins, execute redemption, log order.
    Rate-limited: 5 per user per minute.
    Returns: voucher_code | redirect_url | order_id depending on provider type.
    """
    from redis_cache import get_redis
    from router_service import get_best_provider

    # ── Per-user rate limit (5 settles/min) ──────────────────────────────
    r = get_redis()
    if r:
        import time
        rl_key = f"rl:router_settle:{user.id}:{int(time.time() // 60)}"
        count = r.incr(rl_key)
        if count == 1:
            r.expire(rl_key, 60)
        if count > ROUTER_SETTLE_LIMIT:
            raise HTTPException(status_code=429, detail="Too many redemptions — try again in a minute.")

    # ── Validate SKU & provider ──────────────────────────────────────────
    best = get_best_provider(req.sku, req.geo_state)
    if not best:
        raise HTTPException(status_code=404, detail=f"SKU '{req.sku}' not available from any provider.")

    provider, _ = best
    authoritative_price = provider.get_price(req.sku)

    if authoritative_price <= 0:
        raise HTTPException(status_code=400, detail="Invalid coin price for SKU.")

    # ── Atomic coin deduction (uses cached coins_balance — source of truth) ──
    from motor.motor_asyncio import AsyncIOMotorCollection
    updated = await db.users.find_one_and_update(
        {"id": user.id, "coins_balance": {"$gte": authoritative_price}},
        {"$inc": {"coins_balance": -authoritative_price, "total_redeemed": authoritative_price}},
        return_document=True,
        projection={"_id": 0, "coins_balance": 1},
    )
    if not updated:
        # Either not found or insufficient balance
        doc = await db.users.find_one({"id": user.id}, {"_id": 0, "coins_balance": 1})
        have = doc.get("coins_balance", 0) if doc else 0
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient coins. Need {authoritative_price}, have {have}.",
        )
    new_balance = updated["coins_balance"]

    # Ledger audit entry (non-blocking — ignore failure)
    try:
        import uuid as _uuid
        from datetime import datetime as _dt, timezone as _tz
        await db.ledger.insert_one({
            "id": str(_uuid.uuid4()),
            "user_id": user.id,
            "type": "router_redemption",
            "reference_id": req.sku,
            "credit": 0,
            "debit": authoritative_price,
            "description": f"Smart Router: {req.sku} via {provider.name}",
            "status": "completed",
            "timestamp": _dt.now(_tz.utc).isoformat(),
        })
    except Exception:
        pass

    # ── Execute & log ────────────────────────────────────────────────────
    result = await settle_router_order(
        user_id=user.id,
        sku=req.sku,
        coins_used=authoritative_price,
        geo_state=req.geo_state,
        db=db,
        user_email=getattr(user, "email", ""),
    )

    result["new_balance"] = new_balance
    return result
