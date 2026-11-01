"""Fail-closed Guardian Core regression tests; no live execution or secrets."""
import os
import unittest

from imperial_plugins.core import GuardianCore, sign_claims

PASSPORT_KEY = b"P" * 32
APPROVAL_KEY = b"A" * 32
NOW = 1000
MANIFEST = {
    "id": "imperial.guardian",
    "version": "0.2.0",
    "capabilities": ["read:public", "simulate:task"],
    "description": "Synthetic local signed-policy reference",
}


def test_request():
    return {
        "agent_id": "NCA-424",
        "task_id": "TASK-100",
        "action": "simulate:task",
        "ai_passport": sign_claims(
            {"agent_id": "NCA-424", "issuer": "IMPERIAL Core",
             "issued_at": 990, "expires_at": 1200},
            PASSPORT_KEY, "passport"
        ),
        "approval": sign_claims(
            {"issuer": "OWNER", "agent_id": "NCA-424",
             "task_id": "TASK-100", "action": "simulate:task",
             "expires_at": 1100},
            APPROVAL_KEY, "approval"
        ),
    }


class GuardianHardeningTests(unittest.TestCase):
    def setUp(self):
        self.original = os.environ.get("IMPERIAL_OWNER_KILL_SWITCH")
        os.environ.pop("IMPERIAL_OWNER_KILL_SWITCH", None)
        self.addCleanup(self.restore)
        self.guardian = GuardianCore(
            PASSPORT_KEY, APPROVAL_KEY, kill_switch=False
        )

    def restore(self):
        if self.original is None:
            os.environ.pop("IMPERIAL_OWNER_KILL_SWITCH", None)
        else:
            os.environ["IMPERIAL_OWNER_KILL_SWITCH"] = self.original

    def test_explicit_local_test_opt_out_unchanged(self):
        self.assertTrue(
            self.guardian.evaluate(MANIFEST, test_request(), now=NOW)["allowed"]
        )

    def test_explicit_zero_unchanged(self):
        os.environ["IMPERIAL_OWNER_KILL_SWITCH"] = "0"
        self.assertTrue(
            self.guardian.evaluate(MANIFEST, test_request(), now=NOW)["allowed"]
        )

    def test_unrecognized_kill_switch_settings_all_deny(self):
        for setting in ("", "off", "false", "FALSE", "2", "yes", "1", " 0"):
            with self.subTest(setting=setting):
                os.environ["IMPERIAL_OWNER_KILL_SWITCH"] = setting
                outcome = self.guardian.evaluate(MANIFEST, test_request(), now=NOW)
                self.assertEqual(
                    outcome,
                    {"allowed": False, "reason": "owner_kill_switch"},
                )

    def test_untrusted_nonstring_action_types_never_raise(self):
        for action in ([], {}, [1], 42, True, None):
            with self.subTest(action=repr(action)):
                request = test_request()
                request["action"] = action
                outcome = self.guardian.evaluate(MANIFEST, request, now=NOW)
                self.assertEqual(
                    outcome,
                    {"allowed": False, "reason": "capability_denied"},
                )

    def test_global_kill_switch_cannot_be_overridden(self):
        os.environ["IMPERIAL_OWNER_KILL_SWITCH"] = "0"
        self.assertEqual(
            GuardianCore(
                PASSPORT_KEY, APPROVAL_KEY, kill_switch=True
            ).evaluate(MANIFEST, test_request(), now=NOW)["reason"],
            "owner_kill_switch",
        )


if __name__ == "__main__":
    unittest.main()
