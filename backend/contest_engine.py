"""
Contest Engine for FREE11
Handles: public/private contests, join/create, lock at match start, fill limits, leaderboard, tie-break
Platform contests: auto-seeded per match with FREE COIN prize pools
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

CONTEST_DEFAULTS = {
    "max_participants": 100,
    "entry_fee": 0,
    "prize_pool": 0,
    "min_participants": 2,
}

# ── Platform Contest Tier Definitions ──────────────────────────────────────────
# All prizes in FREE COINS. prize_distribution maps rank → coins awarded.
CONTEST_TIERS = {
    "mega": {
        "name": "Mega Contest",
        "tier": "mega",
        "prize_pool": 5000,
        "max_participants": 500,
        "entry_fee": 0,
        "prize_distribution": {
            "1": 2000, "2": 1000, "3": 500,
            "4": 200, "5": 200, "6": 100, "7": 100, "8": 100, "9": 100, "10": 100,
        },
        "winners_count": 10,
        "badge_color": "yellow",
        "description": "Top 10 win FREE Coins",
    },
    "standard": {
        "name": "Standard Contest",
        "tier": "standard",
        "prize_pool": 1000,
        "max_participants": 100,
        "entry_fee": 0,
        "prize_distribution": {
            "1": 500, "2": 250, "3": 150, "4": 50, "5": 50,
        },
        "winners_count": 5,
        "badge_color": "blue",
        "description": "Top 5 win FREE Coins",
    },
    "practice": {
        "name": "Practice Contest",
        "tier": "practice",
        "prize_pool": 200,
        "max_participants": 50,
        "entry_fee": 0,
        "prize_distribution": {
            "1": 100, "2": 60, "3": 40,
        },
        "winners_count": 3,
        "badge_color": "green",
        "description": "Top 3 win FREE Coins",
    },
    "h2h": {
        "name": "Head to Head",
        "tier": "h2h",
        "prize_pool": 100,
        "max_participants": 2,
        "entry_fee": 0,
        "prize_distribution": {"1": 100},
        "winners_count": 1,
        "badge_color": "red",
        "description": "Winner takes all",
    },
}


def _detect_match_tier(series: str) -> List[str]:
    """Return which contest tiers to seed based on match prominence."""
    s = (series or "").lower()
    if any(k in s for k in ["world cup", "ipl", "champions trophy", "t20i series", "odi series"]):
        return ["mega", "standard", "practice", "h2h"]
    if any(k in s for k in ["test", "tour", "tri-series"]):
        return ["standard", "practice", "h2h"]
    return ["standard", "practice", "h2h"]


class ContestEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ── Seed Platform Contests ─────────────────────────────────────────────────

    async def seed_platform_contests(self, match_id: str, series: str = "") -> List[Dict]:
        """Auto-create platform-managed contests for a match if they don't exist yet."""
        existing = await self.db.contests.count_documents(
            {"match_id": match_id, "is_platform_contest": True}
        )
        if existing > 0:
            return []  # Already seeded

        tiers = _detect_match_tier(series)
        created = []
        for tier_key in tiers:
            tier = CONTEST_TIERS[tier_key]
            contest = await self._create_platform_contest(match_id, tier)
            created.append(contest)
        logger.info(f"SEEDED {len(created)} platform contests for match={match_id}")
        return created

    async def _create_platform_contest(self, match_id: str, tier: Dict) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        contest = {
            "id": str(uuid.uuid4()),
            "match_id": match_id,
            "creator_id": "platform",
            "name": tier["name"],
            "type": "public",
            "tier": tier["tier"],
            "is_platform_contest": True,
            "status": "open",
            "max_participants": tier["max_participants"],
            "current_participants": 0,
            "entry_fee": tier["entry_fee"],
            "prize_pool": tier["prize_pool"],
            "prize_distribution": tier["prize_distribution"],
            "winners_count": tier["winners_count"],
            "badge_color": tier["badge_color"],
            "description": tier["description"],
            "invite_code": None,
            "participants": [],
            "locked": False,
            "finalized": False,
            "created_at": now,
            "updated_at": now,
        }
        await self.db.contests.insert_one(contest)
        return {k: v for k, v in contest.items() if k != "_id"}

    # ── Scoring Engine ────────────────────────────────────────────────────────

    # Contest scoring: different from coin rewards — optimised for ranking
    CONTEST_POINTS = {
        "over_runs":            {"correct": 10, "bonus_streak": 5},
        "over_wicket":          {"correct": 20, "bonus_streak": 10},
        "over_boundary":        {"correct": 15, "bonus_streak": 7},
        "milestone_team_score": {"correct": 25, "bonus_streak": 12},
        "milestone_powerplay":  {"correct": 20, "bonus_streak": 10},
        "match_winner":         {"correct": 50, "bonus_streak": 25},
        "match_total":          {"correct": 30, "bonus_streak": 15},
    }

    def calculate_user_points(self, predictions: List[Dict]) -> float:
        """
        Convert resolved prediction records into contest points.
        Deterministic and reproducible from the same prediction list.

        Scoring logic:
          - Correct over_runs      → +10 pts (+5 streak bonus)
          - Correct over_wicket    → +20 pts (+10 streak bonus)
          - Correct over_boundary  → +15 pts (+7 streak bonus)
          - Correct milestone_*    → +20-25 pts (+10-12 streak bonus)
          - Correct match_winner   → +50 pts (+25 streak bonus)
          - Streak bonus applies when user has 3+ consecutive correct predictions
          - Incorrect predictions  → 0 pts (never negative)
        """
        total = 0.0
        streak = 0
        STREAK_THRESHOLD = 3

        for pred in sorted(predictions, key=lambda p: p.get("submitted_at", "")):
            if pred.get("status") != "resolved":
                continue
            is_correct = pred.get("is_correct", False)
            ptype = pred.get("prediction_type", "")
            pts_config = self.CONTEST_POINTS.get(ptype, {"correct": 10, "bonus_streak": 5})

            if is_correct:
                streak += 1
                pts = pts_config["correct"]
                if streak >= STREAK_THRESHOLD:
                    pts += pts_config["bonus_streak"]
                total += pts
            else:
                streak = 0

        return round(total, 2)

    async def calculate_and_store_points(self, contest_id: str, user_id: str, match_id: str) -> float:
        """Fetch user predictions for match, compute points, store in contest_entries."""
        preds = await self.db.predictions_v2.find(
            {"user_id": user_id, "match_id": match_id, "status": "resolved"},
            {"_id": 0}
        ).to_list(500)

        points = self.calculate_user_points(preds)

        await self.db.contest_entries.update_one(
            {"contest_id": contest_id, "user_id": user_id},
            {"$set": {"points": points, "last_scored_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return points

    # ── Finalize Contest & Pay Out Coins ──────────────────────────────────────

    async def finalize_contest(self, contest_id: str) -> Dict:
        """Distribute coin prizes to top-ranked participants after match ends.
        Idempotent: unique_payout_id prevents double payout even if called twice.
        """
        contest = await self.db.contests.find_one({"id": contest_id}, {"_id": 0})
        if not contest:
            raise ValueError("Contest not found")
        if contest.get("finalized"):
            return {"already_finalized": True, "contest_id": contest_id}
        if contest.get("current_participants", 0) < 2:
            await self.db.contests.update_one(
                {"id": contest_id},
                {"$set": {"status": "voided", "void_reason": "insufficient_participants",
                          "finalized": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            return {"voided": True, "reason": "insufficient_participants"}

        # Recalculate points from resolved predictions before ranking
        match_id = contest.get("match_id", "")
        for uid in contest.get("participants", []):
            try:
                await self.calculate_and_store_points(contest_id, uid, match_id)
            except Exception as e:
                logger.warning(f"finalize: scoring failed user={uid}: {e}")

        leaderboard = await self.get_leaderboard(contest_id)
        dist = contest.get("prize_distribution", {})
        payouts = []

        for entry in leaderboard:
            rank = entry["rank"]
            reward = dist.get(str(rank), 0)
            if reward <= 0:
                continue

            # ── IDEMPOTENCY GUARD ──────────────────────────────────────────
            unique_payout_id = f"payout_{contest_id}_{entry['user_id']}"
            try:
                await self.db.coin_transactions.insert_one({
                    "unique_payout_id": unique_payout_id,
                    "user_id": entry["user_id"],
                    "amount": reward,
                    "type": "contest_prize",
                    "description": f"Contest prize: Rank #{rank} in '{contest['name']}' (Match {match_id})",
                    "contest_id": contest_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                # DuplicateKeyError → already paid; skip silently
                logger.info(f"finalize: payout already issued for {unique_payout_id}, skipping")
                continue

            # ── ATOMIC BALANCE CREDIT ──────────────────────────────────────
            updated = await self.db.users.find_one_and_update(
                {"id": entry["user_id"]},
                {"$inc": {"coins_balance": reward, "total_earned": reward}},
                return_document=True,
                projection={"_id": 0, "coins_balance": 1}
            )
            if updated:
                payouts.append({"user_id": entry["user_id"], "rank": rank, "coins": reward,
                                 "new_balance": updated.get("coins_balance", 0)})

        await self.db.contests.update_one(
            {"id": contest_id},
            {"$set": {"status": "completed", "finalized": True,
                      "payout_count": len(payouts),
                      "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        logger.info(f"CONTEST FINALIZED: {contest_id} payouts={len(payouts)}")
        return {"finalized": True, "payouts": payouts, "total_paid": sum(p["coins"] for p in payouts)}

    # ── Create (user-created contests) ────────────────────────────────────────

    async def create_contest(
        self,
        match_id: str,
        creator_id: str,
        name: str,
        contest_type: str = "public",
        max_participants: int = 100,
        entry_fee: int = 0,
    ) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        invite_code = uuid.uuid4().hex[:6].upper() if contest_type == "private" else None

        contest = {
            "id": str(uuid.uuid4()),
            "match_id": match_id,
            "creator_id": creator_id,
            "name": name,
            "type": contest_type,
            "tier": "user",
            "is_platform_contest": False,
            "status": "open",
            "max_participants": max_participants,
            "current_participants": 0,
            "entry_fee": entry_fee,
            "prize_pool": 0,
            "prize_distribution": {},
            "invite_code": invite_code,
            "participants": [],
            "locked": False,
            "finalized": False,
            "created_at": now,
            "updated_at": now,
        }
        await self.db.contests.insert_one(contest)
        logger.info(f"CONTEST CREATED: {contest['id']} match={match_id} type={contest_type}")
        return {k: v for k, v in contest.items() if k != "_id"}

    # ── Join (atomic) ──────────────────────────────────────────────────────────

    async def join_contest(self, contest_id: str, user_id: str, entry: Optional[Dict] = None) -> Dict:
        """Atomic join: prevents duplicate, overfill, late join"""
        contest = await self.db.contests.find_one({"id": contest_id}, {"_id": 0})
        if not contest:
            raise ValueError("Contest not found")

        if contest["locked"]:
            raise ValueError("Contest is locked (match has started)")
        if contest["status"] not in ("open",):
            raise ValueError(f"Contest is {contest['status']}, cannot join")
        if user_id in contest["participants"]:
            raise ValueError("Already joined this contest")
        if contest["current_participants"] >= contest["max_participants"]:
            raise ValueError("Contest is full")

        result = await self.db.contests.update_one(
            {
                "id": contest_id,
                "locked": False,
                "status": "open",
                "participants": {"$ne": user_id},
                "current_participants": {"$lt": contest["max_participants"]},
            },
            {
                "$push": {"participants": user_id},
                "$inc": {"current_participants": 1},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
            }
        )

        if result.modified_count == 0:
            raise ValueError("Failed to join: contest may be full, locked, or already joined")

        if entry:
            await self.db.contest_entries.update_one(
                {"contest_id": contest_id, "user_id": user_id},
                {"$set": {
                    "contest_id": contest_id,
                    "user_id": user_id,
                    "entry": entry,
                    "points": 0,
                    "rank": 0,
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                }},
                upsert=True
            )

        updated = await self.db.contests.find_one({"id": contest_id}, {"_id": 0})
        if updated and updated["current_participants"] >= updated["max_participants"]:
            await self.db.contests.update_one(
                {"id": contest_id},
                {"$set": {"status": "full"}}
            )

        logger.info(f"CONTEST JOIN: user={user_id} contest={contest_id}")
        return {"success": True, "participants": contest["current_participants"] + 1}

    # ── Lock at match start ────────────────────────────────────────────────────

    async def lock_contest(self, contest_id: str) -> Dict:
        result = await self.db.contests.update_one(
            {"id": contest_id, "locked": False},
            {"$set": {"locked": True, "status": "locked", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"locked": result.modified_count > 0}

    async def lock_all_for_match(self, match_id: str) -> int:
        result = await self.db.contests.update_many(
            {"match_id": match_id, "locked": False},
            {"$set": {"locked": True, "status": "locked", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        logger.info(f"CONTESTS LOCKED: match={match_id} count={result.modified_count}")
        return result.modified_count

    # ── Leaderboard & Scoring ─────────────────────────────────────────────────

    async def update_points(self, contest_id: str, user_id: str, points: float):
        await self.db.contest_entries.update_one(
            {"contest_id": contest_id, "user_id": user_id},
            {"$set": {"points": points}}
        )

    async def get_leaderboard(self, contest_id: str) -> List[Dict]:
        """Get contest leaderboard with prize info per rank."""
        contest = await self.db.contests.find_one({"id": contest_id}, {"_id": 0})
        dist = contest.get("prize_distribution", {}) if contest else {}

        entries = await self.db.contest_entries.find(
            {"contest_id": contest_id},
            {"_id": 0}
        ).sort([("points", -1), ("submitted_at", 1)]).to_list(1000)

        user_ids = [e["user_id"] for e in entries]
        users = await self.db.users.find(
            {"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "name": 1}
        ).to_list(len(user_ids))
        user_map = {u["id"]: u["name"] for u in users}

        for i, entry in enumerate(entries):
            rank = i + 1
            entry["rank"] = rank
            entry["user_name"] = user_map.get(entry["user_id"], "Unknown")
            prize = dist.get(str(rank), 0)
            entry["prize_coins"] = prize

        return entries

    # ── Void ──────────────────────────────────────────────────────────────────

    async def void_contest(self, contest_id: str, reason: str) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.contests.update_one(
            {"id": contest_id},
            {"$set": {"status": "voided", "void_reason": reason, "updated_at": now}}
        )
        logger.warning(f"CONTEST VOIDED: {contest_id} reason={reason}")
        return {"voided": True}

    # ── Query ─────────────────────────────────────────────────────────────────

    async def get_contests_for_match(self, match_id: str, contest_type: Optional[str] = None) -> List[Dict]:
        query = {"match_id": match_id}
        if contest_type:
            query["type"] = contest_type
        # Platform contests first, then user contests
        contests = await self.db.contests.find(query, {"_id": 0}).sort(
            [("is_platform_contest", -1), ("prize_pool", -1), ("created_at", -1)]
        ).to_list(100)
        return contests

    async def get_contest(self, contest_id: str) -> Optional[Dict]:
        return await self.db.contests.find_one({"id": contest_id}, {"_id": 0})

    async def get_user_contests(self, user_id: str) -> List[Dict]:
        return await self.db.contests.find(
            {"participants": user_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)

    async def join_by_invite_code(self, invite_code: str, user_id: str, entry: Optional[Dict] = None) -> Dict:
        contest = await self.db.contests.find_one({"invite_code": invite_code.upper()}, {"_id": 0})
        if not contest:
            raise ValueError("Invalid invite code")
        return await self.join_contest(contest["id"], user_id, entry)

