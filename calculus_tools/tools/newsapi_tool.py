"""NewsAPI Tool — Global news headlines and article search.

Free tier: 100 req/day. Requires free API key.
Get key: https://newsapi.org/register
Docs: https://newsapi.org/docs
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests


_NEWS_BASE = "https://newsapi.org/v2"


class NewsApiInput(BaseModel):
    query: str = Field(..., description="News search term or topic")
    category: str = Field(
        "",
        description=(
            "Top-headlines category filter: 'business', 'technology', 'science', "
            "'health', 'sports', 'entertainment', 'general'. Empty = everything."
        ),
    )
    max_results: int = Field(5, ge=1, le=20, description="Max articles to return")


class NewsApiTool(BaseTool):
    name: str = "newsapi"
    description: str = (
        "Search global news articles and top headlines via NewsAPI. "
        "Covers 80K+ sources. Useful for market awareness, fraud signals, "
        "reputation monitoring, and current events. Requires NEWSAPI_KEY env var."
    )
    args_schema: type = NewsApiInput

    def _run(
        self, query: str, category: str = "", max_results: int = 5
    ) -> str:
        api_key = os.getenv("NEWSAPI_KEY")
        if not api_key:
            return "NewsAPI error: NEWSAPI_KEY not set"

        try:
            # Use /everything for keyword search, /top-headlines if category given
            if category:
                endpoint = f"{_NEWS_BASE}/top-headlines"
                params: dict = {
                    "q": query,
                    "category": category,
                    "language": "en",
                    "pageSize": max_results,
                    "apiKey": api_key,
                }
            else:
                endpoint = f"{_NEWS_BASE}/everything"
                params = {
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": max_results,
                    "apiKey": api_key,
                }

            resp = requests.get(endpoint, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "ok":
                return f"NewsAPI: {data.get('message', 'Unknown error')}"

            articles = data.get("articles", [])[:max_results]
            if not articles:
                return f"No news found for '{query}'."

            lines = [f"News for '{query}' ({data.get('totalResults', 0)} total):"]
            for a in articles:
                lines.append(
                    f"  • {a.get('title', 'N/A')}\n"
                    f"    {a.get('source', {}).get('name', '?')} | "
                    f"{a.get('publishedAt', '?')[:10]}\n"
                    f"    {a.get('description', '')[:150]}\n"
                    f"    {a.get('url', '')}"
                )
            return "\n".join(lines)

        except requests.exceptions.HTTPError as e:
            return f"NewsAPI error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"NewsAPI error: {e}"
