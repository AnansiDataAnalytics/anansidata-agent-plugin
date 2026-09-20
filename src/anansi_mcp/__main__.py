"""Entry point: `uv run anansidata-agent-plugin [--http]`."""

from __future__ import annotations

import argparse

from .server import build_server

# Unauthenticated OAuth endpoints are rate-limited per IP.
OAUTH_RATE_LIMITS = {
    "/register": (10, 60),
    "/token": (60, 60),
    "/login/session": (20, 60),
}


def main() -> None:
    parser = argparse.ArgumentParser(prog="anansidata-agent-plugin")
    parser.add_argument(
        "--http", action="store_true", help="serve streamable HTTP instead of stdio"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    mcp = build_server()
    if not args.http:
        mcp.run()
        return

    import uvicorn
    from starlette.middleware import Middleware

    from .ratelimit import RateLimitMiddleware

    app = mcp.http_app(
        middleware=[Middleware(RateLimitMiddleware, limits=OAUTH_RATE_LIMITS)]
    )
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
