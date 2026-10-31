"""Run from repository root with PYTHONPATH=src."""
import json
from pathlib import Path
from imperial_plugins import validate_manifest

paths = sorted(Path("manifests").glob("*.json"))
if not paths:
    raise SystemExit("No manifests found")
for path in paths:
    value = validate_manifest(json.loads(path.read_text(encoding="utf-8")))
    print(f"VALID {path}: {value['id']}@{value['version']}")
