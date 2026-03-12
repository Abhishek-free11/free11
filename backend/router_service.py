"""
FREE11 Smart Commerce Router v2
================================
Unified redemption layer that dynamically selects the best provider
(ONDC, Xoxoday, Amazon, Flipkart) for maximum user value per coin.

Scoring formula
---------------
  score = 0.50 × delivery_speed
        + 0.25 × value_score
        + 0.15 × margin_score
        + 0.10 × geo_match

Redis TTL: 600 s for tease responses, 3600 s for demand factors.

Backward-compat exports (used by existing v2_routes.py endpoints):
  get_ration_categories(), get_dynamic_coin_price(), get_demand_factor()
"""

import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple

from providers.ondc_provider import ONDCProvider
from providers.xoxoday_provider import XoxodayRouterProvider
from providers.amazon_provider import AmazonProvider
from providers.flipkart_provider import FlipkartProvider
from providers.reloadly_provider import ReloadlyRouterProvider
from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)

ROUTER_CACHE_TTL = 600   # 10 min for tease scores
ROUTER_MODE = os.environ.get("ROUTER_MODE", "mock")

# ── Provider Registry ─────────────────────────────────────────────────────────
_PROVIDERS: Dict[str, BaseProvider] = {
    "ondc":      ONDCProvider(),
    "xoxoday":   XoxodayRouterProvider(),
    "amazon":    AmazonProvider(),
    "flipkart":  FlipkartProvider(),
    "reloadly":  ReloadlyRouterProvider(),
}

# Provider badge labels (used in tease response for UI display)
_PROVIDER_BADGES = {
    "ondc":      "ONDC",
    "xoxoday":   "INSTANT",
    "amazon":    "AMAZON",
    "flipkart":  "FLIPKART",
    "reloadly":  "RELOADLY",
}


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_provider(
    provider: BaseProvider,
    sku: str,
    geo_state: str,
    min_coin_price: int = 0,
) -> float:
    """
    Compute a 0–1 score for a provider × SKU × geo combination.

    Components
    ----------
    delivery_speed  0 → instant = 1.0; 3-day = 0.0
    value_score     cheapest provider for this SKU = 1.0; 2× price = 0.5
    margin_score    normalised commission (max 0.30 = 1.0)
    geo_match       covered state = 1.0; uncovered = 0.8; digital = 1.0
    """
    eta        = provider.get_eta(sku, geo_state)
    coin_price = provider.get_price(sku)
    margin     = provider.get_margin(sku)

    # Geo match — empty covered_states means all-India digital
    if not provider.covered_states:
        geo_match = 1.0
    else:
        gs = (geo_state or "").upper()
        geo_match = 1.0 if gs in provider.covered_states else 0.8

    # Delivery speed (0 = instant → 1.0; 3 days → 0.0)
    delivery_speed = 1.0 if eta == 0 else max(0.0, 1.0 - eta / 3.0)

    # Value score: cheapest provider gets 1.0; pricier providers < 1.0
    if min_coin_price > 0 and coin_price > 0:
        value_score = min_coin_price / coin_price
    else:
        value_score = 1.0

    # Margin score: normalised to 0-1 (0.30 max commission)
    margin_score = min(1.0, margin / 0.30)

    score = (
        0.50 * delivery_speed
        + 0.25 * value_score
        + 0.15 * margin_score
        + 0.10 * geo_match
    )
    return round(score, 4)


# ── Provider helpers ──────────────────────────────────────────────────────────

def get_providers_for_sku(sku: str) -> List[BaseProvider]:
    return [p for p in _PROVIDERS.values() if p.supports_sku(sku)]


def get_best_provider(
    sku: str, geo_state: str = "MH"
) -> Optional[Tuple[BaseProvider, float]]:
    """
    Return (best_provider, score) for a SKU+geo combination.
    Returns None if no provider supports the SKU.
    """
    candidates = get_providers_for_sku(sku)
    if not candidates:
        return None

    min_coin = min(p.get_price(sku) for p in candidates)
    scored = [
        (p, _score_provider(p, sku, geo_state, min_coin))
        for p in candidates
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0]  # (provider, score)


def _get_sku_display_name(sku: str) -> str:
    for p in _PROVIDERS.values():
        if p.supports_sku(sku):
            for s in p.get_skus():
                if s["sku"] == sku:
                    return s["name"]
    return sku


def _build_eta_label(eta: float) -> str:
    if eta == 0:
        return "Instant"
    if eta < 0.1:
        return f"~{round(eta * 24 * 60)} min"
    if eta < 1:
        return f"~{round(eta * 24)}h"
    return f"{round(eta, 1)}d"


