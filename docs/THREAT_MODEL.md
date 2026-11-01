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

## Newly tested v0.3 risks

- Cross-tenant agent and orchestrator reuse is rejected by the explicit federated route table.
- Changed task body with an existing tenant/task ID is denied by atomic SQLite idempotency; exact retries are acknowledged without execution.
- The HANTER intake stores a SHA-256 fingerprint and a no-execution receipt, not signed passport/approval bodies or keys.
- Enterprise Skills refuses unsafe fields, commercial execution capabilities, outside effects and any nonzero budget.
- ProofGraph rejects altered artifact/QA bytes, privilege inflation, tampered previous-proof links and invented independent QA claims.
- The local Owner Kill Switch denies both first-time records and previously recorded replays.

Residual P0 risks remain: local SQLite does not provide distributed exactly-once processing or isolation against host administrators; HMAC keys are reference test keys, not Owner's asymmetric signing authority; no remote NCA execution or external immutable evidence has been tested. Do not assign a production PASS to a unit test.
