"""Synthetic OFFLINE demonstration. No real credentials, models or external calls.

Run from repo root: PYTHONPATH=src python3 examples/federated_fabric_demo.py
"""
import hashlib
import json
import tempfile
from pathlib import Path
from imperial_plugins import (AuditLedger,GuardianCore,EnterpriseSkillsRegistry,
 FederatedRouteTable,HanterIntakeQueue,sign_claims,create_proof_bundle,verify_proof_bundle)
from imperial_plugins.adapters import plan_velion_model_route
from imperial_plugins.core import canonical

P=b"P"*32
A=b"A"*32
M={"id":"imperial.hanter-intake","version":"0.3.0",
 "capabilities":["simulate:task"],"description":"Non-executing federated example"}
registry=EnterpriseSkillsRegistry()
registry.register({"skill_id":"imperial.skill.code-draft","version":"0.3.0",
 "tenant_id":"tenant-01","orchestrator_id":"engineering-orch",
 "runtime_domain":"CODE_ENGINEERING","capability":"simulate:task",
 "risk_tier":"GUARDED","description":"Offline engineering proposal",
 "requires_independent_qa":True,"requires_owner_approval":True,
 "external_effects":False,"spend_usd":0})
routes=FederatedRouteTable([{"tenant_id":"tenant-01","orchestrator_id":"engineering-orch",
 "agent_id":"NCA-424","runtime_domain":"CODE_ENGINEERING"}])
request={"task_id":"TASK-DEMO-001","agent_id":"NCA-424","action":"simulate:task",
 "ai_passport":sign_claims({"agent_id":"NCA-424","issuer":"IMPERIAL Core",
   "issued_at":990,"expires_at":1080},P,"passport"),
 "approval":sign_claims({"issuer":"OWNER","agent_id":"NCA-424",
   "task_id":"TASK-DEMO-001","action":"simulate:task","expires_at":1060},A,"approval")}
with tempfile.TemporaryDirectory() as tmp:
    intake=HanterIntakeQueue(Path(tmp)/"intake.db",GuardianCore(P,A,kill_switch=False),
                             routes,registry,kill_switch=False)
    receipt=intake.record(tenant_id="tenant-01",orchestrator_id="engineering-orch",
       agent_id="NCA-424",runtime_domain="CODE_ENGINEERING",
       skill_id="imperial.skill.code-draft",manifest=M,request=request,now=1000)
    assert receipt["recorded"] and not receipt["execution_authorized"]
    model_plan=plan_velion_model_route([{"model_id":"synthetic-local-model",
       "enabled":True,"capabilities":["code"],"priority":0}],["code"],mode="MAX")
    artifact=canonical({"receipt":receipt["receipt"],"plan":model_plan})
    proof=create_proof_bundle(task_id="TASK-DEMO-001",agent_id="NCA-424",
       orchestrator_id="engineering-orch",tenant_id="tenant-01",
       manifest_sha256=hashlib.sha256(canonical(M)).hexdigest(),
       artifact=artifact,qa_report=b"untrusted demo bytes")
    ledger=AuditLedger(Path(tmp)/"audit.db")
    ledger.append(receipt["receipt"])
    ledger.append(proof)
    verified=verify_proof_bundle(proof,artifact=artifact,qa_report=b"untrusted demo bytes")
    assert verified["integrity_verified"] and ledger.verify()
    print(json.dumps({"mode":"SYNTHETIC_OFFLINE_ONLY",
      "intake_status":receipt["receipt"]["state"],"velion_mode":model_plan["mode"],
      "model_invoked":False,"independent_qa_verified":False,
      "integrity_verified":verified["integrity_verified"],
      "audit_chain_verified":ledger.verify(),
      "production_authorized":False},indent=2))
