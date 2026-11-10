---
name: mojon
description: "Inspect existing IMPERIAL Enterprise Skills through a local read-only MCP interface; validate, plan and simulate discounts without executing agents."
version: 0.1.0
---

# MOJON — Enterprise Skills × MCP

**Owner / Architect:** Alexander Nikolaevich Romaskevich (RomaskevicH)  
**Canonical authority:** Architect → HANTER → Federated Orchestrators → Nano Core Agents → Execution  
**Budget:** FREE_ONLY / USD 0  
**State:** local source-only, **not** a signed remote Skill, hosted ChatGPT Plugin or production agent.

## Intent

MOJON is a thin **read-only adapter** over existing `imperial_plugins.enterprise_skills` validators. The canonical Skill source remains [IMPERIAL-Skill](https://github.com/oromaskevic23-cmd/IMPERIAL-Skill). Never create parallel agent authority, silently install plugins or expand any privilege because a Skill descriptor is valid.

## Local MCP tools

| Tool | Allowed output | Explicit limit |
| --- | --- | --- |
| `mojon.status` | Verified code scope and deployment boundaries | Never claims hosted MCP |
| `mojon.list_skills` | 3 public data-only compatibility descriptors | Not cryptographically pinned to external Skill source |
| `mojon.validate_skill` | Closed-schema validation and SHA-256 of supplied descriptor | Does not verify signatures |
| `mojon.plan_skill` | Tenant/orchestrator/domain/capability exact match | Cannot start a worker |
| `mojon.simulate_discount` | Hypothetical integer-cent calculation | Cannot issue a price, coupon, payment or Owner approval |

## Mandatory security

**Deny by default**: AI Passport, Guardian Core, Approval Gateway, Owner Kill Switch, independent QA, ProofGraph and Audit Ledger are outside this demo. The server cannot make claims that they are connected. Preserve tenant boundaries, Zero Trust, CRYPTO IMPERIAL Ecosystem Boundary and Public/Private Boundary. No code execution, local file fetching beyond its packaged source, network calls, env-key access, credentials or commercial effects.

Users may intend Skills rather than monetary discounts. MOJON supports both safely: Enterprise Skills inspection and *optional mathematical discount simulation*. **There is no real Owner-approved discount schedule** in this repository.

## Usage

Run from repository root with Python 3.11+:

```sh
PYTHONPATH=src python3 tools/mojon_mcp.py
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_mojon_mcp.py' -v
```

MCP supports stateless `2026-07-28` request `_meta` and legacy `2025-11-25` initialize. JSON-RPC messages are one UTF-8 JSON object per line. All tools are read-only and require explicit compatible client behavior. stdout is protocol only.

## Production gates

Read-only localhost demo → CI tests → independent QA → signed release → private host with verified Owner keys → separately approved connector exposure → monitored runtime. No guarantee of ChatGPT plugin installation. No unknown third-party modules or unauthorized services may be installed.

**Architecture Before Implementation. Evidence Before PASS.**
