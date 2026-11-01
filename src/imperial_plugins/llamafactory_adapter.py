"""VELION training adapter for upstream LLaMA-Factory (offline, no training).

Original IMPERIAL Core integration. Never imports third-party frameworks, downloads
models, executes GPU jobs or elevates NCA authority. Synthetic data only.
"""
from __future__ import annotations

import hashlib
import json
import re
from .core import canonical

UPSTREAM_REPO = "https://github.com/hiyouga/LlamaFactory"
# Snapshot observed on 2026-11-01; not a promise of later compatibility.
UPSTREAM_REVIEW_SHA = "9997aa078b4da35e04bb492a8a27d45141f4b80b"
REFERENCE_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
REFERENCE_TEMPLATE = "qwen3_nothink"
SYNTHETIC_RIGHTS = "OWNER_ASSERTED_ORIGINAL_SYNTHETIC"
FIELDS = frozenset({"instruction", "input", "output", "source_id",
                    "source_rights", "data_class"})
POLICY_FIELDS = frozenset({"tenant_id", "orchestrator_id", "base_model_id",
                           "base_model_revision", "training_method",
                           "manual_model_license_review_sha256",
                           "privacy_review_claimed", "gpu_budget_usd",
                           "model_download_permitted"})
IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,100}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SOURCE = re.compile(r"^synthetic:[a-z0-9][a-z0-9_.-]{2,90}$")
# Deliberately conservative best-effort filter, not a comprehensive DLP tool.
SECRET = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"(?:sk-proj-|sk-[A-Za-z0-9]{30,}|ghp_[A-Za-z0-9]{30,}|"
    r"AKIA[0-9A-Z]{16})|[A-Za-z0-9._%+-]{2,}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)


def _load_partition(rows: object, name: str) -> tuple[list[dict], set[str]]:
    if not isinstance(rows, list) or not 2 <= len(rows) <= 10000:
        raise ValueError("DATASET_SPLIT_SIZE_DENIED_" + name)
    output, prompts, identities = [], set(), set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("DATASET_ROW_SCHEMA_DENIED")
        for field in ("instruction", "input", "output"):
            s = row[field]
            if not isinstance(s, str) or len(s) > 4096:
                raise ValueError("DATASET_TEXT_DENIED")
            if field != "input" and not s.strip():
                raise ValueError("EMPTY_INSTRUCTION_OR_ANSWER")
            if "\x00" in s or SECRET.search(s):
                raise ValueError("POSSIBLE_SECRET_OR_PERSONAL_DATA")
        if (not isinstance(row["source_id"], str)
            or not SOURCE.fullmatch(row["source_id"])
            or row["source_id"] in identities
            or row["source_rights"] != SYNTHETIC_RIGHTS
            or row["data_class"] != "PUBLIC_SYNTHETIC"):
            raise ValueError("DATA_PROVENANCE_OR_CLASS_DENIED")
        identities.add(row["source_id"])
        p = hashlib.sha256(canonical({
            "instruction": row["instruction"].strip().casefold(),
            "input": row["input"].strip().casefold(),
        })).hexdigest()
        if p in prompts:
            raise ValueError("DUPLICATE_PROMPT_WITHIN_SPLIT")
        prompts.add(p)
        output.append({key: row[key] for key in ("instruction", "input", "output")})
    # Canonical serialization and prompt fingerprints have strict bounds.
    if len(canonical({"rows": output})) > 8 * 1024 * 1024:
        raise ValueError("DATASET_TOO_LARGE")
    return output, prompts


def _validate_policy(policy: object) -> dict:
    if not isinstance(policy, dict) or set(policy) != POLICY_FIELDS:
        raise ValueError("TRAINING_POLICY_SCHEMA_DENIED")
    for key in ("tenant_id", "orchestrator_id"):
        if not isinstance(policy[key], str) or not IDENTITY.fullmatch(policy[key]):
            raise ValueError("TRAINING_BOUNDARY_DENIED")
    if policy["base_model_id"] != REFERENCE_MODEL:
        raise ValueError("UNREVIEWED_BASE_MODEL_DENIED")
    sha = policy["base_model_revision"]
    if not isinstance(sha, str) or not COMMIT.fullmatch(sha) or sha == "0" * 40:
        raise ValueError("MODEL_REVISION_MUST_BE_PINNED")
    license_sha = policy["manual_model_license_review_sha256"]
    if (not isinstance(license_sha, str) or not SHA.fullmatch(license_sha)):
        raise ValueError("MODEL_RIGHTS_EVIDENCE_DIGEST_REQUIRED")
    if policy["training_method"] not in ("LORA", "QLORA"):
        raise ValueError("UNSUPPORTED_FINETUNING_METHOD")
    if (policy["privacy_review_claimed"] is not True
        or type(policy["privacy_review_claimed"]) is not bool
        or type(policy["gpu_budget_usd"]) is not int
        or policy["gpu_budget_usd"] != 0
        or policy["model_download_permitted"] is not False
        or type(policy["model_download_permitted"]) is not bool):
        raise ValueError("NO_UNREVIEWED_DATA_OR_SPENDING")
    return dict(policy)


