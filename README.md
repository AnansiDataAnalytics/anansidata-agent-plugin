# Anansi Data — Agent Plugin

Read-only access to Anansi's harmonized macroeconomic data — GDP, inflation,
unemployment, government debt, interest rates, and more — across 240+ countries.

The plugin connects to the Anansi MCP server at `https://mcp.anansidata.com/mcp`
and works in **Claude Code** and **Codex / ChatGPT**.

This repository is a plugin **marketplace**: it ships the plugin manifest, skills,
and MCP wiring. It contains no server code and no secrets.

## Install — Codex / ChatGPT

Add the marketplace from this GitHub repo, then install the plugin:

1. Open **Add plugin marketplace**.
2. Source: `thekernelkiller/anansidata-agent-plugin` (or the full Git URL).
3. Git ref: `main`, Sparse paths: leave blank.
4. **Add marketplace** → open the Plugins Directory → install **Anansi Data**.
5. Sign in with your Anansi account when prompted.

CLI equivalent for adding the marketplace (install the plugin from the Plugins Directory):

```bash
codex plugin marketplace add thekernelkiller/anansidata-agent-plugin
```

## Install — Claude Code

```
/plugin marketplace add thekernelkiller/anansidata-agent-plugin
/plugin install anansi-data@anansi
```

Authenticate the MCP server from `/mcp` when prompted.

## Layout

```
.agents/plugins/marketplace.json     Codex marketplace catalog
.claude-plugin/marketplace.json      Claude Code marketplace catalog
plugins/anansi-data/
├── plugin.json                      portable Agent Plugins manifest (Codex)
├── mcp.json                         portable MCP server entry
├── .claude-plugin/plugin.json       Claude Code manifest
├── .mcp.json                        Claude Code MCP server entry
└── skills/                          macro-analysis, country-comparison, data-caveats
```

The two manifest/MCP pairs are the native layouts for each host and point at the
same hosted server. There is no bundled server, so both declare the remote
`streamable-http` endpoint only.

## Links

- Website: https://www.anansidata.com
