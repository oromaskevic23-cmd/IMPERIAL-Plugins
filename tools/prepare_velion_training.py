"""Prepare LLaMA-Factory offline training artifacts. NEVER starts fine-tuning.

Usage:
    PYTHONPATH=src python3 tools/prepare_velion_training.py --input request.json
    PYTHONPATH=src python3 tools/prepare_velion_training.py \
        --input request.json --output ./private_training_run --write

Explicit --write generates only local private data/config files.
No third-party imports, subprocess, downloads, model inference or GPU use.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from imperial_plugins.llamafactory_adapter import prepare_velion_finetune_plan


def _unique_dict(pairs: list[tuple[str, object]]) -> dict:
    value: dict = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("DUPLICATE_JSON_KEY_DENIED")
        value[key] = item
    return value


def read_request(path: Path) -> dict:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("INPUT_PATH_OR_SIZE_DENIED")
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_dict)
    if not isinstance(data, dict) or set(data) != {"training", "evaluation", "policy"}:
        raise ValueError("INPUT_REQUEST_SCHEMA_DENIED")
    return data


def _save_files(path: Path, files: dict[str, str], summary: dict) -> None:
    # Parent must exist; this helper never changes existing directories.
    if (path.exists() or path.is_symlink() or not path.parent.is_dir()
        or path.parent.is_symlink()):
        raise ValueError("PRIVATE_OUTPUT_DIRECTORY_MUST_NOT_EXIST")
    os.mkdir(path, 0o700)
    try:
        all_files = {**files, "plan.json": json.dumps(summary, indent=2) + "\n"}
        for name, content in all_files.items():
            if name not in {"dataset_info.json", "train.json", "eval.json",
                            "train.yaml", "plan.json"}:
                raise ValueError("UNEXPECTED_PLAN_FILE")
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            flags |= getattr(os, "O_NOFOLLOW", 0)
            with os.fdopen(os.open(path / name, flags, 0o600), "w",
                           encoding="utf-8") as output:
                output.write(content)
    except BaseException:
        # A failed write leaves the private directory for explicit inspection.
        # Never auto-delete the user's confidential files.
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True,
                        help="Local synthetic dataset request JSON")
    parser.add_argument("--output", help="New local directory; must not exist")
    parser.add_argument("--write", action="store_true",
                        help="Explicitly write local artifacts, never train")
    options = parser.parse_args(argv)
    if options.write and not options.output:
        parser.error("--write requires --output")
    if options.output and not options.write:
        parser.error("--output requires explicit --write")
    try:
        data = read_request(Path(options.input))
        plan = prepare_velion_finetune_plan(
            data["training"], data["evaluation"], data["policy"])
        summary = {key: value for key, value in plan.items() if key != "files"}
        summary["status"] = "OFFLINE_PLAN_NOT_TRAINING"
        if options.write:
            _save_files(Path(options.output), plan["files"], summary)
        print(json.dumps(summary, sort_keys=True))
        return 0
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError) as exc:
        print(f"PLAN_DENIED:{type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
