# Anansi MCP — Technical Specification

## 1. What we're building

An Agent Plugin that gives AI agents (ChatGPT / Codex, Claude Code, and other MCP-compatible clients) read-only access to Anansi's harmonized macroeconomic data.

A user installs the plugin, signs in with their existing Anansi account, authorizes read-only access, and can then ask the agent questions that it answers by calling Anansi MCP tools.

The backend is not modified. The MCP reuses the existing authenticated platform API exactly as the web console does.

---

## 2. Components

| Component | Host | Responsibility |
|---|---|---|
| Anansi MCP Server | `mcp.anansidata.com` | FastMCP server; owns the OAuth flow for MCP clients; signs users in with their Anansi account; exposes tools |
| Anansi Platform API | `api.anansidata.com/api` | Data access; entitlement enforcement (existing, unchanged) |
| Agent Plugin package | repo `anansidata-agent-plugin` | `plugin.json`, `mcp.json`, `skills/` |

The MCP never stores passwords and never re-implements access rules. Entitlements stay enforced by the platform API.

---

## 3. Datasets

| id | Name | Contents |
|---|---|---|
| `wed` | World Economic Database | Broad economic coverage |
| `gmd` | Global Macro Database | Global macro series, ~14k series, 240 countries, ~50 indicators, 1970–2030 |

The dataset is selected per request with the `X-Database` header. Both datasets share one data shape.

### Series code format

```
USA_CPI_A      {ISO3}_{indicator}_{frequency}
```

Frequencies: `A` (annual), `Q` (quarterly), `M` (monthly).

### Data model

| Collection | One document per | Key fields |
|---|---|---|
| `Series` | country × indicator × frequency | `series_code`, `name`, `country`, `country_code`, `region`, `indicator`, `indicator_short`, `frequency`, `unit`, `unit_metadata`, `stats` (coverage, last value), `available_sources` (name, coverage, is_contributing) |
| `SeriesData` | series × date | `date`, `current.value`, `current.is_forecast`, `versions[]`, `source_values` (internal) |

### Name resolution

Names are resolved with the reference data already in the backend, so spellings stay consistent with the rest of the platform.

| Input | Resolved to | Source |
|---|---|---|
| Country name or code | canonical `country` name + ISO3 | `alphacodes.csv` (alpha-2, alpha-3, numeric, short name) |
| Region | member country names | `config/country-reference.js` |
| Indicator name | exact `indicator` name (or `indicator_short`) | `/api/filters/indicator` and series records |

The platform API filters by canonical `country` name, not ISO3. ISO3 is used only inside series codes.

### What we expose

- Harmonized values only. Per-source values stay internal.
- Forecasts are included and always labelled (`is_forecast`).
- Every value carries its `unit`; derived values are labelled by type (`yoy_pct`, `pct_of_gdp`, etc.).

---

## 4. Authentication

The MCP runs the OAuth 2.1 authorization code flow (with PKCE) for MCP clients, and uses Firebase for the actual sign-in. This is the same identity the web console uses; no backend changes.

| Step | Where | What happens |
|---|---|---|
| 1 | MCP client | User clicks **Install** |
| 2 | MCP | Client discovers `/.well-known/oauth-protected-resource` and the MCP authorization server |
| 3 | MCP | Client registers (Dynamic Client Registration) and opens the browser to `/oauth/authorize` |
| 4 | MCP | Login screen: the user signs in with their Anansi account (Firebase email/password or Google) |
| 5 | MCP | Consent screen: "Anansi MCP Server wants read-only access to your Anansi macro data" |
| 6 | MCP | Redirects back to the client with a code |
| 7 | MCP | Client exchanges the code for an MCP access token (scope `macro.read`) |

### Authorization server endpoints (hosted by the MCP)

| Endpoint | Purpose |
|---|---|
| `/.well-known/oauth-authorization-server` | Server metadata |
| `/.well-known/oauth-protected-resource` | Resource metadata |
| `/oauth/register` | Dynamic Client Registration |
| `/oauth/authorize` | Login (Anansi/Firebase), then consent |
| `/oauth/token` | Code → access token (PKCE verified) |
| `/oauth/jwks.json` | Public key for token verification |

### How the MCP calls the backend

After sign-in the MCP holds the user's Firebase refresh token (encrypted at rest). On every tool call it mints a fresh Firebase ID token and sends it to the platform API:

```
Authorization: Bearer <Firebase ID token>
X-Database: <wed|gmd>
```

The platform API verifies the token with Firebase Admin, resolves the user, and enforces the same entitlements as the web console. The MCP is a resource server to MCP clients and a Firebase client to the backend.

Authentication is mandatory for every tool call. There is no anonymous access, no shared credential, and no development bypass.

The plugin package holds no secrets. Scope: `macro.read` (read-only).

---

## 5. Data access

The MCP calls the platform API at `{ANANSI_API_BASE_URL}/api` with the user's Firebase ID token. No API keys, no `/v1`.

| Piece | Detail |
|---|---|
| Surface | `/api/*` (the same surface the web console uses) |
| Auth | `Authorization: Bearer <Firebase ID token>` |
| Dataset | `X-Database: wed` or `gmd` |
| Enforcement | Existing platform authenticate + entitlement guard — unchanged |
| Base URL | `http://localhost:5001` locally, `https://api.anansidata.com` in production |

