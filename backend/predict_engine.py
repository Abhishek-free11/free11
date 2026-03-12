"""
Predict Engine for FREE11
Over-based + milestone predictions. Server lock, server resolution, idempotent results, audit log.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Prediction types
PREDICTION_TYPES = {
    "over_runs": {"label": "Runs in Over", "options": ["0-5", "6-10", "11-15", "16+"]},
    "over_wicket": {"label": "Wicket in Over?", "options": ["yes", "no"]},
    "over_boundary": {"label": "Boundary in Over?", "options": ["yes", "no"]},
    "milestone_team_score": {"label": "Team Score at 6 overs", "options": ["<40", "40-55", "56-70", "70+"]},
    "milestone_powerplay": {"label": "Powerplay Wickets", "options": ["0", "1", "2", "3+"]},
    "match_winner": {"label": "Match Winner", "options": []},  # Dynamic per match
    "match_total": {"label": "Match Total", "options": ["<140", "140-160", "161-180", "180+"]},
}

# Coin rewards
PREDICTION_REWARDS = {
    "over_runs": 15,
    "over_wicket": 10,
    "over_boundary": 10,
    "milestone_team_score": 25,
    "milestone_powerplay": 20,
    "match_winner": 50,
    "match_total": 30,
}


class PredictEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ── Submit Prediction ──

    async def submit_prediction(
        self,
        user_id: str,
        match_id: str,
        prediction_type: str,
        prediction_value: str,
        over_number: Optional[int] = None,
        server_timestamp: Optional[str] = None,
    ) -> Dict:
        """
        Submit a prediction with server-side lock validation.
        Idempotent: prevents double submission for same type+over+match.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Check if prediction type is valid
        if prediction_type not in PREDICTION_TYPES:
            raise ValueError(f"Invalid prediction type: {prediction_type}")

        # Server lock: check if match/over is still open for predictions
        lock_status = await self._check_lock(match_id, prediction_type, over_number)
        if not lock_status["open"]:
            raise ValueError(f"Prediction window closed: {lock_status['reason']}")

        # Idempotent check: prevent duplicate for same user+match+type+over
        existing = await self.db.predictions_v2.find_one({
            "user_id": user_id,
            "match_id": match_id,
            "prediction_type": prediction_type,
            "over_number": over_number,
        }, {"_id": 0})

        if existing:
            raise ValueError("Prediction already submitted for this window")

        prediction = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "match_id": match_id,
            "prediction_type": prediction_type,
            "prediction_value": prediction_value,
            "over_number": over_number,
            "actual_value": None,
            "is_correct": None,
            "coins_earned": 0,
            "status": "pending",
            "submitted_at": now,
            "resolved_at": None,
            "server_timestamp": server_timestamp or now,
        }
        await self.db.predictions_v2.insert_one(prediction)

        # Audit log
        await self._audit("submit", prediction)

        logger.info(f"PREDICTION: user={user_id} match={match_id} type={prediction_type} value={prediction_value}")
        return {k: v for k, v in prediction.items() if k != "_id"}

    # ── Server Lock Check ──

    async def _check_lock(self, match_id: str, prediction_type: str, over_number: Optional[int]) -> Dict:
        """Check if predictions are still open for this match/over"""
        match = await self.db.matches.find_one({"match_id": match_id}, {"_id": 0})
        if not match:
            return {"open": False, "reason": "match_not_found"}

        status = match.get("status", "")
        if status in ("completed", "abandoned"):
            return {"open": False, "reason": "match_ended"}

        # For over-based predictions, check if the over has already started
        if over_number is not None and prediction_type.startswith("over_"):
            current_ball = match.get("current_ball", "0.0")
            try:
                current_over = int(current_ball.split(".")[0])
                if current_over > over_number:
                    return {"open": False, "reason": "over_completed"}
                if current_over == over_number:
                    ball_in_over = int(current_ball.split(".")[1])
                    if ball_in_over > 1:
                        return {"open": False, "reason": "over_in_progress"}
            except (ValueError, IndexError):
                pass

        return {"open": True, "reason": None}

    # ── Resolution ──

    async def resolve_over(self, match_id: str, over_number: int, over_result: Dict) -> List[Dict]:
        """
        Resolve all predictions for a completed over.
        over_result: { "runs": 12, "wickets": 1, "boundaries": 2 }
        Idempotent: won't double-reward.
        """
        now = datetime.now(timezone.utc).isoformat()
        results = []

        # Get all pending predictions for this over
        predictions = await self.db.predictions_v2.find({
            "match_id": match_id,
            "over_number": over_number,
            "status": "pending",
        }, {"_id": 0}).to_list(10000)

        for pred in predictions:
            is_correct = self._evaluate(pred, over_result)
            coins = PREDICTION_REWARDS.get(pred["prediction_type"], 0) if is_correct else 0

            await self.db.predictions_v2.update_one(
                {"id": pred["id"], "status": "pending"},
                {"$set": {
                    "actual_value": str(over_result.get("runs", "")),
                    "is_correct": is_correct,
                    "coins_earned": coins,
                    "status": "resolved",
                    "resolved_at": now,
                }}
            )

            result = {
                "prediction_id": pred["id"],
                "user_id": pred["user_id"],
                "is_correct": is_correct,
                "coins_earned": coins,
            }
            results.append(result)

            # Audit
            await self._audit("resolve", {**pred, "is_correct": is_correct, "coins_earned": coins})

        logger.info(f"RESOLVE OVER: match={match_id} over={over_number} predictions={len(predictions)} correct={sum(1 for r in results if r['is_correct'])}")
        return results

    async def resolve_milestone(self, match_id: str, milestone_type: str, actual_value: str) -> List[Dict]:
        """Resolve milestone predictions"""
        now = datetime.now(timezone.utc).isoformat()
        results = []

        predictions = await self.db.predictions_v2.find({
            "match_id": match_id,
            "prediction_type": milestone_type,
            "status": "pending",
        }, {"_id": 0}).to_list(10000)

        for pred in predictions:
            is_correct = pred["prediction_value"] == actual_value
            coins = PREDICTION_REWARDS.get(pred["prediction_type"], 0) if is_correct else 0

            await self.db.predictions_v2.update_one(
                {"id": pred["id"], "status": "pending"},
                {"$set": {
                    "actual_value": actual_value,
                    "is_correct": is_correct,
                    "coins_earned": coins,
                    "status": "resolved",
                    "resolved_at": now,
                }}
            )
            results.append({
                "prediction_id": pred["id"],
                "user_id": pred["user_id"],
                "is_correct": is_correct,
                "coins_earned": coins,
            })

        return results

    # ── Evaluation Logic ──

    def _evaluate(self, prediction: Dict, over_result: Dict) -> bool:
        ptype = prediction["prediction_type"]
        pval = prediction["prediction_value"]
        runs = over_result.get("runs", 0)
        wickets = over_result.get("wickets", 0)
        boundaries = over_result.get("boundaries", 0)

        if ptype == "over_runs":
            if pval == "0-5":
                return 0 <= runs <= 5
            elif pval == "6-10":
                return 6 <= runs <= 10
            elif pval == "11-15":
                return 11 <= runs <= 15
            elif pval == "16+":
                return runs >= 16
        elif ptype == "over_wicket":
            return (pval == "yes") == (wickets > 0)
        elif ptype == "over_boundary":
            return (pval == "yes") == (boundaries > 0)

        return False

    # ── Void ──

    async def void_predictions(self, match_id: str, reason: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        result = await self.db.predictions_v2.update_many(
            {"match_id": match_id, "status": "pending"},
            {"$set": {"status": "voided", "void_reason": reason, "resolved_at": now}}
        )
        logger.warning(f"PREDICTIONS VOIDED: match={match_id} count={result.modified_count} reason={reason}")
        return result.modified_count

    # ── Query ──

    async def get_user_predictions(self, user_id: str, match_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        query = {"user_id": user_id}
        if match_id:
            query["match_id"] = match_id
        return await self.db.predictions_v2.find(query, {"_id": 0}).sort("submitted_at", -1).limit(limit).to_list(limit)

    async def get_prediction_stats(self, user_id: str) -> Dict:
        pipeline = [
            {"$match": {"user_id": user_id, "status": "resolved"}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "correct": {"$sum": {"$cond": ["$is_correct", 1, 0]}},
                "total_coins": {"$sum": "$coins_earned"},
            }}
        ]
        result = await self.db.predictions_v2.aggregate(pipeline).to_list(1)
        if not result:
            return {"total": 0, "correct": 0, "accuracy": 0, "total_coins": 0}
        r = result[0]
        return {
            "total": r["total"],
            "correct": r["correct"],
            "accuracy": round(r["correct"] / r["total"] * 100, 1) if r["total"] > 0 else 0,
            "total_coins": r["total_coins"],
        }

    # ── Audit Log ──

    async def _audit(self, action: str, data: Dict):
        await self.db.prediction_audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "action": action,
            "prediction_id": data.get("id"),
            "user_id": data.get("user_id"),
            "match_id": data.get("match_id"),
            "data": {k: v for k, v in data.items() if k != "_id"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
