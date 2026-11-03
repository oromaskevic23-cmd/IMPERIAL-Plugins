# IMPERIAL Plugins — Implementation Gates

Snapshot 2026-10-31. `src/imperial_plugins` is an executable **local security reference**, not a deployed plugin runtime.

- **P0 implemented in source:** manifest allowlist, HMAC-authenticated bounded AI Passport, deny-by-default Guardian, scoped owner approval, Owner Kill Switch, durable local SQLite hash chain, unit tests, CI configuration.
- **P0 not yet verified in production:** secured key management, signed manifests with Ed25519, live authorized orchestrator transport, durable distributed replay protection, sandbox, remote independent QA.
- **P1 planned:** Enterprise Skills registry, approval UI, multi-tenant plugin isolation, release attestation, telemetry/redaction, workflow connector for n8n.
- **P2 planned:** CONSTRUCTOR AI, VELION, ORION, CRM-SOFFT and NCA simulation/training adapters.

**Release policy:** source checks are not proof of a live production service. No external payments, platform logins, wallet operations or commercial tasks without specific owner approval and evidence.

## 2026-11-01 implementation sprint (verified code, NOT production)

- P1 code implemented: Enterprise Skills, HANTER Federated Intake, ProofGraph integrity, negative tests, integrated demonstration and CI manifest validation.
- P0 still pending: separately enrolled Owner Ed25519 keys and AI Passport, protected HANTER issuer service, authenticated federation, revocation, least-privilege sandbox, external proof anchoring, runtime heartbeat and independent NCA QA.
- Future P1: independently attested plugin releases, version pinning and rollback protocol, genuine n8n account integration after authorization.
- Future P2: CONSTRUCTOR AI proof-carrying release, CRM-SOFFT and ORION typed adapters, richer VELION training and benchmarking.

Evidence rule: only claim actual results shown by the current GitHub Actions run; a source build does not imply 24/7 deployment or financial operations.


## 2026-11-03 — Search Indexing MCP

**E1 — SOURCE TESTED:** Implemented actual local stdio MCP JSON-RPC server (modern 2026-07-28 + legacy 2025-11-25); four read-only public project/site tools and an immutable website allowlist. Python 3.11/3.12 deterministic tests and live public-site audits passed on [CI revision `0e0116dd`](https://github.com/oromaskevic23-cmd/IMPERIAL-Plugins/actions/runs/41704769008).

**E2 — NOT IMPLEMENTED:** Installation/connection into the user's MCP host, independent Search Console OAuth and actual Google account property verification, authorized API submission and external Google indexing report.

**E3 — DEPLOYMENT NOT VERIFIED:** Hosted authenticated API, durable external logs, HANTER-to-MCP runtime and a signed AI Passport.

Next actions: host-controlled MCP connection → independent Google OAuth/property owner verification → separately approved sitemap submit → Google-reported status receipts → operational monitoring. Avoid false automatic indexing claims. See [MCP design](docs/SEARCH_INDEXING_MCP.md).

## v0.4 — model fine-tuning readiness

- Source implemented and tested in CI: guarded VELION LLaMA-Factory training planner; pinned model/source revisions; offline synthetic-only dataset provenance; LoRA/QLoRA config generator; explicit-write private CLI; leakage, privacy and YAML negative tests.
- P0 remaining: independently evidenced dataset/model licenses, actual Owner Ed25519/AI Passport authority, verified GPU driver/VRAM/free quotas, isolated training host, third-party dependency provenance and real training receipts.
- P1 remaining: sealed third-party independent model benchmark, governed Model Registry, signed and revocable adapters, ProofGraph release anchoring, rollback.
- Never equate training a model with certifying a professional NCA. No 100-agent live activation or improved VELION model is asserted.
