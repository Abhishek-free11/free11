"""
MatchState Engine for FREE11
Handles: 2s polling, delta detection, internal event bus, snapshot storage, auto-stop, freeze on failure
"""
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Callable
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class MatchStateEngine:
    """
    Manages live match state with 2s polling, delta detection, and event dispatch.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._listeners: Dict[str, List[Callable]] = {}
        self._polling_tasks: Dict[str, asyncio.Task] = {}
        self._frozen_matches: set = set()

    # ── Event Bus ──

    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)

    async def _emit(self, event: str, data: Dict):
        for cb in self._listeners.get(event, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(data)
                else:
                    cb(data)
            except Exception as e:
                logger.error(f"Event handler error: {event} -> {e}")

    # ── Snapshot Storage ──

    async def save_snapshot(self, match_id: str, data: Dict):
        now = datetime.now(timezone.utc).isoformat()
        snapshot = {
            "id": str(uuid.uuid4()),
            "match_id": match_id,
            "data": data,
            "timestamp": now,
        }
        await self.db.match_snapshots.insert_one(snapshot)
        # Keep only last 100 snapshots per match
        count = await self.db.match_snapshots.count_documents({"match_id": match_id})
        if count > 100:
            oldest = await self.db.match_snapshots.find(
                {"match_id": match_id}, {"_id": 1}
            ).sort("timestamp", 1).limit(count - 100).to_list(count - 100)
            if oldest:
                ids = [o["_id"] for o in oldest]
                await self.db.match_snapshots.delete_many({"_id": {"$in": ids}})

    async def get_latest_snapshot(self, match_id: str) -> Optional[Dict]:
        snap = await self.db.match_snapshots.find_one(
            {"match_id": match_id},
            {"_id": 0},
            sort=[("timestamp", -1)]
        )
        return snap

    # ── Delta Detection ──

    def _compute_delta(self, old: Optional[Dict], new: Dict) -> Dict:
        if not old:
            return {"type": "full", "data": new}
        delta = {}
        old_data = old.get("data", {})
        for key in new:
            if new.get(key) != old_data.get(key):
                delta[key] = new[key]
        return delta if delta else {}

    # ── Match State Management ──

    async def update_match_state(self, match_id: str, new_state: Dict) -> Dict:
        """Process a new match state update with delta detection"""
        old_snapshot = await self.get_latest_snapshot(match_id)
        delta = self._compute_delta(old_snapshot, new_state)

        if not delta:
            return {"changed": False}

        await self.save_snapshot(match_id, new_state)

        # Emit events based on delta
        if "status" in delta:
            status = delta["status"]
            if status in ("completed", "abandoned", 2):
                await self._emit("match_end", {"match_id": match_id, "state": new_state})
                self.stop_polling(match_id)
            elif status in ("live", 3):
                await self._emit("match_live", {"match_id": match_id, "state": new_state})

        if "live_score" in delta or "overs" in delta:
            await self._emit("score_update", {"match_id": match_id, "state": new_state})

        await self._emit("state_change", {"match_id": match_id, "delta": delta, "state": new_state})

        return {"changed": True, "delta": delta}

    async def freeze_match(self, match_id: str, reason: str = "api_failure"):
        """Freeze match data updates (on API failure)"""
        self._frozen_matches.add(match_id)
        now = datetime.now(timezone.utc).isoformat()
        await self.db.match_events_log.insert_one({
            "id": str(uuid.uuid4()),
            "match_id": match_id,
            "event": "freeze",
            "reason": reason,
            "timestamp": now,
        })
        logger.warning(f"MATCH FROZEN: {match_id} reason={reason}")

    async def unfreeze_match(self, match_id: str):
        self._frozen_matches.discard(match_id)

    def is_frozen(self, match_id: str) -> bool:
        return match_id in self._frozen_matches

    # ── Polling Control ──

    def stop_polling(self, match_id: str):
        task = self._polling_tasks.pop(match_id, None)
        if task and not task.done():
            task.cancel()
            logger.info(f"Polling stopped for match {match_id}")

    def stop_all(self):
        for mid in list(self._polling_tasks.keys()):
            self.stop_polling(mid)

    # ── Test Match Mode ──

    async def create_test_match(self) -> Dict:
        """Create a simulated test match for admin testing"""
        match_id = f"test_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        test_match = {
            "id": match_id,
            "match_id": match_id,
            "team1": "Test Team A",
            "team2": "Test Team B",
            "team1_short": "TTA",
            "team2_short": "TTB",
            "team1_logo": "",
            "team2_logo": "",
            "venue": "Test Stadium",
            "match_type": "T20",
            "series": "Test Series",
            "status": "live",
            "match_date": now,
            "team1_score": "0/0 (0.0)",
            "team2_score": None,
            "current_ball": "0.1",
            "current_over_balls": [],
            "batting_team": "Test Team A",
            "toss_winner": "Test Team A",
            "toss_decision": "bat",
            "is_test_match": True,
            "created_at": now,
        }
        await self.db.matches.update_one(
            {"match_id": match_id},
            {"$set": test_match},
            upsert=True
        )
        return test_match

    async def advance_test_match(self, match_id: str, runs: int = None, wicket: bool = False) -> Dict:
        """Advance a test match by one ball"""
        import random
        match = await self.db.matches.find_one({"match_id": match_id}, {"_id": 0})
        if not match or not match.get("is_test_match"):
            return {"error": "not_a_test_match"}

        current = match.get("current_ball", "0.1")
        over, ball = current.split(".")
        over, ball = int(over), int(ball)

        if runs is None:
            runs = random.choices([0, 1, 2, 3, 4, 6], weights=[30, 30, 15, 5, 12, 8])[0]

        # Parse current score
        score_str = match.get("team1_score", "0/0 (0.0)")
        try:
            parts = score_str.split("/")
            total_runs = int(parts[0])
            wickets_str = parts[1].split(" ")[0]
            total_wickets = int(wickets_str)
        except (IndexError, ValueError):
            total_runs, total_wickets = 0, 0

        ball_result = str(runs)
        if wicket:
            total_wickets += 1
            ball_result = "W"
        else:
            total_runs += runs

        # Advance ball
        ball += 1
        over_balls = match.get("current_over_balls", [])
        over_balls.append(ball_result)

        if ball > 6:
            over += 1
            ball = 1
            over_balls = []

        new_ball = f"{over}.{ball}"
        new_score = f"{total_runs}/{total_wickets} ({over}.{ball-1 if ball > 1 else 0})"

        # Check match end (20 overs or 10 wickets)
        status = "live"
        if over >= 20 or total_wickets >= 10:
            status = "completed"

        update = {
            "current_ball": new_ball,
            "current_over_balls": over_balls,
            "team1_score": new_score,
            "status": status,
        }
        await self.db.matches.update_one({"match_id": match_id}, {"$set": update})

        # Store ball event for resolution
        ball_event = {
            "id": str(uuid.uuid4()),
            "match_id": match_id,
            "ball": f"{over}.{ball}",
            "runs": runs,
            "wicket": wicket,
            "result": ball_result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_test": True,
        }
        await self.db.ball_events.insert_one(ball_event)

        await self.update_match_state(match_id, {**match, **update})

        return {
            "ball": new_ball,
            "result": ball_result,
            "score": new_score,
            "status": status,
            "over_balls": over_balls,
        }
