"""MOJON MCP compatibility, isolation, and commercial fail-closed tests."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from imperial_plugins.mojon_mcp import (
    MOJONMCPServer, MODERN, LEGACY, VERSION_META, CAPS_META, TOOLS,
    list_skills, plan_skill, simulate_discount, validate_skill, status,
    _object_pairs_no_duplicates
)

ROOT = Path(__file__).resolve().parents[1]


def message(method, *, ident=1, modern=True, params=None):
    data = dict(params or {})
    if modern:
        data["_meta"] = {
            VERSION_META: MODERN,
            CAPS_META: {},
            "io.modelcontextprotocol/clientInfo": {
                "name": "test-client", "version": "0.1.0"
            }
        }
    return {"jsonrpc": "2.0", "id": ident, "method": method, "params": data}


def tool(name, arguments=None, *, modern=True):
    return message("tools/call", modern=modern, params={
        "name": name, "arguments": arguments if arguments is not None else {}
    })


def tool_data(response):
    result = response["result"]
    if result["isError"]:
        return None
    return json.loads(result["content"][0]["text"])


class SkillContract(unittest.TestCase):
    def test_skills_are_isolated_from_real_execution(self):
        entries = list_skills()
        self.assertEqual(entries["count"], 3)
        self.assertFalse(entries["production_authorized"])
        self.assertFalse(entries["source_revision_cryptographically_pinned"])
        self.assertEqual(len({s["skill_id"] for s in entries["skills"]}), 3)
        self.assertTrue(all(not s["execution_authorized"] for s in entries["skills"]))

    def test_plan_existing_review_is_only_a_plan(self):
        result = plan_skill(
            tenant_id="imperial-internal", skill_id="imperial.skill.security-review",
            orchestrator_id="security-orch", runtime_domain="SECURITY_DEFENSIVE",
            capability="simulate:task"
        )
        self.assertTrue(result["planned"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["owner_ed25519_verified"])
        self.assertFalse(result["dispatch_performed"])

    def test_wrong_tenant_and_orchestrator_denied(self):
        for change in (
            {"tenant_id": "business-workspace"},
            {"orchestrator_id": "engineering-orch"},
            {"runtime_domain": "CODE_ENGINEERING"},
            {"capability": "route:internal"}
        ):
            with self.subTest(change=change):
                values = dict(
                    tenant_id="imperial-internal", skill_id="imperial.skill.security-review",
                    orchestrator_id="security-orch", runtime_domain="SECURITY_DEFENSIVE",
                    capability="simulate:task"
                )
                values.update(change)
                self.assertFalse(plan_skill(**values)["planned"])

    def test_validate_closed_skill_schema(self):
        descriptor = {
            "skill_id": "imperial.skill.review-plan", "version": "0.1.0",
            "tenant_id": "imperial-internal", "orchestrator_id": "security-orch",
            "runtime_domain": "SECURITY_DEFENSIVE", "capability": "simulate:task",
            "risk_tier": "GUARDED", "description": "Original local review Skill planning.",
            "requires_independent_qa": True, "requires_owner_approval": True,
            "external_effects": False, "spend_usd": 0,
        }
        ok = validate_skill(descriptor)
        self.assertTrue(ok["schema_valid"])
        self.assertEqual(len(ok["descriptor_sha256"]), 64)
        self.assertFalse(ok["owner_approved"])
        self.assertFalse(ok["signature_verified"])
        bad = copy.deepcopy(descriptor)
        bad["external_effects"] = True
        with self.assertRaisesRegex(ValueError, "SKILL_SAFETY_DENIED"):
            validate_skill(bad)

    def test_status_never_overclaims_installed_cloud_mcp(self):
        s = status()
        self.assertEqual(s["name"], "MOJON")
        self.assertFalse(s["hosted_mcp_deployed"])
        self.assertFalse(s["guardian_connected"])
        self.assertFalse(s["ai_passport_runtime_verified"])
        self.assertFalse(s["execution_authorized"])


class CommercialDiscount(unittest.TestCase):
    def test_integer_cent_round_half_up(self):
        p = simulate_discount(
            list_price_cents=1, requested_discount_bps=5000,
            unverified_policy_limit_bps=5000
        )
        self.assertEqual(p["simulated_discount_cents"], 1)
        self.assertEqual(p["simulated_total_cents"], 0)
        self.assertFalse(p["real_quote_issued"])
        self.assertFalse(p["payment_authorized"])

    def test_discount_boundary(self):
        p = simulate_discount(
            list_price_cents=500000000, requested_discount_bps=2000,
            unverified_policy_limit_bps=1500
        )
        self.assertEqual(p["status"], "LIMIT_EXCEEDED")
        self.assertIsNone(p["simulated_discount_cents"])
        self.assertIsNone(p["simulated_total_cents"])

    def test_no_unverified_policy_can_issue_quote(self):
        p = simulate_discount(
            list_price_cents=20000, requested_discount_bps=0,
            unverified_policy_limit_bps=10000
        )
        self.assertFalse(p["owner_discount_policy_verified"])
        self.assertFalse(p["real_quote_issued"])
        self.assertFalse(p["external_effects"])

    def test_boolean_and_invalid_bps_denied(self):
        for values in (
            {"list_price_cents": True, "requested_discount_bps": 50,
             "unverified_policy_limit_bps": 100},
            {"list_price_cents": 100, "requested_discount_bps": -1,
             "unverified_policy_limit_bps": 100},
            {"list_price_cents": 100, "requested_discount_bps": 10001,
             "unverified_policy_limit_bps": 10000},
            {"list_price_cents": 100, "requested_discount_bps": 100,
             "unverified_policy_limit_bps": 10101},
        ):
            with self.subTest(values=values):
                with self.assertRaisesRegex(ValueError, "INVALID_DISCOUNT_INPUT"):
                    simulate_discount(**values)


class MCPProtocol(unittest.TestCase):
    def test_all_tools_are_read_only(self):
        self.assertEqual(len(TOOLS), 5)
        self.assertTrue(all(t["annotations"]["readOnlyHint"] for t in TOOLS))
        self.assertTrue(all(t["inputSchema"]["additionalProperties"] is False for t in TOOLS))

    def test_modern_server_discover(self):
        result = MOJONMCPServer().dispatch(message("server/discover"))
        self.assertEqual(result["result"]["resultType"], "complete")
        self.assertIn(MODERN, result["result"]["supportedVersions"])
        self.assertIn(LEGACY, result["result"]["supportedVersions"])

    def test_modern_tools_list_and_call(self):
        server = MOJONMCPServer()
        result = server.dispatch(message("tools/list"))
        self.assertEqual(len(result["result"]["tools"]), 5)
        result = server.dispatch(tool("mojon.status"))
        self.assertFalse(result["result"]["isError"])
        self.assertEqual(tool_data(result)["name"], "MOJON")
        self.assertEqual(
            result["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"],
            "imperial-mojon-mcp"
        )

    def test_legacy_protocol_no_auto_handshake(self):
        server = MOJONMCPServer()
        self.assertEqual(server.dispatch(message("tools/list", modern=False))["error"]["code"],
                         -32602)
        accepted = server.dispatch(message("initialize", modern=False, params={
            "protocolVersion": LEGACY, "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"}
        }))
        self.assertEqual(accepted["result"]["protocolVersion"], LEGACY)
        result = server.dispatch(tool("mojon.list_skills", modern=False))
        self.assertEqual(tool_data(result)["count"], 3)
        self.assertNotIn("resultType", result["result"])

    def test_modern_protocol_requires_caps(self):
        item = message("tools/list")
        del item["params"]["_meta"][CAPS_META]
        self.assertEqual(MOJONMCPServer().dispatch(item)["error"]["code"], -32602)

    def test_unsupported_protocol_denied(self):
        item = message("tools/list")
        item["params"]["_meta"][VERSION_META] = "2099-01-01"
        self.assertEqual(MOJONMCPServer().dispatch(item)["error"]["code"], -32022)

    def test_unknown_tool_or_params_denied(self):
        server = MOJONMCPServer()
        err = server.dispatch(tool("mojon.execute_root"))
        self.assertEqual(err["error"]["code"], -32602)
        response = server.dispatch(tool("mojon.plan_skill", {"secret_key": "value"}))
        self.assertTrue(response["result"]["isError"])
        self.assertNotIn("secret_key", response["result"]["content"][0]["text"])

    def test_tool_call_never_grants_real_approval(self):
        args = {
            "tenant_id": "imperial-internal", "skill_id": "imperial.skill.code-review",
            "orchestrator_id": "engineering-orch", "runtime_domain": "CODE_ENGINEERING",
            "capability": "simulate:task"
        }
        item = tool_data(MOJONMCPServer().dispatch(tool("mojon.plan_skill", args)))
        self.assertTrue(item["planned"])
        self.assertFalse(item["execution_authorized"])

    def test_tool_notification_ignored(self):
        item = tool("mojon.simulate_discount", {
            "list_price_cents": 100, "requested_discount_bps": 100,
            "unverified_policy_limit_bps": 100
        })
        del item["id"]
        self.assertIsNone(MOJONMCPServer().dispatch(item))

    def test_bad_rpc_and_id_denied(self):
        server = MOJONMCPServer()
        self.assertEqual(server.dispatch([])["error"]["code"], -32600)
        m = message("ping")
        m["id"] = True
        self.assertEqual(server.dispatch(m)["error"]["code"], -32600)
        m = message("tools/list")
        m["params"] = []
        self.assertEqual(server.dispatch(m)["error"]["code"], -32602)

    def test_duplicate_json_key_prohibited(self):
        with self.assertRaises(ValueError):
            json.loads('{"jsonrpc":"2.0","jsonrpc":"9"}',
                       object_pairs_hook=_object_pairs_no_duplicates)

    def test_stdio_roundtrip_and_sanitized_error(self):
        init = message("server/discover", ident=1)
        listing = message("tools/list", ident=2)
        allowed = tool("mojon.status")
        allowed["id"] = 3
        request = "\n".join(json.dumps(v) for v in (init, listing, allowed)) + "\n"
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools/mojon_mcp.py")],
            cwd=ROOT, env=env, input=request, text=True,
            capture_output=True, timeout=10, check=True
        )
        self.assertEqual(proc.stderr, "")
        responses = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual([r["id"] for r in responses], [1, 2, 3])
        self.assertFalse(responses[-1]["result"]["isError"])

    def test_stdio_rejects_oversized_line(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        very_long = '{"jsonrpc":"2.0","id":1,"method":"tools/list","x":"' + "a"*70000 + '"}\n'
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools/mojon_mcp.py")],
            cwd=ROOT, env=env, input=very_long, text=True,
            capture_output=True, timeout=10, check=True
        )
        responses = [json.loads(s) for s in proc.stdout.splitlines()]
        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0]["error"]["message"], "Oversize request")


if __name__ == "__main__":
    unittest.main()
