"""
Auto-Scoring Scheduler for FREE11
Cron job: every 60 seconds.
- Score fantasy teams for completed matches
- Finalize platform contests and distribute coin prizes
Idempotent — no double scoring or double payouts.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class AutoScorer:
    def __init__(self, db: AsyncIOMotorDatabase, fantasy_engine, entitysport_service, notification_engine):
        self.db = db
        self.fantasy = fantasy_engine
        self.es = entitysport_service
        self.notif = notification_engine
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._contest_engine = None  # Injected after init to avoid circular import
        self._last_weekly_report_date: Optional[str] = None  # Track last Monday run
        self._last_puzzle_date: Optional[str] = None  # Track last daily puzzle generation
        self._fcm_service = None  # Injected after init
        # Track last campaign fire time (ISO date + hour string)
        self._last_campaign: dict = {}

    def set_contest_engine(self, contest_engine):
        self._contest_engine = contest_engine

    def set_fcm_service(self, fcm_service):
        self._fcm_service = fcm_service

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info("AutoScorer started (every 60s)")

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            logger.info("AutoScorer stopped")

    async def _run_loop(self):
        while self._running:
            try:
                await self._tick()
                await self._weekly_report_tick()
                await self._daily_puzzle_tick()
                await self._fcm_campaign_tick()
            except Exception as e:
                logger.error(f"AutoScorer error: {e}")
            await asyncio.sleep(60)

    async def _weekly_report_tick(self):
        """Feature 5: Generate weekly reports for all users every Monday."""
        now = datetime.now(timezone.utc)
        if now.weekday() != 0:  # Only Monday (0)
            return
        today_str = now.strftime("%Y-%m-%d")
        if self._last_weekly_report_date == today_str:
            return  # Already ran today
        try:
            from engagement_engine import WeeklyReportEngine
            report_eng = WeeklyReportEngine(self.db)
            count = await report_eng.generate_all_users()
            self._last_weekly_report_date = today_str
            logger.info(f"AutoScorer: Weekly reports generated for {count} users")
        except Exception as e:
            logger.error(f"AutoScorer: weekly report generation failed: {e}")

    async def _daily_puzzle_tick(self):
        """Feature 4: Pre-generate today's AI puzzle at midnight UTC."""
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        if self._last_puzzle_date == today_str:
            return  # Already generated today
        if now.hour != 0:  # Only run at midnight hour
            return
        try:
            from engagement_engine import PuzzleEngine
            puzzle_eng = PuzzleEngine(self.db)
            puzzle = await puzzle_eng.generate_today()
            self._last_puzzle_date = today_str
            logger.info(f"AutoScorer: Daily puzzle pre-generated: {puzzle.get('id')}")
        except Exception as e:
            logger.error(f"AutoScorer: daily puzzle generation failed: {e}")

    async def _tick(self):
        completed = await self.es.get_matches(status="2", per_page=20)
        if not completed:
            return

        for match in completed:
            match_id = match.get("match_id", "")
            if not match_id:
                continue

            # ── 1. Fantasy Scoring ─────────────────────────────────────────
            already = await self.db.auto_score_log.find_one({"match_id": match_id, "status": "scored"})
            if not already:
                teams_count = await self.db.fantasy_teams.count_documents({
                    "match_id": match_id, "status": {"$in": ["active", "locked"]}
                })
                if teams_count > 0:
                    logger.info(f"AutoScorer: scoring match {match_id} ({teams_count} teams)")
                    locked = await self.fantasy.lock_teams_for_match(match_id)
                    try:
                        scorecard = await self.es.get_match_scorecard(match_id)
                        if scorecard:
                            results = await self.fantasy.calculate_points(match_id, scorecard)
                            logger.info(f"AutoScorer: scored {len(results)} teams for {match_id}")
                            await self.db.auto_score_log.insert_one({
                                "match_id": match_id, "status": "scored",
                                "teams_scored": len(results), "locked": locked,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
                            for r in results:
                                await self.notif.send(
                                    r["user_id"], "team_scored",
                                    f"Your fantasy team scored {r['total_points']} points!",
                                    {"match_id": match_id, "points": r["total_points"]},
                                )
                    except Exception as e:
                        logger.error(f"AutoScorer: fantasy scoring failed for {match_id}: {e}")
                        await self.db.auto_score_log.insert_one({
                            "match_id": match_id, "status": "failed",
                            "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat(),
                        })

            # ── 2. Contest Finalization ────────────────────────────────────
            if self._contest_engine:
                await self._finalize_match_contests(match_id)

    async def _finalize_match_contests(self, match_id: str):
        """Finalize all unfinalized contests for a completed match. Idempotent."""
        open_contests = await self.db.contests.find(
            {"match_id": match_id, "finalized": {"$ne": True}, "status": {"$in": ["open", "full", "locked"]}},
            {"_id": 0, "id": 1, "name": 1}
        ).to_list(50)

        for contest in open_contests:
            try:
                result = await self._contest_engine.finalize_contest(contest["id"])
                logger.info(f"AutoScorer: finalized contest {contest['id']} ({contest['name']}): {result}")
                # Notify winners
                if result.get("payouts"):
                    for payout in result["payouts"]:
                        if payout.get("coins", 0) > 0:
                            await self.notif.send(
                                payout["user_id"], "contest_prize",
                                f"You won {payout['coins']} FREE Coins! Rank #{payout['rank']} in {contest['name']}",
                                {"contest_id": contest["id"], "coins": payout["coins"], "rank": payout["rank"]},
                            )
            except Exception as e:
                logger.error(f"AutoScorer: contest finalization failed for {contest['id']}: {e}")



    async def _fcm_campaign_tick(self):
        """
        Fire FCM campaigns at scheduled IST times (runs every 60s, fires once per slot).
        Slots:
          Every tick  → match_starting (30-60 min window check)
          Every tick  → activation_trigger (20-28h new-user window check, idempotent)
          09:00 IST   → quest_available
          20:00 IST   → streak_reminder (3+ day streak, 20h inactivity)
          22:00 IST   → streak_reminder re-check (second nudge for still-at-risk users)
          10:00 IST   → coin_expiry (daily)
        """
        if not self._fcm_service:
            return
        from fcm_campaigns import (
            send_match_starting_campaign,
            send_coin_expiry_campaign,
            send_streak_reminder_campaign,
            send_quest_available_campaign,
            send_activation_trigger_campaign,
        )
        from datetime import timedelta
        IST = timedelta(hours=5, minutes=30)
        now_ist  = datetime.now(timezone.utc) + IST
        hour_key = now_ist.strftime("%Y-%m-%d-%H")

        # Match starting — check every tick
        await send_match_starting_campaign(self.db, self._fcm_service)

        # Activation trigger — check every tick (idempotent via activation_push_sent flag)
        await send_activation_trigger_campaign(self.db, self._fcm_service)

        # Quest available — 09:00 IST daily
        if now_ist.hour == 9 and self._last_campaign.get("quest") != hour_key:
            self._last_campaign["quest"] = hour_key
            await send_quest_available_campaign(self.db, self._fcm_service)

        # Streak reminder — 20:00 IST daily (primary)
        if now_ist.hour == 20 and self._last_campaign.get("streak_20") != hour_key:
            self._last_campaign["streak_20"] = hour_key
            await send_streak_reminder_campaign(self.db, self._fcm_service)

        # Streak reminder — 22:00 IST (second nudge for still-at-risk users)
        if now_ist.hour == 22 and self._last_campaign.get("streak_22") != hour_key:
            self._last_campaign["streak_22"] = hour_key
            await send_streak_reminder_campaign(self.db, self._fcm_service)

        # Coin expiry — 10:00 IST daily
        if now_ist.hour == 10 and self._last_campaign.get("expiry") != hour_key:
            self._last_campaign["expiry"] = hour_key
            await send_coin_expiry_campaign(self.db, self._fcm_service)
