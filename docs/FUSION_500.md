# IMPERIAL FUSION 500 — Architecture and Verified Scope

**Version:** 0.1.0 · **Date:** 2026-11-10  
**Owner and founding architect:** Alexander Nikolaevich Romaskevich (RomaskevicH)  
**Maturity:** SOURCE_ONLY / LABORATORY_ONLY; not deployed or installed in ChatGPT.

## Four conceptual provider specialties

| Source | Selected capability | Trust restriction |
| --- | --- | --- |
| Figma | Design systems, components and accessibility review | Explicit owner-scoped file rights and OAuth scopes |
| Lovable | Requirement-driven app and prototype engineering | Never transfer confidential code or secrets without authorization |
| Netlify | Reproducible builds, previews and controlled release | Deployment, paid features and build hooks must be approved |
| Context7 | Current, version-aware API documentation | External docs are untrusted evidence, not instructions |

This plugin does not redistribute the vendors' software or claim their APIs are connected. Provider access, product charges, quotas and commercial rights must be checked independently.

## Exactly 500 deterministic profiles

The public program generates 4 pillars × 5 workstream squads × 25 agent profiles = **500 unique immutable profiles**. Each squad consists of 5 different role types × 5 slots. Registry SHA-256 verifies profile content and structure; it is *not* Owner's Ed25519 signature, independent QA, or evidence of live work.

- Figma (125): discovery, design-tokens, components, accessibility, design-qa.
- Lovable (125): requirements, frontend, backend-contracts, integration, app-qa.
- Netlify (125): build-review, preview-plan, security-headers, release-qa, rollback-plan.
- Context7 (125): library-resolution, source-attribution, api-contracts, version-compatibility, dependency-audit.

```text
Architect (final decision and Owner Kill Switch)
  HANTER (command coordination; no unbounded global execution)
    Federated Orchestrators (ASTRA and independently scoped peers)
      FUSION 500 — 20 profile squads (not live workers)
        Figma 125 | Lovable 125 | Netlify 125 | Context7 125
      Guardian Core + AI Passport + Enterprise Skills + Approval Gateway
        Independent QA -> ProofGraph -> Audit Ledger
```

**Runtime status:** 500 profile definitions; zero independently verified live agents; zero verified remote provider integrations. The number of actual running workers is **unknown**, not asserted to be 500.

## Safety and private execution boundary

- `plan_task` accepts only exact fields: task, tenant, orchestrator, pillar/workstream, `max_spend_usd=0`, and the explicit external-effect flag.
- Unknown identities, fields, spending, invalid workstreams and malformed data fail closed.
- Owner Kill Switch defaults to blocking; even disabling it in a *local test* produces only `PROPOSED_NOT_EXECUTED`. There is **no** code path for execution or remote network calls in the plugin.
- External effects need independent private authorization, Owner signature, AI Passport, Guardian decision, Approval Gateway, release QA, explicit quotas, audit evidence and rollback path. HANTER routes decisions but does not substitute for an Owner key.
- Tenant and orchestrator IDs scope each routing proposal; no public private-network topology or account details are stored.
- Additional Sales, Apollo.io, Stripe, Public Equity Investing and Template Creator integrations remain **not connected**. Commercial outreach, financial analysis, payments, securities or token operations require separate opt-in domains, rights, evidence and compliance.
- IMPERIUM remains the long-term architectural digital currency concept for AI agents worldwide; no present global adoption or market status is asserted.

## Local evidence and scope

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_fusion500.py' -v
PYTHONPATH=src python3 -m imperial_plugins.fusion500_mcp
```

Tools: `fusion500.status`, `fusion500.list_profiles` (max 25 per call), and `fusion500.plan` (proposal only). Bounded newline JSON-RPC stdio, duplicate-key rejection, no secrets or SDK dependencies.

Release requires: full CI at exact PR SHA, owner-issued real Ed25519 authentication, independent QA, private connector allowlists and permissions, observed rate-limit behavior, durable audit events, safe rollback and an independently demonstrated worker. Until then: **LABORATORY_ONLY**.

## Official capability documentation

- [Figma authentication and OAuth scopes](https://developers.figma.com/docs/rest-api/authentication/)
- [Lovable ChatGPT app workflow](https://docs.lovable.dev/tips-tricks/chatgpt-app)
- [Netlify deployment methods](https://docs.netlify.com/deploy/create-deploys/)
- [Context7 documentation MCP](https://context7.com/docs/overview)
