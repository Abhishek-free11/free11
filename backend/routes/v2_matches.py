"""
routes/v2_matches.py — Match, EntitySport, Fantasy, Crowd Meter, Puzzle, Report Card routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone

from server import db, get_current_user, User
from v2_engines import matchstate, entitysport, fantasy, crowd_meter, puzzle_engine, report_engine, contests

router = APIRouter()

# ── Request Models ─────────────────────────────────────────────────────────────

class CreateFantasyTeamReq(BaseModel):
    match_id: str
    players: List[Dict]
    captain_id: str
    vc_id: str

class CompareTeamsReq(BaseModel):
    team_id_1: str
    team_id_2: str

class PuzzleAnswerReq(BaseModel):
    answer: str

# ── Match State & Listings ─────────────────────────────────────────────────────

@router.get("/match/{match_id}/state")
async def get_match_state(match_id: str):
    snapshot = await matchstate.get_latest_snapshot(match_id)
    match = await db.matches.find_one({"match_id": match_id}, {"_id": 0})
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
    return {"match": match, "snapshot": snapshot, "frozen": matchstate.is_frozen(match_id)}


@router.get("/matches/live")
async def get_live_matches():
    return await db.matches.find(
        {"status": {"$in": ["live", "upcoming"]}}, {"_id": 0}
    ).sort("match_date", 1).to_list(50)


@router.get("/matches/all")
async def get_all_matches(status: Optional[str] = None, limit: int = Query(20, le=100)):
    query = {}
    if status:
        query["status"] = status
    return await db.matches.find(query, {"_id": 0}).sort("match_date", -1).limit(limit).to_list(limit)


# ── EntitySport Live Data ──────────────────────────────────────────────────────

@router.get("/es/matches")
async def es_get_matches(status: str = "3", per_page: int = Query(20, le=50)):
    return await entitysport.get_matches(status=status, per_page=per_page)

@router.get("/es/match/{match_id}/info")
async def es_get_match_info(match_id: str):
    data = await entitysport.get_match_info(match_id)
    if not data:
        raise HTTPException(404, "Match not found")
    return data

@router.get("/es/match/{match_id}/live")
async def es_get_match_live(match_id: str):
    data = await entitysport.get_match_live(match_id)
    if not data:
        raise HTTPException(404, "No live data")
    return data

@router.get("/es/match/{match_id}/scorecard")
async def es_get_scorecard(match_id: str):
    data = await entitysport.get_match_scorecard(match_id)
    if not data:
        raise HTTPException(404, "No scorecard")
    return data

@router.get("/es/match/{match_id}/squads")
async def es_get_squads(match_id: str):
    data = await entitysport.get_match_squads(match_id)
    if not data:
        raise HTTPException(404, "No squad data")
    return data

@router.post("/es/sync")
async def es_sync_matches(user: User = Depends(get_current_user)):
    count = await entitysport.sync_matches()
    matches_list = await db.matches.find(
        {"status": {"$in": ["live", "upcoming"]}}, {"_id": 0, "match_id": 1, "series": 1}
    ).to_list(50)
    seeded_total = 0
    for m in matches_list:
        created = await contests.seed_platform_contests(m["match_id"], m.get("series", ""))
        seeded_total += len(created)
    return {"synced": count, "contests_seeded": seeded_total}

@router.get("/es/competitions")
async def es_get_competitions():
    return await entitysport.get_competitions()

# ── Fantasy Team Routes ────────────────────────────────────────────────────────

@router.post("/fantasy/create-team")
async def create_fantasy_team(req: CreateFantasyTeamReq, user: User = Depends(get_current_user)):
    try:
        return await fantasy.create_team(
            user_id=user.id, match_id=req.match_id,
            players=req.players, captain_id=req.captain_id, vc_id=req.vc_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/fantasy/my-teams")
async def get_my_fantasy_teams(user: User = Depends(get_current_user)):
    return await fantasy.get_user_teams(user.id)

@router.get("/fantasy/team/{team_id}")
async def get_fantasy_team(team_id: str, user: User = Depends(get_current_user)):
    team = await fantasy.get_team(team_id, user.id)
    if not team:
        raise HTTPException(404, "Team not found")
    return team

@router.get("/fantasy/rankings/{match_id}")
async def get_fantasy_rankings(match_id: str):
    return await fantasy.get_rankings(match_id)

@router.post("/fantasy/compare")
async def compare_fantasy_teams(req: CompareTeamsReq, user: User = Depends(get_current_user)):
    return await fantasy.compare_teams(req.team_id_1, req.team_id_2)

@router.get("/fantasy/points-system")
async def get_fantasy_points():
    return {
        "batting": {"run": 1, "boundary_bonus": 1, "six_bonus": 2, "fifty_bonus": 8, "century_bonus": 16},
        "bowling": {"wicket": 25, "maiden_over": 8, "lbw_bowled_bonus": 8},
        "fielding": {"catch": 8, "stumping": 12, "runout": 6},
        "captain_multiplier": 2.0, "vc_multiplier": 1.5,
    }

# ── Crowd Meter ─────────────────────────────────────────────────────────────────

@router.get("/crowd-meter/{match_id}")
async def get_crowd_meter(match_id: str):
    return await crowd_meter.get_meter(match_id)

# ── Daily Puzzle ───────────────────────────────────────────────────────────────

@router.get("/puzzle/today")
async def get_today_puzzle(user: User = Depends(get_current_user)):
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
        "first_100_reward": 25, "late_reward": 5,
    }

@router.post("/puzzle/answer")
async def answer_puzzle(req: PuzzleAnswerReq, user: User = Depends(get_current_user)):
    from v2_engines import ledger
    return await puzzle_engine.submit_answer(user.id, req.answer, ledger)

# ── Weekly Report Card ─────────────────────────────────────────────────────────

@router.get("/report-card/weekly")
async def get_weekly_report(user: User = Depends(get_current_user)):
    report = await report_engine.get_latest(user.id)
    return {**report, "is_new": not report.get("viewed", False)}

@router.post("/report-card/dismiss")
async def dismiss_weekly_report(user: User = Depends(get_current_user)):
    await report_engine.mark_viewed(user.id)
    return {"dismissed": True}
