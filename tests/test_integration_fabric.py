"""Offline cross-module integration: no real signing, execution or model calls."""
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from imperial_plugins.core import GuardianCore,AuditLedger,sign_claims,canonical
from imperial_plugins.enterprise_skills import EnterpriseSkillsRegistry
from imperial_plugins.hanter_intake import FederatedRouteTable,HanterIntakeQueue
from imperial_plugins.proofgraph import create_proof_bundle,verify_proof_bundle
from imperial_plugins.adapters import plan_velion_model_route,inspect_n8n_workflow,evaluate_nca_exam

P=b"P"*32
A=b"A"*32
M={"id":"imperial.hanter-intake","version":"0.3.0","capabilities":["simulate:task"],
   "description":"Offline non-executing policy reference"}
def fabric(path):
    reg=EnterpriseSkillsRegistry()
    reg.register({"skill_id":"imperial.skill.code-draft","version":"0.3.0",
      "tenant_id":"tenant-01","orchestrator_id":"engineering-orch",
      "runtime_domain":"CODE_ENGINEERING","capability":"simulate:task",
      "risk_tier":"GUARDED","description":"Offline engineering plan",
      "requires_independent_qa":True,"requires_owner_approval":True,
      "external_effects":False,"spend_usd":0})
    routes=FederatedRouteTable([{"tenant_id":"tenant-01",
      "orchestrator_id":"engineering-orch","agent_id":"NCA-424",
      "runtime_domain":"CODE_ENGINEERING"}])
    return HanterIntakeQueue(path,GuardianCore(P,A,kill_switch=False),
                             routes,reg,kill_switch=False)
def request():
    return {"task_id":"TASK-FABRIC-001","agent_id":"NCA-424","action":"simulate:task",
       "ai_passport":sign_claims({"agent_id":"NCA-424","issuer":"IMPERIAL Core",
        "issued_at":990,"expires_at":1050},P,"passport"),
       "approval":sign_claims({"issuer":"OWNER","agent_id":"NCA-424",
        "task_id":"TASK-FABRIC-001","action":"simulate:task",
        "expires_at":1040},A,"approval")}
class TestIntegrationFabric(unittest.TestCase):
    def setUp(self):
        os.environ.pop("IMPERIAL_OWNER_KILL_SWITCH",None)
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.queue=fabric(Path(self.tmp.name)/"intake.db")
        self.args={"tenant_id":"tenant-01","orchestrator_id":"engineering-orch",
          "agent_id":"NCA-424","runtime_domain":"CODE_ENGINEERING",
          "skill_id":"imperial.skill.code-draft","manifest":M,
          "request":request(),"now":1000}
    def test_entire_local_fabric_with_audit_evidence(self):
        recorded=self.queue.record(**self.args)
        self.assertTrue(recorded["recorded"])
        route=plan_velion_model_route([{"model_id":"local-qwen",
           "enabled":True,"capabilities":["code"],"priority":0}],["code"],mode="MAX")
        self.assertEqual(route["model_id"],"local-qwen")
        self.assertFalse(route["model_invoked"])
        artifact=canonical({"route":route,"receipt":recorded["receipt"]})
        qa=canonical({"untrusted_local_test_bytes":True})
        proof=create_proof_bundle(task_id="TASK-FABRIC-001",
          agent_id="NCA-424",orchestrator_id="engineering-orch",
          tenant_id="tenant-01",manifest_sha256=hashlib.sha256(canonical(M)).hexdigest(),
          artifact=artifact,qa_report=qa)
        result=verify_proof_bundle(proof,artifact=artifact,qa_report=qa)
        self.assertTrue(result["integrity_verified"])
        self.assertFalse(result["independent_qa_verified"])
        ledger=AuditLedger(Path(self.tmp.name)/"audit.db")
        ledger.append(recorded["receipt"])
        ledger.append(proof)
        self.assertTrue(ledger.verify())
        self.assertFalse(recorded["execution_authorized"])
    def test_cross_tenant_mismatch_is_denied(self):
        self.assertFalse(self.queue.record(**(self.args|{"tenant_id":"tenant-02"}))["recorded"])
        self.assertEqual(self.queue.count(),0)
    def test_kill_switch_denies_after_prior_record(self):
        self.queue.record(**self.args)
        self.queue.guardian.kill_switch=True
        self.assertEqual(self.queue.record(**self.args)["reason"],"OWNER_KILL_SWITCH")
    def test_n8n_code_never_auto_authorized(self):
        w={"active":False,"nodes":[{"name":"HTTP",
           "type":"n8n-nodes-base.httpRequest"}]}
        result=inspect_n8n_workflow(w)
        self.assertFalse(result["approved_for_unattended_execution"])
        self.assertIn("outbound_http_requires_approval",result["static_flags"])
    def test_training_hash_is_not_independent_professional_exam(self):
        expected=hashlib.sha256(canonical({"ok":True})).hexdigest()
        score=evaluate_nca_exam([{"case_id":"SIM-001",
            "expected_sha256":expected,"critical":True}],{"SIM-001":{"ok":True}})
        self.assertTrue(score["passed"])
        self.assertFalse(score["independent_qa_verified"])
        self.assertFalse(score["real_world_skill_proven"])
    def test_proof_rejects_tampered_result(self):
        accepted=self.queue.record(**self.args)
        artifact=canonical(accepted["receipt"])
        proof=create_proof_bundle(task_id="TASK-FABRIC-001",
          agent_id="NCA-424",orchestrator_id="engineering-orch",
          tenant_id="tenant-01",manifest_sha256=hashlib.sha256(canonical(M)).hexdigest(),
          artifact=artifact,qa_report=b"unverified")
        self.assertFalse(verify_proof_bundle(proof,artifact=artifact+b"tampered",
          qa_report=b"unverified")["integrity_verified"])
if __name__=="__main__":unittest.main()
