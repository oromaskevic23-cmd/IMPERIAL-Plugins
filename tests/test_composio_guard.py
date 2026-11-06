"""Independent offline regression tests for the governed Composio transport.

Fixtures simulate separate Owner/Passport verifiers. Tests do NOT assert real
Owner signature, Composio login, deployed MCP, or live external execution.
"""
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from imperial_plugins.composio_guard import (
    ComposioDenied, GovernedComposioRead, SCHEMA,
)

TOOL = "EXAMPLE_PUBLIC_REPO_READ"  # reviewed synthetic slug, not a vendor API claim


class GovernedComposioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "composio.db"
        self.calls = []
        self.stopped = False

        def passport(digest, token):
            if token != "TEST_ONLY_PASSPORT":
                return None
            return {
                "tenant_id": "imperial-internal",
                "orchestrator_id": "engineering-orch",
                "agent_id": "NCA-424", "task_id": "TEST-RESEARCH-001",
                "capability": "read:public", "expires_at": 1100,
            }

        def permit(digest, token):
            if token != "TEST_ONLY_APPROVAL":
                return None
            return {
                "tenant_id": "imperial-internal",
                "orchestrator_id": "engineering-orch",
                "agent_id": "NCA-424", "task_id": "TEST-RESEARCH-001",
                "request_id": "REQ-ONE-0001", "tool_slug": TOOL,
                "toolkit": "github", "request_hash": digest,
                "capability": "read:public", "expires_at": 1050,
            }

        def tool(slug, args):
            self.calls.append((slug, copy.deepcopy(args)))
            return {"public_repo": args["repo"], "issues": 12}

        self.passport, self.permit, self.tool = passport, permit, tool
        self.gate = self.build()

    def build(self, **kwargs):
        return GovernedComposioRead(
            db_path=self.path,
            allowlist={TOOL: "github"},
            verify_passport=self.passport, verify_owner_permit=self.permit,
            read_tool=self.tool,
            kill_switch=lambda: self.stopped,
            clock=lambda: 1000,
            **kwargs,
        )

    def request(self):
        return {
            "schema": SCHEMA, "tenant_id": "imperial-internal",
            "orchestrator_id": "engineering-orch", "agent_id": "NCA-424",
            "task_id": "TEST-RESEARCH-001", "request_id": "REQ-ONE-0001",
            "tool_slug": TOOL, "toolkit": "github",
            "arguments": {"repo": "owner/public"},
            "passport_token": "TEST_ONLY_PASSPORT",
            "owner_permit_token": "TEST_ONLY_APPROVAL",
        }

    def denied(self, request, reason):
        with self.assertRaises(ComposioDenied) as caught:
            self.gate.execute(request)
        self.assertEqual(str(caught.exception), reason)
        self.assertEqual(self.calls, [])

    def test_successful_bounded_read_has_audit_hash_but_no_token(self):
        output = self.gate.execute(self.request())
        self.assertEqual(output["status"], "READ_ONLY_TRANSPORT_EXECUTED")
        self.assertEqual(output["result"]["public_repo"], "owner/public")
        self.assertEqual(len(output["audit_sha256"]), 64)
        self.assertFalse(output["evidence"]["external_writes_authorized"])
        self.assertTrue(self.gate.audit_valid())
        self.assertEqual(len(self.calls), 1)
        with sqlite3.connect(self.path) as db:
            audit = db.execute("SELECT event_json FROM events").fetchone()[0]
        self.assertNotIn("TEST_ONLY_PASSPORT", audit)
        self.assertNotIn("TEST_ONLY_APPROVAL", audit)
        self.assertNotIn("owner/public", audit)

    def test_default_kill_switch_denies_all_transport(self):
        gate = GovernedComposioRead(
            db_path=self.path, allowlist={TOOL: "github"},
            verify_passport=self.passport, verify_owner_permit=self.permit,
            read_tool=self.tool, clock=lambda: 1000,
        )
        with self.assertRaisesRegex(ComposioDenied, "OWNER_KILL_SWITCH"):
            gate.execute(self.request())
        self.assertEqual(self.calls, [])

    def test_revocation_at_request_time_denies(self):
        self.stopped = True
        self.denied(self.request(), "OWNER_KILL_SWITCH")

    def test_no_implicit_meta_tool_or_open_catalog(self):
        for slug in ("COMPOSIO_MULTI_EXECUTE_TOOL", "COMPOSIO_SEARCH_TOOLS"):
            with self.subTest(slug=slug):
                req = self.request()
                req["tool_slug"] = slug
                self.denied(req, "UNREVIEWED_TOOL_DENIED")
        for allowlist in ({}, {"COMPOSIO_MULTI_EXECUTE_TOOL": "gmail"}):
            with self.assertRaises(ComposioDenied):
                GovernedComposioRead(
                    db_path=self.path, allowlist=allowlist,
                    verify_passport=self.passport, verify_owner_permit=self.permit,
                    read_tool=self.tool,
                )

    def test_app_mismatch_and_private_secrets_denied(self):
        r = self.request()
        r["toolkit"] = "gmail"
        self.denied(r, "UNREVIEWED_TOOL_DENIED")
        for args in ({"api_key": "not-safe"}, {"nested": [{"headers": {}}]},
                     {"cookie": "secret"}, {"nest": [[[[[[[1]]]]]]]}):
            with self.subTest(args=args):
                r = self.request()
                r["arguments"] = args
                self.denied(r, "PRIVATE_BOUNDARY_DENIED")

    def test_invalid_scope_or_expired_permit_never_calls_transport(self):
        for bad in ("WRONG", None):
            with self.subTest(passport=bad):
                r = self.request()
                r["passport_token"] = bad
                self.denied(r, "INDEPENDENT_AUTH_REQUIRED")
        original = self.permit
        self.permit = lambda digest, token: {**original(digest, token), "agent_id": "OTHER"}
        self.gate = self.build()
        self.denied(self.request(), "PERMIT_SCOPE_DENIED")
        self.permit = lambda digest, token: {**original(digest, token), "expires_at": 1000}
        self.gate = self.build()
        self.denied(self.request(), "PERMIT_EXPIRED")

    def test_changes_to_request_break_exact_hash_binding(self):
        old = self.permit
        self.permit = lambda digest, token: {
            **old(digest, token), "request_hash": "0" * 64,
        }
        self.gate = self.build()
        self.denied(self.request(), "PERMIT_SCOPE_DENIED")

    def test_replay_denied_across_gateway_restart(self):
        self.gate.execute(self.request())
        second = self.build()
        with self.assertRaisesRegex(ComposioDenied, "REQUEST_REPLAY_DENIED"):
            second.execute(self.request())
        self.assertEqual(len(self.calls), 1)

    def test_fail_closed_if_transport_throws(self):
        self.tool = lambda *_: (_ for _ in ()).throw(RuntimeError("private details"))
        self.gate = self.build()
        with self.assertRaisesRegex(ComposioDenied, "TRANSPORT_FAILED_CLOSED"):
            self.gate.execute(self.request())
        with sqlite3.connect(self.path) as db:
            state = db.execute(
                "SELECT status FROM composio_requests"
            ).fetchone()[0]
        self.assertEqual(state, "FAILED_CLOSED")
        self.assertNotIn("private details", state)

    def test_bad_response_does_not_claim_success(self):
        self.tool = lambda *_: {"raw": "x" * 50000}
        self.gate = self.build()
        with self.assertRaisesRegex(ComposioDenied, "RESOURCE_LIMIT"):
            self.gate.execute(self.request())
        self.assertTrue(self.gate.audit_valid())

    def test_verifier_exception_fails_closed(self):
        self.passport = lambda *_: (_ for _ in ()).throw(OSError("secret exception"))
        self.gate = self.build()
        self.denied(self.request(), "AUTH_VERIFIER_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
