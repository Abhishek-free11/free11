"""
Rate Limiting Middleware for FREE11
Per-IP and per-user rate limiting using Redis (falls back to in-memory).
"""
import os
import time
import logging
from typing import Optional
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from redis_cache import get_redis

logger = logging.getLogger(__name__)

GLOBAL_LIMIT = 120          # 120 req/min per IP
MATCH_LIMIT = 60            # 60 req/min for match endpoints
AUTH_LIMIT = 5              # 5 req/min for auth endpoints
ADMIN_IPS = set()           # Populated from env

MATCH_PREFIXES = ("/api/v2/es/", "/api/v2/matches/", "/api/v2/fantasy/")
AUTH_PREFIXES = ("/api/auth/login", "/api/auth/register", "/api/auth/send-otp")

# In-memory fallback for when Redis is unavailable
_mem_counters: dict = defaultdict(lambda: [0, 0])  # key -> [count, window_start]
_mem_limit = 1000  # max entries before cleanup


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_limit_memory(key: str, limit: int, window: int = 60) -> tuple:
    """In-memory rate limiting fallback"""
    global _mem_counters
    now = int(time.time())
    window_start = (now // window) * window
    entry = _mem_counters[key]
    if entry[1] != window_start:
        entry[0] = 0
        entry[1] = window_start
    entry[0] += 1
    # Cleanup if too many keys
    if len(_mem_counters) > _mem_limit:
        old_keys = [k for k, v in _mem_counters.items() if v[1] < window_start - window]
        for k in old_keys[:100]:
            del _mem_counters[k]
    remaining = max(0, limit - entry[0])
    ttl = window - (now - window_start)
    return (entry[0] <= limit, remaining, ttl)


def _check_limit(key: str, limit: int, window: int = 60) -> tuple:
    r = get_redis()
    if not r:
        return _check_limit_memory(key, limit, window)
    try:
        current = r.incr(key)
        if current == 1:
            r.expire(key, window)
        ttl = r.ttl(key)
        remaining = max(0, limit - current)
        return (current <= limit, remaining, ttl)
    except Exception:
        return _check_limit_memory(key, limit, window)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)

        if path.startswith("/api/health") or path == "/api/":
            return await call_next(request)

        ip = _get_client_ip(request)

        if ip in ("127.0.0.1", "::1") or ip.startswith("10.") or ip.startswith("192.168."):
            return await call_next(request)

        now_min = int(time.time() // 60)

        allowed, remaining, ttl = _check_limit(f"rl:ip:{ip}:{now_min}", GLOBAL_LIMIT)
        if not allowed:
            logger.warning(f"Rate limit exceeded: IP={ip} path={path}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(ttl), "X-RateLimit-Remaining": "0"},
            )

        if any(path.startswith(p) for p in AUTH_PREFIXES):
            auth_ok, auth_rem, auth_ttl = _check_limit(f"rl:auth:{ip}:{now_min}", AUTH_LIMIT)
            if not auth_ok:
                logger.warning(f"Auth rate limit: IP={ip}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many login attempts. Try again in a minute."},
                    headers={"Retry-After": str(auth_ttl)},
                )

        if any(path.startswith(p) for p in MATCH_PREFIXES):
            match_ok, match_rem, match_ttl = _check_limit(f"rl:match:{ip}:{now_min}", MATCH_LIMIT)
            if not match_ok:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many match requests."},
                    headers={"Retry-After": str(match_ttl)},
                )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
