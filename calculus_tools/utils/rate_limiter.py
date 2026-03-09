"""
Rate limiter for external API calls.

Enforces per-window rate limits to avoid exceeding service quotas.
Thread-safe via asyncio lock.
"""

import asyncio
import time
from typing import Optional
from collections import deque


class RateLimiter:
    """
    Sliding window rate limiter.

    Usage:
        limiter = RateLimiter(max_requests=100, window_seconds=60)
        if await limiter.acquire():
            # proceed with API call
        else:
            # rate limited, wait or skip
    """

    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: deque = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """
        Try to acquire a rate limit slot.
        Returns True if allowed, False if rate limited.
        """
        async with self._lock:
            now = time.monotonic()
            cutoff = now - self.window_seconds

            # Remove expired timestamps
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()

            if len(self._timestamps) < self.max_requests:
                self._timestamps.append(now)
                return True

            return False

    async def wait_and_acquire(self, timeout: float = 30.0) -> bool:
        """
        Wait until a slot is available, up to timeout seconds.
        Returns True if acquired, False if timed out.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if await self.acquire():
                return True
            await asyncio.sleep(0.1)
        return False

    @property
    def remaining(self) -> int:
        """Number of remaining requests in the current window."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        active = sum(1 for t in self._timestamps if t >= cutoff)
        return max(0, self.max_requests - active)
