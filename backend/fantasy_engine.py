"""
Fantasy Team Engine for FREE11
Dream11-style team builder with real EntitySport data.
Credit system, Captain/VC, role constraints, points calculation from scorecard.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# ── Team Constraints ──
TEAM_SIZE = 11
MAX_CREDITS = 100.0
ROLE_CONSTRAINTS = {
    "wk": {"min": 1, "max": 4, "label": "Wicket-keeper"},
    "bat": {"min": 3, "max": 6, "label": "Batsman"},
    "all": {"min": 1, "max": 4, "label": "All-rounder"},
    "bowl": {"min": 3, "max": 6, "label": "Bowler"},
}
MAX_PER_TEAM = 7  # Max players from a single real team

# ── Fantasy Points System ──
POINTS = {
    # Batting
    "run": 1,
    "boundary_bonus": 1,       # per 4
    "six_bonus": 2,            # per 6
    "half_century": 20,
    "century": 50,
    "duck": -5,                # 0 runs (bat only, not bowl)
    "thirty_bonus": 8,         # 30+ runs
    # Bowling
    "wicket": 25,
    "maiden": 12,
    "three_wickets": 15,       # 3+ wickets bonus
    "five_wickets": 30,        # 5+ wickets bonus
    "economy_bonus_good": 6,   # econ < 5 (min 2 overs)
    "economy_bonus_avg": 4,    # econ 5-6
    "economy_penalty_bad": -4, # econ 10-11
    "economy_penalty_awful": -6, # econ > 11
    # Fielding
    "catch": 10,
    "stumping": 15,
    "runout_direct": 15,
    "runout_indirect": 10,
    # Captain / VC multipliers
    "captain_multiplier": 2.0,
    "vc_multiplier": 1.5,
}


class FantasyEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ── Team Validation ──

    def validate_team(self, players: List[Dict], captain_id: str, vc_id: str) -> Dict:
        """Validate a fantasy team against all constraints"""
        errors = []

        if len(players) != TEAM_SIZE:
            errors.append(f"Team must have exactly {TEAM_SIZE} players, got {len(players)}")

        # Credit check
        total_credit = sum(p.get("credit", 0) for p in players)
        if total_credit > MAX_CREDITS:
            errors.append(f"Total credits {total_credit} exceeds max {MAX_CREDITS}")

        # Role constraints
        roles = {}
        for p in players:
            r = p.get("role", "bat")
            roles.setdefault(r, []).append(p)

        for role, constraints in ROLE_CONSTRAINTS.items():
            count = len(roles.get(role, []))
            if count < constraints["min"]:
                errors.append(f"Need at least {constraints['min']} {constraints['label']}, got {count}")
            if count > constraints["max"]:
                errors.append(f"Max {constraints['max']} {constraints['label']}, got {count}")

        # Max per team
        teams = {}
        for p in players:
            t = p.get("team", "")
            teams.setdefault(t, []).append(p)
        for t, plist in teams.items():
            if len(plist) > MAX_PER_TEAM:
                errors.append(f"Max {MAX_PER_TEAM} from {t}, got {len(plist)}")

        # Captain/VC must be in team
        pids = {p.get("player_id") for p in players}
        if captain_id not in pids:
            errors.append("Captain must be in your team")
        if vc_id not in pids:
            errors.append("Vice-Captain must be in your team")
        if captain_id == vc_id:
            errors.append("Captain and Vice-Captain must be different")

        return {"valid": len(errors) == 0, "errors": errors}

    # ── Create Team ──

    async def create_team(
        self,
        user_id: str,
        match_id: str,
        players: List[Dict],
        captain_id: str,
        vc_id: str,
    ) -> Dict:
        """Create a fantasy team after validation"""
        validation = self.validate_team(players, captain_id, vc_id)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))

        # Check match hasn't started
        match = await self.db.matches.find_one({"match_id": match_id}, {"_id": 0})
        if match and match.get("status") in ("live", "completed", "abandoned"):
            raise ValueError("Cannot create team: match already started/completed")

        # Check team limit per user per match (max 3 teams)
        existing = await self.db.fantasy_teams.count_documents(
            {"user_id": user_id, "match_id": match_id}
        )
        if existing >= 3:
            raise ValueError("Max 3 teams per match")

        now = datetime.now(timezone.utc).isoformat()
        team = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "match_id": match_id,
            "players": [
                {
                    "player_id": p["player_id"],
                    "name": p.get("name", ""),
                    "role": p.get("role", ""),
                    "team": p.get("team", ""),
                    "credit": p.get("credit", 0),
                    "is_captain": p["player_id"] == captain_id,
                    "is_vc": p["player_id"] == vc_id,
                }
                for p in players
            ],
            "captain_id": captain_id,
            "vc_id": vc_id,
            "total_credits": round(sum(p.get("credit", 0) for p in players), 1),
            "total_points": 0,
            "points_breakdown": {},
            "status": "active",
            "locked": False,
            "created_at": now,
            "updated_at": now,
        }

        await self.db.fantasy_teams.insert_one(team)
        logger.info(f"FANTASY TEAM: user={user_id} match={match_id} team={team['id']}")
        return {k: v for k, v in team.items() if k != "_id"}

    # ── Lock Teams ──

    async def lock_teams_for_match(self, match_id: str) -> int:
        result = await self.db.fantasy_teams.update_many(
            {"match_id": match_id, "locked": False},
            {"$set": {"locked": True, "status": "locked", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count

    # ── Points Calculation ──

    async def calculate_points(self, match_id: str, scorecard: Dict) -> List[Dict]:
        """Calculate fantasy points for all teams in a match using real scorecard data"""
        teams = await self.db.fantasy_teams.find(
            {"match_id": match_id, "status": {"$in": ["active", "locked"]}},
            {"_id": 0}
        ).to_list(10000)

        if not teams:
            return []

        # Build player performance map from scorecard
        perf = self._extract_performance(scorecard)

        results = []
        for team in teams:
            total = 0
            breakdown = {}

            for tp in team["players"]:
                pid = tp["player_id"]
                player_perf = perf.get(pid, {})
                pts = self._calc_player_points(player_perf)

                # Apply C/VC multiplier
                if tp.get("is_captain"):
                    pts = int(pts * POINTS["captain_multiplier"])
                elif tp.get("is_vc"):
                    pts = int(pts * POINTS["vc_multiplier"])

                breakdown[pid] = {
                    "name": tp.get("name", ""),
                    "points": pts,
                    "is_captain": tp.get("is_captain", False),
                    "is_vc": tp.get("is_vc", False),
                    "perf": player_perf,
                }
                total += pts

            # Update team
            await self.db.fantasy_teams.update_one(
                {"id": team["id"]},
                {"$set": {
                    "total_points": total,
                    "points_breakdown": breakdown,
                    "status": "scored",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }}
            )

            results.append({
                "team_id": team["id"],
                "user_id": team["user_id"],
                "total_points": total,
            })

        logger.info(f"FANTASY SCORING: match={match_id} teams_scored={len(results)}")
        return sorted(results, key=lambda x: -x["total_points"])

    def _extract_performance(self, scorecard: Dict) -> Dict:
        """Extract per-player performance from EntitySport scorecard"""
        perf = {}
        innings_list = scorecard.get("innings", [])

        for inn in innings_list:
            # Batting
            for b in inn.get("batsmen", []):
                pid = str(b.get("batsman_id", ""))
                if not pid:
                    continue
                perf.setdefault(pid, {})
                perf[pid]["runs"] = perf[pid].get("runs", 0) + int(b.get("runs", 0))
                perf[pid]["balls"] = perf[pid].get("balls", 0) + int(b.get("balls_faced", 0))
                perf[pid]["fours"] = perf[pid].get("fours", 0) + int(b.get("fours", 0))
                perf[pid]["sixes"] = perf[pid].get("sixes", 0) + int(b.get("sixes", 0))
                perf[pid]["how_out"] = b.get("how_out", "")
                perf[pid]["did_bat"] = True

            # Bowling
            for bw in inn.get("bowlers", []):
                pid = str(bw.get("bowler_id", ""))
                if not pid:
                    continue
                perf.setdefault(pid, {})
                perf[pid]["overs_bowled"] = perf[pid].get("overs_bowled", 0) + float(bw.get("overs", 0))
                perf[pid]["wickets"] = perf[pid].get("wickets", 0) + int(bw.get("wickets", 0))
                perf[pid]["runs_conceded"] = perf[pid].get("runs_conceded", 0) + int(bw.get("runs_conceded", 0))
                perf[pid]["maidens"] = perf[pid].get("maidens", 0) + int(bw.get("maidens", 0))
                econ_str = bw.get("econ", "0")
                perf[pid]["economy"] = float(econ_str) if econ_str else 0
                perf[pid]["did_bowl"] = True

            # Fielding
            for f in inn.get("fielder", []):
                pid = str(f.get("fielder_id", ""))
                if not pid:
                    continue
                perf.setdefault(pid, {})
                perf[pid]["catches"] = perf[pid].get("catches", 0) + int(f.get("catches", 0))
                perf[pid]["stumpings"] = perf[pid].get("stumpings", 0) + int(f.get("stumping", 0) or 0)
                perf[pid]["runout_direct"] = perf[pid].get("runout_direct", 0) + int(f.get("runout_direct_hit", 0) or 0)
                perf[pid]["runout_indirect"] = perf[pid].get("runout_indirect", 0) + int(f.get("runout_thrower", 0) or 0)

        return perf

    def _calc_player_points(self, perf: Dict) -> int:
        """Calculate points for a single player"""
        pts = 0

        # Batting
        runs = perf.get("runs", 0)
        pts += runs * POINTS["run"]
        pts += perf.get("fours", 0) * POINTS["boundary_bonus"]
        pts += perf.get("sixes", 0) * POINTS["six_bonus"]
        if runs >= 100:
            pts += POINTS["century"]
        elif runs >= 50:
            pts += POINTS["half_century"]
        elif runs >= 30:
            pts += POINTS["thirty_bonus"]
        if perf.get("did_bat") and runs == 0 and perf.get("how_out") and perf.get("how_out") != "not out":
            pts += POINTS["duck"]

        # Bowling
        wickets = perf.get("wickets", 0)
        pts += wickets * POINTS["wicket"]
        pts += perf.get("maidens", 0) * POINTS["maiden"]
        if wickets >= 5:
            pts += POINTS["five_wickets"]
        elif wickets >= 3:
            pts += POINTS["three_wickets"]
        # Economy bonus/penalty (min 2 overs)
        overs = perf.get("overs_bowled", 0)
        econ = perf.get("economy", 0)
        if overs >= 2 and econ > 0:
            if econ < 5:
                pts += POINTS["economy_bonus_good"]
            elif econ <= 6:
                pts += POINTS["economy_bonus_avg"]
            elif 10 <= econ <= 11:
                pts += POINTS["economy_penalty_bad"]
            elif econ > 11:
                pts += POINTS["economy_penalty_awful"]

        # Fielding
        pts += perf.get("catches", 0) * POINTS["catch"]
        pts += perf.get("stumpings", 0) * POINTS["stumping"]
        pts += perf.get("runout_direct", 0) * POINTS["runout_direct"]
        pts += perf.get("runout_indirect", 0) * POINTS["runout_indirect"]

        return pts

    # ── Query ──

    async def get_user_teams(self, user_id: str, match_id: Optional[str] = None) -> List[Dict]:
        query = {"user_id": user_id}
        if match_id:
            query["match_id"] = match_id
        return await self.db.fantasy_teams.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)

    async def get_team(self, team_id: str) -> Optional[Dict]:
        return await self.db.fantasy_teams.find_one({"id": team_id}, {"_id": 0})

    async def get_match_rankings(self, match_id: str) -> List[Dict]:
        """Get fantasy rankings for a match"""
        teams = await self.db.fantasy_teams.find(
            {"match_id": match_id, "status": {"$in": ["active", "locked", "scored"]}},
            {"_id": 0}
        ).sort("total_points", -1).to_list(10000)

        for i, t in enumerate(teams):
            t["rank"] = i + 1
            user = await self.db.users.find_one({"id": t["user_id"]}, {"_id": 0, "name": 1})
            t["user_name"] = user.get("name", "Unknown") if user else "Unknown"

        return teams

    async def compare_teams(self, team_id_1: str, team_id_2: str) -> Dict:
        """Compare two fantasy teams"""
        t1 = await self.get_team(team_id_1)
        t2 = await self.get_team(team_id_2)
        if not t1 or not t2:
            raise ValueError("Team not found")

        p1 = {p["player_id"] for p in t1["players"]}
        p2 = {p["player_id"] for p in t2["players"]}
        common = p1 & p2
        unique_1 = p1 - p2
        unique_2 = p2 - p1

        return {
            "team_1": {"id": t1["id"], "points": t1.get("total_points", 0), "captain": t1.get("captain_id"), "vc": t1.get("vc_id")},
            "team_2": {"id": t2["id"], "points": t2.get("total_points", 0), "captain": t2.get("captain_id"), "vc": t2.get("vc_id")},
            "common_players": len(common),
            "unique_to_team_1": len(unique_1),
            "unique_to_team_2": len(unique_2),
        }
