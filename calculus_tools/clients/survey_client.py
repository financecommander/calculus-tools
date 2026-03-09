"""
Survey Client — Stub for MVP.

Planned capabilities:
- Survey creation (Typeform, etc.)
- Response collection and retrieval
- Survey distribution via email and other channels
- NPS score calculation
- Response summary and analytics
"""

from typing import Dict, Any, Optional, List


class SurveyClient:
    """Survey API client (stub — not yet implemented)."""

    def __init__(
        self, provider: str = "typeform", api_key: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key

    async def create_survey(
        self, title: str, questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        raise NotImplementedError("Survey create_survey not yet implemented")

    async def get_responses(
        self,
        survey_id: str,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("Survey get_responses not yet implemented")

    async def send_survey(
        self,
        survey_id: str,
        recipients: List[str],
        channel: str = "email",
    ) -> Dict[str, Any]:
        raise NotImplementedError("Survey send_survey not yet implemented")

    async def calculate_nps(self, survey_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Survey calculate_nps not yet implemented")

    async def get_summary(self, survey_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Survey get_summary not yet implemented")
