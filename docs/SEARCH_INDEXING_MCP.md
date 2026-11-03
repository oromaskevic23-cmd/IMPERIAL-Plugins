# IMPERIAL Search Indexing MCP — Enterprise reference v0.1

**Founding Architect:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder • Owner • CEO • Chief Systems Architect of IMPERIAL Core.

**Implementation state:** Runnable **read-only local MCP stdio server**, with actual JSON-RPC tool discovery/calls. Real public website checks are supported on demand. This is not a hosted, registered or connected ChatGPT plugin and does **not** claim Google indexation. No Google account, Google Contacts, Search Console authorization or OAuth session is attached to this server.

## Purpose

A single, reusable MCP interface for the **public** IMPERIAL Core project registry, evidence-driven SEO audits and prepared Google Search Console submission steps. It is a public-discovery skill that can be used from compatible MCP clients after the client operator connects the local process. Its core code is deliberately separate from any production permission/approval or crawler service.

This public project registry was reconciled on **2026-11-03** from the authorized GitHub owner's inventory: **32** repositories, of which **25** were public and **7** private. It lists **23** public technology/business projects, excluding the separate founder profile and non-product legal planning blueprint. Repository visibility and project inventory may change: **the manifest is a dated snapshot, not live GitHub search**.

## Tools

| Tool name | Inputs | Verified operation | Important limit |
|---|---|---|---|
| `imperial.indexing_status` | none | Returns snapshot scope and Google evidence status | Google remains `UNVERIFIED` |
| `imperial.list_public_projects` | none | Lists 23 public GitHub project URLs and descriptions | Never lists private repository URLs |
| `imperial.audit_published_site` | `{"site_id":"founder"}` or `{"site_id":"company"}` | GET of four strict allowlisted URLs; robots + sitemap + canonical + ItemList validation | This proves published HTTP/content checks only, not Google crawl or indexing |
| `imperial.search_console_plan` | none | Returns correct Google URL-prefix properties, sitemaps, evidence limits | Read-only; does **not** submit to Google |

The network tool does not accept arbitrary URLs; the two hosts, URL subtrees and exact endpoints are hardcoded against SSRF and private-network access. Redirects and oversize responses are rejected. It runs **no untrusted repository code** and has no capability to read local private files, customer databases or Google tokens.

## Run

From a local checkout of [IMPERIAL-Plugins](https://github.com/oromaskevic23-cmd/IMPERIAL-Plugins) with Python 3.11+:

```sh
python3 tools/search_indexing_mcp.py
```

The process uses **MCP stdio**, so it emits no human log text to stdout. A compatible MCP client launches it as a child process and communicates with JSON-RPC newline-delimited frames.

Example **local MCP client configuration** (replace the path with an actual checked-out local path):

```json
{
  "mcpServers": {
    "imperial-search-indexing": {
      "command": "python3",
      "args": ["/ABSOLUTE/PATH/IMPERIAL-Plugins/tools/search_indexing_mcp.py"]
    }
  }
}
```

On Windows, replace `python3` with the installed Python executable as appropriate. MCP clients use different setup interfaces, configuration locations and approval flows; this example is **not an installed integration** or evidence that the user has already connected the MCP.

## Protocol and verification

- Dual-era JSON-RPC: **MCP 2025-11-25** (legacy `initialize`, `tools/list`, `tools/call`) and **MCP 2026-07-28** (modern `server/discover`, request `_meta`, `resultType: complete`, response serverInfo).
- The implementations use Python standard library only; no arbitrary pip dependency or unpinned remote installer.
- Only the `tools` capability is advertised; no capabilities for OAuth prompts, resources, subscriptions, trading, financial transfers, external task execution or Google search-spam APIs.
- Tests cover protocol message validation, hostile input, public/private boundaries, dangerous URLs, malformed sitemaps, duplicate URLs, wrong canonical and altered structured data.
- Reproducible offline test: `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_indexing_mcp.py' -v`.
- Full existing suite: `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
- CI: `.github/workflows/search-indexing-mcp.yml`. A PASS proves that **specific commit's tests**, not a production hosted MCP deployment.

## Enterprise integration architecture

```text
Architect / Final Architectural Decision Authority
  -> HANTER AI Command Center
      -> Federated SEO/Publishing Orchestrator (future private runtime)
          -> Search Indexing MCP (this public read-only interface)
              -> Public registry / approved GitHub Pages
              -> HTTP / robots / XML sitemap / JSON-LD source evidence
          -> Privately provisioned Google Search Console read connector (source implemented, not OAuth-connected)
              -> sites.list / sitemaps.list / URL Inspection (read-only API methods)
              -> Mutation path kept disabled; owner-approved submit still requires separate gateway
              -> AI Passport + Enterprise Skills
              -> Guardian Core (deny by default)
              -> Approval Gateway (explicit human authorization)
              -> Audit Ledger (durable immutable evidence)
              -> External API receipt + Search Console URL Inspection
```

The private production connector must use OAuth with the user's actual Search Console property, isolated secrets, audit logs and explicit human approval for any write. The separately implemented [Google submission gate](../src/imperial_plugins/search_console_submit.py) contains an exact allowlisted `PUT` transport, short-lived Owner/independent-QA verifier hooks, a default-enabled kill switch, local SQLite replay prevention and a hash-linked operation journal. It is **not exported as an MCP tool**, and actual Google OAuth and a production permit verifier are absent. See the [release and security specification](GOOGLE_SEARCH_CONSOLE_APPROVAL_GATEWAY.md). Google Search Console `sitemaps.submit` requires `https://www.googleapis.com/auth/webmasters`; successful submission is not proof that URLs were indexed.

**Do not abuse Google's restricted Indexing API for generic software project pages**: it is intended for supported `JobPosting` and `BroadcastEvent` livestream structured-data content. Public project pages should use valid sitemap discovery and Search Console ownership/inspection rather than fake rapid-indexing APIs.

## Required future production gates

1. Verified current GitHub read-only token scope or safe public inventory crawl; detect repo-visibility changes before updating the public registry. Never write private names/paths into publicly exposed telemetry.
2. Actual local operator-controlled MCP installation, host-level permissions and audit logs.
3. Independent OAuth connection for both distinct Search Console URL-prefix properties.
4. Implement, independently review and authorize the separate sitemap submission writer only after real owner approval; the currently implemented Google adapter is **read-only** and provides an exact allowlisted PUT preflight but does not send it.
5. Optional Google Search Console read-only inspection reports and reconciled errors.
6. Separate sandbox integration, credential isolation, signed releases, rollback and security review.
7. If ever served over HTTP, implement a production-approved Streamable HTTP transport, Origin checks, authenticated sessions, rate limits and network ACLs. **Do not expose this stdio prototype directly to the public internet**.

## Primary specs and reference documentation

- MCP 2026-07-28 tools: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- MCP versioning: https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
- MCP 2025-11-25 tools: https://modelcontextprotocol.io/specification/2025-11-25/server/tools
- Google Search Console sites.list: https://developers.google.com/webmaster-tools/v1/sites/list
- Google Search Console sitemaps.list: https://developers.google.com/webmaster-tools/v1/sitemaps/list
- Google URL Inspection: https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect
- Google Search Console sitemaps.submit: https://developers.google.com/webmaster-tools/v1/sitemaps/submit
- Google restricted Indexing API: https://developers.google.com/search/apis/indexing-api/v3/using-api

**Architecture → Implementation → Evidence**. No false Google ranking, indexing, legal authority, financial returns or live NCA claims.