### Endpoints used

| Endpoint | Returns |
|---|---|
| `/api/auth/entitlements` | The signed-in user's datasets and access |
| `/api/series` | Series search (`country`, `indicator`, `frequency`, `source`, `search`, `startDate`, `endDate`, `page`, `limit`) |
| `/api/series/{code}` | One series' metadata and provenance |
| `/api/series/{code}/data` | Observations (`startDate`, `endDate`, `limit`) |
| `/api/series/download` | Bulk observations as CSV by `series_codes` or filters |
| `/api/series/{code}/versions` | Version history for one data point |
| `/api/filters/{field}` | Distinct values: `country`, `indicator`, `frequency`, `source`, `unit`, `region` |
| `/api/filters/stats` | Dataset totals |
| `/api/sources` | Displayable source hierarchy |
| `/api/sources/available` | Sources with data, with coverage statistics |

Parameters are camelCase on this surface (`startDate`, `endDate`, `search`); responses use the existing shapes and `{ data, pagination }` envelope.

---

## 6. Tools

The MCP composes `/api` calls into task-shaped tools. The agent works with country and indicator names; the MCP resolves them to canonical names and series codes internally, and returns codes only for chaining.

| Tool | Purpose | Built from |
|---|---|---|
| `list_datasets` | Datasets this account can access | `/api/auth/entitlements` |
| `list_countries` | Countries with ISO3 and region | `/api/filters/country` + reference |
| `list_indicators` | Indicator names and codes | `/api/filters/indicator` |
| `list_frequencies` | Frequencies present | `/api/filters/frequency` |
| `list_sources` | Data sources and coverage | `/api/sources`, `/api/sources/available` |
| `search_series` | Find series by country, indicator, region, frequency, coverage | `/api/series` |
| `get_series` | Metadata and provenance for one series | `/api/series/{code}` |
| `get_series_data` | Observations for one or more series | `/api/series/{code}/data`, `/api/series/download` |
| `compare_countries` | One indicator across several countries, aligned | `/api/series` + `/api/series/{code}/data` |
| `get_country_profile` | Headline macro snapshot for a country | `/api/series` + data + local compute |
| `rank_countries` | Countries ranked by an indicator for a period | `/api/series` + `/api/series/download` |
| `compute_series` | Growth, CAGR, correlation, spread, rebase, moving average | data + local compute |
| `check_coverage` | Coverage, forecast tail, and contributing sources | `/api/series/{code}` + `stats` |
| `chart_series` | Single-series chart | Data tools + view |
| `chart_compare` | Multi-country chart | Data tools + view |
| `chart_country_profile` | Country dashboard | Data tools + view |

### Rules

- The agent never supplies a series code for a normal request; tools resolve country names (or ISO3) and exact indicator names internally.
- Resolution is exact. A name that doesn't match returns `status: not_found`, echoes the input, and includes a clear hint naming the right discovery tool. The agent then self-serves with `list_countries`, `list_indicators`, or `search_series` and retries. There is no fuzzy matching and no suggestion engine.
- Hints are written per tool — specific and actionable, never a generic "not found". For example:
  - `"No country matched 'Bharat'. Call list_countries for valid countries, or pass the ISO3 code (e.g. IND)."`
  - `"No India series for 'Weekly'. This indicator has Annual, Quarterly, and Monthly — call search_series to see what exists."`
- Deterministic math (growth, CAGR, correlation, spread) happens in the tool, not the model.
- Responses default to concise (summary + latest points); full series is opt-in.
- All values carry units; forecasts are always labelled.
- The MCP never dumps raw series into the model; it aggregates, trims, and paginates.

---

## 7. Response format and charts

Every tool returns structured data and a text summary. Chart tools additionally return a UI view via MCP Apps.

| Host | What the user sees |
|---|---|
| MCP Apps capable (Claude, VS Code, M365 Copilot) | Data plus rendered chart |
| No UI support (ChatGPT) | Data plus text summary |

Charts are never required for a tool to work, and no tool fails when the client cannot render UI.

---

## 8. Plugin package

```
anansidata-agent-plugin/
├── plugin.json          # Agent Plugins 1.0 manifest
├── mcp.json             # remote server: streamable-http → https://mcp.anansidata.com/mcp
└── skills/
    ├── macro-analysis/SKILL.md
    ├── country-comparison/SKILL.md
    └── data-caveats/SKILL.md
```

`mcp.json` declares a single `streamable-http` server. No stdio, no secrets in the package.

Skills carry the domain knowledge that keeps tool use correct: how to choose indicators, how to interpret units, forecast vs actual, coverage gaps, aggregate vs country.

---

## 9. Deployment

| Item | Decision |
|---|---|
| MCP repo | Separate repository (`anansidata-agent-plugin`), Python, FastMCP |
| MCP transport | Streamable HTTP at `mcp.anansidata.com` |
| Backend changes | None |
| Data surface | Platform `/api`, Firebase ID token + `X-Database` |
| Auth | MCP-hosted OAuth 2.1 server, federating to the Anansi (Firebase) login |
