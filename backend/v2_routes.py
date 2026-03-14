"""
FREE11 V2 Routes — Aggregator
=============================================================
Previously a 1329-line monolith. Now delegates to domain-specific
sub-routers in the /routes/ package for maintainability.

Exports for backwards-compat with server.py:
  - v2_router     → main APIRouter included by server.py
  - contests      → ContestEngine instance (AutoScorer)
  - puzzle_engine → PuzzleEngine instance (AI puzzle scheduler)
"""
from fastapi import APIRouter

# ── Engine instances (re-exported for server.py backward compat) ──────────────
from v2_engines import (
    ledger, contests, predictions, cards, matchstate, referrals,
    voucher_provider, ads_provider, entitysport, fantasy,
    crowd_meter, puzzle_engine, report_engine, quest_engine,
    xoxoday, _analytics,
)

# ── Main V2 Router ─────────────────────────────────────────────────────────────
v2_router = APIRouter(prefix="/v2", tags=["V2"])

# ── Include Domain Sub-Routers ─────────────────────────────────────────────────
from routes.v2_contests   import router as _contests_router
from routes.v2_earn       import router as _earn_router
from routes.v2_matches    import router as _matches_router
from routes.v2_commerce   import router as _commerce_router
from routes.v2_engagement import router as _engagement_router

v2_router.include_router(_contests_router)
v2_router.include_router(_earn_router)
v2_router.include_router(_matches_router)
v2_router.include_router(_commerce_router)
v2_router.include_router(_engagement_router)
