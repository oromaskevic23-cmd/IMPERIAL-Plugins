import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from imperial_plugins.core import AuditLedger, GuardianCore, sign_claims, validate_manifest

P = b"P" * 32
A = b"A" * 32
M = {"id": "imperial.guardian", "version": "0.2.0",
     "capabilities": ["read:public", "simulate:task"],
     "description": "Local reference"}


def request(now=1000, action="simulate:task"):
    passport = sign_claims(
        {"agent_id": "NCA-424", "issuer": "IMPERIAL Core",
         "issued_at": now - 10, "expires_at": now + 300}, P, "passport")
    approval = sign_claims(
        {"issuer": "OWNER", "agent_id": "NCA-424", "task_id": "TASK-1",
         "action": action, "expires_at": now + 120}, A, "approval")
    return {"task_id": "TASK-1", "agent_id": "NCA-424", "action": action,
            "ai_passport": passport, "approval": approval}


class PolicyTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("IMPERIAL_OWNER_KILL_SWITCH", None)
        self.gate = GuardianCore(P, A, kill_switch=False)

    def test_manifest(self):
        self.assertEqual(validate_manifest(M)["id"], M["id"])

    def test_manifest_rejects_unknown_capability(self):
        with self.assertRaises(ValueError):
            validate_manifest({**M, "capabilities": ["execute:payment"]})

    def test_manifest_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            validate_manifest({**M, "capabilities": ["read:public"] * 2})

    def test_kill_switch_defaults_to_engaged(self):
        self.assertFalse(GuardianCore(P, A).evaluate(M, request(), now=1000)["allowed"])

    def test_environment_kill_switch(self):
        os.environ["IMPERIAL_OWNER_KILL_SWITCH"] = "1"
        try:
            self.assertEqual(self.gate.evaluate(M, request(), now=1000)["reason"], "owner_kill_switch")
        finally:
            os.environ.pop("IMPERIAL_OWNER_KILL_SWITCH", None)

    def test_simulation_approved(self):
        self.assertTrue(self.gate.evaluate(M, request(), now=1000)["allowed"])

    def test_missing_approval(self):
        r = request()
        r.pop("approval")
        self.assertEqual(self.gate.evaluate(M, r, now=1000)["reason"], "approval_required")

    def test_approval_cannot_change_action(self):
        r = request()
        r["action"] = "read:public"
        self.assertTrue(self.gate.evaluate(M, r, now=1000)["allowed"])
        r["action"] = "simulate:task"
        r["task_id"] = "TASK-2"
        self.assertFalse(self.gate.evaluate(M, r, now=1000)["allowed"])

    def test_tamper_detected(self):
        r = request()
        r["ai_passport"]["claims"]["agent_id"] = "NCA-425"
        self.assertEqual(self.gate.evaluate(M, r, now=1000)["reason"], "passport_invalid")

    def test_expired_passport(self):
        self.assertFalse(self.gate.evaluate(M, request(), now=2000)["allowed"])

    def test_payment_never_authorized(self):
        r = request()
        r["action"] = "execute:payment"
        self.assertFalse(self.gate.evaluate(M, r, now=1000)["allowed"])

    def test_mismatched_passport(self):
        r = request()
        r["agent_id"] = "NCA-500"
        self.assertFalse(self.gate.evaluate(M, r, now=1000)["allowed"])

    def test_wrong_issuer(self):
        r = request()
        r["ai_passport"] = sign_claims(
            {**r["ai_passport"]["claims"], "issuer": "other"},
            P, "passport")
        self.assertFalse(self.gate.evaluate(M, r, now=1000)["allowed"])

    def test_no_shared_key(self):
        with self.assertRaises(ValueError):
            GuardianCore(P, P)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "audit.db"
        self.ledger = AuditLedger(self.path)

    def test_chain_integrity(self):
        self.ledger.append({"action": "read", "allowed": True})
        self.ledger.append({"action": "simulate", "allowed": False})
        self.assertTrue(self.ledger.verify())

    def test_tamper_detected(self):
        self.ledger.append({"x": 1})
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE events SET event_json='{}' WHERE seq=1")
        self.assertFalse(self.ledger.verify())

    def test_deterministic_chain(self):
        first = self.ledger.append({"b": 2, "a": 1})
        self.assertEqual(len(first["hash"]), 64)


if __name__ == "__main__":
    unittest.main()
