"""
EntitySport Live Data Service for FREE11
Uses REAL API data from EntitySport Pro plan.
Redis-cached: match list 60s, info 30s, live 5s, scorecard 60s, squads 24h.
"""
import os
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis_cache import cache_get, cache_set, TTL_MATCH_LIST, TTL_MATCH_INFO, TTL_LIVE, TTL_SCORECARD, TTL_SQUADS, TTL_COMPETITIONS

logger = logging.getLogger(__name__)

BASE_URL = "https://rest.entitysport.com/v2"
TOKEN = os.environ.get("ENTITYSPORT_TOKEN", "")


class EntitySportService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.token = TOKEN

    def _url(self, path: str, **params) -> str:
        qs = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        sep = "&" if "?" in path else "?"
        return f"{BASE_URL}{path}{sep}token={self.token}&{qs}" if qs else f"{BASE_URL}{path}?token={self.token}"

    async def _get(self, path: str, **params) -> Optional[Dict]:
        url = self._url(path, **params)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"EntitySport {resp.status_code}: {path}")
                    return None
                data = resp.json()
                if data.get("status") != "ok":
                    logger.warning(f"EntitySport not ok: {path} -> {data.get('status')}")
                    return None
                return data.get("response", {})
        except Exception as e:
            logger.error(f"EntitySport request failed: {path} -> {e}")
            return None

    async def _cached_get(self, cache_key: str, ttl: int, path: str, **params) -> Optional[Dict]:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
        data = await self._get(path, **params)
        if data is not None:
            cache_set(cache_key, data, ttl)
        return data

    # ── Matches ──

    async def get_matches(self, status: str = "3", per_page: int = 20) -> List[Dict]:
        """Get matches by status: 1=upcoming, 2=completed, 3=live"""
        cache_key = f"es:matches:{status}:{per_page}"
        ttl = TTL_LIVE if status == "3" else TTL_MATCH_LIST
        data = await self._cached_get(cache_key, ttl, "/matches", status=status, per_page=str(per_page))
        if not data:
            return []
        items = data.get("items", [])
        return [self._transform_match(m) for m in items]

    async def get_match_info(self, match_id: str) -> Optional[Dict]:
        cache_key = f"es:info:{match_id}"
        data = await self._cached_get(cache_key, TTL_MATCH_INFO, f"/matches/{match_id}/info")
        if not data:
            return None
        return self._transform_match(data)

    async def get_match_live(self, match_id: str) -> Optional[Dict]:
        cache_key = f"es:live:{match_id}"
        data = await self._cached_get(cache_key, TTL_LIVE, f"/matches/{match_id}/live")
        if not data:
            return None
        return self._transform_live(data)

    async def get_match_scorecard(self, match_id: str) -> Optional[Dict]:
        cache_key = f"es:scorecard:{match_id}"
        return await self._cached_get(cache_key, TTL_SCORECARD, f"/matches/{match_id}/scorecard")

    async def get_match_squads(self, match_id: str) -> Optional[Dict]:
        """Get squads with full player details - used for fantasy team building"""
        cache_key = f"es:squads:{match_id}"
        data = await self._cached_get(cache_key, TTL_SQUADS, f"/matches/{match_id}/squads")
        if not data:
            return None
        return self._transform_squads(data)

    async def get_competitions(self, status: str = "live") -> List[Dict]:
        cache_key = f"es:competitions:{status}"
        data = await self._cached_get(cache_key, TTL_COMPETITIONS, "/competitions", status=status)
        if not data:
            return []
        return data.get("items", []) if isinstance(data, dict) else data

    # ── Transform helpers ──

    def _transform_match(self, m: Dict) -> Dict:
        teama = m.get("teama", {})
        teamb = m.get("teamb", {})
        competition = m.get("competition", {})

        status_num = m.get("status")
        status_map = {1: "upcoming", 2: "completed", 3: "live"}
        status = status_map.get(status_num, str(status_num)) if isinstance(status_num, int) else str(status_num)

        return {
            "match_id": str(m.get("match_id", "")),
            "title": m.get("title", ""),
            "short_title": m.get("short_title", ""),
            "status": status,
            "status_note": m.get("status_note", ""),
            "match_type": m.get("format_str", m.get("format", "")),
            "series": competition.get("title", ""),
            "series_id": str(competition.get("cid", "")),
            "venue": m.get("venue", {}).get("name", "") if isinstance(m.get("venue"), dict) else str(m.get("venue", "")),
            "match_date": m.get("date_start_ist", m.get("date_start", "")),
            "team1": teama.get("name", ""),
            "team1_short": teama.get("short_name", ""),
            "team1_id": str(teama.get("team_id", "")),
            "team1_logo": teama.get("logo_url", ""),
            "team1_score": teama.get("scores_full", teama.get("scores", "")),
            "team2": teamb.get("name", ""),
            "team2_short": teamb.get("short_name", ""),
            "team2_id": str(teamb.get("team_id", "")),
            "team2_logo": teamb.get("logo_url", ""),
            "team2_score": teamb.get("scores_full", teamb.get("scores", "")),
            "toss": m.get("toss", {}) if isinstance(m.get("toss"), dict) else {},
            "source": "entitysport",
        }

    def _transform_live(self, data: Dict) -> Dict:
        match = self._transform_match(data)
        live_score = data.get("live_score", {})
        match.update({
            "current_ball": f"{live_score.get('overs', '0')}" if live_score else "0.0",
            "batting_team": live_score.get("batting_team_id", "") if live_score else "",
            "current_run_rate": live_score.get("runrate", "") if live_score else "",
            "required_run_rate": live_score.get("required_runrate", "") if live_score else "",
            "batsmen": data.get("batsmen", []),
            "bowlers": data.get("bowlers", []),
            "last_wicket": data.get("live_innings", {}).get("last_wicket", "") if isinstance(data.get("live_innings"), dict) else "",
            "recent_scores": live_score.get("recent_scores", "") if live_score else "",
        })
        return match

    def _transform_squads(self, data: Dict) -> Dict:
        teama = data.get("teama", {})
        teamb = data.get("teamb", {})
        teams_list = data.get("teams", [])
        players_list = data.get("players", [])

        # Build team name lookup from teams list
        team_names = {}
        for t in teams_list:
            tid = str(t.get("tid", t.get("team_id", "")))
            team_names[tid] = t.get("title", t.get("name", f"Team {tid}"))

        player_details = {}
        for p in players_list:
            pid = str(p.get("pid", ""))
            raw_role = (p.get("playing_role", "bat") or "bat").lower().strip()
            # Normalize to standard keys
            if raw_role in ("wk", "wkbat", "keeper", "wicketkeeper", "wicket-keeper"):
                norm_role = "wk"
            elif raw_role in ("bat", "batsman", "batter", "top"):
                norm_role = "bat"
            elif raw_role in ("all", "allrounder", "all-rounder", "ar"):
                norm_role = "all"
            elif raw_role in ("bowl", "bowler", "bowling"):
                norm_role = "bowl"
            else:
                norm_role = "bat"
            player_details[pid] = {
                "id": pid,
                "name": p.get("title", p.get("short_name", "")),
                "short_name": p.get("short_name", ""),
                "role": norm_role,
                "batting_style": p.get("batting_style", ""),
                "bowling_style": p.get("bowling_style", ""),
                "nationality": p.get("nationality", p.get("country", "")),
                "logo": p.get("logo_url", p.get("thumb_url", "")),
                "fantasy_rating": p.get("fantasy_player_rating", 7),
            }

        team_a_id = str(teama.get("team_id", ""))
        team_b_id = str(teamb.get("team_id", ""))
        team_a_name = team_names.get(team_a_id, teama.get("name", teama.get("title", "Team A")))
        team_b_name = team_names.get(team_b_id, teamb.get("name", teamb.get("title", "Team B")))

        def normalize_role(raw_role: str) -> str:
            """Normalize EntitySport role values to standard keys: wk, bat, all, bowl"""
            r = (raw_role or "bat").lower().strip()
            if r in ("wk", "wkbat", "keeper", "wicketkeeper", "wicket-keeper"):
                return "wk"
            if r in ("bat", "batsman", "batter", "top"):
                return "bat"
            if r in ("all", "allrounder", "all-rounder", "ar"):
                return "all"
            if r in ("bowl", "bowler", "bowling"):
                return "bowl"
            return "bat"  # default fallback

        def build_squad(team_data, team_name):
            squad = []
            for s in team_data.get("squads", []):
                pid = str(s.get("player_id", ""))
                details = player_details.get(pid, {})
                raw_role = s.get("role", details.get("role", "bat"))
                role = normalize_role(raw_role)
                is_playing = s.get("playing11", "false") == "true"
                rating = details.get("fantasy_rating", 7)
                # Dream11-style credit distribution: wider range for better team-building
                # Role-based modifier: star batsmen/WK cost more, bowlers slightly less
                role_mod = {"wk": 0.3, "bat": 0.2, "all": 0.0, "bowl": -0.2}.get(role, 0)
                base = 2.5 + (float(rating) if rating else 7) * 0.8 + role_mod
                credit = round(max(6.0, min(10.5, base)), 1)

                squad.append({
                    "player_id": pid,
                    "name": details.get("name", s.get("name", "")),
                    "short_name": details.get("short_name", s.get("name", "")),
                    "role": role,
                    "role_str": s.get("role_str", f"({role.upper()})"),
                    "team": team_name,
                    "playing11": is_playing,
                    "credit": credit,
                    "batting_style": details.get("batting_style", ""),
                    "bowling_style": details.get("bowling_style", ""),
                    "logo": details.get("logo", ""),
                })
            return squad

        return {
            "team_a": {
                "team_id": team_a_id,
                "name": team_a_name,
                "squad": build_squad(teama, team_a_name),
            },
            "team_b": {
                "team_id": team_b_id,
                "name": team_b_name,
                "squad": build_squad(teamb, team_b_name),
            },
            "all_players": list(player_details.values()),
        }

    # ── Sync to DB ──

    async def sync_matches(self, statuses=("1", "3")) -> int:
        count = 0
        for status in statuses:
            matches = await self.get_matches(status=status, per_page=50)
            for m in matches:
                await self.db.matches.update_one(
                    {"match_id": m["match_id"]},
                    {"$set": m},
                    upsert=True,
                )
                count += 1
        logger.info(f"EntitySport sync: {count} matches synced")
        return count

    async def sync_live_data(self, match_id: str) -> Optional[Dict]:
        live = await self.get_match_live(match_id)
        if live:
            await self.db.matches.update_one(
                {"match_id": match_id},
                {"$set": live},
                upsert=True,
            )
        return live
