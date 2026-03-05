"""AI Portal Pipeline Client.

Async client for executing multi-agent pipelines via the AI Portal
``/api/v2/pipelines/*`` endpoints.  Supports both fire-and-forget (poll)
and WebSocket streaming modes.

Usage::

    from calculus_tools.clients import PipelineClient

    async with PipelineClient(
        base_url="http://34.139.78.75:8000",
        email="swarm@calculusresearch.io",
        password="swarm",
    ) as client:
        # List available pipelines
        pipelines = await client.list_pipelines()
        for p in pipelines:
            print(p["name"], "—", p["description"])

        # Run a pipeline (blocks until completion via WebSocket)
        result = await client.run_pipeline(
            "lex_intelligence",
            "What are the legal implications of AI-generated contracts?",
        )
        print(result.output)
        print(f"Cost: ${result.total_cost:.4f}  Tokens: {result.total_tokens}")

    # Or use the sync convenience wrapper
    from calculus_tools.clients.pipeline_client import run_pipeline_sync
    result = run_pipeline_sync(
        "calculus_intelligence",
        "Explain quantum error correction in simple terms",
    )
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable, Optional

import httpx

logger = logging.getLogger(__name__)

# Default AI Portal URL (fc-ai-portal VM)
_DEFAULT_BASE_URL = "http://34.139.78.75:8000"


# ── Result dataclass ──────────────────────────────────────────────────────


@dataclass
class PipelineResult:
    """Result from a completed pipeline execution."""

    pipeline_id: str
    pipeline_name: str
    status: str  # "completed" | "failed"
    output: str = ""
    total_tokens: int = 0
    total_cost: float = 0.0
    duration_ms: float = 0.0
    agent_breakdown: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == "completed"


# ── Progress event ─────────────────────────────────────────────────────


@dataclass
class PipelineEvent:
    """A progress event from a running pipeline."""

    event_type: str  # "agent_start" | "agent_complete" | "complete" | "error"
    data: dict = field(default_factory=dict)
    timestamp: float = 0.0


# ── Client ───────────────────────────────────────────────────────────


class PipelineClient:
    """Async client for AI Portal pipeline APIs.

    Authenticates via ``/auth/login`` and auto-refreshes JWT when it expires.

    Parameters
    ----------
    base_url : str
        AI Portal base URL (e.g. ``http://34.139.78.75:8000``).
    email : str
        Login email.
    password : str
        Login password.
    token : str | None
        Pre-existing JWT access token (skips login if provided).
    refresh_token : str | None
        Pre-existing refresh token.
    timeout : float
        HTTP request timeout in seconds (default 300 for long pipelines).
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        email: str = "swarm@calculusresearch.io",
        password: str = "swarm",
        token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        timeout: float = 300.0,
    ):
        self.base_url = base_url.rstrip("/")
        self._email = email
        self._password = password
        self._token = token
        self._refresh_token = refresh_token
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    # ── Context manager ───────────────────────────────────────────────

    async def __aenter__(self) -> "PipelineClient":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self._timeout, connect=10.0),
        )
        if not self._token:
            await self._login()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── Auth ────────────────────────────────────────────────────────

    async def _login(self) -> None:
        """Authenticate and store JWT tokens."""
        assert self._client is not None
        resp = await self._client.post(
            "/auth/login",
            json={"email": self._email, "password": self._password},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._refresh_token = data.get("refresh_token", "")
        logger.debug("Pipeline client authenticated (user=%s)", self._email)

    async def _refresh(self) -> bool:
        """Try to refresh the access token. Returns True on success."""
        if not self._refresh_token or not self._client:
            return False
        try:
            resp = await self._client.post(
                "/auth/refresh",
                json={"refresh_token": self._refresh_token},
            )
            if resp.status_code == 200:
                data = resp.json()
                self._token = data["access_token"]
                self._refresh_token = data.get("refresh_token", self._refresh_token)
                return True
        except Exception:
            pass
        return False

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    async def _authed_request(
        self, method: str, path: str, **kwargs: Any
    ) -> httpx.Response:
        """Make an authenticated request, retrying once on 401 with refresh."""
        assert self._client is not None
        resp = await self._client.request(
            method, path, headers=self._headers(), **kwargs
        )
        if resp.status_code == 401:
            if await self._refresh():
                resp = await self._client.request(
                    method, path, headers=self._headers(), **kwargs
                )
            else:
                await self._login()
                resp = await self._client.request(
                    method, path, headers=self._headers(), **kwargs
                )
        return resp

    # ── Pipeline list ─────────────────────────────────────────────────

    async def list_pipelines(self) -> list[dict]:
        """Return list of available pipelines from the AI Portal.

        Each item has keys: ``name``, ``display_name``, ``description``,
        ``agents`` (list), ``type`` ("multi_agent"|"single").
        """
        resp = await self._authed_request("GET", "/api/v2/pipelines/list")
        resp.raise_for_status()
        data = resp.json()
        return data.get("pipelines", [])

    # ── Pipeline execution (polling mode) ─────────────────────

    async def run_pipeline(
        self,
        pipeline_name: str,
        query: str,
        on_event: Optional[Callable[[PipelineEvent], Any]] = None,
        poll_interval: float = 2.0,
        ws_timeout: float = 600.0,
    ) -> PipelineResult:
        """Execute a pipeline and wait for completion.

        Starts the pipeline via ``POST /api/v2/pipelines/run``, then
        connects to the WebSocket to stream progress events.  Falls back
        to polling if WebSocket is unavailable.

        Parameters
        ----------
        pipeline_name : str
            Pipeline name (e.g. ``"lex_intelligence"``).
        query : str
            The user query / prompt for the pipeline.
        on_event : callable | None
            Optional callback invoked for each progress event.
        poll_interval : float
            Seconds between poll attempts (only used in fallback mode).
        ws_timeout : float
            Maximum seconds to wait for pipeline completion.

        Returns
        -------
        PipelineResult
            The completed (or failed) pipeline result.
        """
        # Step 1: Start the pipeline
        resp = await self._authed_request(
            "POST",
            "/api/v2/pipelines/run",
            json={"pipeline_name": pipeline_name, "query": query},
        )
        resp.raise_for_status()
        start_data = resp.json()

        pipeline_id = start_data["pipeline_id"]
        ws_path = start_data.get("ws_url", f"/api/v2/pipelines/ws/{pipeline_id}")

        logger.info(
            "Pipeline '%s' started (id=%s)", pipeline_name, pipeline_id
        )

        # Step 2: Stream events via WebSocket
        events: list[dict] = []
        result = PipelineResult(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            status="running",
        )

        try:
            result = await self._stream_ws(
                pipeline_id, pipeline_name, ws_path, events, on_event, ws_timeout
            )
        except Exception as ws_err:
            logger.warning(
                "WebSocket streaming failed (%s), pipeline may still be running. "
                "Check AI Portal logs for pipeline_id=%s",
                ws_err, pipeline_id,
            )
            result.status = "unknown"
            result.events = events

        return result

    async def _stream_ws(
        self,
        pipeline_id: str,
        pipeline_name: str,
        ws_path: str,
        events: list[dict],
        on_event: Optional[Callable],
        timeout: float,
    ) -> PipelineResult:
        """Connect to WebSocket and collect events until completion."""
        import websockets  # type: ignore[import-untyped]

        # Build ws:// URL from http:// base
        ws_base = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_base}{ws_path}"

        result = PipelineResult(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            status="running",
        )

        deadline = time.monotonic() + timeout

        async with websockets.connect(ws_url) as ws:
            # Authenticate
            await ws.send(json.dumps({"type": "auth", "token": self._token}))

            while time.monotonic() < deadline:
                try:
                    remaining = deadline - time.monotonic()
                    raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 30.0))
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    await ws.send("ping")
                    continue

                if raw == "pong":
                    continue

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                event_type = msg.get("type", msg.get("event_type", "unknown"))
                event_data = msg.get("data", msg)
                ev = PipelineEvent(
                    event_type=event_type,
                    data=event_data,
                    timestamp=time.time(),
                )
                events.append({"type": event_type, **event_data})

                if on_event:
                    try:
                        cb_result = on_event(ev)
                        if asyncio.iscoroutine(cb_result):
                            await cb_result
                    except Exception:
                        pass

                logger.debug("Pipeline %s event: %s", pipeline_id, event_type)

                if event_type == "complete":
                    result.status = "completed"
                    result.output = event_data.get("output", "")
                    result.total_tokens = event_data.get("total_tokens", 0)
                    result.total_cost = event_data.get("total_cost", 0.0)
                    result.duration_ms = event_data.get("duration_ms", 0.0)
                    result.agent_breakdown = event_data.get("agent_breakdown", [])
                    result.events = events
                    return result

                if event_type == "error":
                    result.status = "failed"
                    result.output = event_data.get("message", "Pipeline execution failed")
                    result.events = events
                    return result

        # Timed out
        result.status = "timeout"
        result.events = events
        return result

    # ── Convenience: stream events as async generator ─────────

    async def stream_pipeline(
        self,
        pipeline_name: str,
        query: str,
    ) -> AsyncGenerator[PipelineEvent, None]:
        """Start a pipeline and yield events as they arrive.

        Example::

            async for event in client.stream_pipeline("lex_intelligence", query):
                print(f"[{event.event_type}] {event.data}")
        """
        resp = await self._authed_request(
            "POST",
            "/api/v2/pipelines/run",
            json={"pipeline_name": pipeline_name, "query": query},
        )
        resp.raise_for_status()
        start_data = resp.json()
        pipeline_id = start_data["pipeline_id"]
        ws_path = start_data.get("ws_url", f"/api/v2/pipelines/ws/{pipeline_id}")

        import websockets

        ws_base = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_base}{ws_path}"

        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps({"type": "auth", "token": self._token}))

            deadline = time.monotonic() + 600.0
            while time.monotonic() < deadline:
                try:
                    remaining = deadline - time.monotonic()
                    raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 30.0))
                except asyncio.TimeoutError:
                    await ws.send("ping")
                    continue

                if raw == "pong":
                    continue

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                event_type = msg.get("type", msg.get("event_type", "unknown"))
                event_data = msg.get("data", msg)

                yield PipelineEvent(
                    event_type=event_type,
                    data=event_data,
                    timestamp=time.time(),
                )

                if event_type in ("complete", "error"):
                    return


# ── Sync convenience wrapper ─────────────────────────────────────────


def run_pipeline_sync(
    pipeline_name: str,
    query: str,
    base_url: str = _DEFAULT_BASE_URL,
    email: str = "swarm@calculusresearch.io",
    password: str = "swarm",
    **kwargs: Any,
) -> PipelineResult:
    """Synchronous convenience wrapper for ``PipelineClient.run_pipeline``.

    Useful for scripts, notebooks, and non-async contexts.
    """

    async def _run() -> PipelineResult:
        async with PipelineClient(
            base_url=base_url, email=email, password=password
        ) as client:
            return await client.run_pipeline(pipeline_name, query, **kwargs)

    return asyncio.run(_run())
