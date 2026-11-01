import hashlib
import unittest
from imperial_plugins.proofgraph import create_proof_bundle,verify_proof_bundle,digest_bytes

ARTIFACT=b"export function clamp(v,lo,hi){return Math.max(lo,Math.min(v,hi));}"
QA=b'{"local_untrusted_qa_report":true}'
def proof(**changes):
    return create_proof_bundle(task_id="TASK-001",agent_id="NCA-424",
        orchestrator_id="engineering-orch",tenant_id="tenant-01",
        manifest_sha256="a"*64,artifact=ARTIFACT,qa_report=QA,**changes)

class TestProofGraph(unittest.TestCase):
    def verify(self,p,artifact=ARTIFACT,qa_report=QA,**kw):
        return verify_proof_bundle(p,artifact=artifact,qa_report=qa_report,**kw)
    def test_integrity_is_not_independent_qa_or_permission(self):
        result=self.verify(proof())
        self.assertTrue(result["integrity_verified"])
        self.assertFalse(result["independent_qa_verified"])
        self.assertFalse(result["production_authorized"])
    def test_actual_artifact_and_qa_bytes_bound(self):
        p=proof()
        self.assertEqual(p["artifact_sha256"],hashlib.sha256(ARTIFACT).hexdigest())
        self.assertFalse(self.verify(p,artifact=ARTIFACT+b"x")["integrity_verified"])
        self.assertFalse(self.verify(p,qa_report=QA+b"x")["integrity_verified"])
    def test_tamper_and_privilege_inflation_denied(self):
        p=proof()
        for key,value in (("agent_id","NCA-999"),("tenant_id","tenant-02"),
                          ("qa_verdict_claim","PASS"),("qa_provenance","INDEPENDENT"),
                          ("production_authorized",True),("external_effects",True),
                          ("spend_usd",10),("proof_sha256","0"*64)):
            with self.subTest(key=key):
                self.assertFalse(self.verify(p|{key:value})["integrity_verified"])
    def test_unknown_fields_denied(self):
        p=proof()
        self.assertFalse(self.verify(p|{"remote_exec":"yes"})["integrity_verified"])
        del p["proof_sha256"]
        self.assertFalse(self.verify(p)["integrity_verified"])
    def test_proof_chain_requires_external_expected_anchor(self):
        first=proof()
        second=proof(previous_proof_sha256=first["proof_sha256"])
        self.assertTrue(self.verify(second,expected_previous=first["proof_sha256"])["integrity_verified"])
        self.assertFalse(self.verify(second,expected_previous="f"*64)["integrity_verified"])
    def test_invalid_digest_and_oversize(self):
        for x in ("INVALID","A"*64,100):
            with self.subTest(x=x),self.assertRaises(ValueError):
                proof(previous_proof_sha256=x)
        with self.assertRaises(ValueError):digest_bytes(b"x"*(8*1024*1024+1))
    def test_non_json_tampering_denied(self):
        self.assertFalse(self.verify(proof()|{"agent_id":{}})["integrity_verified"])

if __name__=="__main__":unittest.main()