async def _increment_tease_view_mongo(sku: str) -> None:
    """MongoDB fallback counter for tease views when Redis is unavailable."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
        if not mongo_url or not db_name:
            return
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        await db.router_metrics.update_one(
            {"_id": "tease_views"},
            {"$inc": {"count": 1, f"by_sku.{sku}": 1}},
            upsert=True,
        )
    except Exception:
        pass


# ── Aggregated SKU catalogue ──────────────────────────────────────────────────

def get_aggregated_skus() -> List[Dict]:
    """
    Merge all providers' SKU lists.
    Each SKU appears once; lists all providers that carry it.
    """
    seen: Dict[str, Dict] = {}
    for provider in _PROVIDERS.values():
        for item in provider.get_skus():
            sku_key = item["sku"]
            if sku_key not in seen:
                seen[sku_key] = {**item, "all_providers": [provider.provider_id]}
            else:
                seen[sku_key]["all_providers"].append(provider.provider_id)
    return list(seen.values())


# ── Tease ─────────────────────────────────────────────────────────────────────

async def get_router_tease(sku: str = "cola_2l", geo_state: str = "MH") -> Dict:
    """
    Score all providers for this SKU × geo, return ranked options.
    Result is Redis-cached for ROUTER_CACHE_TTL seconds.
    """
    from redis_cache import cache_get, cache_set

    cache_key = f"router_v2:tease:{sku}:{geo_state}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    candidates = get_providers_for_sku(sku)
    if not candidates:
        return {
            "sku": sku,
            "sku_name": sku,
            "geo_state": geo_state,
            "options": [],
            "best": None,
            "best_provider": None,
            "status": "not_found",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    min_coin = min(p.get_price(sku) for p in candidates)
    options = []

    for provider in candidates:
        score      = _score_provider(provider, sku, geo_state, min_coin)
        eta        = provider.get_eta(sku, geo_state)
        coin_price = provider.get_price(sku)
        real_price = provider.get_real_price(sku)

        value_note = "Best value" if coin_price == min_coin else f"₹{real_price:.0f} value"

        options.append({
            "provider_id":   provider.provider_id,
            "provider_name": provider.name,
            "badge":         _PROVIDER_BADGES.get(provider.provider_id, provider.provider_id.upper()),
            "sku":           sku,
            "sku_name":      _get_sku_display_name(sku),
            "coin_price":    coin_price,
            "real_price":    real_price,
            "eta":           eta,
            "eta_label":     _build_eta_label(eta),
            "margin":        provider.get_margin(sku),
            "score":         score,
            "value_note":    value_note,
        })

    options.sort(key=lambda x: x["score"], reverse=True)
    best = options[0] if options else None

    result = {
        "sku":         sku,
        "sku_name":    _get_sku_display_name(sku),
        "geo_state":   geo_state,
        "options":     options,
        "best":        best,
        "best_provider": best["provider_id"] if best else None,
        "status":      "success",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer":  "Prices are indicative. Provider availability varies by location.",
    }

    # Track tease view count for conversion rate KPI
    # Primary: Redis incr; Fallback: MongoDB upsert counter
    try:
        from redis_cache import get_redis
        r = get_redis()
        if r:
            r.incr("router:tease:total_views")
        else:
            # MongoDB fallback counter
            await _increment_tease_view_mongo(sku)
    except Exception:
        pass

    cache_set(cache_key, result, ttl=ROUTER_CACHE_TTL)
    return result


# ── Settle ────────────────────────────────────────────────────────────────────

async def settle_router_order(
    user_id: str,
    sku: str,
    coins_used: int,
    geo_state: str,
    db,
    user_email: str = "",
) -> Dict:
    """
    1. Auto-select best provider for sku × geo.
    2. Execute provider.redeem().
    3. Log to router_orders collection.
    4. Return combined result.
    Coin deduction is handled by the calling route (v2_routes.py).
    """
    best_result = get_best_provider(sku, geo_state)
    if not best_result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No provider available for SKU: {sku}")

    provider, score = best_result
    eta            = provider.get_eta(sku, geo_state)
    min_coin_price = min(p.get_price(sku) for p in get_providers_for_sku(sku))
    coin_price     = provider.get_price(sku)
    value_score    = round(min_coin_price / coin_price, 4) if coin_price > 0 else 1.0

    # Execute fulfilment
    result = await provider.redeem(sku, coins_used, user_id, user_email=user_email)

    order_id = str(uuid.uuid4())
    order_record = {
        "id":              order_id,
        "user_id":         user_id,
        "sku":             sku,
        "provider":        provider.provider_id,
        "provider_name":   provider.name,
        "coins_used":      coins_used,
        "order_status":    result.get("status", "unknown"),
        "result_data":     result,
        "created_at":      datetime.now(timezone.utc).isoformat(),
        "score_used":      score,
        "eta_used":        eta,
        "value_score_used": value_score,
        "geo_state":       geo_state,
    }

    await db.router_orders.insert_one(order_record)
    doc = {k: v for k, v in order_record.items() if k != "_id"}

    # Merge result fields into top-level for convenience
    return {**doc, **result}


# ── Backward-compat exports ───────────────────────────────────────────────────

def get_ration_categories() -> List[Dict]:
    """Legacy: Return grocery SKUs from ONDC provider."""
    ondc = _PROVIDERS["ondc"]
    return [
        {"sku": s["sku"], "name": s["name"], "mrp": s["display_price"],
         "image": s.get("image", "")}
        for s in ondc.get_skus()
    ]


def get_dynamic_coin_price(base_price: int, demand_factor: float = 1.0) -> int:
    return round(base_price * max(0.5, min(3.0, demand_factor)))


async def get_demand_factor(sku: str, db) -> float:
    from redis_cache import cache_get, cache_set

    cache_key = f"demand_factor:{sku}"
    cached = cache_get(cache_key)
    if cached is not None:
        return float(cached)

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent = await db.router_orders.count_documents(
        {"sku": sku, "created_at": {"$gte": cutoff}}
    )

    factor = 1.5 if recent >= 100 else 1.2 if recent >= 50 else 1.0 if recent >= 20 else 0.9
    cache_set(cache_key, str(factor), ttl=3600)
    return factor
