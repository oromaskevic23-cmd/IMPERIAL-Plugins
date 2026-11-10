"""MOJON: local, read-only MCP bridge for existing IMPERIAL Enterprise Skills.

Founder / final architecture: Alexander Nikolaevich Romaskevich (RomaskevicH).
These public, data-only descriptions mirror selected published IMPERIAL-Skill
examples; they are NOT a signed live registry or a production authority source.
No network requests, shell execution, dynamic plugin imports or payments.
"""
from __future__ import annotations

import hashlib
import json
import sys
from typing import Any

from .core import canonical
from .enterprise_skills import EnterpriseSkillsRegistry, validate_enterprise_skill

MODERN = "2026-07-28"
LEGACY = "2025-11-25"
VERSION_META = "io.modelcontextprotocol/protocolVersion"
CAPS_META = "io.modelcontextprotocol/clientCapabilities"
SERVER_META = "io.modelcontextprotocol/serverInfo"
SERVER_INFO = {"name": "imperial-mojon-mcp", "version": "0.1.0"}
MAX_RPC_BYTES = 65536
MAX_RESULT_BYTES = 65536
SOURCE_REPO = "https://github.com/oromaskevic23-cmd/IMPERIAL-Skill"

# Reviewed, data-only compatibility projections of existing IMPERIAL-Skill examples.
# Never dynamically download or auto-install Skills from untrusted input.
SKILL_SOURCES = (
    ("imperial.skill.code-review", "imperial-internal", "engineering-orch",
     "CODE_ENGINEERING", "Read-only engineering review proposal for independent examination."),
    ("imperial.skill.security-review", "imperial-internal", "security-orch",
     "SECURITY_DEFENSIVE", "Defensive offline software risk assessment without exploitation."),
    ("imperial.skill.data-quality", "business-workspace", "analytics-orch",
     "DATA_ANALYSIS", "Offline data-quality analysis for owner-approved synthetic records."),
)


def _registry() -> EnterpriseSkillsRegistry:
    registry = EnterpriseSkillsRegistry()
    for skill_id, tenant, orchestrator, domain, description in SKILL_SOURCES:
        registry.register({
            "skill_id": skill_id, "version": "0.1.0",
            "tenant_id": tenant, "orchestrator_id": orchestrator,
            "runtime_domain": domain, "capability": "simulate:task",
            "risk_tier": "GUARDED", "description": description,
            "requires_independent_qa": True, "requires_owner_approval": True,
            "external_effects": False, "spend_usd": 0,
        })
    return registry


NO_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}
VALIDATE_ARGS = {"type": "object", "properties": {
    "descriptor": {"type": "object"}}, "required": ["descriptor"],
    "additionalProperties": False}
PLAN_PROPS = {
    key: {"type": "string"} for key in (
        "tenant_id", "skill_id", "orchestrator_id", "runtime_domain", "capability"
    )
}
PLAN_ARGS = {"type": "object", "properties": PLAN_PROPS,
             "required": list(PLAN_PROPS), "additionalProperties": False}
DISCOUNT_PROPS = {
    "list_price_cents": {"type": "integer", "minimum": 0, "maximum": 1000000000},
    "requested_discount_bps": {"type": "integer", "minimum": 0, "maximum": 10000},
    "unverified_policy_limit_bps": {"type": "integer", "minimum": 0, "maximum": 10000},
}
DISCOUNT_ARGS = {"type": "object", "properties": DISCOUNT_PROPS,
                 "required": list(DISCOUNT_PROPS), "additionalProperties": False}

