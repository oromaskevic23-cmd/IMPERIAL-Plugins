# IMPERIAL Search Indexing MCP — Source/Protocol Evidence (2026-11-03)

**Architect:** Alexander Nikolaevich Romaskevich (RomaskevicH).  
**Release classification:** FUNCTIONAL LOCAL MCP STDIO PROTOTYPE / NOT HOSTED / NOT CONNECTED TO GOOGLE SEARCH CONSOLE.

## Verified CI

**Run:** https://github.com/oromaskevic23-cmd/IMPERIAL-Plugins/actions/runs/41704769008  
**Revision:** `0e0116ddf7b6a54ff1748f3e426ed878c590fab3`  
**Result:** SUCCESS on Python 3.11 and 3.12.

Each Python-version job ran **20 deterministic/adversarial tests** successfully (40 test executions total, consisting of the same 20 tests repeated across two Python versions). The suite exercises:

- Modern MCP `2026-07-28`: `server/discover`, per-request metadata, tool discovery and invocation.
- Legacy MCP `2025-11-25`: `initialize`, `tools/list`, `tools/call`.
- Real stdio subprocess and newline-delimited JSON-RPC round trip.
- Strict four-tool read-only registry and evidence scope.
- Deny unknown tools/versions, inappropriate arguments, invalid inputs and notification-driven tool execution.
- Reject public-site redirect, foreign host/path, malformed/duplicated sitemap, missing canonical or inconsistent JSON-LD, unsafe `robots.txt`.
- Defend private repository boundary and return `UNVERIFIED` for Google indexing.

## Real public HTTP tests (same CI run)

The read-only MCP verifier requested the fixed, approved GitHub Pages endpoints. The runner recorded:

| Site | Real HTTP/source audit | Canonical sitemap entries | Public project metadata |
|---|---|---:|---:|
| Founder — `/oromaskevic23-cmd/` | PASS | 12 | 23 |
| IMPERIAL Core company — `/Capital-Core-Public/` | PASS | 25 | 23 |

For each site, the implementation checked base, project directory, root sitemap and `robots.txt` (four GETs; eight total). Verified only source/published-web correctness. All requests use exact host/path allowlists and refuse redirects.

## What this does not prove

- No currently installed/registered ChatGPT MCP connection.
- No deployed server on an internet-accessible host.
- No authorized Google Search Console OAuth account or verified property.
- No sitemap submitted to Google's `sitemaps.submit` API.
- No Google crawled or indexed URL count, no query impressions, rankings or Knowledge Graph.
- No autonomous running NCA orchestrator, persistent external Audit Ledger, or financially authorized actions.

The future production connector needs AI Passport, Enterprise Skills, Guardian Core, Approval Gateway, Owner Kill Switch, Audit Ledger, real owner authorization and independent Google API receipt. Do not substitute GitHub test outcomes for Google indexing evidence.

**Operator guide:** [SEARCH_INDEXING_MCP.md](SEARCH_INDEXING_MCP.md)  
**Code:** [indexing_mcp.py](../src/imperial_plugins/indexing_mcp.py)  
**Tests:** [test_indexing_mcp.py](../tests/test_indexing_mcp.py).

Architecture → Implementation → Evidence.
