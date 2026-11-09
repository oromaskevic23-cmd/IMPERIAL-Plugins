# VELION Training Adapter × LLaMA-Factory

**Checkpoint:** 2026-11-01. **Founder • Owner • CEO:** Alexander Nikolaevich Romaskevich (RomaskevicH).

**Verified status: Python offline adapter + GitHub CI. NOT trained, deployed or independently model-benchmarked.**

## 1. Architectural decision

LLaMA-Factory is an optional third-party fine-tuning backend for VELION model development, **not a replacement for VELION, HANTER, ORION, CONSTRUCTOR AI, Guardian Core or NCA professional qualification**. This public repository contains only original IMPERIAL Core integration code. No third-party model/framework source or weights have been copied, forked or rebranded.

Architect / Owner → HANTER Command Center → federated engineering orchestrator → Enterprise Skills → VELION Model Fabric → VELION Training Adapter → optional future isolated LLaMA-Factory GPU job → independent model benchmark → signed ProofGraph/Audit Ledger → distinct release approval.

This is a **federated Multi-Orchestrator Architecture**, not one global orchestrator. VELION MAX is an operating mode, not a separate LLM.

## 2. Verified third-party sources and licensing

| Source | Snapshot / interface |
| --- | --- |
| LLaMA-Factory | https://github.com/hiyouga/LlamaFactory — source license Apache-2.0 |
| Reviewed upstream source commit | 9997aa078b4da35e04bb492a8a27d45141f4b80b |
| LoRA example | https://github.com/hiyouga/LlamaFactory/blob/main/examples/train_lora/qwen3_lora_sft.yaml |
| QLoRA example | https://github.com/hiyouga/LlamaFactory/blob/main/examples/train_qlora/qwen3_lora_sft_otfq.yaml |
| Dataset standard | https://github.com/hiyouga/LlamaFactory/blob/main/data/README.md — Alpaca JSON and dataset_info.json |
| Reference model | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 — Apache-2.0 in the model repository |
| Reviewed model SHA | cdbee75f17c01a7cc42f958dc650907174af0554 |
| Model LICENSE | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/LICENSE |

**Important intellectual-property boundary:** An Apache license for framework code does not automatically cover all third-party model weights or user datasets. Our reviewed Qwen checkpoint has a separate Apache-2.0 license. Proper attribution and preservation of upstream notices remain necessary if distributing upstream materials. IMPERIAL Core original code remains subject to its own LICENSE.md; claiming upstream rights or applying that license to third-party weights would be incorrect.

No LLaMA-Factory Python source or Qwen weights are vendored. The model-revision and license fields in local planning input are documentary claims, not automatically verified legal title.

## 3. Implemented v0.4 code

- **Pure offline planning:** prepare_velion_finetune_plan(training, evaluation, policy), without network, subprocesses, GPU operations or LLM calls.
- **Data handling:** strict owner-asserted synthetic provenance, PUBLIC_SYNTHETIC only; bounds, duplicated prompt/source rejection, train-vs-validation intersection check, conservative secret/email detector. This is not a complete DLP scan or legal certification.
- **Reproducibility:** pins an observed LLaMA-Factory code revision, the Qwen base model and a specific Hugging Face checkpoint; generates four locally reusable files and SHA-256 hashes.
- **Training config:** strict allowlisted LoRA or QLoRA SFT configuration, qwen3_nothink template; QLoRA uses four-bit bitsandbytes. Remote model code execution is off, experiment telemetry is off, no forced output overwrite.
- **Local preparation tool:** tools/prepare_velion_training.py is read-only by default. Explicit --write creates a *new* local directory with private file permissions and no existing-file overwrite.
- **No training authority:** every plan asserts training_authorized=false, model_downloaded=false, gpu_allocated=false, independent_evaluation_verified=false, owner_production_approval_verified=false, cost_usd=0. A manifest, plan or manual rights digest is never Owner approval.

## 4. Safe local usage

Run only offline synthetic demonstration (no extra dependencies):

~~~bash
PYTHONPATH=src python3 examples/velion_training_plan_demo.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
~~~

Prepare your own locally reviewed synthetic dataset request JSON using exactly three top-level fields: training, evaluation, policy. Every training/validation sample has these fields:

