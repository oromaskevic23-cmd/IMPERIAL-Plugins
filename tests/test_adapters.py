import hashlib
import unittest
from imperial_plugins.adapters import (
    evaluate_nca_exam, inspect_n8n_workflow, plan_velion_model_route)
from imperial_plugins.core import canonical


class AdapterTests(unittest.TestCase):
    def test_exam_pass_and_evidence_limits(self):
        expected = hashlib.sha256(canonical({"answer": "safe"})).hexdigest()
        result = evaluate_nca_exam(
            [{"case_id": "SIM-01", "expected_sha256": expected, "critical": True}],
            {"SIM-01": {"answer": "safe"}})
        self.assertTrue(result["passed"])
        self.assertFalse(result["independent_qa_verified"])

    def test_exam_rejects_wrong_answer(self):
        digest = hashlib.sha256(canonical({"value": 2})).hexdigest()
        result = evaluate_nca_exam(
            [{"case_id": "SIM-01", "expected_sha256": digest, "critical": True}],
            {"SIM-01": {"value": 3}})
        self.assertFalse(result["passed"])

    def test_exam_requires_critical_pass(self):
        good = hashlib.sha256(canonical({"ok": True})).hexdigest()
        result = evaluate_nca_exam([
            {"case_id": "SIM-01", "expected_sha256": good, "critical": True},
            {"case_id": "SIM-02", "expected_sha256": good, "critical": False}],
            {"SIM-02": {"ok": True}}, pass_fraction=0.5)
        self.assertFalse(result["passed"])

    def test_duplicate_exam_cases_blocked(self):
        c = {"case_id": "SIM-01", "expected_sha256": "0"*64, "critical": False}
        with self.assertRaises(ValueError):
            evaluate_nca_exam([c, c], {})

    def test_workflow_code_needs_review(self):
        result = inspect_n8n_workflow({"active": False, "nodes": [
            {"name": "Code", "type": "n8n-nodes-base.code"}]})
        self.assertIn("code_requires_human_review", result["static_flags"])
        self.assertFalse(result["approved_for_unattended_execution"])

    def test_workflow_network_needs_approval(self):
        result = inspect_n8n_workflow({"active": False, "nodes": [
            {"name": "HTTP", "type": "n8n-nodes-base.httpRequest"}]})
        self.assertIn("outbound_http_requires_approval", result["static_flags"])

    def test_workflow_activated_not_approved(self):
        result = inspect_n8n_workflow({"active": True, "nodes": [
            {"name": "Trigger", "type": "n8n-nodes-base.manualTrigger"}]})
        self.assertIn("workflow_not_inactive", result["static_flags"])

    def test_velion_route_selects_allowlisted_capability(self):
        candidates = [{"model_id": "local-model", "enabled": True,
                       "capabilities": ["text"], "priority": 1},
                      {"model_id": "disabled", "enabled": False,
                       "capabilities": ["text"], "priority": 0}]
        result = plan_velion_model_route(candidates, ["text"], mode="MAX")
        self.assertEqual(result["model_id"], "local-model")
        self.assertEqual(result["mode"], "MAX")
        self.assertFalse(result["model_invoked"])

    def test_velion_denies_no_capable_model(self):
        self.assertIsNone(plan_velion_model_route([], ["tools"])["model_id"])

    def test_velion_bad_mode(self):
        with self.assertRaises(ValueError):
            plan_velion_model_route([], [], mode="VELEON")
