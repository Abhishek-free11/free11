"""
Abstract base provider for FREE11 Smart Commerce Router.
All provider implementations must subclass this.
"""
from abc import ABC, abstractmethod
from typing import List, Dict


class BaseProvider(ABC):
    """
    Contract every commerce provider must fulfil.

    Attributes
    ----------
    name          Human-readable display name  ("ONDC Network", "Xoxoday Plum", …)
    provider_id   Short slug used as dict key  ("ondc", "xoxoday", …)
    covered_states
                  List of ISO-3166-2 state codes covered for physical delivery.
                  Empty list means all-India (digital / affiliate providers).
    """

    name: str = "base"
    provider_id: str = "base"
    covered_states: List[str] = []

    # ── Catalogue ──────────────────────────────────────────────────────────────

    @abstractmethod
    def get_skus(self) -> List[Dict]:
        """
        Return all SKUs this provider can fulfil.
        Each dict must have:
          sku, name, coins (int), category (str), provider (str),
          display_price (float, optional – real ₹ price shown to user),
          image (str, optional)
        """

    @abstractmethod
    def supports_sku(self, sku: str) -> bool:
        """Return True if this provider can fulfil the given SKU."""

    # ── Pricing ────────────────────────────────────────────────────────────────

    @abstractmethod
    def get_price(self, sku: str) -> int:
        """Coin cost to redeem this SKU."""

    @abstractmethod
    def get_real_price(self, sku: str) -> float:
        """
        Actual market price (MRP / discounted price) in ₹.
        Used for value scoring: higher real_price per coin = better value.
        """

    # ── Scoring inputs ─────────────────────────────────────────────────────────

    @abstractmethod
    def get_eta(self, sku: str, geo_state: str) -> float:
        """
        Estimated delivery time in days.
        0.0  = instant (voucher / affiliate redirect)
        0.031 ≈ 45 minutes
        1.0  = next day
        """

    @abstractmethod
    def get_margin(self, sku: str) -> float:
        """
        Provider margin / commission fraction (0.0 – 0.30).
        e.g. 0.08 = 8 % affiliate commission.
        """

    # ── Fulfilment ─────────────────────────────────────────────────────────────

    @abstractmethod
    async def redeem(self, sku: str, coins_used: int, user_id: str, **kwargs) -> Dict:
        """
        Execute the redemption for this provider.
        Must return a dict containing at least:
          status:       "delivered" | "redirect" | "placed" | "failed"
        And one of:
          voucher_code: str   (for digital vouchers)
          redirect_url: str   (for affiliate links)
          order_id:     str   (for physical delivery)
        Optional kwargs:
          user_email: str   (used by providers that need it for delivery)
        """
