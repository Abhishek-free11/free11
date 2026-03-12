"""
Geo-Fencing Middleware for FREE11
Restricts API access to India-only based on IP address
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import httpx
import logging
import os

logger = logging.getLogger(__name__)

# Environment variable to enable/disable geo-fencing
GEO_FENCE_ENABLED = os.environ.get('GEO_FENCE_ENABLED', 'true').lower() == 'true'

# Allowed countries (ISO 3166-1 alpha-2 codes)
ALLOWED_COUNTRIES = {'IN'}  # India only

# Restricted Indian states (per legal requirements)
RESTRICTED_STATES = {
    'AP',  # Andhra Pradesh
    'AS',  # Assam
    'NL',  # Nagaland
    'OR',  # Odisha
    'SK',  # Sikkim
    'TS',  # Telangana
}

# Paths that should bypass geo-fencing (public routes + infrastructure)
BYPASS_PATHS = {
    '/health',          # Kubernetes health check — MUST bypass (runs from US infra IPs)
    '/api/',
    '/api/health',
    '/api/docs',
    '/api/openapi.json',
    '/api/terms',
    '/api/privacy',
    '/api/about',
}

# Cache for IP lookups to reduce API calls
_ip_cache = {}
_cache_ttl = 3600  # 1 hour cache


async def get_country_from_ip(ip: str) -> dict:
    """Get country info from IP address using free ip-api.com"""
    
    # Check cache first
    if ip in _ip_cache:
        cached = _ip_cache[ip]
        if cached.get('timestamp', 0) > (import_time() - _cache_ttl):
            return cached
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # ip-api.com is free for non-commercial use (45 req/min)
            response = await client.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,region")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    result = {
                        'country_code': data.get('countryCode', ''),
                        'country': data.get('country', ''),
                        'region': data.get('region', ''),
                        'region_name': data.get('regionName', ''),
                        'timestamp': import_time()
                    }
                    _ip_cache[ip] = result
                    return result
    except Exception as e:
        logger.warning(f"IP lookup failed for {ip}: {e}")
    
    return {}


def import_time():
    """Get current timestamp"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).timestamp()


class GeoFenceMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict access based on geographic location"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip if geo-fencing is disabled
        if not GEO_FENCE_ENABLED:
            return await call_next(request)
        
        # Skip for bypass paths
        path = request.url.path
        if any(path.startswith(bypass) for bypass in BYPASS_PATHS):
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Skip localhost/development
        if client_ip in ('127.0.0.1', 'localhost', '::1') or client_ip.startswith('10.') or client_ip.startswith('192.168.'):
            return await call_next(request)
        
        # Lookup country
        geo_info = await get_country_from_ip(client_ip)
        country_code = geo_info.get('country_code', '')
        region_code = geo_info.get('region', '')
        
        # Check if country is allowed
        if country_code and country_code not in ALLOWED_COUNTRIES:
            logger.warning(f"Geo-blocked request from {country_code} (IP: {client_ip})")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "geo_restricted",
                    "message": "FREE11 is currently only available in India.",
                    "country": geo_info.get('country', 'Unknown')
                }
            )
        
        # Check if Indian state is restricted
        if country_code == 'IN' and region_code in RESTRICTED_STATES:
            logger.warning(f"Geo-blocked request from restricted state {region_code} (IP: {client_ip})")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "state_restricted",
                    "message": f"FREE11 is not available in {geo_info.get('region_name', region_code)} due to local regulations.",
                    "state": geo_info.get('region_name', region_code)
                }
            )
        
        # Attach geo info to request state for logging
        request.state.geo_info = geo_info
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        # Check X-Forwarded-For (load balancer/proxy)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            # Take the first IP (original client)
            return forwarded.split(',')[0].strip()
        
        # Check X-Real-IP
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return ''
