# IMPERIAL Plugins — Implementation Gates

Snapshot 2026-10-31. `src/imperial_plugins` is an executable **local security reference**, not a deployed plugin runtime.

- **P0 implemented in source:** manifest allowlist, HMAC-authenticated bounded AI Passport, deny-by-default Guardian, scoped owner approval, Owner Kill Switch, durable local SQLite hash chain, unit tests, CI configuration.
- **P0 not yet verified in production:** secured key management, signed manifests with Ed25519, live authorized orchestrator transport, durable distributed replay protection, sandbox, remote independent QA.
- **P1 planned:** Enterprise Skills registry, approval UI, multi-tenant plugin isolation, release attestation, telemetry/redaction, workflow connector for n8n.
- **P2 planned:** CONSTRUCTOR AI, VELION, ORION, CRM-SOFFT and NCA simulation/training adapters.

**Release policy:** source checks are not proof of a live production service. No external payments, platform logins, wallet operations or commercial tasks without specific owner approval and evidence.