def _render_yaml(values: dict) -> str:
    """Serialize ONLY fixed keys with strictly validated scalar values."""
    allowed = {
        "model_name_or_path", "model_revision", "trust_remote_code", "stage",
        "do_train", "do_eval", "finetuning_type", "lora_rank", "lora_target",
        "quantization_bit", "quantization_method", "dataset", "eval_dataset",
        "dataset_dir", "template", "cutoff_len", "max_samples",
        "preprocessing_num_workers", "dataloader_num_workers", "output_dir",
        "logging_steps", "save_steps", "plot_loss", "overwrite_output_dir",
        "report_to", "per_device_train_batch_size", "gradient_accumulation_steps",
        "learning_rate", "num_train_epochs", "lr_scheduler_type", "warmup_ratio",
        "fp16", "bf16", "per_device_eval_batch_size", "eval_strategy"
    }
    if set(values) - allowed:
        raise ValueError("UNAPPROVED_TRAINING_PARAMETER")
    lines = [
        "# IMPERIAL Core VELION — PLAN ONLY. NOT AUTHORIZED TO EXECUTE.",
        "# Requires independent license, privacy, GPU and Owner release gates.",
    ]
    for key, val in values.items():
        if isinstance(val, bool):
            representation = "true" if val else "false"
        elif type(val) in (int, float):
            representation = str(val)
        elif isinstance(val, str) and re.fullmatch(r"[A-Za-z0-9_./:-]+", val):
            representation = val
        else:
            raise ValueError("UNSAFE_YAML_SCALAR")
        lines.append(f"{key}: {representation}")
    return "\n".join(lines) + "\n"


def prepare_velion_finetune_plan(training: object, evaluation: object,
                                 policy: object) -> dict:
    """Build reproducible config files only. No downloads or GPU execution.

    license 'review' and synthetic provenance here are supplied assertions,
    not independent legal verification. The plan is *never* an execution permit.
    """
    approved_policy = _validate_policy(policy)
    train, train_hashes = _load_partition(training, "training")
    held_out, eval_hashes = _load_partition(evaluation, "evaluation")
    if train_hashes & eval_hashes:
        raise ValueError("TRAIN_EVAL_PROMPT_LEAKAGE")
    train_sources = {x["source_id"] for x in training}
    eval_sources = {x["source_id"] for x in evaluation}
    if train_sources & eval_sources:
        raise ValueError("TRAIN_EVAL_SOURCE_LEAKAGE")
    manifest = {
        "imperial_train": {"file_name": "train.json", "formatting": "alpaca",
                           "columns": {"prompt": "instruction", "query": "input",
                                       "response": "output"}},
        "imperial_eval": {"file_name": "eval.json", "formatting": "alpaca",
                          "columns": {"prompt": "instruction", "query": "input",
                                      "response": "output"}},
    }
    cfg = {
        "model_name_or_path": REFERENCE_MODEL,
        "model_revision": approved_policy["base_model_revision"],
        "trust_remote_code": False,
        "stage": "sft", "do_train": True, "do_eval": True,
        "finetuning_type": "lora", "lora_rank": 8, "lora_target": "all",
    }
    if approved_policy["training_method"] == "QLORA":
        cfg.update({"quantization_bit": 4, "quantization_method": "bnb"})
    cfg.update({
        "dataset": "imperial_train", "eval_dataset": "imperial_eval",
        "dataset_dir": ".", "template": REFERENCE_TEMPLATE,
        "cutoff_len": 1024, "max_samples": len(train),
        "preprocessing_num_workers": 1, "dataloader_num_workers": 0,
        "output_dir": "./artifacts", "logging_steps": 10, "save_steps": 500,
        "plot_loss": False, "overwrite_output_dir": False, "report_to": "none",
        "per_device_train_batch_size": 1, "gradient_accumulation_steps": 8,
        "learning_rate": 0.0001, "num_train_epochs": 1.0,
        "lr_scheduler_type": "cosine", "warmup_ratio": 0.1,
        "fp16": True, "bf16": False,
        "per_device_eval_batch_size": 1, "eval_strategy": "epoch",
    })
    files = {
        "dataset_info.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        "train.json": json.dumps(train, indent=2, ensure_ascii=False) + "\n",
        "eval.json": json.dumps(held_out, indent=2, ensure_ascii=False) + "\n",
        "train.yaml": _render_yaml(cfg),
    }
    fingerprints = {name: hashlib.sha256(text.encode("utf-8")).hexdigest()
                    for name, text in files.items()}
    recipe_fingerprint = hashlib.sha256(canonical({
        "files": fingerprints, "policy": approved_policy,
        "reviewed_upstream_commit": UPSTREAM_REVIEW_SHA,
    })).hexdigest()
    return {
        "schema": "imperial.velion.llamafactory.offline-plan.v1",
        "integration_name": "VELION Training Adapter",
        "source_project": "hiyouga/LlamaFactory",
        "reviewed_upstream_commit": UPSTREAM_REVIEW_SHA,
        "tenant_id": approved_policy["tenant_id"],
        "orchestrator_id": approved_policy["orchestrator_id"],
        "training_method": approved_policy["training_method"],
        "training_examples": len(train), "validation_examples": len(held_out), "independent_test_examples": 0,
        "config_sha256": recipe_fingerprint, "file_sha256": fingerprints,
        "files": files,
        "training_invoked": False, "model_downloaded": False,
        "gpu_allocated": False, "model_weights_changed": False,
        "independent_evaluation_verified": False,
        "legal_rights_independently_verified": False,
        "model_license_review_claim_digest":
            approved_policy["manual_model_license_review_sha256"],
        "owner_production_approval_verified": False,
        "training_authorized": False, "external_effects": False,
        "cost_usd": 0,
        "release_blockers": [
            "OWNER_PRODUCTION_APPROVAL_MISSING",
            "MODEL_AND_DATA_LICENSE_INDEPENDENT_REVIEW_PENDING",
            "BASE_MODEL_REVISION_AND_WEIGHTS_NOT_FETCHED_OR_VERIFIED",
            "GPU_MEMORY_AND_ZERO_COST_NOT_MEASURED",
            "INDEPENDENT_HELDOUT_BENCHMARK_NOT_RUN",
            "NO_SIGNED_TRAINING_ATTESTATION",
        ],
    }
