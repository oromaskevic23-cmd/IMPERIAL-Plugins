"""Security tests for owner-gated Search Console sitemap submission.

All data is simulated. There is no actual OAuth or Google submission.
"""
from __future__ import annotations

from dataclasses import replace
import os
import sqlite3
import tempfile
from unittest import TestCase, main
from unittest.mock import patch
from pathlib import Path

from imperial_plugins.indexing_mcp import ALLOWED_SITES
from imperial_plugins.search_console_read import (
    GoogleAccessError, SearchConsoleReadBridge, GOOGLE_SITES,
)
from imperial_plugins.search_console_submit import (
    SitemapIntent, SubmissionGate, request_google_sitemap_put,
)


class FakeGoogleReader(SearchConsoleReadBridge):
    def __init__(self, role="siteOwner"):
        super().__init__(access_token="synthetic-token-not-real")
        self.role = role
        self.calls = []

    def check_property(self, site_id):
        self.calls.append(site_id)
        return {"google_permission": self.role}


class SubmissionTests(TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Path(tmp.name) / "sitemap.db"
        self.send_log = []
        self.site_checks = []
        self.reader = FakeGoogleReader()
        self.intent = SitemapIntent("founder", "operation-001", "owner-permit-001",
                                   "qa-permit-001", "policy-v001", 900, 1100)
        self.kill_env = patch.dict(os.environ, {"IMPERIAL_OWNER_KILL_SWITCH": "0"})
        self.kill_env.start()
        self.addCleanup(self.kill_env.stop)

    def audit(self, site_id):
        self.site_checks.append(site_id)
        return {"site_id": site_id, "public_http_audit": "PASS",
                "google_indexed": "UNVERIFIED"}

    def send(self, method, endpoint, token):
        self.send_log.append((method, endpoint, token))
        return 204

    def gate(self, **kw):
        options = {
            "approval_verifier": lambda payload, ref: ref == "owner-permit-001",
            "qa_verifier": lambda payload, ref: ref == "qa-permit-001",
            "site_auditor": self.audit, "kill_switch": False,
        }
        options.update(kw)
        return SubmissionGate(self.db, **options)

    def call(self, gate=None, intent=None, send=None):
        return (gate or self.gate()).submit(intent or self.intent, self.reader,
                                            send=send or self.send, now=1000)

    def test_exact_google_submission_result_not_indexed(self):
        result = self.call()
        self.assertEqual(result["status"], "GOOGLE_SITEMAP_SUBMITTED")
        self.assertEqual(result["google_http_status"], 204)
        self.assertEqual(result["google_indexed"], "UNVERIFIED")
        self.assertEqual(len(self.send_log), 1)
        method, endpoint, token = self.send_log[0]
        self.assertEqual(method, "PUT")
        self.assertEqual(token, "synthetic-token-not-real")
        self.assertIn("%3A%2F%2F", endpoint)
        self.assertEqual(self.site_checks, ["founder"])
        with sqlite3.connect(self.db) as db:
            row = db.execute("SELECT intent_sha256,status,provider_http_status FROM submissions").fetchone()
        self.assertEqual(len(row[0]), 64)
        self.assertEqual(row[1:], ("GOOGLE_SITEMAP_SUBMITTED", 204))
        self.assertNotIn("synthetic-token-not-real", str(row))

    def test_local_audit_ledger_is_hash_linked(self):
        result = self.call()
        self.assertEqual(len(result["local_audit_event_sha256"]), 64)
        gate = self.gate()
        self.assertTrue(gate.verify_audit_chain())
        with sqlite3.connect(self.db) as db:
            count = db.execute("SELECT COUNT(*) FROM submission_events").fetchone()[0]
        self.assertEqual(count, 2)

    def test_tampering_breaks_local_evidence_chain(self):
        self.call()
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE submission_events SET event_json='{}' WHERE seq=1")
        self.assertFalse(self.gate().verify_audit_chain())

    def test_unconfirmed_response_still_records_evidence(self):
        with self.assertRaises(GoogleAccessError):
            self.call(send=lambda *_: 403)
        with sqlite3.connect(self.db) as db:
            values = db.execute("SELECT event_json FROM submission_events ORDER BY seq").fetchall()
        self.assertEqual(len(values), 2)
        self.assertIn("UNCONFIRMED_HTTP", values[1][0])
        self.assertTrue(self.gate().verify_audit_chain())

    def test_default_kill_switch_refuses_without_side_effects(self):
        gate = SubmissionGate(self.db, approval_verifier=lambda *_: True,
                              qa_verifier=lambda *_: True,
                              site_auditor=self.audit)
        with self.assertRaisesRegex(GoogleAccessError, "OWNER_KILL_SWITCH"):
            self.call(gate=gate)
        self.assertFalse(self.send_log)

    def test_environment_stop_takes_precedence(self):
        with patch.dict(os.environ, {"IMPERIAL_OWNER_KILL_SWITCH": "1"}):
            with self.assertRaisesRegex(GoogleAccessError, "OWNER_KILL_SWITCH"):
                self.call()
        self.assertFalse(self.reader.calls)
        self.assertFalse(self.send_log)

    def test_missing_or_rejected_owner_proof(self):
        for verifier in (None, lambda *_: False):
            with self.subTest(verifier=verifier):
                with self.assertRaisesRegex(GoogleAccessError, "OWNER_APPROVAL_NOT_VERIFIED"):
                    self.call(gate=self.gate(approval_verifier=verifier))
        self.assertFalse(self.reader.calls)

    def test_missing_or_rejected_independent_qa(self):
        for verifier in (None, lambda *_: False):
            with self.subTest(verifier=verifier):
                with self.assertRaisesRegex(GoogleAccessError, "INDEPENDENT_QA_NOT_VERIFIED"):
                    self.call(gate=self.gate(qa_verifier=verifier))
        self.assertFalse(self.reader.calls)

    def test_self_approval_or_malformed_ids_blocked(self):
        same = replace(self.intent, qa_proof_ref=self.intent.owner_proof_ref)
        with self.assertRaisesRegex(GoogleAccessError, "INDEPENDENT_QA_REQUIRED"):
            self.call(intent=same)
        with self.assertRaisesRegex(GoogleAccessError, "INCOMPLETE_APPROVAL_EVIDENCE"):
            self.call(intent=replace(self.intent, operation_id="invalid\noperation"))
        self.assertFalse(self.reader.calls)

    def test_expired_or_invalid_time_window(self):
        for intent in (replace(self.intent, expires_at=1000),
                       replace(self.intent, issued_at=1200),
                       replace(self.intent, expires_at=1700),
                       replace(self.intent, issued_at=True)):
            with self.subTest(intent=intent), self.assertRaisesRegex(
                    GoogleAccessError, "PERMIT_EXPIRED_OR_INVALID"):
                self.call(intent=intent)
        self.assertFalse(self.send_log)

    def test_foreign_site_denied_before_read(self):
        with self.assertRaisesRegex(GoogleAccessError, "UNREVIEWED_PROPERTY"):
            self.call(intent=replace(self.intent, site_id="http://localhost"))
        self.assertFalse(self.reader.calls)

    def test_gsc_property_write_permission_required(self):
        self.reader.role = "siteRestrictedUser"
        with self.assertRaisesRegex(GoogleAccessError, "WRITE_PERMISSION_NOT_VERIFIED"):
            self.call()
        self.assertFalse(self.send_log)

    def test_missing_trusted_write_transport(self):
        gate = self.gate()
        with self.assertRaisesRegex(GoogleAccessError, "PRIVATE_WRITE_TRANSPORT_NOT_CONNECTED"):
            gate.submit(self.intent, self.reader, now=1000)
        self.assertFalse(self.send_log)

    def test_public_sitemap_must_pass_live_audit(self):
        gate = self.gate(site_auditor=lambda site: {
            "site_id": site, "public_http_audit": "FAIL", "google_indexed": "UNVERIFIED"
        })
        with self.assertRaisesRegex(GoogleAccessError, "PUBLIC_SITEMAP_AUDIT_REQUIRED"):
            self.call(gate=gate)
        self.assertFalse(self.send_log)

    def test_restart_and_new_operation_id_cannot_repeat_property(self):
        self.call()
        new_gate = self.gate()
        with self.assertRaisesRegex(GoogleAccessError, "REPLAY_OR_UNKNOWN"):
            self.call(gate=new_gate, intent=replace(self.intent, operation_id="operation-002"))
        self.assertEqual(len(self.send_log), 1)

    def test_transport_error_is_unknown_never_auto_retried(self):
        def fail(*args):
            raise TimeoutError("unknown remote outcome")
        gate = self.gate()
        with self.assertRaisesRegex(GoogleAccessError, "OUTCOME_UNKNOWN"):
            self.call(gate=gate, send=fail)
        with sqlite3.connect(self.db) as db:
            state = db.execute("SELECT status FROM submissions").fetchone()[0]
        self.assertEqual(state, "NEEDS_RECONCILIATION")
        with self.assertRaisesRegex(GoogleAccessError, "REPLAY_OR_UNKNOWN"):
            self.call(gate=self.gate())
        self.assertEqual(len(self.send_log), 0)

    def test_google_unexpected_http_status_not_claimed_success(self):
        with self.assertRaisesRegex(GoogleAccessError, "NOT_CONFIRMED"):
            self.call(send=lambda *_: 403)
        with sqlite3.connect(self.db) as db:
            state = db.execute("SELECT status FROM submissions").fetchone()[0]
        self.assertEqual(state, "NEEDS_RECONCILIATION")


    def test_reconciliation_observes_real_registration_without_resending(self):
        self.call()
        fake_entries = [{
            "path": ALLOWED_SITES["founder"]["sitemap"],
            "lastSubmitted": "2026-11-03T21:00:00Z",
        }]
        self.reader.list_submitted_sitemaps = lambda site: {
            "site_id": site,
            "expected_sitemap": ALLOWED_SITES[site]["sitemap"],
            "found_in_google_account": True,
            "google_sitemap_entries": fake_entries,
        }
        gate = self.gate()
        result = gate.reconcile("founder", self.reader)
        self.assertEqual(result["status"], "GOOGLE_SITEMAP_OBSERVED")
        self.assertEqual(result["google_indexed"], "UNVERIFIED")
        self.assertEqual(result["new_submission_sent"], False)
        self.assertEqual(len(self.send_log), 1)
        self.assertTrue(gate.verify_audit_chain())
        again = gate.reconcile("founder", self.reader)
        self.assertEqual(again["status"], "GOOGLE_SITEMAP_OBSERVED")
        self.assertEqual(len(self.send_log), 1)
        with sqlite3.connect(self.db) as db:
            count = db.execute("SELECT COUNT(*) FROM submission_events").fetchone()[0]
        self.assertEqual(count, 3)

    def test_unknown_outcome_stays_blocked_until_google_observes(self):
        gate = self.gate()
        with self.assertRaisesRegex(GoogleAccessError, "OUTCOME_UNKNOWN"):
            self.call(gate=gate, send=lambda *_: (_ for _ in ()).throw(TimeoutError()))
        self.reader.list_submitted_sitemaps = lambda site: {
            "site_id": site,
            "expected_sitemap": ALLOWED_SITES[site]["sitemap"],
            "found_in_google_account": False,
            "google_sitemap_entries": [],
        }
        result = gate.reconcile("founder", self.reader)
        self.assertEqual(result["status"], "REQUIRES_MANUAL_REVIEW_NOT_OBSERVED")
        self.assertFalse(result["new_submission_sent"])
        with sqlite3.connect(self.db) as db:
            state = db.execute("SELECT status FROM submissions").fetchone()[0]
        self.assertEqual(state, "NEEDS_RECONCILIATION")
        with self.assertRaisesRegex(GoogleAccessError, "REPLAY_OR_UNKNOWN"):
            self.call(gate=gate)
        self.assertFalse(self.send_log)

    def test_reconcile_wrong_site_and_missing_local_operation_denied(self):
        with self.assertRaisesRegex(GoogleAccessError, "UNREVIEWED_PROPERTY"):
            self.gate().reconcile("localhost", self.reader)
        with self.assertRaisesRegex(GoogleAccessError, "UNKNOWN_LOCAL"):
            self.gate().reconcile("founder", self.reader)

    def test_reconcile_rejects_untrusted_google_result(self):
        self.call()
        self.reader.list_submitted_sitemaps = lambda site: {
            "site_id": "company",
            "expected_sitemap": ALLOWED_SITES["company"]["sitemap"],
            "found_in_google_account": True,
            "google_sitemap_entries": [{"path": ALLOWED_SITES["company"]["sitemap"]}],
        }
        with self.assertRaisesRegex(GoogleAccessError, "EVIDENCE_INVALID"):
            self.gate().reconcile("founder", self.reader)
        self.assertEqual(len(self.send_log), 1)

    def test_reconciliation_fails_closed_on_tampered_local_audit(self):
        self.call()
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE submission_events SET event_json='{}' WHERE seq=1")
        with self.assertRaisesRegex(GoogleAccessError, "AUDIT_CHAIN_TAMPERED"):
            self.gate().reconcile("founder", self.reader)

    def test_submit_transport_rejects_arbitrary_host_and_method(self):
        for method, url in (
            ("POST", GOOGLE_SITES), ("PUT", "http://169.254.169.254/"),
            ("DELETE", GOOGLE_SITES), ("PUT", GOOGLE_SITES + "/arbitrary"),
        ):
            with self.subTest(method=method, url=url), self.assertRaisesRegex(
                    GoogleAccessError, "DESTINATION_DENIED"):
                request_google_sitemap_put(method, url, "synthetic-token-not-real")


if __name__ == "__main__":
    main()
