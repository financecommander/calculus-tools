"""CourtListener Tool — Search federal & state court opinions, dockets, and oral arguments.

Free API (100 req/day basic, higher with account). Token optional for basic use.
Docs: https://www.courtlistener.com/api/rest/v4/
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests


_CL_BASE = "https://www.courtlistener.com/api/rest/v4"


class CourtListenerInput(BaseModel):
    query: str = Field(..., description="Legal search query (case name, topic, statute)")
    search_type: str = Field(
        "opinions",
        description="Search type: 'opinions', 'dockets', or 'recap'",
    )
    max_results: int = Field(5, ge=1, le=20, description="Max results to return")


class CourtListenerTool(BaseTool):
    name: str = "courtlistener"
    description: str = (
        "Search U.S. federal and state court opinions, dockets, and RECAP archives. "
        "Essential for legal research, compliance checks, and fraud signal detection."
    )
    args_schema: type = CourtListenerInput

    def _run(
        self, query: str, search_type: str = "opinions", max_results: int = 5
    ) -> str:
        headers: dict = {"Accept": "application/json"}
        token = os.getenv("COURTLISTENER_API_KEY")
        if token:
            headers["Authorization"] = f"Token {token}"

        endpoint = f"{_CL_BASE}/search/"
        params: dict = {
            "q": query,
            "type": {"opinions": "o", "dockets": "d", "recap": "r"}.get(
                search_type, "o"
            ),
            "page_size": max_results,
        }

        try:
            resp = requests.get(
                endpoint, params=params, headers=headers, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])[:max_results]

            if not results:
                return f"No court records found for '{query}'."

            lines = [f"CourtListener {search_type} for '{query}':"]
            for r in results:
                if search_type == "opinions":
                    lines.append(
                        f"  • {r.get('caseName', 'N/A')} | "
                        f"{r.get('court', 'N/A')} | "
                        f"{r.get('dateFiled', '?')} | "
                        f"https://www.courtlistener.com{r.get('absolute_url', '')}"
                    )
                elif search_type == "dockets":
                    lines.append(
                        f"  • {r.get('caseName', 'N/A')} | "
                        f"Docket #{r.get('docketNumber', '?')} | "
                        f"{r.get('court', 'N/A')} | "
                        f"{r.get('dateFiled', '?')}"
                    )
                else:
                    lines.append(
                        f"  • {r.get('short_description', r.get('description', 'N/A')[:120])}"
                    )
            return "\n".join(lines)

        except requests.exceptions.HTTPError as e:
            return f"CourtListener error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"CourtListener error: {e}"
