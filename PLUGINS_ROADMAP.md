# IMPERIAL Plugins — Engineering Roadmap

Status: prototype source only; no deployed plugin runtime or security certification claimed.

## Initial modules
- Guardian Policy: deny-by-default allowlist and approval check.
- Audit Ledger: deterministic SHA-256 hash-chain event helper (in-memory only).
- AI Passport: structural validation only; cryptographic verification is pending.

## Next implementation gates
1. Signed plugin manifests and Ed25519 verification.
2. Scoped capabilities, explicit Approval Gateway and Owner Kill Switch.
3. Federated orchestrator routing via HANTER; no global orchestrator.
4. Durable append-only Audit Ledger, replay protection and audit export.
5. Sandbox isolation, independent QA, CI and release provenance.
6. Connector plugins for CONSTRUCTOR AI, VELION, NCA training and CRM-SOFFT.

Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary are mandatory. No production credentials or private code in this repository.
