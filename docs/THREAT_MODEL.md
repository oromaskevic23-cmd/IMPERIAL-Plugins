# Threat model and release gates

| Threat | Local control in this repository | Remaining risk |
| --- | --- | --- |
| Forged agent identity | HMAC-bound passport + trusted issuer + expiry | issuer-side secret compromise |
| Capability escalation | strict manifest and request allowlist | no isolated executor yet |
| Unauthorized action | exact signed approval, Owner Kill Switch | issuer custody / human approval channel |
| Cross-task approval reuse | approval bound to task + agent + action | replay storage not part of this kernel |
| Audit manipulation | SQLite chained SHA-256 and verification | DB administrator can rewrite entire history |
| Malicious plugin source | **no dynamic execution at all** | production sandbox unresolved |
| CI workflow compromise | read-only permissions and pinned checkout | runner/supply-chain risks |
| Data and financial leakage | no live external connectors | production security controls missing |

## Mandatory production blockers

- Hardware-backed or otherwise protected Ed25519 trust/issuer infrastructure and revocation.
- Durable centralized replay/nonce coordination and tenant separation.
- Isolated plugin process/container with resource limits, network egress controls and signed manifests.
- Production-grade multi-operator approval, auditable owner revocation, independent QA and external logs.
- Authenticated HANTER ↔ federated orchestrator ↔ NCA protocol and proof-carrying execution.
- License counsel review and copyright attribution audit.

No PASS or deployed/24×7 claim is made until external evidence exists.
