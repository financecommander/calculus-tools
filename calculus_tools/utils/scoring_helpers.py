"""
Lead scoring utilities.

Provides composable scoring functions for lead qualification.
"""

from typing import Dict, Any, List, Optional


def score_lead(
    lead: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Score a lead 0-100 based on available data quality and engagement signals.

    Default weights:
    - has_email: 25 points
    - has_phone: 15 points
    - has_name: 10 points
    - has_company: 15 points
    - has_title: 10 points
    - industry_match: 15 points
    - recency (days since captured): up to 10 points

    Args:
        lead: Dict with lead data fields
        weights: Optional custom weights override

    Returns:
        Score from 0.0 to 100.0
    """
    if weights is None:
        weights = {
            "has_email": 25.0,
            "has_phone": 15.0,
            "has_name": 10.0,
            "has_company": 15.0,
            "has_title": 10.0,
            "industry_match": 15.0,
            "recency": 10.0,
        }

    score = 0.0

    if lead.get("email"):
        score += weights.get("has_email", 0)
    if lead.get("phone"):
        score += weights.get("has_phone", 0)
    if lead.get("contact_name") or lead.get("first_name"):
        score += weights.get("has_name", 0)
    if lead.get("company") or lead.get("organization"):
        score += weights.get("has_company", 0)
    if lead.get("title") or lead.get("job_title"):
        score += weights.get("has_title", 0)

    # Industry match — if target industries provided
    target_industries = lead.get("_target_industries", [])
    lead_industry = (lead.get("industry") or "").lower()
    if target_industries and lead_industry:
        if any(t.lower() in lead_industry for t in target_industries):
            score += weights.get("industry_match", 0)

    # Recency bonus (placeholder — needs timestamp field)
    if lead.get("captured_at"):
        score += weights.get("recency", 0) * 0.5  # half credit for having timestamp

    return min(100.0, max(0.0, score))


def classify_lead(score: float) -> str:
    """
    Classify a lead by score tier.

    Returns: "hot" (80+), "warm" (50-79), "cold" (20-49), "unqualified" (<20)
    """
    if score >= 80:
        return "hot"
    elif score >= 50:
        return "warm"
    elif score >= 20:
        return "cold"
    else:
        return "unqualified"
