# MOJON — Enterprise Skills × MCP × Commercial Simulation

**Program:** IMPERIAL Core  
**Founder / Owner / CEO / Chief Systems Architect:** Alexander Nikolaevich Romaskevich (RomaskevicH)  
**Release candidate:** 0.1.0 — local source only  
**Date:** 2026-11-10  
**Budget:** FREE_ONLY / USD 0

## Purpose

MOJON is an original **plugin inside the existing IMPERIAL-Plugins repository**, not a new GitHub repository or an independently deployed cloud service. It bridges:

1. Canonical **IMPERIAL-Skill** source-controlled Enterprise Skills,
2. Existing **IMPERIAL-Plugins** strict Skill descriptor validator and tenant-bound registry,
3. JSON-RPC **Model Context Protocol (MCP)** tool discovery and read-only calls,
4. A future protected HANTER adapter and optional **commercial discount simulations** for HARVEY.

**Important interpretation:** The user's phrase may refer to Skills (`скиллы`) or commercial discounts (`скидки`). MOJON supports both conservatively: reviewed Skill planning and a *non-binding mathematical pricing simulation*. No discount schedule, coupon, final price, external sale or payment is approved.

## Canonical architecture

```text
Architect — final authority
  |
HANTER — AI Command Center
  |
Federated Orchestrators (ASTRA one of them)
  |
MOJON — local read-only MCP tool surface
  +-- IMPERIAL-Skill reference → Enterprise Skills Registry validator
  +-- Skill tenant/orchestrator/Runtime Domain planning
  +-- Optional HARVEY discount arithmetic simulation
  |
Guardian Core / Approval Gateway / AI Passport (NOT CONNECTED)
  |
Nano Core Agents / Execution (NOT ENABLED)
  |
Independent QA → ProofGraph → Audit Ledger (NOT CONNECTED)
```

MOJON does not issue AI Passport, owner permits or keys; it cannot call VELION, affect sales, access Supabase/Render/CRM, deploy a worker, alter GitHub or write to CRYPTO IMPERIAL Ecosystem.

## MCP compatibility

The **2026-07-28** MCP protocol uses stateless requests carrying `_meta` with `io.modelcontextprotocol/protocolVersion` and `io.modelcontextprotocol/clientCapabilities`; `server/discover` and `tools/list` are supported. MOJON additionally supports **2025-11-25** legacy `initialize` on the same local stdio runner. No HTTP endpoint or OAuth server is enabled.

**Protocol source:** https://modelcontextprotocol.io/specification/2026-07-28/ and https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/docs/specification/2026-07-28

### Available read-only tools

| MCP tool | Meaning | Authorizes execution? |
| --- | --- | --- |
| `mojon.status` | Actual local source/deployment limits | No |
| `mojon.list_skills` | Data-only compatibility summaries of three existing reviewed Skills | No |
| `mojon.validate_skill` | Validate a closed-schema descriptor, calculate SHA-256 | No |
| `mojon.plan_skill` | Check tenant, orchestrator, Runtime Domain and capability match | No |
| `mojon.simulate_discount` | Proposed discount in integer cents using client-supplied, **unverified** percentage limit | No |

Skill source: [IMPERIAL-Skill](https://github.com/oromaskevic23-cmd/IMPERIAL-Skill). MOJON intentionally **does not pin or cryptographically attest the current upstream revision**. A data-only match must not be represented as certified source equality or independent QA.

### Demonstration

From the repository root:

```sh
PYTHONPATH=src python3 tools/mojon_mcp.py
```

Send a JSON-RPC message on **one line**:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{},"io.modelcontextprotocol/clientInfo":{"name":"authorized-local-client","version":"0.1"}}}}
```

A second request to inspect a Skill without starting a worker:

```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mojon.plan_skill","arguments":{"skill_id":"imperial.skill.security-review","tenant_id":"imperial-internal","orchestrator_id":"security-orch","runtime_domain":"SECURITY_DEFENSIVE","capability":"simulate:task"},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}
```

Expected scope: `planned=true`, `execution_authorized=false`, `owner_ed25519_verified=false`, `dispatch_performed=false`. A plan is not an Approval Gateway permit.

### Optional discount simulation

The simulation takes:
- `list_price_cents`: unsigned integer 0–1,000,000,000
- `requested_discount_bps`: integer basis points, 0–10,000 (1% = 100 bps)
- `unverified_policy_limit_bps`: upper limit supplied *by the caller*, not a trusted policy

It returns a proposed mathematical amount in integer cents with half-up rounding only when request ≤ supplied limit. Every result includes `real_quote_issued=false`, `payment_authorized=false`, and `owner_discount_policy_verified=false`. Real policies, discount authority, legal invoices, contract approvals and tax rules require a future private signed HARVEY integration.

## Development and CI

Python 3.11+; no third-party runtime libraries:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_mojon_mcp.py' -v
PYTHONPATH=src python3 tools/validate_manifests.py
python3 -m py_compile src/imperial_plugins/mojon_mcp.py tools/mojon_mcp.py
```

The separate GitHub Actions workflow `.github/workflows/mojon-mcp.yml` runs Python 3.11/3.12 tests, malicious input and protocol regression cases, manifest checks and fail-closed authority checks. PR approval and production integration are separate gates.

### Security and denial principles

- No untrusted Skill execution, remote module import, subprocess invocation or arbitrary file access.
- Bounded 64 KiB JSON-RPC request frames, reject duplicate JSON keys, invalid method/ID, unsupported protocol and malformed `_meta`.
- No sensitive arguments reflected in error responses, no progress logs on stdout.
- No arbitrary network or browser actions; no usernames/passwords, keys, cameras or personal data captured.
- Skills are exact version, tenant/orchestrator and Runtime Domain isolated; source registry claims are **unverified until signed external source checks**.
- No hidden elevation from `mojon.plan_skill`, `mojon.validate_skill`, a discount percentage or MCP capability registration.
- Owner Kill Switch, Guardian Core, Approval Gateway, AI Passport, Enterprise Skills, Audit Ledger, ProofGraph, Zero Trust, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary remain mandatory before any future external execution.

## Production gate / honest maturity

**SOURCE-IMPLEMENTED:** Local stdio MCP, data-only Skill planner, simulated discounts, tests, manifest and CI configuration.

**NOT DELIVERED:** Installed ChatGPT plugin, hosted MCP server, real Owner Ed25519 enrollment, authenticated connector to HANTER/ASTRA/VELION/NCA, independent security review, enforced release signature, approved commercial discount rules, actual customer price or production agent execution.

Next gate: private, signed, read-only HANTER integration and independent QA of exact PR revision; keep user pricing and authority changes out of automatic MCP tools.

**Architecture Before Implementation. Evidence Before PASS.**
