"""Per-IP fixed-window rate limiting for the OAuth endpoints.

Pure ASGI middleware (no Starlette BaseHTTPMiddleware) so it stays cheap and
only guards the unauthenticated OAuth surface. Bounded: empty buckets are
swept periodically.
"""

from __future__ import annotations

import time
from typing import Any

Limits = dict[str, tuple[int, int]]  # path -> (max_requests, window_seconds)
_SWEEP_INTERVAL_S = 60


class RateLimitMiddleware:
    def __init__(self, app: Any, *, limits: Limits):
        self.app = app
        self.limits = limits
        self._hits: dict[tuple[str, str], list[float]] = {}
        self._last_sweep = 0.0

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        rule = self.limits.get(path)
        if rule:
            now = time.monotonic()
            self._sweep(now)
            ip = (scope.get("client") or ("unknown", 0))[0]
            bucket = self._hits.setdefault((path, ip), [])
            bucket[:] = [t for t in bucket if t > now - rule[1]]
            if len(bucket) >= rule[0]:
                await self._reject(send)
                return
            bucket.append(now)

        await self.app(scope, receive, send)

    def _sweep(self, now: float) -> None:
        if now - self._last_sweep < _SWEEP_INTERVAL_S:
            return
        self._last_sweep = now
        for key in [k for k, v in self._hits.items() if not v or v[-1] <= now - _SWEEP_INTERVAL_S]:
            self._hits.pop(key, None)

    @staticmethod
    async def _reject(send: Any) -> None:
        body = b'{"error":"rate_limited","error_description":"Too many requests."}'
        await send(
            {
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", b"60"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
