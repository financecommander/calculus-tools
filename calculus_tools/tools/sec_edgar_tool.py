"""SEC EDGAR Tool — Search and retrieve SEC filings (10-K, 10-Q, 8-K, etc.).

Free API, rate-limited (10 req/sec). Requires User-Agent header per SEC policy.
Docs: https://efts.sec.gov/LATEST/search-index?q=
      https://data.sec.gov/submissions/
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests

_SEC_HEADERS = {
    "User-Agent": os.getenv(
        "SEC_USER_AGENT",
        "CalcSwarm/1.0 (admin@calculusholdings.com)",
    ),
    "Accept": "application/json",
}
_EFTS_SEARCH = "https://efts.sec.gov/LATEST/search-index"
_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"


class SecEdgarInput(BaseModel):
    query: str = Field(
        ..., description="Company name, ticker, CIK, or free-text filing search"
    )
    filing_type: str = Field(
        "", description="Filing type filter (e.g. '10-K', '10-Q', '8-K'). Empty = all."
    )
    max_results: int = Field(5, ge=1, le=20, description="Max filings to return")


class SecEdgarTool(BaseTool):
    name: str = "sec_edgar"
    description: str = (
        "Search SEC EDGAR for company filings (10-K, 10-Q, 8-K, insider trades). "
        "Returns filing metadata and direct links. Essential for fraud detection "
        "and financial due diligence."
    )
    args_schema: type = SecEdgarInput

    def _run(
        self, query: str, filing_type: str = "", max_results: int = 5
    ) -> str:
        try:
            params: dict = {
                "q": query,
                "dateRange": "custom",
                "startdt": "2020-01-01",
                "enddt": "2026-12-31",
            }
            if filing_type:
                params["forms"] = filing_type

            resp = requests.get(
                "https://efts.sec.gov/LATEST/search-index",
                params=params,
                headers=_SEC_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])[:max_results]

            if not hits:
                return self._try_fulltext(query, filing_type, max_results)

            lines = [f"SEC EDGAR results for '{query}':"]
            for h in hits:
                src = h.get("_source", {})
                name = (src.get("display_names") or ["N/A"])[0]
                cik = (src.get("ciks") or [""])[0].lstrip("0")
                adsh = src.get("adsh", "").replace("-", "")
                lines.append(
                    f"  • {src.get('form', '?')} | "
                    f"{name} | "
                    f"Filed {src.get('file_date', '?')} | "
                    f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh}"
                )
            return "\n".join(lines)

        except requests.exceptions.HTTPError as e:
            return f"SEC EDGAR error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"SEC EDGAR error: {e}"

    def _try_fulltext(
        self, query: str, filing_type: str, max_results: int
    ) -> str:
        """Fall back to EDGAR full-text search (EFTS)."""
        try:
            params: dict = {"q": query, "from": 0, "size": max_results}
            if filing_type:
                params["forms"] = filing_type
            resp = requests.get(
                "https://efts.sec.gov/LATEST/search-index",
                params=params,
                headers=_SEC_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])[:max_results]
            if not hits:
                return f"No SEC filings found for '{query}'."
            lines = [f"SEC full-text results for '{query}':"]
            for h in hits:
                src = h.get("_source", {})
                name = (src.get("display_names") or ["N/A"])[0]
                lines.append(
                    f"  • {src.get('form', '?')} | "
                    f"{name} | "
                    f"Filed {src.get('file_date', '?')}"
                )
            return "\n".join(lines)
        except Exception:
            return f"No SEC filings found for '{query}'."
