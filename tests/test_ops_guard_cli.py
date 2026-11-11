"""End-to-end offline CLI tests with synthetic inputs only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestOperatorCLI(unittest.TestCase):
    def call(self, kind, data, extra=()):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        return subprocess.run(
            [sys.executable, str(ROOT / "tools/ops_guard.py"),
             "--kind", kind, "--now", "2026-11-10T10:30:00Z", *extra],
            input=data, text=True, capture_output=True, env=env,
            cwd=ROOT, timeout=5, check=False)

    def test_render_oom_output(self):
        event = [{"timestamp":"2026-11-10T10:00:00Z","type":"server_failed",
                  "details":{"reason":{"oomKilled":{"memoryLimit":"512Mi"}}}}]
        p = self.call("render", json.dumps(event), ("--service-id", "srv-test"))
        self.assertEqual(p.returncode, 0, p.stderr)
        response = json.loads(p.stdout)
        self.assertEqual(response["status"], "OOM_OBSERVED")
        self.assertFalse(response["recovery_authorized"])

    def test_reject_malformed_json_without_traceback(self):
        p = self.call("camera", "not-json")
        self.assertEqual(p.returncode, 2)
        self.assertFalse(json.loads(p.stdout)["execution_authorized"])
        self.assertNotIn("Traceback", p.stderr)

    def test_missing_service_id_denied(self):
        p = self.call("render", "[]")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads(p.stdout)["reason"], "SERVICE_ID_REQUIRED")


if __name__ == "__main__":
    unittest.main()
