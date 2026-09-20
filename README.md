# Anansi MCP

FastMCP server exposing Anansi's harmonized macroeconomic data to AI agents.

Read-only. See [`spec.md`](./spec.md) for the source of truth.

## Layout

```
src/anansi_mcp/     server, Anansi API client, name resolution, compute, tools
skills/             Agent Plugin skills (domain knowledge)
plugin.json         Agent Plugins 1.0 manifest (+ OpenAI presentation)
mcp.json            MCP server entry (production URL)
dist/               built plugin folder + anansi-data-plugin.zip
.agents/plugins/    local marketplace pointing at dist/anansi-data
```

## Run locally

```bash
cp .env.example .env      # fill in the Firebase web config + MCP_SESSION_SECRET
uv sync
uv run anansidata-agent-plugin --http  # streamable HTTP on http://127.0.0.1:8000/mcp
```

`ANANSI_MCP_BASE_URL` must exactly match the URL the client connects to. Codex
uses `127.0.0.1` loopback callbacks, so keep `127.0.0.1` (not `localhost`) here
and in the client config — a host mismatch stops OAuth discovery.

## Connect a client (Codex)

Add the server with the matching URL, then start the login:

```bash
codex mcp add anansi --url http://127.0.0.1:8000/mcp
codex mcp login anansi            # opens the browser: sign in, then Authorize
```

In the ChatGPT desktop app / IDE extension: Settings → MCP servers → Add server
→ Streamable HTTP → `http://127.0.0.1:8000/mcp` → Save → **Restart**, then click
**Authenticate** on the server row.

## Install the plugin locally

The bundle is a portable Agent Plugins package: root `plugin.json` (with the
OpenAI `extensions.com.openai` presentation block), `mcp.json`, and `skills/`.
`dist/anansi-data/mcp.json` points at the local server; the repo-root
`mcp.json` keeps the production URL.

Use the repo marketplace (`.agents/plugins/` points at `dist/anansi-data`):

```bash
codex plugin marketplace add "<path to this repo>"
```

Then open the Plugins Directory, pick the **Anansi (local)** marketplace, and
install **Anansi Data**. Or unzip `dist/anansi-data-plugin.zip` and point the
host at the extracted `anansi-data/` folder. Start the server first so the MCP
URL resolves.

When `plugin.json` or `skills/` change, refresh `dist/anansi-data/` from them
and re-zip.

## Test

```bash
uv run pytest
uv run ruff check .
```

