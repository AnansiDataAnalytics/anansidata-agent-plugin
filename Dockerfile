# syntax=docker/dockerfile:1

# --- builder: install dependencies, then the project -------------------------
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first (cached layer; only uv.lock/pyproject.toml are inputs).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable --no-dev --extra apps

# Project source.
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev --extra apps

# --- runner: virtualenv only, non-root ---------------------------------------
FROM python:3.13-slim AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY --from=builder --chown=app:app /app/.venv /app/.venv

USER app
EXPOSE 8000

# Liveness via the public discovery endpoint (returns 200; /mcp is 401 by design).
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/.well-known/oauth-authorization-server', timeout=3).status == 200 else 1)"

# Runtime config comes from the environment, never baked in:
#   ANANSI_API_BASE_URL, ANANSI_MCP_BASE_URL, ANANSI_DATASET,
#   FIREBASE_API_KEY, FIREBASE_PROJECT_ID, FIREBASE_AUTH_DOMAIN, MCP_SESSION_SECRET
#
# Behind a reverse proxy, disable response buffering so MCP SSE streams work.
ENTRYPOINT ["anansidata-agent-plugin", "--http", "--host", "0.0.0.0", "--port", "8000"]
