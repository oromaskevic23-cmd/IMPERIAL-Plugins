"""Offline synthetic data demonstration; no real model downloads or training."""
from __future__ import annotations
import json
from imperial_plugins.llamafactory_adapter import (
    REFERENCE_MODEL, SYNTHETIC_RIGHTS, prepare_velion_finetune_plan,
)


def example(i: int) -> dict:
    return {
        "instruction": f"Explain synthetic transaction-free workflow {i}",
        "input": "A simulated engineering task",
        "output": f"Return a structured plan for toy task {i}, without side effects.",
        "source_id": f"synthetic:workflow-{i:04d}",
        "source_rights": SYNTHETIC_RIGHTS,
        "data_class": "PUBLIC_SYNTHETIC",
    }


def main() -> None:
    plan = prepare_velion_finetune_plan(
        [example(1), example(2)],
        [example(3), example(4)],
        {
            "tenant_id": "imperial-internal", "orchestrator_id": "engineering-orch",
            "base_model_id": REFERENCE_MODEL,
            # A deliberately fake example SHA, never use for real model fetching.
            "base_model_revision": "1" * 40,
            "training_method": "QLORA",
            # Only a test claim; not actual external licence verification.
            "manual_model_license_review_sha256": "a" * 64,
            "privacy_review_claimed": True,
            "gpu_budget_usd": 0, "model_download_permitted": False,
        })
    report = {key: value for key, value in plan.items() if key != "files"}
    assert report["training_invoked"] is False
    assert report["training_authorized"] is False
    assert report["external_effects"] is False
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
