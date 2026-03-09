"""
Analytics Reporting Client — Stub for MVP.

Planned capabilities:
- Campaign performance aggregation
- Conversion tracking
- A/B test result analysis
"""

from typing import Dict, Any, List, Optional


class AnalyticsClient:
    """Analytics reporting client (stub — not yet implemented)."""

    def __init__(self, provider: str = "internal", api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key

    async def get_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Campaign analytics not yet implemented")

    async def track_conversion(self, event_type: str, entity_id: str,
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        raise NotImplementedError("Conversion tracking not yet implemented")

    async def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        raise NotImplementedError("A/B test analytics not yet implemented")
