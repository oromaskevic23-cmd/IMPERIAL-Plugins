# IMPERIAL Plugins

**Enterprise-oriented plugin foundation for IMPERIAL Core** · Experimental / not production-deployed.

**Architect and original project owner:** Alexander Nikolaevich Romaskevich (RomaskevicH).  
**Core principle:** Architecture → Implementation → Evidence.

This repository contains a small, executable reference security kernel for plugin authorization and auditability. It is **not** a hosted marketplace, arbitrary-code sandbox, or a claim of completed Enterprise certification.

## Implemented now

| Capability | Status | Evidence |
| --- | --- | --- |
| Strict declarative manifest validation | Implemented | `tests/test_core.py` |
| HMAC-authenticated AI Passport (prototype trust domain) | Implemented | expiry, issuer, signature tests |
| Guardian Core default-deny evaluation | Implemented | action and scope tests |
| Approval Gateway tokens bound to agent, task and capability | Implemented | scope/expiry/tamper tests |
| Owner Kill Switch | Implemented | enabled by default |
| Durable local SQLite Audit Ledger with hash-chain verification | Implemented | integrity tests |
| Independent CI for the new kernel and legacy prototypes | Configured | GitHub Actions (check run for status) |
| Ed25519 issuer PKI / protected signing service | Not implemented | release gate |
| Real worker sandbox / remote orchestration / LLM dispatch | Not implemented | release gate |
| Commercial platform access / payouts | Not implemented | deny by default |

## Quick start

Python 3.11+; no runtime third-party dependencies.

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m unittest discover -s plugins/guardian-policy -p 'test_*.py' -v
python3 -m unittest discover -s plugins/audit-ledger -p 'test_*.py' -v
```

Integration API: `imperial_plugins.core.validate_manifest`, `sign_claims`, `GuardianCore.evaluate`, and `AuditLedger`. Signing helpers are for trusted backend/issuer code, **never for untrusted plugins**. Cryptographic authentication here uses a **shared-secret HMAC**, not the future asymmetric AI Passport/Ed25519 issuance infrastructure.

## IMPERIAL Search Indexing MCP — protocol server v0.1 (2026-11-03)

**A runnable, read-only local MCP server has been implemented and added to the enterprise test suite.** It exposes four indexing tools using both modern **MCP 2026-07-28** discovery and legacy **MCP 2025-11-25** initialization, through a newline-delimited JSON-RPC stdio process.

- **Verified public project registry:** 23 technical/business projects from 25 public repos; 7 private repos explicitly excluded from the snapshot.
- **Public-site audit:** only two canonical GitHub Pages properties allowed, checking actual HTTP, robots.txt, XML sitemap, canonical and JSON-LD ItemList.
- **Search Console integration:** exact property/sitemap URLs plus a separate [OAuth-bound, read-only Google API adapter](src/imperial_plugins/search_console_read.py). It can check real property permissions, sitemap registration and Google URL Inspection **only after an independently authorized private host supplies OAuth**. No Google token is present in this repository, and the public MCP never invokes the Google adapter automatically. Submission and actual indexing remain **UNVERIFIED**.
- **Google read-only operator and reconciliation:** [local operator preflight](tools/gsc_operator.py) has explicit site checks requiring a private short-lived OAuth token; [SubmissionGate.reconcile](src/imperial_plugins/search_console_submit.py) checks sitemap presence through Google without ever retrying the PUT automatically. Neither tool is connected to a real Google account.
- **Approval-gated sitemap submission reference:** [SubmissionGate](src/imperial_plugins/search_console_submit.py) now contains an exact Google PUT transport callable **only from a separately authorized private host** after time-limited Owner and independent-QA proof verification, real property access and public sitemap checks. The local kill switch defaults to ON; no Google OAuth or actual submission is connected. [Enterprise release and incident controls](docs/GOOGLE_SEARCH_CONSOLE_APPROVAL_GATEWAY.md). The four public MCP tools remain read-only.
- **Source:** [indexing_mcp.py](src/imperial_plugins/indexing_mcp.py) · [public-only inventory](data/search-indexing-public.json) · [adversarial tests](tests/test_indexing_mcp.py) · [MCP CI](.github/workflows/search-indexing-mcp.yml).
- **Operations and connecting a compatible MCP client:** [Complete local integration guide](docs/SEARCH_INDEXING_MCP.md).
- **Current production checkpoint:** [4 November Google Search Console readiness and independently verified blockers](docs/SEARCH_INDEXING_PRODUCTION_CHECKPOINT_20261104.md) — signed Owner/QA verifier, safe reconciliation, documented OAuth dependency and exact CI evidence.

Start the real MCP stdio process from a local checkout:

```bash
python3 tools/search_indexing_mcp.py
```

Run the tests independently:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_indexing_mcp.py' -v
```

This is **source implementation**, not a hosted server or already-installed ChatGPT integration. The public MCP cannot submit sitemaps; the separate guarded write module has only been tested with synthetic Google responses. No real OAuth grant, submission, indexing result or search ranking is verified.

## Chat History Recovery — Ten Specialized Search NCA (v0.1)