TOOLS = [
    {"name": "mojon.status", "title": "MOJON capability and authority status",
     "description": "Describe local Skills/MCP source state; never claims installed production access.",
     "inputSchema": NO_ARGS, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "mojon.list_skills", "title": "Reviewed Enterprise Skills",
     "description": "List three public, data-only existing IMPERIAL-Skill compatibility descriptions.",
     "inputSchema": NO_ARGS, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "mojon.validate_skill", "title": "Validate a data-only Enterprise Skill",
     "description": "Strict schema validation and SHA-256; no signature or authority verification.",
     "inputSchema": VALIDATE_ARGS, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "mojon.plan_skill", "title": "Plan a federated Skill boundary",
     "description": "Check tenant/orchestrator/runtime/capability against the local registry; no dispatch.",
     "inputSchema": PLAN_ARGS, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "mojon.simulate_discount", "title": "Commercial discount arithmetic simulator",
     "description": "Calculate a hypothetical discount from unverified limits; cannot authorize a price or sale.",
     "inputSchema": DISCOUNT_ARGS, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
]
EXACT_ARGUMENTS = {
    "mojon.status": frozenset(),
    "mojon.list_skills": frozenset(),
    "mojon.validate_skill": frozenset({"descriptor"}),
    "mojon.plan_skill": frozenset(PLAN_PROPS),
    "mojon.simulate_discount": frozenset(DISCOUNT_PROPS),
}


def simulate_discount(*, list_price_cents: object,
                      requested_discount_bps: object,
                      unverified_policy_limit_bps: object) -> dict:
    """Integer-cent rounding (half up). Proposal only, never a real price quote."""
    for value, cap in (
        (list_price_cents, 1000000000),
        (requested_discount_bps, 10000),
        (unverified_policy_limit_bps, 10000),
    ):
        if type(value) is not int or not 0 <= value <= cap:
            raise ValueError("INVALID_DISCOUNT_INPUT")
    permitted = requested_discount_bps <= unverified_policy_limit_bps
    # The supplied limit is NOT an authenticated Owner approval or real policy.
    reduction = (list_price_cents * requested_discount_bps + 5000) // 10000
    return {
        "schema": "imperial.mojon.discount-simulation.v1",
        "status": "UNVERIFIED_LIMIT_REVIEW_REQUIRED" if permitted else "LIMIT_EXCEEDED",
        "list_price_cents": list_price_cents,
        "requested_discount_bps": requested_discount_bps,
        "simulated_discount_cents": reduction if permitted else None,
        "simulated_total_cents": list_price_cents - reduction if permitted else None,
        "owner_discount_policy_verified": False,
        "real_quote_issued": False,
        "payment_authorized": False,
        "external_effects": False,
        "spend_usd": 0,
    }


def status() -> dict:
    return {
        "name": "MOJON", "version": "0.1.0",
        "scope": "LOCAL_READ_ONLY_SKILL_MCP",
        "supported_protocols": [MODERN, LEGACY],
        "skill_source_reference": SOURCE_REPO,
        "source_revision_cryptographically_pinned": False,
        "skills_registered": len(SKILL_SOURCES),
        "owner_ed25519_enrolled": False,
        "ai_passport_runtime_verified": False,
        "guardian_connected": False,
        "approval_gateway_connected": False,
        "independent_qa_verified": False,
        "execution_authorized": False,
        "hosted_mcp_deployed": False,
        "commercial_discount_policy_verified": False,
        "spend_usd": 0,
    }


def list_skills() -> dict:
    entries = _registry().snapshot()
    return {
        "schema": "imperial.mojon.skills-snapshot.v1",
        "source": SOURCE_REPO,
        "source_revision_cryptographically_pinned": False,
        "count": len(entries),
        "skills": [{
            "skill_id": v["skill_id"], "version": v["version"],
            "tenant_id": v["tenant_id"], "orchestrator_id": v["orchestrator_id"],
            "runtime_domain": v["runtime_domain"],
            "descriptor_sha256": hashlib.sha256(canonical(v)).hexdigest(),
            "execution_authorized": False, "source_copy_only": True,
        } for v in entries],
        "production_authorized": False,
    }


def validate_skill(descriptor: object) -> dict:
    item = validate_enterprise_skill(descriptor)
    return {
        "schema": "imperial.mojon.skill-validation.v1",
        "schema_valid": True,
        "descriptor_sha256": hashlib.sha256(canonical(item)).hexdigest(),
        "signature_verified": False,
        "owner_approved": False,
        "independent_qa_verified": False,
        "execution_authorized": False,
    }


def plan_skill(*, tenant_id: str, skill_id: str, orchestrator_id: str,
               runtime_domain: str, capability: str) -> dict:
    outcome = _registry().plan(tenant_id=tenant_id, skill_id=skill_id,
                               orchestrator_id=orchestrator_id,
                               runtime_domain=runtime_domain, capability=capability)
    return {
        **outcome, "schema": "imperial.mojon.skill-plan.v1",
        "owner_ed25519_verified": False, "independent_qa_verified": False,
        "execution_authorized": False, "dispatch_performed": False,
    }


EXECUTORS = {
    "mojon.status": status,
    "mojon.list_skills": list_skills,
    "mojon.validate_skill": validate_skill,
    "mojon.plan_skill": plan_skill,
    "mojon.simulate_discount": simulate_discount,
}


class MOJONMCPServer:
    """Dual-protocol JSON-RPC stdio; no network/socket/listener or external action."""

    def __init__(self) -> None:
        self.legacy_initialized = False

    @staticmethod
    def error(ident: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": ident,
                "error": {"code": code, "message": message}}

    @staticmethod
    def result(ident: Any, payload: dict, modern: bool) -> dict:
        if modern:
            payload = {**payload, "resultType": "complete",
                       "_meta": {SERVER_META: SERVER_INFO}}
        return {"jsonrpc": "2.0", "id": ident, "result": payload}

    def dispatch(self, message: object) -> dict | None:
        if type(message) is not dict or message.get("jsonrpc") != "2.0":
            return self.error(None, -32600, "Invalid JSON-RPC request")
        method = message.get("method")
        if type(method) is not str or not method:
            return self.error(message.get("id"), -32600, "Invalid method")
        if "id" not in message:
            # Notifications, including forged tool calls, must never be executed.
            return None
        ident = message["id"]
        if type(ident) not in (int, str) or (type(ident) is str and len(ident) > 80):
            return self.error(None, -32600, "Invalid request ID")
        params = message.get("params", {})
        if type(params) is not dict:
            return self.error(ident, -32602, "Invalid params")
        if method == "initialize":
            if params.get("protocolVersion") != LEGACY:
                return self.error(ident, -32602, "Unsupported legacy initialization")
            self.legacy_initialized = True
            return self.result(ident, {
                "protocolVersion": LEGACY, "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            }, False)
        meta = params.get("_meta")
        modern = type(meta) is dict and VERSION_META in meta
        if modern:
            if meta.get(VERSION_META) != MODERN:
                return self.error(ident, -32022, "Unsupported protocol version")
            if type(meta.get(CAPS_META)) is not dict:
                return self.error(ident, -32602, "Missing client capabilities")
            client = meta.get("io.modelcontextprotocol/clientInfo")
            if client is not None and type(client) is not dict:
                return self.error(ident, -32602, "Invalid client info")
        elif not self.legacy_initialized:
            return self.error(ident, -32602, "MCP protocol metadata or legacy init required")

        if method == "server/discover":
            if not modern:
                return self.error(ident, -32601, "Legacy discover unsupported")
            return self.result(ident, {
                "supportedVersions": [MODERN, LEGACY],
                "capabilities": {"tools": {"listChanged": False}},
                "instructions": "MOJON local Skills inspection only; no execution authority.",
                "ttlMs": 0, "cacheScope": "public",
            }, True)
        if method == "ping":
            return self.result(ident, {}, modern)
        if method == "tools/list":
            if set(params) - {"_meta"}:
                return self.error(ident, -32602, "Invalid list arguments")
            out = {"tools": TOOLS}
            if modern:
                out.update({"ttlMs": 0, "cacheScope": "public"})
            return self.result(ident, out, modern)
        if method == "tools/call":
            if set(params) - {"_meta", "name", "arguments"}:
                return self.error(ident, -32602, "Invalid tool parameters")
            name, args = params.get("name"), params.get("arguments", {})
            if type(name) is not str or name not in EXECUTORS:
                return self.error(ident, -32602, "Unknown tool")
            if type(args) is not dict or set(args) != EXACT_ARGUMENTS[name]:
                return self.result(ident, {
                    "content": [{"type": "text", "text": "Tool arguments denied"}],
                    "isError": True,
                }, modern)
            try:
                value = EXECUTORS[name](**args)
                encoded = json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)
                if len(encoded.encode("utf-8")) > MAX_RESULT_BYTES:
                    raise ValueError("RESULT_TOO_LARGE")
                return self.result(ident, {
                    "content": [{"type": "text", "text": encoded}], "isError": False,
                }, modern)
            except (TypeError, ValueError, KeyError):
                return self.result(ident, {
                    "content": [{"type": "text", "text": "Validation denied"}],
                    "isError": True,
                }, modern)
            except Exception:
                return self.result(ident, {
                    "content": [{"type": "text", "text": "Internal failure; request denied"}],
                    "isError": True,
                }, modern)
        return self.error(ident, -32601, "Method not found")


def _object_pairs_no_duplicates(pairs: list[tuple]) -> dict:
    obj: dict = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON key")
        obj[key] = value
    return obj


def main() -> None:
    server = MOJONMCPServer()
    stdin, stdout = sys.stdin.buffer, sys.stdout
    while True:
        raw = stdin.readline(MAX_RPC_BYTES + 1)
        if not raw:
            break
        if len(raw) > MAX_RPC_BYTES:
            # Consume a single oversized input line, do not misread it as tools/call.
            while raw and not raw.endswith(b"\n"):
                raw = stdin.readline(MAX_RPC_BYTES + 1)
            response = server.error(None, -32600, "Oversize request")
        else:
            try:
                message = json.loads(raw, object_pairs_hook=_object_pairs_no_duplicates,
                                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                response = server.dispatch(message)
            except (ValueError, UnicodeDecodeError, TypeError):
                response = server.error(None, -32700, "Invalid JSON")
        if response is not None:
            stdout.write(json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n")
            stdout.flush()


if __name__ == "__main__":
    main()
