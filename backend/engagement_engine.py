"""
Engagement Engine — Feature 3, 4, 5
- Crowd Meter: Anonymous aggregate prediction distribution per match
- Daily Puzzle: AI-generated daily cricket puzzle (Gemini Flash) with static fallback
- Weekly Report Card: Per-user weekly stats summary
"""
import uuid
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 3 — Crowd Meter
# ─────────────────────────────────────────────────────────────────────────────

class CrowdMeterEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_meter(self, match_id: str) -> Dict:
        """Aggregate prediction distribution for a match, anonymously."""
        pipeline = [
            {"$match": {"match_id": match_id}},
            {"$group": {
                "_id": {
                    "prediction_type": "$prediction_type",
                    "prediction_value": "$prediction_value",
                },
                "count": {"$sum": 1},
            }},
        ]
        rows = await self.db.predictions_v2.aggregate(pipeline).to_list(1000)

        # Group by type then calc percentages
        by_type: Dict[str, Dict[str, int]] = {}
        for r in rows:
            pt = r["_id"]["prediction_type"]
            pv = r["_id"]["prediction_value"]
            by_type.setdefault(pt, {})[pv] = r["count"]

        meter = {}
        for pt, opts in by_type.items():
            total = sum(opts.values())
            meter[pt] = {
                "total_predictions": total,
                "options": {
                    v: {"count": c, "pct": round(c / total * 100) if total else 0}
                    for v, c in sorted(opts.items(), key=lambda x: -x[1])
                },
            }

        total_predictions = sum(v["total_predictions"] for v in meter.values())
        return {"match_id": match_id, "total_predictions": total_predictions, "meter": meter}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 4 — Daily Cricket Puzzle (AI-generated via Gemini Flash)
# ─────────────────────────────────────────────────────────────────────────────

FIRST_100_REWARD    = 25   # coins for first 100 correct answers per day
LATE_CORRECT_REWARD = 5    # coins for correct answers after first 100

# Static fallback puzzles (used if AI generation fails)
FALLBACK_PUZZLES = [
    {
        "question": "India needs 47 runs in 5 overs with 3 wickets in hand. What is the most likely result?",
        "options": ["India wins comfortably", "India loses", "Match tied", "Super Over needed"],
        "correct": "India loses",
        "explanation": "Required rate of 9.4 with only 3 wickets left makes it nearly impossible — statistically India loses ~78% of such chases.",
    },
    {
        "question": "A T20 team scores 220/3 batting first at a home venue. What is the win probability?",
        "options": ["Around 50%", "Around 65%", "Around 78%", "Above 85%"],
        "correct": "Around 78%",
        "explanation": "Historical T20 data shows 220+ scores at home venues lead to a win in ~78% of matches.",
    },
    {
        "question": "A fast bowler bowls 4 overs giving 52 runs with 0 wickets. What is the economy rate?",
        "options": ["11.0", "13.0", "9.5", "12.5"],
        "correct": "13.0",
        "explanation": "Economy = runs / overs = 52 / 4 = 13.0. Very expensive for a fast bowler.",
    },
    {
        "question": "Which over in a T20 innings typically yields the most runs on average?",
        "options": ["Over 1", "Over 6 (last powerplay)", "Over 16", "Over 20 (last over)"],
        "correct": "Over 20 (last over)",
        "explanation": "The 20th over averages 11-12 runs in T20 cricket due to big hitting at the death.",
    },
    {
        "question": "A spinner bowls on a dry pitch in the 4th innings. What is the expected wicket rate?",
        "options": ["1 wicket per 30 balls", "1 wicket per 20 balls", "1 wicket per 15 balls", "1 wicket per 10 balls"],
        "correct": "1 wicket per 15 balls",
        "explanation": "Spinners on dry 4th innings pitches average one wicket every 14-17 balls due to rough and turn.",
    },
    {
        "question": "In a T20, team batting second needs 12 off the last over with 2 wickets left. What usually happens?",
        "options": ["Win — scores easily", "Lose — falls short", "Tie — goes to Super Over", "Match abandoned"],
        "correct": "Lose — falls short",
        "explanation": "Teams needing 12 off the last over with 2 wickets succeed only ~31% of the time under pressure.",
    },
    {
        "question": "A batter has a T20 strike rate of 185 in the last 5 matches. How many runs per over is that?",
        "options": ["About 9 runs", "About 11 runs", "About 13 runs", "About 7 runs"],
        "correct": "About 11 runs",
        "explanation": "Strike rate 185 means 185 runs per 100 balls = 11.1 runs per 6 balls (one over).",
    },
]

