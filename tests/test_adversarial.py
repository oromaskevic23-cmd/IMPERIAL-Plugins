import hashlib
import hmac
import os
import tempfile
import unittest

from imperial_plugins.core import AuditLedger, GuardianCore, sign_claims, validate_manifest

P = b"P"*32
A = b"A"*32
M = {"id": "imperial.policy", "version": "0.2.0",
     "capabilities": ["read:public", "simulate:task"], "description": "policy"}


def request():
    return {"task_id": "JOB-11", "agent_id": "NCA-501", "action": "simulate:task",
            "ai_passport": sign_claims(
                {"agent_id": "NCA-501", "issuer": "IMPERIAL Core",
                 "issued_at": 100, "expires_at": 300}, P, "passport"),
            "approval": sign_claims(
                {"issuer": "OWNER", "agent_id": "NCA-501", "task_id": "JOB-11",
                 "action": "simulate:task", "expires_at": 250}, A, "approval")}


class AdversarialTests(unittest.TestCase):
    def setUp(self):
        self.old = os.environ.get("IMPERIAL_OWNER_KILL_SWITCH")
        os.environ["IMPERIAL_OWNER_KILL_SWITCH"] = "0"
        self.g = GuardianCore(P, A, kill_switch=False)

    def tearDown(self):
        if self.old is None:
            os.environ.pop("IMPERIAL_OWNER_KILL_SWITCH", None)
        else:
            os.environ["IMPERIAL_OWNER_KILL_SWITCH"] = self.old

    def test_signed_good(self):
        self.assertTrue(self.g.evaluate(M, request(), now=200)["allowed"])

    def test_cross_purpose_signature_rejected(self):
        r = request()
        r["approval"] = sign_claims(r["approval"]["claims"], P, "passport")
        self.assertFalse(self.g.evaluate(M, r, now=200)["allowed"])

    def test_expired_approval(self):
        self.assertFalse(self.g.evaluate(M, request(), now=270)["allowed"])

    def test_approval_wrong_agent(self):
        r = request()
        r["approval"] = sign_claims(
            {**r["approval"]["claims"], "agent_id": "NCA-999"}, A, "approval")
        self.assertFalse(self.g.evaluate(M, r, now=200)["allowed"])

    def test_boolean_expiry_rejected(self):
        r = request()
        r["approval"] = sign_claims(
            {**r["approval"]["claims"], "expires_at": True}, A, "approval")
        self.assertFalse(self.g.evaluate(M, r, now=200)["allowed"])

    def test_empty_issuer_rejected(self):
        r = request()
        r["ai_passport"] = sign_claims(
            {**r["ai_passport"]["claims"], "issuer": ""}, P, "passport")
        self.assertFalse(self.g.evaluate(M, r, now=200)["allowed"])

    def test_no_passport_read_denied(self):
        r = request()
        r["action"] = "read:public"
        r["ai_passport"] = None
        self.assertFalse(self.g.evaluate(M, r, now=200)["allowed"])

    def test_unknown_fields_manifest_denied(self):
        with self.assertRaises(ValueError):
            validate_manifest({**M, "entrypoint": "evil.py"})

    def test_overlong_passport_lifetime_denied(self):
        r = request()
        r["ai_passport"] = sign_claims(
            {**r["ai_passport"]["claims"], "expires_at": 5000}, P, "passport")
        self.assertFalse(self.g.evaluate(M, r, now=200)["allowed"])

    def test_invalid_signer_key(self):
        with self.assertRaises(ValueError):
            sign_claims({}, b"x", "approval")

    def test_ledger_previous_hash_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = AuditLedger(tmp + "/audit.db")
            led.append({"e": 1})
            db = led._connect()
            try:
                db.execute("UPDATE events SET previous_hash=? WHERE seq=1", ("1"*64,))
            finally:
                db.close()
            self.assertFalse(led.verify())
