"""
FREE11 Admin V2 Routes
Full admin control: kill match, void contests/predictions, freeze wallet, feature flags, test mode
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, timezone
import uuid

from server import db, get_current_user, User

from ledger_engine import LedgerEngine
from contest_engine import ContestEngine
from predict_engine import PredictEngine
from matchstate_engine import MatchStateEngine
from services.voucher_provider import MockVoucherProvider
from entitysport_service import EntitySportService
from fantasy_engine import FantasyEngine

ledger = LedgerEngine(db)
contest_engine = ContestEngine(db)
predict_engine = PredictEngine(db)
matchstate_engine = MatchStateEngine(db)
voucher_provider = MockVoucherProvider(db)
entitysport_svc = EntitySportService(db)
fantasy_engine = FantasyEngine(db)

admin_v2_router = APIRouter(prefix="/admin/v2", tags=["Admin V2"])


async def require_admin(user: User):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")


# ── Request Models ──

class KillMatchReq(BaseModel):
    match_id: str
    reason: str = "admin_kill"

class VoidContestReq(BaseModel):
    contest_id: str
    reason: str

class VoidPredictionsReq(BaseModel):
    match_id: str
    reason: str

class FreezeWalletReq(BaseModel):
    user_id: str
    reason: str

class AdjustCoinsReq(BaseModel):
    user_id: str
    amount: int
    reason: str

class VoucherActionReq(BaseModel):
    voucher_id: str

class FeatureFlagReq(BaseModel):
    flag: str
    enabled: bool

class ResolveOverReq(BaseModel):
    match_id: str
    over_number: int
    runs: int
    wickets: int = 0
    boundaries: int = 0

class AdvanceTestMatchReq(BaseModel):
    match_id: str
    runs: Optional[int] = None
    wicket: bool = False


# ── Match Controls ──

@admin_v2_router.post("/match/kill")
async def kill_match(req: KillMatchReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    now = datetime.now(timezone.utc).isoformat()

    await db.matches.update_one(
        {"match_id": req.match_id},
        {"$set": {"status": "abandoned", "updated_at": now}}
    )
    # Void all pending predictions
    voided = await predict_engine.void_predictions(req.match_id, req.reason)
    # Lock all contests
    locked = await contest_engine.lock_all_for_match(req.match_id)
    matchstate_engine.stop_polling(req.match_id)

    await _log_admin_action(user.id, "kill_match", {"match_id": req.match_id, "reason": req.reason, "voided": voided, "locked": locked})
    return {"killed": True, "predictions_voided": voided, "contests_locked": locked}

@admin_v2_router.post("/match/freeze")
async def freeze_match(req: KillMatchReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await matchstate_engine.freeze_match(req.match_id, req.reason)
    await _log_admin_action(user.id, "freeze_match", {"match_id": req.match_id, "reason": req.reason})
    return {"frozen": True}

@admin_v2_router.post("/match/unfreeze")
async def unfreeze_match(req: KillMatchReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await matchstate_engine.unfreeze_match(req.match_id)
    return {"unfrozen": True}

# ── Test Match Mode ──

@admin_v2_router.post("/match/test/create")
async def create_test_match(user: User = Depends(get_current_user)):
    await require_admin(user)
    match = await matchstate_engine.create_test_match()
    await _log_admin_action(user.id, "create_test_match", {"match_id": match["match_id"]})
    return match

@admin_v2_router.post("/match/test/advance")
async def advance_test_match(req: AdvanceTestMatchReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    result = await matchstate_engine.advance_test_match(req.match_id, req.runs, req.wicket)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# ── Contest Controls ──

@admin_v2_router.post("/contest/void")
async def void_contest(req: VoidContestReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    result = await contest_engine.void_contest(req.contest_id, req.reason)
    await _log_admin_action(user.id, "void_contest", {"contest_id": req.contest_id, "reason": req.reason})
    return result

# ── Prediction Controls ──

@admin_v2_router.post("/predictions/void")
async def void_predictions(req: VoidPredictionsReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    count = await predict_engine.void_predictions(req.match_id, req.reason)
    await _log_admin_action(user.id, "void_predictions", {"match_id": req.match_id, "reason": req.reason, "count": count})
    return {"voided": count}

def _streak_multiplier(streak: int) -> int:
    """Feature 2: Hot Hand streak multiplier. Affects coin rewards ONLY, not contest points."""
    if streak >= 7: return 4
    if streak >= 5: return 3
    if streak >= 3: return 2
    return 1

@admin_v2_router.post("/predictions/resolve-over")
async def resolve_over(req: ResolveOverReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    results = await predict_engine.resolve_over(
        req.match_id, req.over_number,
        {"runs": req.runs, "wickets": req.wickets, "boundaries": req.boundaries}
    )

    # Feature 2: Streak Multiplier — real-time per prediction, coins only
    total_correct = 0
    for r in results:
        if r["is_correct"] and r["coins_earned"] > 0:
            # Fetch current streak before incrementing
            u_doc = await db.users.find_one({"id": r["user_id"]}, {"_id": 0, "prediction_streak": 1})
            current_streak = (u_doc or {}).get("prediction_streak", 0)
            multiplier = _streak_multiplier(current_streak)
            final_coins = r["coins_earned"] * multiplier

            # Increment streak atomically
            await db.users.update_one({"id": r["user_id"]}, {"$inc": {"prediction_streak": 1}})

            streak_note = f" (Hot Hand {multiplier}x!)" if multiplier > 1 else ""
            await ledger.credit(
                r["user_id"], final_coins,
                "prediction_reward", r["prediction_id"],
                f"Correct prediction! Over {req.over_number}{streak_note}"
            )
            r["multiplier"] = multiplier
            r["final_coins"] = final_coins
            total_correct += 1
        elif not r["is_correct"]:
            # Reset streak on incorrect prediction
            await db.users.update_one({"id": r["user_id"]}, {"$set": {"prediction_streak": 0}})
            r["multiplier"] = 1
            r["final_coins"] = 0

    await _log_admin_action(user.id, "resolve_over", {
        "match_id": req.match_id, "over": req.over_number,
        "total": len(results), "correct": total_correct,
    })
    return {"resolved": len(results), "results": results}

# ── Wallet Controls ──

@admin_v2_router.post("/wallet/freeze")
async def freeze_wallet(req: FreezeWalletReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await db.users.update_one(
        {"id": req.user_id},
        {"$set": {"wallet_frozen": True, "wallet_freeze_reason": req.reason}}
    )
    await _log_admin_action(user.id, "freeze_wallet", {"target_user": req.user_id, "reason": req.reason})
    return {"frozen": True}

@admin_v2_router.post("/wallet/unfreeze")
async def unfreeze_wallet(req: FreezeWalletReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await db.users.update_one(
        {"id": req.user_id},
        {"$set": {"wallet_frozen": False, "wallet_freeze_reason": None}}
    )
    return {"unfrozen": True}

@admin_v2_router.post("/wallet/adjust")
async def adjust_coins(req: AdjustCoinsReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    if req.amount > 0:
        await ledger.credit(req.user_id, req.amount, "admin_adjust", user.id, f"Admin adjustment: {req.reason}")
    elif req.amount < 0:
        await ledger.debit(req.user_id, abs(req.amount), "admin_adjust", user.id, f"Admin adjustment: {req.reason}")
    else:
        raise HTTPException(status_code=400, detail="Amount cannot be zero")
    await _log_admin_action(user.id, "adjust_coins", {"target_user": req.user_id, "amount": req.amount, "reason": req.reason})
    return {"adjusted": True, "amount": req.amount}

# ── Voucher Controls ──

@admin_v2_router.post("/voucher/force-complete")
async def force_complete_voucher(req: VoucherActionReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    result = await voucher_provider.force_complete(req.voucher_id)
    await _log_admin_action(user.id, "force_complete_voucher", {"voucher_id": req.voucher_id})
    return result

@admin_v2_router.post("/voucher/force-fail")
async def force_fail_voucher(req: VoucherActionReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    result = await voucher_provider.force_fail(req.voucher_id)
    await _log_admin_action(user.id, "force_fail_voucher", {"voucher_id": req.voucher_id})
    return result

# ── Feature Flags ──

@admin_v2_router.post("/feature-flag")
async def set_feature_flag(req: FeatureFlagReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await db.feature_flags.update_one(
        {"flag": req.flag},
        {"$set": {"flag": req.flag, "enabled": req.enabled, "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    await _log_admin_action(user.id, "feature_flag", {"flag": req.flag, "enabled": req.enabled})
    return {"flag": req.flag, "enabled": req.enabled}

@admin_v2_router.get("/feature-flags")
async def get_feature_flags(user: User = Depends(get_current_user)):
    await require_admin(user)
    flags = await db.feature_flags.find({}, {"_id": 0}).to_list(100)
    return flags

# ── Toggle Test Mode ──

@admin_v2_router.post("/toggle-test-mode")
async def toggle_test_mode(user: User = Depends(get_current_user)):
    await require_admin(user)
    current = await db.feature_flags.find_one({"flag": "test_mode"}, {"_id": 0})
    new_val = not (current.get("enabled", False) if current else False)
    await db.feature_flags.update_one(
        {"flag": "test_mode"},
        {"$set": {"flag": "test_mode", "enabled": new_val, "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"test_mode": new_val}

# ── Ledger Reconciliation ──

@admin_v2_router.post("/ledger/reconcile-all")
async def reconcile_all_ledgers(user: User = Depends(get_current_user)):
    await require_admin(user)
    mismatches = await ledger.reconcile_all()
    await _log_admin_action(user.id, "ledger_reconcile_all", {"mismatches": len(mismatches)})
    return {"mismatches": mismatches, "count": len(mismatches)}

# ── Admin Action Log ──

@admin_v2_router.get("/action-log")
async def get_admin_action_log(limit: int = 50, user: User = Depends(get_current_user)):
    await require_admin(user)
    logs = await db.admin_action_log.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return logs

# ── Observability ──

@admin_v2_router.get("/logs/predictions")
async def get_prediction_logs(match_id: Optional[str] = None, limit: int = 100, user: User = Depends(get_current_user)):
    await require_admin(user)
    query = {}
    if match_id:
        query["match_id"] = match_id
    logs = await db.prediction_audit_log.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return logs

@admin_v2_router.get("/logs/ledger")
async def get_ledger_logs(user_id: Optional[str] = None, limit: int = 100, user: User = Depends(get_current_user)):
    await require_admin(user)
    query = {}
    if user_id:
        query["user_id"] = user_id
    logs = await db.ledger.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return logs

# ── Fantasy Scoring ──

class ScoreFantasyReq(BaseModel):
    match_id: str

@admin_v2_router.post("/fantasy/score")
async def score_fantasy_match(req: ScoreFantasyReq, user: User = Depends(get_current_user)):
    """Calculate fantasy points from real EntitySport scorecard"""
    await require_admin(user)
    scorecard = await entitysport_svc.get_match_scorecard(req.match_id)
    if not scorecard:
        raise HTTPException(status_code=404, detail="Scorecard not available")
    results = await fantasy_engine.calculate_points(req.match_id, scorecard)
    await _log_admin_action(user.id, "score_fantasy", {"match_id": req.match_id, "teams_scored": len(results)})
    return {"scored": len(results), "results": results}

@admin_v2_router.post("/fantasy/lock-teams")
async def lock_fantasy_teams(req: ScoreFantasyReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    count = await fantasy_engine.lock_teams_for_match(req.match_id)
    return {"locked": count}

# ── EntitySport Sync ──

@admin_v2_router.post("/es/sync")
async def admin_sync_matches(user: User = Depends(get_current_user)):
    await require_admin(user)
    count = await entitysport_svc.sync_matches(statuses=("1", "2", "3"))
    await _log_admin_action(user.id, "es_sync", {"matches_synced": count})
    return {"synced": count}



async def _log_admin_action(admin_id: str, action: str, details: Dict):
    await db.admin_action_log.insert_one({
        "id": str(uuid.uuid4()),
        "admin_id": admin_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ══════════════════════ FRAUD & ABUSE ADMIN ══════════════════════

from fraud_engine import FraudEngine
from freebucks_engine import FreeBucksEngine
from notification_engine import NotificationEngine

_fraud = FraudEngine(db)
_fb_admin = FreeBucksEngine(db)
_notif_admin = NotificationEngine(db)


class FlagUserReq(BaseModel):
    user_id: str
    reason: str


class BanUserReq(BaseModel):
    user_id: str
    reason: str


class FreeBucksAdjustReq(BaseModel):
    user_id: str
    amount: int
    reason: str


@admin_v2_router.get("/fraud/flagged")
async def get_flagged_users(user: User = Depends(get_current_user)):
    await require_admin(user)
    return await _fraud.get_flagged_users()


@admin_v2_router.post("/fraud/flag")
async def flag_user(req: FlagUserReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await _fraud.flag_user(req.user_id, req.reason, user.id)
    await _log_admin_action(user.id, "fraud_flag", {"target": req.user_id, "reason": req.reason})
    return {"ok": True}


@admin_v2_router.post("/fraud/ban")
async def ban_user(req: BanUserReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await _fraud.ban_user(req.user_id, req.reason, user.id)
    await _log_admin_action(user.id, "ban_user", {"target": req.user_id, "reason": req.reason})
    return {"ok": True}


@admin_v2_router.post("/fraud/unban")
async def unban_user(req: FlagUserReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await _fraud.unban_user(req.user_id)
    await _log_admin_action(user.id, "unban_user", {"target": req.user_id})
    return {"ok": True}


@admin_v2_router.post("/fraud/check-duplicates")
async def check_duplicates(req: FlagUserReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    target = await db.users.find_one({"id": req.user_id}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    devices = target.get("known_devices", [])
    ips = target.get("known_ips", [])
    suspects = []
    for dh in devices:
        suspects.extend(await _fraud.check_duplicate_account(dh, "", req.user_id))
    for ip in ips:
        s = await _fraud.check_duplicate_account("", ip, req.user_id)
        for item in s:
            if not any(x["user_id"] == item["user_id"] for x in suspects):
                suspects.append(item)
    return {"user_id": req.user_id, "suspects": suspects}


@admin_v2_router.post("/freebucks/adjust")
async def admin_freebucks_adjust(req: FreeBucksAdjustReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    result = await _fb_admin.admin_adjust(req.user_id, req.amount, req.reason, user.id)
    await _log_admin_action(user.id, "freebucks_adjust", {"target": req.user_id, "amount": req.amount, "reason": req.reason})
    return result


@admin_v2_router.post("/freebucks/freeze")
async def admin_freebucks_freeze(req: FlagUserReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await _fb_admin.freeze(req.user_id)
    await _log_admin_action(user.id, "freebucks_freeze", {"target": req.user_id})
    return {"ok": True}


@admin_v2_router.post("/freebucks/unfreeze")
async def admin_freebucks_unfreeze(req: FlagUserReq, user: User = Depends(get_current_user)):
    await require_admin(user)
    await _fb_admin.unfreeze(req.user_id)
    await _log_admin_action(user.id, "freebucks_unfreeze", {"target": req.user_id})
    return {"ok": True}


@admin_v2_router.post("/notifications/send")
async def admin_send_notification(user: User = Depends(get_current_user)):
    """Send notification to all users - placeholder for bulk ops"""
    await require_admin(user)
    return {"ok": True, "note": "Use specific trigger endpoints for targeted notifications"}