The [offline Chat History Recovery Plugin](plugins/chat-history-recovery/SKILL.md) provides a real Python/SQLite FTS5 index and ten role-specific source-grounded searches for **user-supplied ChatGPT exports**, including optional historical filtering before the first **user mention of Val Town** (heuristic) or an Owner-confirmed UTC date. Run `PYTHONPATH=src python tools/chat_history_recovery.py --help` locally and review its [adversarial test suite](tests/test_chat_recovery.py). Results contain original conversation/message IDs and redacted excerpts, not fabricated live chat links.

This module does **not** automatically read ChatGPT account history, run ten LLM agents, access private servers, or encrypt the local database. No personal export is stored in the repository. The 6–8-week roadmap is a target for subsequent work, not a claim of autonomous background progress.

## Canonical architecture

Architect → HANTER (command center) → **federated orchestrators** → NCA/sub-NCA workers. ORION is collective intelligence, not a replacement for orchestrator isolation. The Guardian Core + Approval Gateway + Audit Ledger apply before all execution boundaries; every agent is expected to hold an AI Passport and Enterprise Skills. Runtime Domains, ProofGraph, IntentLock, Owner Kill Switch, Zero Trust, Public/Private Boundary and **CRYPTO IMPERIAL Ecosystem Boundary** remain mandatory.

The public repository excludes credentials, payout controls, proprietary private modules and customer data. The related [IMPERIAL n8n Automation](https://github.com/oromaskevic23-cmd/IMPERIAL-n8n-Automation) repo contains an independent ingress prototype.

## Security and license

See [SECURITY.md](SECURITY.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) and [LICENSE.md](LICENSE.md). This code is source-visible but **not** offered under an OSI open-source license. External components retain their own rights; no n8n source code or marks are licensed by IMPERIAL Core.

## Additional prototype plugins

Five declarative plugin manifest examples and deterministic offline adapters are documented in [the plugin catalog](docs/PLUGIN_CATALOG.md): NCA training assessment, n8n workflow auditing and VELION routing plans join Guardian and Audit Ledger. None enables unattended or commercial execution.


---

### Canonical founder and public project identity

This public repository is listed in the [founder-maintained IMPERIAL Core engineering portfolio](https://oromaskevic23-cmd.github.io/oromaskevic23-cmd/projects/). The public [engineering source registry](https://oromaskevic23-cmd.github.io/Capital-Core-Public/reference/projects/) links this source to the account's published project records under **Alexander Nikolaevich Romaskevich (RomaskevicH)**, Founder, Owner and CEO of IMPERIAL Core and its final architectural decision authority. Repository-specific governance, contributor rights, third-party intellectual property, and documented independence of individual projects remain unchanged. Publication does not prove production execution, market adoption or Google indexing.

## v0.3 — Enterprise Skills × HANTER × ProofGraph plugin fabric

Three new functional modules have been added to the Python package:

- **Enterprise Skills Registry:** closed schemas, tenant/orchestrator/Runtime Domain binding, explicit capability controls, and zero spending. Descriptor registration creates no permission to execute.
- **HANTER Federated Intake:** Guardian Core and skill-checked local SQLite task records, explicit federated routes, kill-switch enforcement, atomic duplicate-task handling, and no credentials stored in receipts. No remote worker or plugin is invoked.
- **ProofGraph Evidence:** content hashes for manifests, untrusted artifacts and QA-report bytes, with optional previous-proof SHA-256. Integrity verification is **not** independent QA, cryptographic author identity or a release permit.
- **Integration suite:** a complete offline test path through HANTER → VELION route plan → ProofGraph → Audit Ledger, including n8n review and NCA simulation semantics.

Run the source and deterministic synthetic demo (Python 3.11+, no third-party dependencies):

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 examples/federated_fabric_demo.py
PYTHONPATH=src python3 tools/validate_manifests.py
```

The demo uses test-only HMAC reference keys; no actual Ed25519 Owner credential, model, browser, payment, commercial platform or server runtime is invoked. The private production authority, revocation, independent QA, signed manifests and worker sandbox remain mandatory release blockers.


## v0.4 — VELION × LLaMA-Factory Training Adapter

An offline **LoRA/QLoRA configuration and synthetic-data preparation module** is now implemented. It validates local original-synthetic dataset claims, screens some secrets, rejects train/validation overlap, pins reviewed LLaMA-Factory and Qwen revisions, builds Alpaca/dataset_info and train YAML, and records SHA-256. The local CLI requires explicit --write and never downloads or fine-tunes a model. No independent model-performance claim or NCA production certification is made.

See [complete VELION training architecture, licensing and procedures](docs/VELION_LLAMAFACTORY_TRAINING.md), [adapter source](src/imperial_plugins/llamafactory_adapter.py), [offline CLI](tools/prepare_velion_training.py) and [synthetic demonstration](examples/velion_training_plan_demo.py).

~~~bash
PYTHONPATH=src python3 examples/velion_training_plan_demo.py
PYTHONPATH=src python3 tools/prepare_velion_training.py --help
~~~

Third-party LLaMA-Factory and Qwen model weights retain their own Apache-2.0 rights; no third-party source is represented as IMPERIAL-owned.

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

