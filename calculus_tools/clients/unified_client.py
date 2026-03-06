"""Unified API client with retry, circuit-breaker, and auth handling.

Provides a single ``UnifiedClient`` that wraps any API from the registry
and transparently handles:
- Automatic retries with exponential backoff
- Circuit-breaker pattern (fail-fast after repeated errors)
- Auth injection (API key, Bearer, Basic)
- Rate-limit awareness (429 back-off)

Usage::

    from calculus_tools.clients.unified_client import UnifiedClient

    async with UnifiedClient() as client:
        data = await client.call("Cat Fact")        # GET by default
        data = await client.call("JSONPlaceholder")  # returns parsed JSON
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

import httpx

from calculus_tools.registry.models import ApiEntry, AuthType

logger = logging.getLogger(__name__)


# ── Circuit-breaker states ────────────────────────────────────


class CircuitState(str, Enum):
    CLOSED = "closed"        # normal operation
    OPEN = "open"            # failing — reject calls
    HALF_OPEN = "half_open"  # testing recovery


@dataclass
class CircuitBreaker:
    """Per-API circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0  # seconds before half-open retry

    _failures: int = 0
    _state: CircuitState = CircuitState.CLOSED
    _opened_at: float = 0.0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        self._failures = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()
            logger.warning("Circuit OPEN after %d failures", self._failures)

    @property
    def allow_request(self) -> bool:
        s = self.state
        return s in (CircuitState.CLOSED, CircuitState.HALF_OPEN)


@dataclass
class CallResult:
    """Result of a unified API call."""

    api_name: str
    status_code: int
    data: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    retries: int = 0


# ── Unified client ────────────────────────────────────────────


class UnifiedClient:
    """Async HTTP client with retry, circuit-breaker, and auth."""

    def __init__(
        self,
        timeout: float = 15.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        auth_secrets: Optional[dict[str, str]] = None,
    ):
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._auth_secrets = auth_secrets or {}  # {"API Name": "key-or-token"}
        self._breakers: dict[str, CircuitBreaker] = {}
        self._client: Optional[httpx.AsyncClient] = None

    # ── context manager ──────────────────────────────────

    async def __aenter__(self) -> UnifiedClient:
        self._client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, *exc) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── breaker lookup ───────────────────────────────────

    def _breaker(self, name: str) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                failure_threshold=self._failure_threshold,
                recovery_timeout=self._recovery_timeout,
            )
        return self._breakers[name]

    # ── auth injection ───────────────────────────────────

    def _apply_auth(
        self, entry: ApiEntry, headers: dict, params: dict
    ) -> None:
        secret = self._auth_secrets.get(entry.name)
        if not secret:
            return
        if entry.auth_type == AuthType.BEARER:
            headers["Authorization"] = f"Bearer {secret}"
        elif entry.auth_type == AuthType.API_KEY:
            params["api_key"] = secret
        elif entry.auth_type == AuthType.BASIC:
            # expect "user:pass"
            import base64
            cred = base64.b64encode(secret.encode()).decode()
            headers["Authorization"] = f"Basic {cred}"

    # ── core call ────────────────────────────────────────

    async def call(
        self,
        entry: ApiEntry,
        method: str = "GET",
        path: str = "",
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> CallResult:
        """Execute an API call with retry and circuit-breaker protection."""
        if not self._client:
            raise RuntimeError("Use 'async with UnifiedClient() as client:'")

        cb = self._breaker(entry.name)
        if not cb.allow_request:
            return CallResult(
                api_name=entry.name,
                status_code=0,
                error=f"Circuit OPEN for {entry.name} — skipping",
            )

        url = entry.base_url.rstrip("/")
        if path:
            url = f"{url}/{path.lstrip('/')}"

        req_headers = dict(headers or {})
        req_params = dict(params or {})
        self._apply_auth(entry, req_headers, req_params)

        last_error = None
        retries = 0

        for attempt in range(self._max_retries + 1):
            t0 = time.monotonic()
            try:
                resp = await self._client.request(
                    method,
                    url,
                    params=req_params or None,
                    json=json_body,
                    headers=req_headers,
                )
                latency = (time.monotonic() - t0) * 1000

                if resp.status_code == 429:
                    # rate-limited — back off and retry
                    retry_after = float(resp.headers.get("Retry-After", self._backoff_base * (2 ** attempt)))
                    logger.info("%s rate-limited, waiting %.1fs", entry.name, retry_after)
                    await asyncio.sleep(retry_after)
                    retries += 1
                    continue

                if resp.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )

                # success
                cb.record_success()
                try:
                    data = resp.json()
                except Exception:
                    data = resp.text

                return CallResult(
                    api_name=entry.name,
                    status_code=resp.status_code,
                    data=data,
                    latency_ms=round(latency, 1),
                    retries=retries,
                )

            except Exception as exc:
                latency = (time.monotonic() - t0) * 1000
                last_error = str(exc)
                retries += 1
                cb.record_failure()

                if attempt < self._max_retries:
                    wait = self._backoff_base * (2 ** attempt)
                    logger.info(
                        "%s attempt %d failed (%s), retrying in %.1fs",
                        entry.name, attempt + 1, last_error, wait,
                    )
                    await asyncio.sleep(wait)

        return CallResult(
            api_name=entry.name,
            status_code=0,
            error=last_error,
            latency_ms=round((time.monotonic() - t0) * 1000, 1),
            retries=retries,
        )

    # ── parallel multi-call ──────────────────────────────

    async def call_many(
        self,
        entries: list[ApiEntry],
        method: str = "GET",
        params: Optional[dict] = None,
    ) -> list[CallResult]:
        """Call multiple APIs in parallel, returning all results."""
        tasks = [self.call(entry, method=method, params=params) for entry in entries]
        return await asyncio.gather(*tasks)
