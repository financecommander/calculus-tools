"""Wikipedia Tool — Quick general knowledge lookup.

Free, unlimited, no API key.
Docs: https://en.wikipedia.org/api/rest_v1/
      https://en.wikipedia.org/w/api.php
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests


_WIKI_API = "https://en.wikipedia.org/w/api.php"
_WIKI_REST = "https://en.wikipedia.org/api/rest_v1"
_WIKI_HEADERS = {
    "User-Agent": "CalcSwarm/2.0 (admin@calculusholdings.com)",
    "Accept": "application/json",
}


class WikipediaInput(BaseModel):
    query: str = Field(..., description="Topic or article title to look up")
    sentences: int = Field(
        5, ge=1, le=20, description="Max sentences in the summary"
    )


class WikipediaTool(BaseTool):
    name: str = "wikipedia"
    description: str = (
        "Look up any topic on Wikipedia. Returns article summary, key facts, "
        "and links. Free, unlimited, no API key. Great general research fallback."
    )
    args_schema: type = WikipediaInput

    def _run(self, query: str, sentences: int = 5) -> str:
        # Try REST summary endpoint first (cleaner output)
        summary = self._rest_summary(query)
        if summary:
            return summary

        # Fallback to MediaWiki API search + extract
        return self._mw_search(query, sentences)

    def _rest_summary(self, query: str) -> str | None:
        title = query.replace(" ", "_")
        try:
            resp = requests.get(
                f"{_WIKI_REST}/page/summary/{requests.utils.quote(title, safe='')}",
                headers=_WIKI_HEADERS,
                timeout=10,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()

            if data.get("type") == "disambiguation":
                return self._mw_search(query, 5)

            extract = data.get("extract", "")
            if not extract:
                return None

            title_display = data.get("title", query)
            desc = data.get("description", "")
            url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

            lines = [f"Wikipedia: {title_display}"]
            if desc:
                lines.append(f"  ({desc})")
            lines.append(f"\n{extract[:1500]}")
            if url:
                lines.append(f"\n  URL: {url}")
            return "\n".join(lines)

        except Exception:
            return None

    def _mw_search(self, query: str, sentences: int) -> str:
        try:
            # Search for the best matching page
            resp = requests.get(
                _WIKI_API,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": 1,
                    "format": "json",
                },
                headers=_WIKI_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json().get("query", {}).get("search", [])
            if not results:
                return f"No Wikipedia article found for '{query}'."

            title = results[0]["title"]

            # Get extract
            resp2 = requests.get(
                _WIKI_API,
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "exsentences": sentences,
                    "format": "json",
                },
                headers=_WIKI_HEADERS,
                timeout=10,
            )
            resp2.raise_for_status()
            pages = resp2.json().get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})
            extract = page.get("extract", "No content available.")

            url = f"https://en.wikipedia.org/wiki/{requests.utils.quote(title.replace(' ', '_'), safe='')}"
            return f"Wikipedia: {title}\n\n{extract[:1500]}\n\n  URL: {url}"

        except requests.exceptions.HTTPError as e:
            return f"Wikipedia error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"Wikipedia error: {e}"
