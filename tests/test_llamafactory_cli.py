import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

from imperial_plugins.llamafactory_adapter import (
    REFERENCE_MODEL, SYNTHETIC_RIGHTS,
)

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "tools" / "prepare_velion_training.py"


def row(index):
    return {
        "instruction": f"Explain the state of a toy counter {index}",
        "input": "synthetic counters only",
        "output": f"The toy counter is {index}.",
        "source_id": f"synthetic:unit-{index:04d}",
        "source_rights": SYNTHETIC_RIGHTS,
        "data_class": "PUBLIC_SYNTHETIC",
    }


def request():
    return {
        "training": [row(1), row(2)],
        "evaluation": [row(3), row(4)],
        "policy": {
            "tenant_id": "imperial-internal",
            "orchestrator_id": "engineering-orch",
            "base_model_id": REFERENCE_MODEL,
            # Pinned real HF model revision; still NO download or license release.
            "base_model_revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
            "training_method": "QLORA",
            # Test digest is only a claim, NOT an actual verified model licence.
            "manual_model_license_review_sha256": "a" * 64,
            "privacy_review_claimed": True,
            "gpu_budget_usd": 0,
            "model_download_permitted": False,
        },
    }


class TestVELIONTrainingCLI(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.source = self.root / "request.json"
        self.source.write_text(json.dumps(request()), encoding="utf-8")
        self.output = self.root / "private-output"

    def invoke(self, *args):
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, str(CLI), "--input",
                               str(self.source), *args], check=False,
                              capture_output=True, text=True, env=env)

    def test_dry_run_produces_no_files_or_training(self):
        p = self.invoke()
        self.assertEqual(p.returncode, 0, p.stderr)
        summary = json.loads(p.stdout)
        self.assertEqual(summary["status"], "OFFLINE_PLAN_NOT_TRAINING")
        self.assertFalse(summary["training_authorized"])
        self.assertFalse(summary["model_downloaded"])
        self.assertNotIn("files", summary)
        self.assertFalse(self.output.exists())

    def test_explicit_write_creates_private_unexecuted_files(self):
        p = self.invoke("--output", str(self.output), "--write")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(self.output.is_dir())
        self.assertEqual({v.name for v in self.output.iterdir()},
                         {"train.json", "eval.json", "dataset_info.json",
                          "train.yaml", "plan.json"})
        mode = stat.S_IMODE(self.output.stat().st_mode)
        self.assertEqual(mode & 0o077, 0)
        for item in self.output.iterdir():
            self.assertEqual(stat.S_IMODE(item.stat().st_mode) & 0o077, 0)
        self.assertFalse(json.loads((self.output/"plan.json").read_text())
                         ["training_invoked"])

    def test_cannot_overwrite_prior_training_workspace(self):
        self.output.mkdir()
        sentinel = self.output / "existing.marker"
        sentinel.write_text("untouched", encoding="utf-8")
        p = self.invoke("--output", str(self.output), "--write")
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(sentinel.read_text(), "untouched")

    def test_requires_explicit_write_opt_in(self):
        p = self.invoke("--output", str(self.output))
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_invalid_sensitive_data_denied_before_output(self):
        data = request()
        data["training"][0]["input"] = "secret: ghp_" + "A" * 35
        self.source.write_text(json.dumps(data), encoding="utf-8")
        p = self.invoke("--output", str(self.output), "--write")
        self.assertEqual(p.returncode, 2)
        self.assertFalse(self.output.exists())

    def test_duplicate_policy_key_denied(self):
        raw = self.source.read_text()
        raw = raw.replace('"gpu_budget_usd": 0,', '"gpu_budget_usd": 0, "gpu_budget_usd": 1,')
        self.source.write_text(raw)
        p = self.invoke()
        self.assertEqual(p.returncode, 2)
        self.assertNotIn("Traceback", p.stderr)

    def test_input_is_never_exec(self):
        malicious = self.root / "exec.txt"
        self.source.write_text('{"training": "os.system(\\"touch ' +
                               str(malicious) + '\\")"}')
        self.assertEqual(self.invoke().returncode, 2)
        self.assertFalse(malicious.exists())


if __name__ == "__main__":
    unittest.main()
