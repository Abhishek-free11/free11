"""
Redis Caching Layer for FREE11
Caches EntitySport API responses with configurable TTLs.
Logs cache hit/miss ratio.
"""
import os
import json
import logging
import time
from typing import Optional
import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL")  # None if not configured — Redis disabled gracefully

TTL_MATCH_LIST = 60       # 60s for match listings
TTL_MATCH_INFO = 30       # 30s for match info
TTL_LIVE = 5              # 5s for live endpoints
TTL_SCORECARD = 60        # 60s for scorecards
TTL_SQUADS = 86400        # 24h for squad data
TTL_COMPETITIONS = 3600   # 1h for competitions

_hits = 0
_misses = 0


def _get_client() -> redis.Redis:
    return redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)


_client: Optional[redis.Redis] = None
_connection_failed: bool = False  # Avoid spam-reconnecting after first failure


def get_redis() -> Optional[redis.Redis]:
    global _client, _connection_failed
    if not REDIS_URL:
        return None  # Redis not configured — skip entirely, no connection attempt
    if _connection_failed:
        return None
    if _client is None:
        try:
            _client = _get_client()
            _client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _client = None
            _connection_failed = True  # Stop retrying — will be None for this process lifetime
    return _client


def cache_get(key: str) -> Optional[dict]:
    global _hits, _misses
    r = get_redis()
    if not r:
        _misses += 1
        return None
    try:
        data = r.get(key)
        if data:
            _hits += 1
            return json.loads(data)
        _misses += 1
        return None
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
        _misses += 1
        return None


def cache_set(key: str, value, ttl: int = 60):
    r = get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"Cache set error: {e}")


def cache_delete(pattern: str):
    r = get_redis()
    if not r:
        return
    try:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception:
        pass


def get_cache_stats() -> dict:
    total = _hits + _misses
    return {
        "hits": _hits,
        "misses": _misses,
        "total": total,
        "hit_rate": round(_hits / total * 100, 1) if total > 0 else 0,
    }
