"""Tavily-augmented Grok provider.

Performs real-time web research via Tavily, then sends the augmented prompt
to Grok for intelligent synthesis.  Used by copilot, scout, and code_review
specialist types.

This is the canonical implementation. AI-PORTAL imports a thin adapter that
wraps this class to conform to its internal BaseProvider interface.
"""

import logging
import httpx

from typing import AsyncGenerator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── Lightweight response types (no framework dependency) ──────


@dataclass
class ProviderResponse:
    content: str
    model: str = ""
    usage: dict = field(default_factory=dict)


@dataclass
class StreamChunk:
    content: str = ""
    done: bool = False


class TavilyGrokProvider:
    """Provider that enriches prompts with Tavily web search before calling Grok."""

    def __init__(
        self,
        tavily_api_key: str,
        xai_api_key: str,
        name: str = "copilot",
    ):
        self.name = name
        self.tavily_key = tavily_api_key
        self.xai_api_key = xai_api_key

    # ── Tavily search ─────────────────────────────────────────

    async def _tavily_search(self, query: str) -> str:
        """Call Tavily search API and return an answer summary + sources."""
        if not self.tavily_key or not query:
            return ""
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_key,
                        "query": query[:400],
                        "search_depth": "advanced",
                        "include_answer": True,
                    },
                )
                data = resp.json()
                answer = (data.get("answer") or "")[:800]
                sources = [
                    r.get("url", "") for r in data.get("results", [])[:3]
                ]
                src_text = "\n".join(f"- {u}" for u in sources if u)
                result = answer
                if src_text:
                    result += f"\n\nSources:\n{src_text}"
                return result
        except Exception as exc:
            logger.warning("Tavily search failed: %s", exc)
            return ""

    # ── Helpers ────────────────────────────────────────────

    @staticmethod
    def _extract_user_query(messages: list[dict]) -> str:
        """Extract the last user message as a search query."""
        for m in reversed(messages):
            if m.get("role") == "user":
                content = m.get("content", "")
                if isinstance(content, str):
                    return content[:500]
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            return part.get("text", "")[:500]
        return ""

    def _augment_system_prompt(
        self, system_prompt: str | None, context: str
    ) -> str | None:
        """Inject web research context into the system prompt."""
        if not context:
            return system_prompt
        tag = "\n\n[Real-Time Web Research Results]\n" + context
        return (system_prompt or "") + tag

    # ── Core API ───────────────────────────────────────────

    async def send_message(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
    ) -> ProviderResponse:
        """Search Tavily, augment prompt, call Grok, return response."""
        query = self._extract_user_query(messages)
        context = await self._tavily_search(query)
        augmented = self._augment_system_prompt(system_prompt, context)

        api_messages = list(messages)
        if augmented:
            api_messages = [{"role": "system", "content": augmented}] + api_messages

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.xai_api_key}"},
                json={
                    "model": model,
                    "messages": api_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            data = resp.json()
            return ProviderResponse(
                content=data["choices"][0]["message"]["content"],
                model=data.get("model", model),
                usage=data.get("usage", {}),
            )

    async def stream_message(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Search Tavily, augment prompt, stream Grok response."""
        query = self._extract_user_query(messages)
        context = await self._tavily_search(query)
        augmented = self._augment_system_prompt(system_prompt, context)

        api_messages = list(messages)
        if augmented:
            api_messages = [{"role": "system", "content": augmented}] + api_messages

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.xai_api_key}"},
                json={
                    "model": model,
                    "messages": api_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        yield StreamChunk(done=True)
                        return
                    import json

                    chunk = json.loads(payload)
                    delta = chunk["choices"][0].get("delta", {})
                    text = delta.get("content", "")
                    if text:
                        yield StreamChunk(content=text)
