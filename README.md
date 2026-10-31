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
