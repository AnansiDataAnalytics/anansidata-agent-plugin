"""HTTP client for the Anansi platform API (`/api`).

This is the same surface the web console uses. Auth is the user's Firebase ID
token and the dataset travels as the `X-Database` header. Entitlement
enforcement stays on the server.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from .config import Settings
from .errors import AnansiAPIError

PLATFORM_PATH = "/api"

TokenProvider = Callable[[bool], Awaitable[str | None]]

# Retry once with a freshly minted token when the backend rejects a cached one
# (e.g. the user verified their email after the token was issued).
_RETRY_STATUSES = (401, 403)


def _clean(params: dict[str, Any] | None) -> dict[str, Any]:
    return {k: v for k, v in (params or {}).items() if v is not None and v != ""}


def _norm_date(value: Any) -> str | None:
    if not value:
        return None
    return str(value)[:10]


class AnansiClient:
    def __init__(self, settings: Settings, token_provider: TokenProvider):
        self._settings = settings
        self._token_provider = token_provider
        self._http = httpx.AsyncClient(
            base_url=f"{settings.base_url}{PLATFORM_PATH}",
            timeout=settings.timeout,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _headers(self, dataset: str | None, force: bool = False) -> dict[str, str]:
        token = await self._token_provider(force)
        if not token:
            raise AnansiAPIError(
                401, "unauthenticated", "Sign in required to access Anansi data."
            )
        headers = {
            "Accept": "application/json",
            "X-Anansi-Client": "mcp",
            "Authorization": f"Bearer {token}",
        }
        if dataset:
            headers["X-Database"] = dataset
        return headers

    async def _request(
        self, path: str, params: dict[str, Any] | None, dataset: str | None
    ) -> httpx.Response:
        clean = _clean(params)
        response = await self._http.get(
            path, params=clean, headers=await self._headers(dataset)
        )
        if response.status_code in _RETRY_STATUSES:
            response = await self._http.get(
                path, params=clean, headers=await self._headers(dataset, force=True)
            )
        return response

    async def _get(
        self, path: str, params: dict[str, Any] | None = None, dataset: str | None = None
    ) -> Any:
        response = await self._request(path, params, dataset)
        if response.status_code >= 400:
            raise self._error(response)
        return response.json()

    @staticmethod
    def _error(response: httpx.Response) -> AnansiAPIError:
        code: Any = response.status_code
        message = response.reason_phrase
        reason = None
        try:
            error = response.json().get("error")
            if isinstance(error, dict):
                code = error.get("code") or code
                message = error.get("message") or message
                reason = error.get("reason")
            elif isinstance(error, str):
                message = error
        except ValueError:
            message = response.text[:200] or message
        return AnansiAPIError(
            response.status_code, str(code), message, reason=reason
        )

    # --- account ---

    async def entitlements(self) -> dict[str, Any]:
        return await self._get("/auth/entitlements")

    # --- dimensions (names / values, dataset-scoped) ---

    async def countries(self, dataset: str) -> list[str]:
        return await self._get("/filters/country", dataset=dataset)

    async def indicators(self, dataset: str) -> list[str]:
        return await self._get("/filters/indicator", dataset=dataset)

    async def frequencies(self, dataset: str) -> list[str]:
        return await self._get("/filters/frequency", dataset=dataset)

    async def units(self, dataset: str) -> list[str]:
        return await self._get("/filters/unit", dataset=dataset)

    async def stats(self, dataset: str) -> dict[str, Any]:
        return await self._get("/filters/stats", dataset=dataset)

    async def sources(self, dataset: str) -> dict[str, Any]:
        return await self._get("/sources", dataset=dataset)

    async def sources_available(self, dataset: str, **filters: Any) -> dict[str, Any]:
        return await self._get("/sources/available", filters, dataset=dataset)

    # --- catalog ---

    async def series_search(self, dataset: str, **params: Any) -> dict[str, Any]:
        return await self._get("/series", params, dataset=dataset)

    async def search_all_series(self, dataset: str, **params: Any) -> list[dict[str, Any]]:
        page, out = 1, []
        while True:
            body = await self.series_search(
                dataset, page=page, limit=self._settings.page_size, **params
            )
            out.extend(body.get("data", []))
            pages = (body.get("pagination") or {}).get("pages") or 1
            if page >= pages:
                return out
            page += 1

    async def series(self, dataset: str, code: str) -> dict[str, Any] | None:
        try:
            return await self._get(f"/series/{code}", dataset=dataset)
        except AnansiAPIError as err:
            if err.status == 404:
                return None
            raise

    # --- observations ---

    async def series_data(
        self,
        dataset: str,
        code: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        body = await self._get(
            f"/series/{code}/data",
            {"startDate": start_date, "endDate": end_date, "limit": limit},
            dataset=dataset,
        )
        return [self._obs(point) for point in body.get("data", [])]

    def _obs(self, point: dict[str, Any]) -> dict[str, Any]:
        return {
            "date": _norm_date(point.get("date")),
            "value": point.get("value"),
            "is_forecast": bool(point.get("is_forecast")),
        }

    async def series_data_many(
        self,
        dataset: str,
        codes: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        concurrency: int = 10,
    ) -> dict[str, list[dict[str, Any]]]:
        """Read several series concurrently via the read endpoint.

        Deliberately not the CSV `/download` endpoint: the platform treats that
        as an export and blocks it for trials. Reads honor the read limits.
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch(code: str):
            async with semaphore:
                return code, await self.series_data(
                    dataset, code, start_date, end_date, limit
                )

        pairs = await asyncio.gather(*(fetch(code) for code in codes))
        return {code: observations for code, observations in pairs}
