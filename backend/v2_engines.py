"""
v2_engines.py — Central engine initialization for FREE11 V2.

Initializes all business logic engines using the shared DB connection.
Both v2_routes.py and domain sub-routers import engine instances from here.

Import chain (no circular deps):
  server.py → v2_routes.py → v2_engines.py → server.py (db only, early-defined)
  server.py → v2_routes.py → routes/*.py   → v2_engines.py (already loaded)
"""
from server import db

from ledger_engine           import LedgerEngine
from contest_engine          import ContestEngine
from predict_engine          import PredictEngine
from cards_engine            import CardsEngine
from matchstate_engine       import MatchStateEngine
from referral_engine         import ReferralEngine
from services.voucher_provider import MockVoucherProvider
from services.ads_provider   import MockAdsProvider
from entitysport_service     import EntitySportService
from fantasy_engine          import FantasyEngine
from engagement_engine       import CrowdMeterEngine, PuzzleEngine, WeeklyReportEngine
from quest_engine            import QuestEngine
from xoxoday_provider        import XoxodayProvider
from analytics_engine        import AnalyticsEngine

# Singletons — one instance per process
ledger           = LedgerEngine(db)
contests         = ContestEngine(db)      # exported → server.py AutoScorer
predictions      = PredictEngine(db)
cards            = CardsEngine(db)
matchstate       = MatchStateEngine(db)
referrals        = ReferralEngine(db)
voucher_provider = MockVoucherProvider(db)
ads_provider     = MockAdsProvider(db)
entitysport      = EntitySportService(db)
fantasy          = FantasyEngine(db)
crowd_meter      = CrowdMeterEngine(db)
puzzle_engine    = PuzzleEngine(db)       # exported → server.py AI puzzle scheduler
report_engine    = WeeklyReportEngine(db)
quest_engine     = QuestEngine(db)
xoxoday          = XoxodayProvider(db)
_analytics       = AnalyticsEngine(db)