~~~json
{
  "instruction": "Explain a synthetic code task",
  "input": "toy value 3",
  "output": "The toy value is 3.",
  "source_id": "synthetic:my-original-001",
  "source_rights": "OWNER_ASSERTED_ORIGINAL_SYNTHETIC",
  "data_class": "PUBLIC_SYNTHETIC"
}
~~~

Policy fields are tenant_id, orchestrator_id, base_model_id, base_model_revision, training_method (LORA or QLORA), manual_model_license_review_sha256, privacy_review_claimed=true, gpu_budget_usd=0, model_download_permitted=false. Base-model identity and revision must equal the reviewed Qwen reference above. At least two training and two validation samples are required for *structural validation*. That tiny minimum is not sufficient to claim a useful fine-tuned model.

Preview without writing:

~~~bash
PYTHONPATH=src python3 tools/prepare_velion_training.py --input ./private-request.json
~~~

Explicitly create private local files **without any fine-tuning**:

~~~bash
PYTHONPATH=src python3 tools/prepare_velion_training.py \
  --input ./private-request.json \
  --output ./private-velion-train-run --write
~~~

Result: train.yaml, train.json, eval.json, dataset_info.json and plan.json. Keep private training artifacts, customer data and any credentials out of public repositories. The CLI prints only source hashes and release blockers, never training text.

The supplied evaluation file is **training-time validation** (eval_dataset), not a sealed independent exam. It must not be promoted into proof of improved model capability. The current plan explicitly reports independent_test_examples=0.

## 5. Mandatory gates before real GPU execution

1. **Rights and privacy:** independent review of model weights, train/validation/test data rights and provenance, privacy scanning, authorized acquisition, upstream attribution; owner-asserted fields alone do not prove clearance.
2. **Source supply chain:** verified upstream Git SHA, pinned model revision, dependency version review and reproducible lockfiles. Our parser generates configurations; compatibility with exact installed runtime must still be checked.
3. **Compute:** specific authorized host, measured GPU driver/CUDA/bitsandbytes compatibility, disk, RAM/VRAM and zero-cost quotas. **No promise** that Qwen3 4B training fits any particular 8GB GPU (including RTX 2070 SUPER).
4. **Security:** protected training container, network isolation, no private credentials inside data, scoped VELION runtime identity, AI Passport, Guardian Core, Approval Gateway, Owner Kill Switch, separation of Public/Private Boundary.
5. **Owner approval:** cryptographically verified Owner release bound to exact data hashes, model revision, host, budget and intent. No synthetic signer/ChatGPT approval may replace it.
6. **Independent evaluation:** a separate, sealed exam unknown to training, actual training receipts, cryptographically bound model/adapter SHA-256, regressions and safety checks, ProofGraph plus Audit Ledger.
7. **Release:** governed Model Registry, versioned adapters and rollback, NCA-specific professional exams and independent production admission. Fine-tuning weights does not certify a NCA, HANTER or any of the 100/1700 agents.

Only on an explicitly approved training host might the upstream tool be run manually:

~~~bash
# NOT AUTHORIZED BY THIS REPOSITORY — do not execute without release gates:
# llamafactory-cli train train.yaml
~~~

The adapter **never** runs that command. Real GPU training, model quality, model weights and production deployment are NOT claimed.

## 6. Threats and known limits

| Threat | Present mitigation | Remaining risk |
| --- | --- | --- |
| Unlicensed data | synthetic-only classes and provenance IDs | source rights self-asserted, not externally proven |
| PII/secrets | conservative local token/email scanner | incomplete DLP coverage |
| Data leakage | exact normalized prompt/source split checks | semantic/near-duplicate prompts may escape |
| Supply chain | reviewed fixed source and reference model hashes | weights and dependencies not downloaded/verified |
| GPU spending | no execution/download, zero-budget policy | manual downstream operator may incur cost |
| Telemetry | report_to none in draft YAML | actual runtime egress not enforced here |
| Untrusted code | trust_remote_code false | some architectures need additional reviewed code |
| Inflated QA claims | independent model-test status always false | separate sealed benchmark not yet built |

FREE_ONLY, Zero Trust, Guardian Core, Enterprise Skills, AI Passport, Approval Gateway, IntentLock, ProofGraph, Audit Ledger, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary remain mandatory. IMPERIUM is a long-term architectural digital currency concept for AI agents worldwide; no present global adoption or exchange status is asserted.

**Architecture → Implementation → Evidence.**
