# IMPERIAL Plugins — Verified Source Catalog

These are offline prototypes under owner-controlled source control. **None is a deployed service or a signed marketplace package.**

| Plugin | Callable function | Available now | Not available |
| --- | --- | --- | --- |
| Guardian Policy | `GuardianCore.evaluate` | HMAC passport and explicit approval gate | PKI, distributed trust, external worker |
| Audit Ledger | `AuditLedger.append / verify` | local SQLite hash chain | immutable external attestation |
| NCA Training | `evaluate_nca_exam` | deterministic precommitted answer matching, critical cases | actual LLM training, independent exam issuance |
| n8n Workflow Audit | `inspect_n8n_workflow` | static red flags for Code/HTTP/credentials | safety proof of arbitrary JavaScript |
| VELION Route | `plan_velion_model_route` | capability-filtered deterministic route plan | LLM calls, live pricing, model benchmarking |

Additional planned integrations: HANTER transport adapter, Enterprise Skills registry, CRM-SOFFT, CONSTRUCTOR AI proof-carrying release, ORION collective intelligence, and NCA execution sandbox.

**Cross-boundary rule:** a plan, score or static inspection never authorizes execution. Guardian Core, Approval Gateway, Owner Kill Switch, AI Passport, Runtime Domain, Enterprise Skills and Audit Ledger remain separate mandatory controls.

## v0.3 source-implemented plugins — 2026-11-01

| Plugin | Python API | Verified design contract | Deliberately not claimed |
| --- | --- | --- | --- |
| Enterprise Skills | `EnterpriseSkillsRegistry`, `validate_enterprise_skill` | strict skill metadata, tenant/domain binding, immutable local registry snapshots | certification, production execution |
| HANTER Federated Intake | `HanterIntakeQueue`, `FederatedRouteTable` | local SQLite idempotent proposals, explicit federated agent routes, Guardian default-deny | authenticated remote dispatch or live workers |
| ProofGraph Evidence | `create_proof_bundle`, `verify_proof_bundle` | SHA-256 linked untrusted artifact and QA bytes; mutation detection | independent QA, externally immutable proofs, Owner signature |

The synthetic integrated example is [examples/federated_fabric_demo.py](../examples/federated_fabric_demo.py); it intentionally **does not** load plugins dynamically or call models. A real signed AI Passport cannot be replaced by this public HMAC simulation.
