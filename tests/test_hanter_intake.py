import concurrent.futures
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from imperial_plugins.core import AuditLedger,GuardianCore,sign_claims
from imperial_plugins.enterprise_skills import EnterpriseSkillsRegistry
from imperial_plugins.hanter_intake import FederatedRouteTable,HanterIntakeQueue

P=b"P"*32
A=b"A"*32
M={"id":"imperial.hanter-intake","version":"0.3.0",
   "capabilities":["simulate:task"],"description":"Bounded internal lab"}
ROUTES=[{"tenant_id":"tenant-01","orchestrator_id":"engineering-orch",
         "agent_id":"NCA-424","runtime_domain":"CODE_ENGINEERING"},
        {"tenant_id":"tenant-02","orchestrator_id":"security-orch",
         "agent_id":"NCA-501","runtime_domain":"SECURITY_DEFENSIVE"}]

def req(task="TASK-001",agent="NCA-424",now=1000):
    return {"task_id":task,"agent_id":agent,"action":"simulate:task",
        "ai_passport":sign_claims({"agent_id":agent,"issuer":"IMPERIAL Core",
                      "issued_at":now-10,"expires_at":now+100},P,"passport"),
        "approval":sign_claims({"issuer":"OWNER","agent_id":agent,
                      "task_id":task,"action":"simulate:task","expires_at":now+60},
                      A,"approval")}

def registry():
    r=EnterpriseSkillsRegistry()
    r.register({"skill_id":"imperial.skill.code-draft","version":"0.3.0",
      "tenant_id":"tenant-01","orchestrator_id":"engineering-orch",
      "runtime_domain":"CODE_ENGINEERING","capability":"simulate:task",
      "risk_tier":"GUARDED","description":"Offline engineering draft assessment",
      "requires_independent_qa":True,"requires_owner_approval":True,
      "external_effects":False,"spend_usd":0})
    return r

class TestHanterIntake(unittest.TestCase):
    def setUp(self):
        os.environ.pop("IMPERIAL_OWNER_KILL_SWITCH",None)
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"jobs.db"
        self.guard=GuardianCore(P,A,kill_switch=False)
        self.queue=HanterIntakeQueue(self.path,self.guard,
                       FederatedRouteTable(ROUTES),registry(),kill_switch=False)
    def record(self,**updates):
        args={"tenant_id":"tenant-01","orchestrator_id":"engineering-orch",
              "agent_id":"NCA-424","runtime_domain":"CODE_ENGINEERING",
              "skill_id":"imperial.skill.code-draft","manifest":M,
              "request":req(),"now":1000}
        return self.queue.record(**(args|updates))
    def test_record_only_no_execution(self):
        x=self.record()
        self.assertTrue(x["recorded"])
        self.assertEqual(x["receipt"]["state"],"RECORDED_LAB_ONLY")
        for k in ("execution_authorized","model_invoked","independent_qa_verified","external_effects"):
            self.assertFalse(x["receipt"][k])
        self.assertEqual(self.queue.count(),1)
    def test_exact_replay_idempotent(self):
        x=self.record()
        y=self.record()
        self.assertEqual(y["reason"],"IDEMPOTENT_REPLAY")
        self.assertEqual(y["receipt"],x["receipt"])
        self.assertEqual(self.queue.count(),1)
    def test_changed_replay_denied(self):
        self.record()
        modified=req()
        modified["ai_passport"]=sign_claims({"agent_id":"NCA-424",
             "issuer":"IMPERIAL Core","issued_at":980,"expires_at":1100},P,"passport")
        self.assertEqual(self.record(request=modified)["reason"],"TASK_REPLAY_WITH_DIFFERENT_CONTENT")
    def test_federated_tenant_and_orchestrator_isolation(self):
        for bad in ({"tenant_id":"tenant-02"},{"agent_id":"NCA-501"},
                    {"orchestrator_id":"security-orch"},
                    {"runtime_domain":"SECURITY_DEFENSIVE"}):
            with self.subTest(bad=bad):
                self.assertEqual(self.record(**bad)["reason"],"FEDERATED_ROUTE_DENIED")
        self.assertEqual(self.queue.count(),0)
    def test_missing_skill_and_approval_denied(self):
        self.assertEqual(self.record(skill_id="imperial.skill.fake")["reason"],
                         "ENTERPRISE_SKILL_DENIED")
        unsigned=req();unsigned.pop("approval")
        self.assertEqual(self.record(request=unsigned)["reason"],"GUARDIAN_DENIED")
        self.assertEqual(self.queue.count(),0)
    def test_foreign_signed_agent_denied(self):
        self.assertEqual(self.record(request=req(agent="NCA-501"))["reason"],"GUARDIAN_DENIED")
    def test_default_owner_kill_switch(self):
        q=HanterIntakeQueue(Path(self.tmp.name)/"deny.db",self.guard,
             FederatedRouteTable(ROUTES),registry())
        self.assertTrue(q.kill_switch)
        self.assertEqual(q.count(),0)
    def test_guardian_stop_denies_old_replay(self):
        self.record()
        self.guard.kill_switch=True
        self.assertEqual(self.record()["reason"],"OWNER_KILL_SWITCH")
    def test_environment_stop_refused(self):
        os.environ["IMPERIAL_OWNER_KILL_SWITCH"]="1"
        try:self.assertEqual(self.record()["reason"],"GUARDIAN_DENIED")
        finally:os.environ.pop("IMPERIAL_OWNER_KILL_SWITCH",None)
    def test_concurrent_same_task_recorded_once(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _:self.record(),range(16)))
        self.assertTrue(all(x["recorded"] for x in results))
        self.assertEqual(sum(x["reason"]=="PROPOSAL_RECORDED_ONLY" for x in results),1)
        self.assertEqual(self.queue.count(),1)
    def test_only_hash_and_public_receipt_stored(self):
        self.record()
        with sqlite3.connect(self.path) as db:
            data=db.execute("SELECT receipt_json FROM proposals").fetchone()[0]
        self.assertNotIn("ai_passport",data)
        self.assertNotIn("signature",data)
        self.assertNotIn("approval",data)
    def test_restarted_queue_preserves_receipt(self):
        self.record()
        another=HanterIntakeQueue(self.path,self.guard,FederatedRouteTable(ROUTES),
                                  registry(),kill_switch=False)
        x=another.record(tenant_id="tenant-01",orchestrator_id="engineering-orch",
           agent_id="NCA-424",runtime_domain="CODE_ENGINEERING",
           skill_id="imperial.skill.code-draft",manifest=M,request=req(),now=1000)
        self.assertEqual(x["reason"],"IDEMPOTENT_REPLAY")
    def test_integrates_with_local_audit_chain(self):
        data=self.record()
        a=AuditLedger(Path(self.tmp.name)/"audit.db")
        a.append(data["receipt"])
        self.assertTrue(a.verify())
    def test_cross_tenant_router_configuration_rejected(self):
        for bad in ([ROUTES[0],ROUTES[0]],
          [ROUTES[0],{"tenant_id":"tenant-02","orchestrator_id":"engineering-orch",
                       "agent_id":"NCA-501","runtime_domain":"SECURITY_DEFENSIVE"}],
          [{**ROUTES[0],"runtime_domain":"PAYMENTS"}],
          [{**ROUTES[0],"entrypoint":"evil.py"}]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                FederatedRouteTable(bad)
    def test_unhashable_action_denied(self):
        bad=req();bad["action"]={"exec":"anything"}
        self.assertFalse(self.record(request=bad)["recorded"])

if __name__=="__main__":unittest.main()
