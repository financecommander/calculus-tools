"""API Intelligence Tool — CrewAI specialist for multi-API routing.

Given a user task, this tool:
1. Loads the API registry
2. Uses Grok to select the 3–10 most relevant APIs for the task
3. Calls them in parallel via the UnifiedClient
4. Aggregates results and returns a synthesised answer

Example queries:
    "Latest fraud signals on $TSLA"
    "Person intel on John Smith, age ~35, New York"
    "Current USD/EUR exchange rate and US public holidays"
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

import requests
from pydantic import BaseModel, Field

try:
    from crewai.tools import BaseTool
except ImportError:  # crewai is optional
    from pydantic import BaseModel as BaseTool

from calculus_tools.registry.models import ApiEntry
from calculus_tools.registry.store import RegistryStore
from calculus_tools.clients.unified_client import UnifiedClient, CallResult

logger = logging.getLogger(__name__)


class ApiIntelligenceInput(BaseModel):
    query: str = Field(..., description="The task or question to investigate via APIs")
    max_apis: int = Field(10, ge=1, le=20, description="Max APIs to call (3–10 recommended)")


class ApiIntelligenceTool(BaseTool):
    """Specialist that routes tasks across multiple APIs and aggregates results."""

    name: str = "api_intelligence"
    description: str = (
        "Multi-API intelligence router. Analyses a query, selects the most "
        "relevant APIs from the registry, calls them in parallel, and "
        "synthesises a unified answer."
    )

    def _run(self, query: str, max_apis: int = 10) -> str:
        """Synchronous entry point — wraps the async pipeline."""
        try:
            return asyncio.run(self._execute(query, max_apis))
        except Exception as exc:
            logger.exception("api_intelligence failed")
            return f"Error: {exc}"

    async def _execute(self, query: str, max_apis: int) -> str:
        # 1. Load registry
        store = RegistryStore()
        await store.connect()
        all_apis = await store.list_apis(enabled_only=True)

        # If registry is empty, auto-seed from bundled JSON
        if not all_apis:
            from pathlib import Path
            seed = Path(__file__).parent.parent / "registry" / "seed_apis.json"
            if seed.exists():
                await store.import_json(seed)
                all_apis = await store.list_apis(enabled_only=True)

        if not all_apis:
            return "No APIs available in registry."

        # 2. Ask Grok to select the best APIs for this query
        selected = self._select_apis(query, all_apis, max_apis)

        if not selected:
            return "Could not determine relevant APIs for this query."

        # 3. Call selected APIs in parallel
        async with UnifiedClient(timeout=12.0, max_retries=2) as client:
            results = await client.call_many(selected)

        await store.close()

        # 4. Aggregate and synthesise
        return self._synthesise(query, results)

    # ── API selection via Grok ───────────────────────────

    def _select_apis(
        self, query: str, apis: list[ApiEntry], max_apis: int
    ) -> list[ApiEntry]:
        """Use Grok to pick the most relevant APIs for the query."""
        api_catalog = "\n".join(
            f"  {i+1}. {a.name} | {a.category.value} | {a.base_url} | {a.notes}"
            for i, a in enumerate(apis)
        )

        xai_key = os.getenv("XAI_API_KEY")
        if not xai_key:
            # fallback: return all (up to max)
            logger.warning("No XAI_API_KEY — selecting all APIs (up to %d)", max_apis)
            return apis[:max_apis]

        prompt = f"""You are an API routing engine. Given the user's query and an API catalog,
select the {min(max_apis, len(apis))} MOST RELEVANT APIs to call.

Return ONLY a JSON array of API names (strings). No explanation.

User query: {query}

Available APIs:
{api_catalog}

JSON array of selected API names:"""

        try:
            resp = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {xai_key}"},
                json={
                    "model": "grok-4-0709",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 300,
                },
                timeout=20,
            )
            content = resp.json()["choices"][0]["message"]["content"]
            selected_names = json.loads(content)
            name_set = set(selected_names)
            return [a for a in apis if a.name in name_set][:max_apis]
        except Exception as exc:
            logger.warning("API selection failed (%s) — using category heuristic", exc)
            return self._heuristic_select(query, apis, max_apis)

    def _heuristic_select(
        self, query: str, apis: list[ApiEntry], max_apis: int
    ) -> list[ApiEntry]:
        """Fallback: keyword-based matching when Grok is unavailable."""
        q = query.lower()
        scored: list[tuple[int, ApiEntry]] = []
        for api in apis:
            score = 0
            searchable = f"{api.name} {api.category.value} {api.notes}".lower()
            for word in q.split():
                if len(word) > 2 and word in searchable:
                    score += 1
            scored.append((score, api))
        scored.sort(key=lambda x: x[0], reverse=True)
        # take top matches, at least 3
        return [a for _, a in scored[:max(3, max_apis)]]

    # ── Aggregation + synthesis ──────────────────────────

    def _synthesise(self, query: str, results: list[CallResult]) -> str:
        """Combine API responses into a unified answer."""
        successes = [r for r in results if r.error is None]
        failures = [r for r in results if r.error is not None]

        parts = [f"## API Intelligence Report\n\n**Query:** {query}\n"]
        parts.append(f"**APIs called:** {len(results)} | "
                      f"**Succeeded:** {len(successes)} | "
                      f"**Failed:** {len(failures)}\n")

        if successes:
            parts.append("### Results\n")
            for r in successes:
                data_preview = json.dumps(r.data, indent=2, default=str)
                if len(data_preview) > 800:
                    data_preview = data_preview[:800] + "\n... (truncated)"
                parts.append(
                    f"**{r.api_name}** (HTTP {r.status_code}, {r.latency_ms}ms, "
                    f"{r.retries} retries)\n```json\n{data_preview}\n```\n"
                )

        if failures:
            parts.append("### Failures\n")
            for r in failures:
                parts.append(f"- **{r.api_name}**: {r.error}\n")

        # Try Grok synthesis of raw results
        synthesis = self._grok_synthesise(query, successes)
        if synthesis:
            parts.append(f"### Synthesised Analysis\n\n{synthesis}\n")

        return "\n".join(parts)

    def _grok_synthesise(self, query: str, results: list[CallResult]) -> str:
        """Optional: ask Grok to produce a narrative from raw API data."""
        xai_key = os.getenv("XAI_API_KEY")
        if not xai_key or not results:
            return ""

        data_summary = "\n\n".join(
            f"[{r.api_name}]: {json.dumps(r.data, default=str)[:600]}"
            for r in results
        )

        try:
            resp = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {xai_key}"},
                json={
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an intelligence analyst. Synthesise the following "
                                "API responses into a concise, actionable briefing that "
                                "directly answers the user's query."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Query: {query}\n\nAPI Data:\n{data_summary}",
                        },
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1024,
                },
                timeout=30,
            )
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.warning("Grok synthesis failed: %s", exc)
            return ""
