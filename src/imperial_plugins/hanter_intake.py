"""Federated HANTER intake: records proposals, NEVER dispatches NCA or plugins.

Uses legacy shared-secret HMAC GuardianCore in ONE test trust domain only.
Real Owner/AI Passport issuance, remote NCA runtime and PKI are elsewhere.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from .core import AGENT_PATTERN, GuardianCore, canonical, validate_manifest
from .enterprise_skills import DOMAINS, EnterpriseSkillsRegistry

ROUTE_FIELDS = frozenset({"tenant_id", "orchestrator_id", "agent_id", "runtime_domain"})

class FederatedRouteTable:
    """Explicit per-agent routes; no cross-tenant agent or orchestrator reuse."""
    def __init__(self, entries: list[dict]):
        if not isinstance(entries, list) or not entries:
            raise ValueError("ROUTES_REQUIRED")
        self._routes: dict[str, dict] = {}
        self._orch_tenants: dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != ROUTE_FIELDS:
                raise ValueError("INVALID_ROUTE_SCHEMA")
            if any(not isinstance(entry[k], str) or not AGENT_PATTERN.fullmatch(entry[k])
                   for k in ("tenant_id", "orchestrator_id", "agent_id")):
                raise ValueError("INVALID_ROUTE_IDENTITY")
            if not isinstance(entry["runtime_domain"], str) or entry["runtime_domain"] not in DOMAINS:
                raise ValueError("INVALID_RUNTIME_DOMAIN")
            agent, orch, tenant = entry["agent_id"], entry["orchestrator_id"], entry["tenant_id"]
            if agent in self._routes:
                raise ValueError("DUPLICATE_AGENT_ROUTE")
            if orch in self._orch_tenants and self._orch_tenants[orch] != tenant:
                raise ValueError("CROSS_TENANT_ORCHESTRATOR")
            self._routes[agent] = dict(entry)
            self._orch_tenants[orch] = tenant

    def match(self, *, tenant_id: str, orchestrator_id: str,
              agent_id: str, runtime_domain: str) -> bool:
        if any(not isinstance(x, str) for x in (
             tenant_id, orchestrator_id, agent_id, runtime_domain)):
            return False
        return self._routes.get(agent_id) == {
            "tenant_id": tenant_id, "orchestrator_id": orchestrator_id,
            "agent_id": agent_id, "runtime_domain": runtime_domain}

class HanterIntakeQueue:
    """Single-host SQLite idempotent intake without executing any task.

    All decisions are scoped by explicit tenant / federation route and a
    reference Guardian. Does not store full passport or approval documents.
    """

    def __init__(self, path: str | Path, guardian: GuardianCore,
                 routes: FederatedRouteTable, skills: EnterpriseSkillsRegistry,
                 *, kill_switch: bool = True):
        if not isinstance(guardian, GuardianCore) or not isinstance(routes, FederatedRouteTable):
            raise ValueError("BAD_GUARD_OR_ROUTE")
        if not isinstance(skills, EnterpriseSkillsRegistry):
            raise ValueError("BAD_SKILLS")
        self.path, self.guardian, self.routes, self.skills = str(path), guardian, routes, skills
        self.kill_switch = kill_switch
        with closing(self._connect()) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS proposals(
              tenant_id TEXT NOT NULL,task_id TEXT NOT NULL,
              agent_id TEXT NOT NULL,orchestrator_id TEXT NOT NULL,
              runtime_domain TEXT NOT NULL,skill_id TEXT NOT NULL,
              proposal_sha256 TEXT NOT NULL,receipt_json TEXT NOT NULL,
              PRIMARY KEY(tenant_id,task_id))""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def record(self, *, tenant_id: str, orchestrator_id: str, agent_id: str,
               runtime_domain: str, skill_id: str, manifest: dict,
               request: dict, now: int | None = None) -> dict:
        def deny(reason: str) -> dict:
            return {"recorded": False, "reason": reason, "execution_authorized": False}
        if self.kill_switch or self.guardian.kill_switch:
            return deny("OWNER_KILL_SWITCH")
        if not isinstance(request, dict) or not isinstance(manifest, dict):
            return deny("INVALID_PROPOSAL")
        task_id = request.get("task_id")
        if not isinstance(task_id, str) or not AGENT_PATTERN.fullmatch(task_id):
            return deny("INVALID_TASK")
        if not self.routes.match(tenant_id=tenant_id, orchestrator_id=orchestrator_id,
                                 agent_id=agent_id, runtime_domain=runtime_domain):
            return deny("FEDERATED_ROUTE_DENIED")
        try:
            checked = validate_manifest(manifest)
        except (ValueError, TypeError):
            return deny("INVALID_MANIFEST")
        action = request.get("action")
        if not isinstance(action, str) or action == "read:public":
            return deny("OWNER_APPROVAL_REQUIRED_FOR_INTAKE")
        skill = self.skills.plan(tenant_id=tenant_id, skill_id=skill_id,
                                 orchestrator_id=orchestrator_id,
                                 runtime_domain=runtime_domain, capability=action)
        if not skill["planned"] or action not in checked["capabilities"]:
            return deny("ENTERPRISE_SKILL_DENIED")
        decision = self.guardian.evaluate(checked, request, now=now)
        if decision["allowed"] is not True or request.get("agent_id") != agent_id:
            return deny("GUARDIAN_DENIED")
        try:
            digest = hashlib.sha256(canonical({
                "tenant_id": tenant_id, "orchestrator_id": orchestrator_id,
                "agent_id": agent_id, "runtime_domain": runtime_domain,
                "skill_id": skill_id, "skill_sha256": skill["descriptor_sha256"],
                "manifest": checked, "request": request})).hexdigest()
        except (ValueError, TypeError, OverflowError):
            return deny("INVALID_REQUEST_ENCODING")
        receipt = {"schema": "imperial.hanter.intake.local.v1",
                   "task_id": task_id, "agent_id": agent_id,
                   "tenant_id": tenant_id, "orchestrator_id": orchestrator_id,
                   "runtime_domain": runtime_domain, "skill_id": skill_id,
                   "request_sha256": digest, "state": "RECORDED_LAB_ONLY",
                   "execution_authorized": False, "model_invoked": False,
                   "independent_qa_verified": False, "external_effects": False,
                   "spending_usd": 0}
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                existing = db.execute(
                  "SELECT proposal_sha256,receipt_json FROM proposals WHERE tenant_id=? AND task_id=?",
                  (tenant_id, task_id)).fetchone()
                if existing:
                    db.commit()
                    if not hmac.compare_digest(existing[0], digest):
                        return deny("TASK_REPLAY_WITH_DIFFERENT_CONTENT")
                    try:
                        saved_receipt = json.loads(existing[1])
                    except (TypeError, ValueError, json.JSONDecodeError):
                        return deny("PERSISTED_RECEIPT_TAMPERED")
                    if saved_receipt != receipt:
                        return deny("PERSISTED_RECEIPT_TAMPERED")
                    return {"recorded": True, "reason": "IDEMPOTENT_REPLAY",
                            "receipt": receipt, "execution_authorized": False}
                db.execute("""INSERT INTO proposals(
                    tenant_id,task_id,agent_id,orchestrator_id,runtime_domain,
                    skill_id,proposal_sha256,receipt_json)
                    VALUES(?,?,?,?,?,?,?,?)""",
                    (tenant_id,task_id,agent_id,orchestrator_id,runtime_domain,
                     skill_id,digest,canonical(receipt).decode("utf-8")))
                db.commit()
            except Exception:
                db.rollback()
                raise
        return {"recorded": True, "reason": "PROPOSAL_RECORDED_ONLY",
                "receipt": receipt, "execution_authorized": False}

    def count(self) -> int:
        with closing(self._connect()) as db:
            return db.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]
