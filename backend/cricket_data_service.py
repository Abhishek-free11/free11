"""
Cricket Data Service for FREE11
Multi-source with HOT FAILOVER and ICC T20 World Cup prioritization

Sources (in priority order):
1) CricketData.org (Primary - subscribed)
2) Sportmonks (Secondary failover - free tier 180 req/hr)
3) Stale Cache (1 hour fallback)
4) NO MOCK DATA - Shows proper error message

Hot Failover Logic:
- Primary fails -> Instantly switch to Secondary (Sportmonks free)
- Both fail -> Use stale cache if < 1 hour old
- All fail -> Show "No data available" error
- Primary recovers -> Auto-switch back on next request
"""

import os
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
import logging
import json
import re
import asyncio

logger = logging.getLogger(__name__)

# Primary API - CricketData.org (subscribed)
CRICKET_API_KEY = os.environ.get('CRICKET_API_KEY')
CRICKET_API_BASE = "https://api.cricapi.com/v1"

# Secondary API - Sportmonks (FREE tier: 180 requests/hour)
SPORTMONKS_API_TOKEN = os.environ.get('SPORTMONKS_API_TOKEN')
SPORTMONKS_API_BASE = "https://cricket.sportmonks.com/api/v2.0"

# File-based cache - 2 SECONDS for live data (strict for integrity)
CACHE_FILE = "/tmp/cricket_api_cache.json"
CACHE_DURATION = 2  # 2 seconds for live match data

# Fallback cache - DISABLED for live matches (5 min for non-live only)
FALLBACK_CACHE_FILE = "/tmp/cricket_fallback_cache.json"
FALLBACK_CACHE_DURATION = 300  # Only used for non-live data
FALLBACK_ENABLED_FOR_LIVE = False  # NO stale fallback during live matches

# API health tracking for smart failover
API_HEALTH_FILE = "/tmp/cricket_api_health.json"
API_FAILURE_THRESHOLD = 3  # failures before marking unhealthy
API_RECOVERY_TIME = 300  # seconds before retrying failed API


