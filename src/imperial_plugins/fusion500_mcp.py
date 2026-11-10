"""Offline read-only JSON-RPC MCP stdio adapter for IMPERIAL FUSION 500.

The interface exposes roster facts and simulation plans, no provider calls.
"""
from __future__ import annotations

import json
import sys
from typing import Any
from imperial_plugins.fusion500 import (
    FusionValidationError, list_profiles, plan_task, roster_proof,
)

MAX_RPC_BYTES = 65536
SUPPORTED = ("2025-11-25", "2026-07-28")
SERVER = {"name": "imperial-fusion-500-offline", "version": "0.1.0"}


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("duplicate JSON key")
        result[k] = v
    return result


TOOLS = [
    {"name": "fusion500.status", "description": "Deterministic roster invariants, NOT live-agent readiness",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "fusion500.list_profiles", "description": "Paginated synthetic profiles for one pillar",
     "inputSchema": {"type": "object", "properties": {
         "pillar": {"type": "string", "enum": ["figma", "lovable", "netlify", "context7"]},
         "offset": {"type": "integer", "minimum": 0, "maximum": 125},
         "limit": {"type": "integer", "minimum": 1, "maximum": 25},
     }, "required": ["pillar"], "additionalProperties": False}},
    {"name": "fusion500.plan", "description": "Offline HANTER/Orchestrator routing proposal; no execution",
     "inputSchema": {"type": "object", "properties": {
         "task_id": {"type": "string"}, "tenant_id": {"type": "string"},
         "orchestrator_id": {"type": "string"},
         "pillar": {"type": "string", "enum": ["figma", "lovable", "netlify", "context7"]},
         "workstream": {"type": "string"},
         "max_spend_usd": {"type": "integer", "const": 0},
         "requested_external_effect": {"type": "boolean"},
     }, "required": ["task_id", "tenant_id", "orchestrator_id", "pillar",
                    "workstream", "max_spend_usd", "requested_external_effect"],
     "additionalProperties": False}},
]


def _tool(name: str, args: Any) -> dict[str, Any]:
    if type(args) is not dict:
        raise FusionValidationError("tool args must be object")
    if name == "fusion500.status" and not args:
        return roster_proof()
    if name == "fusion500.list_profiles" and set(args).issubset({"pillar", "offset", "limit"}) and "pillar" in args:
        return list_profiles(**args)
    if name == "fusion500.plan":
        return plan_task(args)
    raise FusionValidationError("unknown tool or unsupported arguments")


def handle_rpc(req: Any) -> dict[str, Any] | None:
    if type(req) is not dict or req.get("jsonrpc") != "2.0":
        return _error(None, -32600, "invalid JSON-RPC request")
    if "id" not in req:
        # Notifications never trigger work, and produce no response.
        return None
    rid = req["id"]
    if type(rid) not in (str, int) or (type(rid) is str and len(rid) > 64):
        return _error(None, -32600, "invalid id")
    if set(req) - {"jsonrpc", "id", "method", "params", "_meta"}:
        return _error(rid, -32600, "unexpected request fields")
    method = req.get("method")
    params = req.get("params", {})
    if type(params) is not dict:
        return _error(rid, -32602, "invalid params")
    if method == "initialize":
        requested = params.get("protocolVersion", "2025-11-25")
        if requested not in SUPPORTED:
            return _error(rid, -32602, "unsupported protocol version")
        return _ok(rid, {"protocolVersion": requested, "capabilities": {"tools": {}},
                         "serverInfo": SERVER})
    if method == "ping" and not params:
        return _ok(rid, {})
    if method == "tools/list" and not params:
        return _ok(rid, {"tools": TOOLS})
    if method == "tools/call":
        if set(params) - {"name", "arguments"} or type(params.get("name")) is not str:
            return _error(rid, -32602, "invalid tool call")
        try:
            result = _tool(params["name"], params.get("arguments", {}))
        except (FusionValidationError, TypeError, ValueError) as exc:
            return _ok(rid, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        return _ok(rid, {"content": [{"type": "text", "text": json.dumps(result,
                         separators=(",", ":"), sort_keys=True)}], "isError": False})
    return _error(rid, -32601, "method not found")


def _ok(rid: str | int, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _error(rid: str | int | None, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def serve(stdin: Any = None, stdout: Any = None) -> None:
    inp = stdin or sys.stdin.buffer
    out = stdout or sys.stdout
    while True:
        line = inp.readline(MAX_RPC_BYTES + 2)
        if not line:
            break
        if len(line) > MAX_RPC_BYTES or not line.endswith(b"\n"):
            response = _error(None, -32700, "request exceeds bounded line limit")
            # Drain oversized line without interpreting any of its content.
            if not line.endswith(b"\n"):
                while True:
                    chunk = inp.readline(MAX_RPC_BYTES + 2)
                    if not chunk or chunk.endswith(b"\n"):
                        break
        else:
            try:
                data = json.loads(line, object_pairs_hook=_no_duplicate_keys,
                                  parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite number")))
                response = handle_rpc(data)
            except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
                response = _error(None, -32700, "invalid JSON")
        if response is not None:
            out.write(json.dumps(response, allow_nan=False, separators=(",", ":")) + "\n")
            out.flush()


if __name__ == "__main__":
    serve()
