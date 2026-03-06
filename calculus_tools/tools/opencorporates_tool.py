"""OpenCorporates Tool — Global company registry lookup.

Requires API key (free tier discontinued). Get key at:
https://opencorporates.com/api_accounts/new
Docs: https://api.opencorporates.com/documentation/API-Reference
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests


_OC_BASE = "https://api.opencorporates.com/v0.4"


class OpenCorporatesInput(BaseModel):
    query: str = Field(
        ..., description="Company name, officer name, or jurisdiction code"
    )
    search_type: str = Field(
        "companies",
        description="Search type: 'companies' or 'officers'",
    )
    max_results: int = Field(5, ge=1, le=20, description="Max results to return")


class OpenCorporatesTool(BaseTool):
    name: str = "opencorporates"
    description: str = (
        "Search the global OpenCorporates registry for company records, officers, "
        "subsidiaries, and filings. Covers 200M+ companies across 140+ jurisdictions. "
        "Essential for skip-trace, due diligence, and fraud enrichment."
    )
    args_schema: type = OpenCorporatesInput

    def _run(
        self, query: str, search_type: str = "companies", max_results: int = 5
    ) -> str:
        params: dict = {"q": query, "per_page": max_results}
        token = os.getenv("OPENCORPORATES_API_KEY")
        if not token:
            return "OpenCorporates error: OPENCORPORATES_API_KEY not set (required since free tier discontinued)."
        params["api_token"] = token

        endpoint = f"{_OC_BASE}/{search_type}/search"

        try:
            resp = requests.get(endpoint, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if search_type == "companies":
                return self._format_companies(query, data, max_results)
            else:
                return self._format_officers(query, data, max_results)

        except requests.exceptions.HTTPError as e:
            return f"OpenCorporates error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"OpenCorporates error: {e}"

    def _format_companies(self, query: str, data: dict, limit: int) -> str:
        companies = data.get("results", {}).get("companies", [])[:limit]
        if not companies:
            return f"No companies found for '{query}'."

        lines = [f"OpenCorporates companies for '{query}':"]
        for item in companies:
            c = item.get("company", {})
            lines.append(
                f"  • {c.get('name', 'N/A')} | "
                f"{c.get('jurisdiction_code', '?').upper()} | "
                f"#{c.get('company_number', '?')} | "
                f"Status: {c.get('current_status', '?')} | "
                f"Inc. {c.get('incorporation_date', '?')} | "
                f"{c.get('opencorporates_url', '')}"
            )
        return "\n".join(lines)

    def _format_officers(self, query: str, data: dict, limit: int) -> str:
        officers = data.get("results", {}).get("officers", [])[:limit]
        if not officers:
            return f"No officers found for '{query}'."

        lines = [f"OpenCorporates officers for '{query}':"]
        for item in officers:
            o = item.get("officer", {})
            lines.append(
                f"  • {o.get('name', 'N/A')} | "
                f"Position: {o.get('position', '?')} | "
                f"Company: {o.get('company', {}).get('name', '?')} | "
                f"{o.get('opencorporates_url', '')}"
            )
        return "\n".join(lines)