class CricketDataService:
    """Service to fetch live cricket match data with HOT FAILOVER (NO MOCK DATA)"""
    
    def __init__(self):
        self.primary_api_key = CRICKET_API_KEY
        self.sportmonks_token = SPORTMONKS_API_TOKEN
        self.client = None
        self._api_health = self._load_api_health()
        
    async def _get_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=10.0)  # Reduced timeout for faster failover
        return self.client
    
    def _load_api_health(self) -> Dict:
        """Load API health status from file"""
        try:
            if os.path.exists(API_HEALTH_FILE):
                with open(API_HEALTH_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            'primary': {'failures': 0, 'last_failure': 0, 'healthy': True},
            'sportmonks': {'failures': 0, 'last_failure': 0, 'healthy': True}
        }
    
    def _save_api_health(self):
        """Save API health status to file"""
        try:
            with open(API_HEALTH_FILE, 'w') as f:
                json.dump(self._api_health, f)
        except Exception as e:
            logger.error(f"Failed to save API health: {e}")
    
    def _mark_api_failure(self, api_name: str):
        """Mark an API as having failed"""
        now = datetime.now(timezone.utc).timestamp()
        health = self._api_health.get(api_name, {'failures': 0, 'last_failure': 0, 'healthy': True})
        health['failures'] = health.get('failures', 0) + 1
        health['last_failure'] = now
        if health['failures'] >= API_FAILURE_THRESHOLD:
            health['healthy'] = False
            logger.warning(f"API {api_name} marked UNHEALTHY after {health['failures']} failures")
        self._api_health[api_name] = health
        self._save_api_health()
    
    def _mark_api_success(self, api_name: str):
        """Mark an API as healthy after successful request"""
        self._api_health[api_name] = {'failures': 0, 'last_failure': 0, 'healthy': True}
        self._save_api_health()
    
    def _is_api_available(self, api_name: str) -> bool:
        """Check if an API should be tried (healthy or recovery time passed)"""
        health = self._api_health.get(api_name, {'healthy': True, 'last_failure': 0})
        if health.get('healthy', True):
            return True
        # Check if recovery time has passed
        now = datetime.now(timezone.utc).timestamp()
        if now - health.get('last_failure', 0) > API_RECOVERY_TIME:
            logger.info(f"API {api_name} recovery time passed, will retry")
            return True
        return False
    
    def get_failover_status(self) -> Dict:
        """Get current failover status for admin monitoring"""
        return {
            'primary': {
                'name': 'CricketData.org',
                'configured': bool(self.primary_api_key),
                **self._api_health.get('primary', {'healthy': True, 'failures': 0})
            },
            'sportmonks': {
                'name': 'Sportmonks (Free Tier)',
                'configured': bool(self.sportmonks_token),
                **self._api_health.get('sportmonks', {'healthy': True, 'failures': 0})
            }
        }
    
    def _get_cached_data(self) -> Optional[Dict]:
        """Get cached data if still valid (5 min cache)"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    age = datetime.now(timezone.utc).timestamp() - cache.get('timestamp', 0)
                    if age < CACHE_DURATION:
                        logger.info(f"Returning cached cricket data (age: {int(age)}s)")
                        return cache.get('data')
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        return None
    
    def _get_fallback_cache(self) -> Optional[Dict]:
        """Get older fallback cache when all APIs fail"""
        try:
            if os.path.exists(FALLBACK_CACHE_FILE):
                with open(FALLBACK_CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    age = datetime.now(timezone.utc).timestamp() - cache.get('timestamp', 0)
                    if age < FALLBACK_CACHE_DURATION:
                        logger.info(f"Using fallback cache (age: {int(age/60)} min)")
                        data = cache.get('data', {})
                        matches = data.get('matches', [])
                        for m in matches:
                            m['is_stale'] = True
                            m['stale_age_minutes'] = int(age / 60)
                        return data
        except Exception as e:
            logger.error(f"Fallback cache read error: {e}")
        return None
    
    def _save_cache(self, data: Dict):
        """Save data to both primary and fallback cache"""
        try:
            now = datetime.now(timezone.utc).timestamp()
            cache_data = {'timestamp': now, 'data': data}
            
            # Primary cache (5 min TTL)
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f)
            
            # Fallback cache (1 hour TTL) - only save real data, not mock
            if data.get('matches') and not data['matches'][0].get('is_mock'):
                with open(FALLBACK_CACHE_FILE, 'w') as f:
                    json.dump(cache_data, f)
                    
        except Exception as e:
            logger.error(f"Cache write error: {e}")
        
    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """Get list of live/current matches with HOT FAILOVER (NO STALE FALLBACK FOR LIVE)"""
        
        # Check primary cache first (2 sec)
        cached = self._get_cached_data()
        if cached:
            return cached.get('matches', [])
        
        # HOT FAILOVER: Try APIs in order, with health-aware routing
        matches = None
        source_used = None
        
        # Source 1: Primary API (CricketData.org - your subscription)
        if self.primary_api_key and self._is_api_available('primary'):
            try:
                matches = await self._fetch_from_cricketdata(self.primary_api_key)
                if matches:
                    self._mark_api_success('primary')
                    source_used = 'primary'
                    logger.info(f"✓ PRIMARY API: {len(matches)} matches from CricketData.org")
            except Exception as e:
                self._mark_api_failure('primary')
                logger.warning(f"✗ PRIMARY API failed: {e}")
        
        # Source 2: Sportmonks FREE tier (instant failover)
        if not matches and self.sportmonks_token and self._is_api_available('sportmonks'):
            try:
                matches = await self._fetch_from_sportmonks()
                if matches:
                    self._mark_api_success('sportmonks')
                    source_used = 'sportmonks'
                    logger.info(f"✓ SPORTMONKS (failover): {len(matches)} matches")
            except Exception as e:
                self._mark_api_failure('sportmonks')
                logger.warning(f"✗ SPORTMONKS API failed: {e}")
        
        # If we got matches from any API, cache and return
        if matches:
            for m in matches:
                m['failover_source'] = source_used
            self._save_cache({'matches': matches})
            return matches
        
        # NO STALE FALLBACK FOR LIVE DATA - return empty for integrity
        # Stale data during live matches can cause prediction integrity issues
        if not FALLBACK_ENABLED_FOR_LIVE:
            logger.warning("✗ ALL APIs FAILED - No stale fallback (integrity mode)")
            return []
        
        # Fallback only for non-live scenarios (match lists, etc.)
        fallback = self._get_fallback_cache()
        if fallback and fallback.get('matches'):
            matches = fallback['matches']
            for m in matches:
                m['source'] = 'cached_stale'
                m['failover_source'] = 'stale_cache'
                m['is_mock'] = False
            self._save_cache({'matches': matches})
            logger.info(f"⚠ STALE CACHE: Using {len(matches)} cached matches")
            return matches
        
        # NO MOCK DATA - Return empty list with proper error handling
        logger.error("✗ ALL DATA SOURCES UNAVAILABLE - No matches to show")
        return []
    
    async def _fetch_from_sportmonks(self) -> List[Dict[str, Any]]:
        """Fetch from Sportmonks FREE tier API (180 req/hour)"""
        client = await self._get_client()
        
        response = await client.get(
            f"{SPORTMONKS_API_BASE}/livescores",
            params={
                "api_token": self.sportmonks_token,
                "include": "batting,bowling,runs"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        matches = []
        for match in data.get("data", []):
            localteam = match.get("localteam", {})
            visitorteam = match.get("visitorteam", {})
            
            # Get scores from runs data
            runs = match.get("runs", [])
            team1_score = ""
            team2_score = ""
            for run in runs:
                if run.get("team_id") == localteam.get("id"):
                    team1_score = f"{run.get('score', 0)}/{run.get('wickets', 0)} ({run.get('overs', 0)})"
                elif run.get("team_id") == visitorteam.get("id"):
                    team2_score = f"{run.get('score', 0)}/{run.get('wickets', 0)} ({run.get('overs', 0)})"
            
            status = match.get("status", "").lower()
            if status in ["ns", "not started"]:
                status = "upcoming"
            elif status in ["1st innings", "2nd innings", "innings break"]:
                status = "live"
            elif status in ["finished", "aban.", "abandoned"]:
                status = "completed"
            
            matches.append({
                'id': f"sm_{match.get('id', '')}",
                'match_id': str(match.get('id', '')),
                'team1': localteam.get('name', 'Team A'),
                'team2': visitorteam.get('name', 'Team B'),
                'team1_short': localteam.get('code', 'TA'),
                'team2_short': visitorteam.get('code', 'TB'),
                'team1_score': team1_score,
                'team2_score': team2_score,
                'status': status,
                'venue': match.get('venue', {}).get('name', 'TBD'),
                'match_type': match.get('type', 'T20').upper(),
                'series_name': match.get('league', {}).get('name', 'Cricket Match'),
                'start_time': match.get('starting_at', ''),
                'source': 'sportmonks_api',
                'is_mock': False
            })
        
        return matches
    
    def _extract_series_info(self, match_name: str) -> tuple:
        """
        Extract series name from match name
        Format: "Team1 vs Team2, Match#, Series Name, Tournament Year"
        Returns: (series_name, is_icc_worldcup, is_ipl)
        """
        is_icc_worldcup = False
        is_ipl = False
        series_name = "Cricket Match"
        
        if not match_name:
            return series_name, is_icc_worldcup, is_ipl
        
        # Check for ICC T20 World Cup
        name_upper = match_name.upper()
        if 'ICC' in name_upper and ('T20' in name_upper or 'WORLD CUP' in name_upper):
            is_icc_worldcup = True
        
        # Check for IPL
        if 'IPL' in name_upper or 'INDIAN PREMIER LEAGUE' in name_upper:
            is_ipl = True
        
        # Extract series from name (format: "Team1 vs Team2, Match#, Series Name")
        parts = match_name.split(',')
        if len(parts) >= 3:
            # Series is typically the 3rd part onwards
            series_parts = parts[2:]
            series_name = ','.join(series_parts).strip()
            
            # If it contains ICC World Cup, prioritize that part
            if is_icc_worldcup:
                for part in series_parts:
                    if 'ICC' in part.upper() or 'WORLD CUP' in part.upper():
                        series_name = part.strip()
                        break
        elif len(parts) == 2:
            series_name = parts[1].strip()
        
        return series_name, is_icc_worldcup, is_ipl
    
    async def _fetch_from_cricketdata(self, api_key: str) -> List[Dict[str, Any]]:
        """Fetch from licensed CricketData.org API with ICC prioritization"""
        client = await self._get_client()
        
        response = await client.get(
            f"{CRICKET_API_BASE}/currentMatches",
            params={"apikey": api_key}
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "success":
            error_msg = data.get('reason', 'Unknown API error')
            if 'limit' in error_msg.lower() or 'quota' in error_msg.lower():
                logger.warning(f"API rate limit reached: {error_msg}")
                raise Exception(f"Rate limit: {error_msg}")
            logger.error(f"CricketData API error: {error_msg}")
            raise Exception(error_msg)
        
        matches = []
        for match in data.get("data", []):
            teams = match.get("teams", [])
            team1 = teams[0] if len(teams) > 0 else "Team A"
            team2 = teams[1] if len(teams) > 1 else "Team B"
            
            # Extract scores properly
            scores = match.get("score", [])
            team1_score = None
            team2_score = None
            
            for score in scores:
                innings = score.get("inning", "")
                runs = score.get('r', 0)
                wickets = score.get('w', 0)
                overs = score.get('o', 0)
                score_str = f"{runs}/{wickets} ({overs})"
                
                # Match team name in innings string
                if team1.lower() in innings.lower():
                    team1_score = score_str
                elif team2.lower() in innings.lower():
                    team2_score = score_str
            
            # Determine match status
            match_started = match.get("matchStarted", False)
            match_ended = match.get("matchEnded", False)
            
            if match_ended:
                status = "completed"
            elif match_started:
                status = "live"
            else:
                status = "upcoming"
            
            # Extract series info from match name
            match_name = match.get('name', f'{team1} vs {team2}')
            series_name, is_icc_worldcup, is_ipl = self._extract_series_info(match_name)
            
            # Priority scoring (lower = higher priority)
            # ICC T20 World Cup Live = 0
            # ICC T20 World Cup Upcoming = 1
            # IPL Live = 2
            # ICC T20 World Cup Completed = 3
            # India matches = 4
            # Other T20 = 5
            # Everything else = 10
            
            priority = 10
            is_india = 'INDIA' in team1.upper() or 'INDIA' in team2.upper()
            is_t20 = match.get('matchType', '').upper() == 'T20'
            
            if is_icc_worldcup:
                if status == 'live':
                    priority = 0
                elif status == 'upcoming':
                    priority = 1
                else:
                    priority = 3
            elif is_ipl:
                if status == 'live':
                    priority = 2
                else:
                    priority = 4
            elif is_india:
                priority = 5
            elif is_t20:
                priority = 6
            
            matches.append({
                'id': match.get('id'),
                'name': match_name,
                'series': series_name,
                'team1': team1,
                'team1_short': self._get_short_name(team1),
                'team2': team2,
                'team2_short': self._get_short_name(team2),
                'status': status,
                'status_text': match.get('status', ''),
                'venue': match.get('venue', 'TBD'),
                'match_type': match.get('matchType', 'T20'),
                'start_time': match.get('dateTimeGMT'),
                'team1_score': team1_score,
                'team2_score': team2_score,
                'source': 'cricketdata_api',
                'is_mock': False,
                'is_icc_worldcup': is_icc_worldcup,
                'is_ipl': is_ipl,
                'priority': priority,
            })
        
        # Sort by priority (ICC T20 World Cup first), then by status (live first)
        status_order = {'live': 0, 'upcoming': 1, 'completed': 2}
        matches.sort(key=lambda x: (x.get('priority', 10), status_order.get(x.get('status'), 3)))
        
        return matches
    
    def _get_short_name(self, team_name: str) -> str:
        """Get short name for a team"""
        if not team_name:
            return "TBD"
        
        abbrevs = {
            'india': 'IND', 'australia': 'AUS', 'england': 'ENG',
            'pakistan': 'PAK', 'south africa': 'SA', 'new zealand': 'NZ',
            'sri lanka': 'SL', 'bangladesh': 'BAN', 'west indies': 'WI',
            'afghanistan': 'AFG', 'ireland': 'IRE', 'zimbabwe': 'ZIM',
            'scotland': 'SCO', 'netherlands': 'NED', 'nepal': 'NEP',
            'usa': 'USA', 'canada': 'CAN', 'oman': 'OMA', 'uae': 'UAE',
            'namibia': 'NAM', 'uganda': 'UGA', 'papua new guinea': 'PNG',
            'hong kong': 'HK', 'kuwait': 'KUW', 'thailand': 'THA',
            'japan': 'JPN', 'bahrain': 'BAH', 'bhutan': 'BHU',
            'chennai super kings': 'CSK', 'mumbai indians': 'MI',
            'royal challengers': 'RCB', 'kolkata knight riders': 'KKR',
            'delhi capitals': 'DC', 'punjab kings': 'PBKS',
            'rajasthan royals': 'RR', 'sunrisers hyderabad': 'SRH',
            'gujarat titans': 'GT', 'lucknow super giants': 'LSG',
            'knights': 'KNI', 'border': 'BOR', 'limpopo': 'LIM',
            'northern cape': 'NC', 'eastern storm': 'ES',
            'mpumalanga rhinos': 'MR', 'south western districts': 'SWD',
        }
        
        team_lower = team_name.lower()
        for key, abbrev in abbrevs.items():
            if key in team_lower:
                return abbrev
        
        # For teams like "South Africa Emerging Players"
        if 'south africa' in team_lower:
            return 'SA'
        
        words = team_name.split()
        if len(words) >= 2:
            return ''.join(w[0].upper() for w in words[:3])
        return team_name[:3].upper()
    
    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()


# Singleton instance
cricket_service = CricketDataService()
