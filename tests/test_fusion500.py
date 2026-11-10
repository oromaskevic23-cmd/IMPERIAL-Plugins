"""Adversarial offline tests: identities, scope, no side effects, bounded MCP."""
import io
import os
import unittest
from unittest.mock import patch

from imperial_plugins.fusion500 import (
    FusionValidationError, PILLARS, ROSTER, build_roster,
    list_profiles, plan_task, roster_proof,
)
from imperial_plugins.fusion500_mcp import handle_rpc, serve


def sample(**kwargs):
    r = {"task_id": "TASK-001", "tenant_id": "tenant-01",
         "orchestrator_id": "ASTRA", "pillar": "figma",
         "workstream": "components", "max_spend_usd": 0,
         "requested_external_effect": False}
    return r | kwargs


class Fusion500Tests(unittest.TestCase):
    def test_exact_500_unique_profiles_20_squads(self):
        proof = roster_proof()
        self.assertEqual(proof["profile_count"], 500)
        self.assertEqual(proof["squad_count"], 20)
        self.assertEqual(proof["profiles_by_pillar"], {p: 125 for p in PILLARS})
        self.assertEqual(len({p.profile_id for p in ROSTER}), 500)

    def test_roster_deterministic(self):
        self.assertEqual(build_roster(), ROSTER)
        self.assertEqual(roster_proof()["roster_sha256"], roster_proof()["roster_sha256"])

    def test_none_live(self):
        self.assertTrue(all(p.status == "PROFILE_ONLY_NOT_RUNNING" for p in ROSTER))
        self.assertFalse(roster_proof()["provider_connections_verified"])
        self.assertFalse(roster_proof()["production_ready"])

    def test_25_per_squad(self):
        for squad in {p.squad_id for p in ROSTER}:
            self.assertEqual(sum(p.squad_id == squad for p in ROSTER), 25)

    def test_pagination(self):
        first = list_profiles(pillar="netlify", limit=25)
        second = list_profiles(pillar="netlify", offset=25, limit=25)
        self.assertEqual(len(first["profiles"]), 25)
        self.assertFalse(set(x["profile_id"] for x in first["profiles"]) &
                         set(x["profile_id"] for x in second["profiles"]))

    def test_no_other_pillar(self):
        with self.assertRaises(FusionValidationError):
            list_profiles(pillar="stripe")

    def test_bad_pagination(self):
        for kwargs in ({"pillar":"figma","limit":26}, {"pillar":"figma","limit":True},
                       {"pillar":"figma","offset":-1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(FusionValidationError):
                list_profiles(**kwargs)

    def test_default_owner_kill_switch(self):
        with patch.dict(os.environ, {}, clear=True):
            p = plan_task(sample())
        self.assertEqual(p["status"], "BLOCKED_OWNER_KILL_SWITCH")
        self.assertFalse(p["execution_authorized"])

    def test_lab_plan_still_cannot_execute(self):
        with patch.dict(os.environ, {"IMPERIAL_OWNER_KILL_SWITCH":"0"}):
            p = plan_task(sample(), kill_switch=False)
        self.assertEqual(p["status"], "PROPOSED_NOT_EXECUTED")
        self.assertTrue(p["requires_ai_passport"])
        self.assertFalse(p["execution_authorized"])
        self.assertFalse(p["provider_called"])
        self.assertFalse(p["owner_signature_verified"])

    def test_routing_is_stable_and_tenant_scoped(self):
        with patch.dict(os.environ, {"IMPERIAL_OWNER_KILL_SWITCH":"0"}):
            a = plan_task(sample(), kill_switch=False)
            b = plan_task(sample(), kill_switch=False)
            c = plan_task(sample(tenant_id="tenant-02"), kill_switch=False)
        self.assertEqual(a["profile_id"], b["profile_id"])
        self.assertEqual(a["tenant_id"], "tenant-01")
        self.assertEqual(c["tenant_id"], "tenant-02")
        self.assertTrue(a["profile_id"].startswith("F500-FIGMA"))

    def test_external_action_requires_owner_approval(self):
        with patch.dict(os.environ, {"IMPERIAL_OWNER_KILL_SWITCH":"0"}):
            p = plan_task(sample(requested_external_effect=True), kill_switch=False)
        self.assertTrue(p["requires_owner_approval"])
        self.assertFalse(p["execution_authorized"])

    def test_netlify_requires_approval_even_for_planning(self):
        with patch.dict(os.environ, {"IMPERIAL_OWNER_KILL_SWITCH":"0"}):
            p = plan_task(sample(pillar="netlify", workstream="preview-plan"), kill_switch=False)
        self.assertTrue(p["requires_owner_approval"])
        self.assertFalse(p["execution_authorized"])

    def test_spend_rejected(self):
        for bad in (1, -1, 0.0, True, "0", None):
            with self.subTest(value=bad), self.assertRaises(FusionValidationError):
                plan_task(sample(max_spend_usd=bad))

    def test_unknown_keys_fail_closed(self):
        for k, value in (("api_key","secret"), ("execute",True), ("signed",True)):
            with self.subTest(key=k), self.assertRaises(FusionValidationError):
                plan_task(sample(**{k:value}))

    def test_cross_pillar_and_non_boolean_effect_denied(self):
        with self.assertRaises(FusionValidationError):
            plan_task(sample(workstream="release-qa"))
        with self.assertRaises(FusionValidationError):
            plan_task(sample(requested_external_effect="false"))

    def test_invalid_identity_denied(self):
        for bad in (" ", "../unsafe", "a", "T"*81, "tenant\nfoo", 10, None):
            with self.subTest(value=bad), self.assertRaises(FusionValidationError):
                plan_task(sample(tenant_id=bad))

    def test_kill_switch_bad_environment_fails_closed(self):
        with patch.dict(os.environ, {"IMPERIAL_OWNER_KILL_SWITCH":"false"}):
            p = plan_task(sample(), kill_switch=False)
        self.assertEqual(p["status"], "BLOCKED_OWNER_KILL_SWITCH")

    def test_requires_no_network_or_token(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(roster_proof()["profile_count"], 500)
            self.assertFalse(plan_task(sample())["provider_called"])


class MCPTests(unittest.TestCase):
    def rpc(self, method, params=None, rid=1):
        return handle_rpc({"jsonrpc":"2.0", "id":rid, "method":method,
                           "params":params or {}})

    def test_initialize_legacy(self):
        self.assertEqual(self.rpc("initialize", {"protocolVersion":"2025-11-25"})
                         ["result"]["serverInfo"]["name"], "imperial-fusion-500-offline")

    def test_initialize_modern(self):
        self.assertEqual(self.rpc("initialize", {"protocolVersion":"2026-07-28"})
                         ["result"]["protocolVersion"], "2026-07-28")

    def test_tools_list(self):
        self.assertEqual(len(self.rpc("tools/list")["result"]["tools"]), 3)

    def test_status_tool(self):
        res = self.rpc("tools/call", {"name":"fusion500.status","arguments":{}})
        self.assertFalse(res["result"]["isError"])
        self.assertIn('"profile_count":500',res["result"]["content"][0]["text"])

    def test_plan_is_blocked_by_default(self):
        res = self.rpc("tools/call", {"name":"fusion500.plan","arguments":sample()})
        self.assertIn("BLOCKED_OWNER_KILL_SWITCH", res["result"]["content"][0]["text"])

    def test_no_arbitrary_tool_invocation(self):
        res = self.rpc("tools/call", {"name":"subprocess.exec","arguments":{}})
        self.assertTrue(res["result"]["isError"])

    def test_forged_tool_args_rejected(self):
        res = self.rpc("tools/call", {"name":"fusion500.status","arguments":{"execute":True}})
        self.assertTrue(res["result"]["isError"])

    def test_nonstandard_notification_ignored(self):
        self.assertIsNone(handle_rpc({"jsonrpc":"2.0", "method":"tools/call",
                                      "params":{"name":"fusion500.plan","arguments":sample()}}))

    def test_duplicate_json_keys_rejected(self):
        inp = io.BytesIO(b'{"jsonrpc":"2.0","id":1,"method":"tools/list","id":2}\n')
        out = io.StringIO()
        serve(inp, out)
        self.assertIn('"code":-32700', out.getvalue())

    def test_oversize_line_rejected(self):
        inp = io.BytesIO(b' ' * 65537 + b'\n')
        out = io.StringIO()
        serve(inp, out)
        self.assertIn("request exceeds bounded line limit", out.getvalue())

    def test_bool_rpc_id_rejected(self):
        res = handle_rpc({"jsonrpc":"2.0", "id":True, "method":"tools/list"})
        self.assertEqual(res["error"]["code"], -32600)

    def test_mcp_no_network(self):
        inp = io.BytesIO(b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n')
        out = io.StringIO()
        serve(inp, out)
        self.assertIn("fusion500.status", out.getvalue())


if __name__ == "__main__":
    unittest.main()
