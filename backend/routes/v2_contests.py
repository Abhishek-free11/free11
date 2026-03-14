"""
routes/v2_contests.py — Contest & Prediction routes for FREE11 V2
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict

from server import db, get_current_user, User
from v2_engines import contests, predictions, referrals, ledger

router = APIRouter()

MAX_PREDICTIONS_PER_MATCH = 10

# ── Request Models ────────────────────────────────────────────────────────────

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

# ── Contest Routes ────────────────────────────────────────────────────────────

@router.post("/contests/create")
async def create_contest(req: CreateContestReq, user: User = Depends(get_current_user)):
    try:
        return await contests.create_contest(
            match_id=req.match_id, creator_id=user.id, name=req.name,
            contest_type=req.contest_type, max_participants=req.max_participants,
            entry_fee=req.entry_fee,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/contests/join")
async def join_contest(req: JoinContestReq, user: User = Depends(get_current_user)):
    try:
        contest = await contests.get_contest(req.contest_id)
        if not contest:
            raise HTTPException(404, "Contest not found")
        if contest.get("entry_fee", 0) > 0:
            await ledger.debit(user.id, contest["entry_fee"], "contest_entry",
                               req.contest_id, f"Contest entry: {contest['name']}")
        result = await contests.join_contest(req.contest_id, user.id, req.team)
        try:
            await referrals.check_and_complete_referral(user.id)
        except Exception:
            pass
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/contests/join-code")
async def join_by_invite_code(req: JoinByCodeReq, user: User = Depends(get_current_user)):
    try:
        return await contests.join_by_invite_code(req.invite_code, user.id, req.team)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/contests/match/{match_id}")
async def get_match_contests(match_id: str, contest_type: Optional[str] = None):
    return await contests.get_contests_for_match(match_id, contest_type)


@router.get("/contests/user/my")
async def get_my_contests(user: User = Depends(get_current_user)):
    return await contests.get_user_contests(user.id)


@router.post("/contests/seed/{match_id}")
async def seed_match_contests(match_id: str, user: User = Depends(get_current_user)):
    match = await db.matches.find_one({"match_id": match_id}, {"_id": 0, "series": 1})
    series = match.get("series", "") if match else ""
    created = await contests.seed_platform_contests(match_id, series)
    return {"seeded": len(created), "contests": created}


@router.post("/contests/{contest_id}/finalize")
async def finalize_contest(contest_id: str, user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    try:
        return await contests.finalize_contest(contest_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/contests/{contest_id}/leaderboard")
async def get_contest_leaderboard(contest_id: str):
    return await contests.get_leaderboard(contest_id)


@router.get("/contests/{contest_id}")
async def get_contest_detail(contest_id: str):
    contest = await contests.get_contest(contest_id)
    if not contest:
        raise HTTPException(404, "Contest not found")
    return contest


# ── Admin: finalize all contests for a match ─────────────────────────────────

@router.post("/admin/finalize-match/{match_id}")
async def admin_finalize_match(match_id: str, user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin only")
    open_contests = await db.contests.find(
        {"match_id": match_id, "finalized": {"$ne": True}}, {"_id": 0, "id": 1, "name": 1}
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


# ── Prediction Routes ─────────────────────────────────────────────────────────

@router.post("/predictions/submit")
async def submit_prediction(req: SubmitPredictionReq, user: User = Depends(get_current_user)):
    count = await db.predictions_v2.count_documents({"user_id": user.id, "match_id": req.match_id})
    if count >= MAX_PREDICTIONS_PER_MATCH:
        raise HTTPException(429, f"Maximum {MAX_PREDICTIONS_PER_MATCH} predictions per match reached")
    try:
        prediction = await predictions.submit_prediction(
            user_id=user.id, match_id=req.match_id,
            prediction_type=req.prediction_type, prediction_value=req.prediction_value,
            over_number=req.over_number,
        )
        try:
            await referrals.check_and_complete_referral(user.id)
        except Exception:
            pass
        return prediction
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/predictions/my")
async def get_my_predictions(match_id: Optional[str] = None, user: User = Depends(get_current_user)):
    return await predictions.get_user_predictions(user.id, match_id)


@router.get("/predictions/stats")
async def get_prediction_stats(user: User = Depends(get_current_user)):
    return await predictions.get_prediction_stats(user.id)


@router.get("/predictions/types")
async def get_prediction_types():
    return {"types": ["toss", "first_wicket", "over_runs", "match_winner"]}


@router.get("/predictions/match/{match_id}/count")
async def get_user_prediction_count(match_id: str, user: User = Depends(get_current_user)):
    count = await db.predictions_v2.count_documents({"user_id": user.id, "match_id": match_id})
    return {"count": count, "limit": MAX_PREDICTIONS_PER_MATCH, "remaining": max(0, MAX_PREDICTIONS_PER_MATCH - count)}


@router.get("/predictions/streak")
async def get_prediction_streak(user: User = Depends(get_current_user)):
    u_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "prediction_streak": 1})
    streak = (u_doc or {}).get("prediction_streak", 0)
    if streak >= 7:   multiplier = 4
    elif streak >= 5: multiplier = 3
    elif streak >= 3: multiplier = 2
    else:             multiplier = 1
    return {"streak": streak, "multiplier": multiplier, "hot_hand": streak >= 3}