PUZZLE_SYSTEM_PROMPT = """You are a cricket statistics and scenario expert creating daily quiz questions for FREE11, a cricket prediction platform.

Generate ONE engaging multiple-choice cricket puzzle. Focus on:
- Realistic match scenarios (run chases, scoring rates, wickets remaining)
- Statistical cricket knowledge (economy rates, strike rates, averages)
- Tactical cricket decisions (bowling changes, field placements)
- IPL, international T20, or Test cricket contexts

Rules:
- Question must have a clear, unambiguous correct answer based on cricket statistics/rules
- 4 options, exactly ONE correct
- Explanation should teach the user something interesting about cricket
- Vary the difficulty — mix easy, medium, and hard questions
- Make it fun and engaging, not just trivia

Respond ONLY with a valid JSON object in exactly this format:
{
  "question": "...",
  "options": ["option1", "option2", "option3", "option4"],
  "correct": "exact text matching one of the options",
  "explanation": "brief explanation of the correct answer (1-2 sentences)"
}"""


async def _generate_puzzle_with_gemini() -> Optional[Dict]:
    """Generate a fresh cricket puzzle using Gemini Flash."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            logger.warning("EMERGENT_LLM_KEY not set — skipping AI puzzle generation")
            return None

        session_id = f"puzzle-gen-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=PUZZLE_SYSTEM_PROMPT,
        ).with_model("gemini", "gemini-3-flash-preview")

        today_dow = datetime.now(timezone.utc).weekday()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        prompt = (
            f"Generate a fresh cricket puzzle for {day_names[today_dow]}. "
            "Pick a scenario type at random: run chase, bowling figures, batting milestone, T20 strategy, or Test cricket. "
            "Return ONLY the JSON object, no markdown, no extra text."
        )

        response = await chat.send_message(UserMessage(text=prompt))

        # Robustly extract JSON — find first { and last } regardless of markdown fences
        text = response.strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end <= start:
            raise ValueError(f"No JSON object found in response: {text[:200]}")
        text = text[start:end]

        data = json.loads(text)

        # Validate required fields
        required = {"question", "options", "correct", "explanation"}
        if not required.issubset(data.keys()):
            raise ValueError(f"Missing fields: {required - data.keys()}")
        if len(data["options"]) != 4:
            raise ValueError("Must have exactly 4 options")
        if data["correct"] not in data["options"]:
            raise ValueError("Correct answer must match one of the options")

        logger.info("AI puzzle generated successfully via Gemini Flash")
        return data

    except Exception as e:
        logger.error(f"AI puzzle generation failed: {e}")
        return None


class PuzzleEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def _today_str(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async def generate_today(self) -> Dict:
        """
        Generate (or fetch cached) today's AI puzzle.
        Falls back to a static puzzle if AI generation fails.
        Idempotent — only generates once per day.
        """
        today = self._today_str()

        # Return cached if already generated today
        existing = await self.db.daily_puzzles.find_one({"puzzle_date": today}, {"_id": 0})
        if existing:
            logger.info(f"Using cached puzzle for {today}")
            return existing

        # Try AI generation
        ai_puzzle = await _generate_puzzle_with_gemini()

        if ai_puzzle:
            doc = {
                "id": f"puzzle-ai-{today}",
                "puzzle_date": today,
                "source": "gemini",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                **ai_puzzle,
            }
        else:
            # Fallback: pick a static puzzle by day-of-week
            import random
            fallback = random.choice(FALLBACK_PUZZLES)
            doc = {
                "id": f"puzzle-fallback-{today}",
                "puzzle_date": today,
                "source": "fallback",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                **fallback,
            }
            logger.warning(f"Using fallback puzzle for {today}")

        await self.db.daily_puzzles.insert_one(doc)
        # Remove _id before returning
        doc.pop("_id", None)
        return doc

    async def get_today(self) -> Optional[Dict]:
        """Return today's puzzle (generating it if needed). Never exposes the answer."""
        puzzle = await self.generate_today()
        # Strip correct answer before returning to client
        return {k: v for k, v in puzzle.items() if k not in ("correct",)}

    async def submit_answer(self, user_id: str, answer: str, ledger) -> Dict:
        """
        Submit answer for today's puzzle.
        Idempotent — one attempt per user per day, all rewards via coin_transactions.
        """
        today = self._today_str()

        # Idempotency check
        existing = await self.db.puzzle_completions.find_one(
            {"user_id": user_id, "puzzle_date": today}, {"_id": 0}
        )
        if existing:
            return {
                "already_answered": True,
                "is_correct": existing["is_correct"],
                "coins_earned": existing["coins_earned"],
                "correct_answer": existing.get("correct_answer", ""),
                "explanation": existing.get("explanation", ""),
            }

        # Fetch today's puzzle (generates if needed)
        puzzle = await self.generate_today()
        is_correct = answer.strip().lower() == puzzle["correct"].strip().lower()

        coins_earned = 0
        if is_correct:
            correct_count = await self.db.puzzle_completions.count_documents(
                {"puzzle_date": today, "is_correct": True}
            )
            coins_earned = FIRST_100_REWARD if correct_count < 100 else LATE_CORRECT_REWARD

        completion = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "puzzle_id": puzzle["id"],
            "puzzle_date": today,
            "answer": answer,
            "correct_answer": puzzle["correct"],
            "is_correct": is_correct,
            "coins_earned": coins_earned,
            "answered_at": datetime.now(timezone.utc).isoformat(),
            "explanation": puzzle["explanation"],
        }
        await self.db.puzzle_completions.insert_one(completion)

        if coins_earned > 0:
            await ledger.credit(
                user_id, coins_earned,
                "puzzle_reward", completion["id"],
                f"Daily Cricket Puzzle — correct! {'(Fast solver bonus)' if coins_earned == FIRST_100_REWARD else ''}",
            )

        logger.info(f"PUZZLE: user={user_id} date={today} correct={is_correct} coins={coins_earned}")
        return {
            "already_answered": False,
            "is_correct": is_correct,
            "coins_earned": coins_earned,
            "correct_answer": puzzle["correct"],
            "explanation": puzzle["explanation"],
        }


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 5 — Weekly Report Card
# ─────────────────────────────────────────────────────────────────────────────

class WeeklyReportEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def _week_start(self, ref: Optional[datetime] = None) -> str:
        """Return ISO date string for the most recent Monday."""
        d = ref or datetime.now(timezone.utc)
        monday = d - timedelta(days=d.weekday())
        return monday.strftime("%Y-%m-%d")

    async def generate_report(self, user_id: str) -> Dict:
        """Generate (or refresh) the weekly report for a user."""
        week_start = self._week_start()
        since = datetime.strptime(week_start, "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat()

        # Predictions this week
        pred_pipeline = [
            {"$match": {"user_id": user_id, "status": "resolved", "resolved_at": {"$gte": since}}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "correct": {"$sum": {"$cond": ["$is_correct", 1, 0]}},
                "coins_earned": {"$sum": "$coins_earned"},
            }},
        ]
        pred_stats = await self.db.predictions_v2.aggregate(pred_pipeline).to_list(1)
        ps = pred_stats[0] if pred_stats else {"total": 0, "correct": 0, "coins_earned": 0}
        accuracy = round(ps["correct"] / ps["total"] * 100, 1) if ps["total"] > 0 else 0

        # Contests joined this week
        contests_joined = await self.db.contest_entries.count_documents(
            {"user_id": user_id, "joined_at": {"$gte": since}}
        )

        # Coins earned this week (all sources)
        coin_pipeline = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": since}, "amount": {"$gt": 0}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]
        coin_stats = await self.db.coin_transactions.aggregate(coin_pipeline).to_list(1)
        coins_this_week = (coin_stats[0]["total"] if coin_stats else 0)

        # Global rank
        user_doc = await self.db.users.find_one({"id": user_id}, {"_id": 0, "total_earned": 1})
        total_earned = (user_doc or {}).get("total_earned", 0)
        rank = await self.db.users.count_documents({"total_earned": {"$gt": total_earned}}) + 1

        # Previous week's rank for delta
        prev_report = await self.db.weekly_reports.find_one(
            {"user_id": user_id, "week_start": {"$ne": week_start}},
            {"_id": 0, "rank": 1},
            sort=[("generated_at", -1)],
        )
        prev_rank = (prev_report or {}).get("rank", rank)
        rank_change = prev_rank - rank  # positive = improved

        report = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "week_start": week_start,
            "predictions_total": ps["total"],
            "predictions_correct": ps["correct"],
            "accuracy": accuracy,
            "coins_earned_this_week": coins_this_week,
            "contests_joined": contests_joined,
            "rank": rank,
            "rank_change": rank_change,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "viewed": False,
        }

        # Upsert for this week
        await self.db.weekly_reports.update_one(
            {"user_id": user_id, "week_start": week_start},
            {"$set": report},
            upsert=True,
        )
        return report

    async def get_latest(self, user_id: str) -> Dict:
        """Get or generate the weekly report for the current week."""
        week_start = self._week_start()
        existing = await self.db.weekly_reports.find_one(
            {"user_id": user_id, "week_start": week_start}, {"_id": 0}
        )
        if existing:
            return existing
        # Generate fresh if none exists
        return await self.generate_report(user_id)

    async def mark_viewed(self, user_id: str):
        week_start = self._week_start()
        await self.db.weekly_reports.update_one(
            {"user_id": user_id, "week_start": week_start},
            {"$set": {"viewed": True, "viewed_at": datetime.now(timezone.utc).isoformat()}},
        )

    async def generate_all_users(self):
        """Called by scheduler every Monday — pre-generate reports for all active users."""
        active_ids = await self.db.users.distinct("id", {})
        generated = 0
        for uid in active_ids:
            try:
                await self.generate_report(uid)
                generated += 1
            except Exception as e:
                logger.error(f"WeeklyReport: failed for user={uid}: {e}")
        logger.info(f"WeeklyReport: generated {generated} reports for week starting {self._week_start()}")
        return generated
