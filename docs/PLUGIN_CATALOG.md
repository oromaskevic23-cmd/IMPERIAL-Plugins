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


## v0.4 — VELION Training Adapter

| Plugin | API | Tested code | Explicitly not implemented |
| --- | --- | --- | --- |
| VELION × LLaMA-Factory | prepare_velion_finetune_plan; prepare_velion_training.py | offline Alpaca and dataset_info generator, LoRA/QLoRA YAML, synthetic-only license/PII review gates, split checks, SHA-256 evidence, pinned reference model, private explicit-write CLI | actual training, GPU resources, independently verified model/data title, blind final evaluation or model release |

Detailed [VELION LLaMA-Factory integration](VELION_LLAMAFACTORY_TRAINING.md). The upstream LLaMA-Factory code is **not** included or relicensed.

## IMPERIAL-Skill v0.2.0 — verified cross-repository contract

The standalone [IMPERIAL-Skill](https://github.com/oromaskevic23-cmd/IMPERIAL-Skill)
repository now owns the versioned Enterprise Skills manifest, pinned dependency
DAG, exam-definition provenance, guarded Owner/AI Passport plan checks, signed
source review, source-only CLI and local ProofGraph/Audit Ledger implementation.

Its [GitHub Actions](https://github.com/oromaskevic23-cmd/IMPERIAL-Skill/actions/workflows/enterprise-skill-ci.yml)
test the actual pinned IMPERIAL-Plugins validation contract across Python 3.11
and 3.12, rather than claiming a live orchestration service. The two repositories
remain independent: this plugin package does not inherit release privileges
from a passing Skill review or from a shared-secret HMAC demonstration.

**Integration status:** source-contract compatible, not production-connected.
The real Owner key, AI Passport, independent professional QA and actual NCA
worker require separate evidence and approval.

