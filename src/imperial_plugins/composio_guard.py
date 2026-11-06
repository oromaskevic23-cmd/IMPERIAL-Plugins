"""Governed, bounded Composio read-only transport boundary.

Original IMPERIAL Core integration by Alexander Nikolaevich Romaskevich (RomaskevicH).
No Composio SDK, credentials, OAuth, network, or production Owner keys are bundled.
Only a trusted host may supply independently verified Passport and Owner permit
callbacks and a tool-specific read-only Composio SDK transport.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Callable

from .core import AuditLedger, canonical

SCHEMA = "imperial.composio.read.v1"
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,99}$")
TOOL = re.compile(r"^[A-Z][A-Z0-9_]{3,127}$")
TOOLKIT = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
HASH = re.compile(r"^[a-f0-9]{64}$")
MAX_REQUEST_BYTES = 8192
MAX_RESULT_BYTES = 32768
MAX_LEASE_SECONDS = 300
PRIVATE_KEYS = frozenset({
    "password", "passphrase", "api_key", "apikey", "token", "access_token",
    "refresh_token", "authorization", "cookie", "secret", "private_key",
    "credentials", "headers", "client_secret",
})
META_EXECUTION = frozenset({
    "COMPOSIO_MULTI_EXECUTE_TOOL", "COMPOSIO_MANAGE_CONNECTIONS",
    "COMPOSIO_SEARCH_TOOLS", "COMPOSIO_GET_TOOL_SCHEMAS",
})


class ComposioDenied(ValueError):
    """Denial includes only a static code; no user data or provider response."""


def _json_bytes(value: object, limit: int) -> bytes:
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ComposioDenied("INVALID_JSON") from exc
    if len(raw) > limit:
        raise ComposioDenied("RESOURCE_LIMIT")
    return raw


def _contains_secret_fields(value: object, depth: int = 0) -> bool:
    if depth > 6:
        return True
    if isinstance(value, dict):
        return any(
            not isinstance(k, str) or k.lower() in PRIVATE_KEYS
            or _contains_secret_fields(v, depth + 1)
            for k, v in value.items()
        )
    if isinstance(value, list):
        return any(_contains_secret_fields(v, depth + 1) for v in value)
    return False


class GovernedComposioRead:
    """Synchronous, replay-resistant read-only adapter; NEVER a signed permit issuer.

    verifier(envelope_hash, untrusted_token) must return authenticated claims or
    None. Host is responsible for actual cryptographic verification, tenant
    authentication, session/toolkit enforcement, egress, and transport timeouts.
    The default kill switch is ON, and there is no default provider tool.
    """

    def __init__(
        self, *, db_path: str | Path, allowlist: dict[str, str],
        verify_passport: Callable, verify_owner_permit: Callable,
        read_tool: Callable, kill_switch: Callable = lambda: True,
        clock: Callable = time.time,
    ):
        if (type(allowlist) is not dict or not allowlist
            or any(type(t) is not str or TOOL.fullmatch(t) is None
                   or t in META_EXECUTION
                   or type(k) is not str or TOOLKIT.fullmatch(k) is None
                   for t, k in allowlist.items())):
            raise ComposioDenied("REVIEWED_READ_ALLOWLIST_REQUIRED")
        if not all(callable(x) for x in (
            verify_passport, verify_owner_permit, read_tool, kill_switch, clock
        )):
            raise ComposioDenied("TRUSTED_HOST_CALLBACK_REQUIRED")
        self.allowlist = dict(allowlist)
        self.verify_passport = verify_passport
        self.verify_owner_permit = verify_owner_permit
        self.read_tool = read_tool
        self.kill_switch = kill_switch
        self.clock = clock
        self.db_path = str(db_path)
        self.audit = AuditLedger(self.db_path)
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS composio_requests(
                tenant_id TEXT NOT NULL,
                request_id TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, request_id)
            )""")

    def _check_claims(self, claims: object, expected: dict, now: int) -> None:
        if not isinstance(claims, dict):
            raise ComposioDenied("INDEPENDENT_AUTH_REQUIRED")
        if any(claims.get(key) != val for key, val in expected.items()):
            raise ComposioDenied("PERMIT_SCOPE_DENIED")
        expiry = claims.get("expires_at")
        if type(expiry) is not int or not now < expiry <= now + MAX_LEASE_SECONDS:
            raise ComposioDenied("PERMIT_EXPIRED")
        if claims.get("capability") != "read:public":
            raise ComposioDenied("CAPABILITY_DENIED")

    def _reserve(self, tenant: str, request_id: str, digest: str, now: int) -> None:
        # BEGIN IMMEDIATE and PRIMARY KEY give durable, cross-process anti-replay.
        with sqlite3.connect(self.db_path, timeout=10, isolation_level=None) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    "INSERT INTO composio_requests VALUES (?,?,?,?,?)",
                    (tenant, request_id, digest, "RESERVED", now)
                )
            except sqlite3.IntegrityError as exc:
                db.rollback()
                raise ComposioDenied("REQUEST_REPLAY_DENIED") from exc
            db.commit()

    def _finish(self, tenant: str, request_id: str, status: str) -> None:
        with sqlite3.connect(self.db_path, timeout=10) as db:
            db.execute(
                "UPDATE composio_requests SET status=? "
                "WHERE tenant_id=? AND request_id=? AND status='RESERVED'",
                (status, tenant, request_id)
            )

    def execute(self, envelope: object) -> dict:
        if self.kill_switch():
            raise ComposioDenied("OWNER_KILL_SWITCH")
        if not isinstance(envelope, dict) or set(envelope) != {
            "schema", "tenant_id", "orchestrator_id", "agent_id", "task_id",
            "request_id", "tool_slug", "toolkit", "arguments",
            "passport_token", "owner_permit_token",
        }:
            raise ComposioDenied("REQUEST_SCHEMA_DENIED")
        if envelope["schema"] != SCHEMA:
            raise ComposioDenied("REQUEST_SCHEMA_DENIED")
        for field in ("tenant_id", "orchestrator_id", "agent_id", "task_id", "request_id"):
            value = envelope[field]
            if type(value) is not str or IDENT.fullmatch(value) is None:
                raise ComposioDenied("IDENTITY_INVALID")
        tool_slug = envelope["tool_slug"]
        toolkit = envelope["toolkit"]
        if (type(tool_slug) is not str or tool_slug not in self.allowlist
            or toolkit != self.allowlist[tool_slug]):
            raise ComposioDenied("UNREVIEWED_TOOL_DENIED")
        args = envelope["arguments"]
        if type(args) is not dict or _contains_secret_fields(args):
            raise ComposioDenied("PRIVATE_BOUNDARY_DENIED")
        body = {
            k: v for k, v in envelope.items()
            if k not in ("passport_token", "owner_permit_token")
        }
        raw = _json_bytes(body, MAX_REQUEST_BYTES)
        digest = hashlib.sha256(raw).hexdigest()
        now = int(self.clock())
        shared = {key: body[key] for key in (
            "tenant_id", "orchestrator_id", "agent_id", "task_id"
        )}
        try:
            passport = self.verify_passport(digest, envelope["passport_token"])
            self._check_claims(passport, shared, now)
            permit = self.verify_owner_permit(digest, envelope["owner_permit_token"])
            self._check_claims(permit, {
                **shared, "request_hash": digest, "request_id": body["request_id"],
                "tool_slug": tool_slug, "toolkit": toolkit,
            }, now)
        except ComposioDenied:
            raise
        except Exception as exc:
            raise ComposioDenied("AUTH_VERIFIER_UNAVAILABLE") from exc

        if self.kill_switch():
            raise ComposioDenied("OWNER_KILL_SWITCH")
        self._reserve(body["tenant_id"], body["request_id"], digest, now)
        try:
            # The injected transport is responsible for hosting, OAuth and
            # proving this exact reviewed slug is read-only for PUBLIC data.
            if self.kill_switch():
                raise ComposioDenied("OWNER_KILL_SWITCH")
            result = self.read_tool(tool_slug, args)
            result_raw = _json_bytes(result, MAX_RESULT_BYTES)
            if self.kill_switch():
                raise ComposioDenied("OWNER_KILL_SWITCH")
            result_hash = hashlib.sha256(result_raw).hexdigest()
            evidence = {
                "schema": "imperial.composio.read-receipt.v1",
                **shared,
                "request_id": body["request_id"],
                "tool_slug": tool_slug,
                "toolkit": toolkit,
                "request_sha256": digest,
                "result_sha256": result_hash,
                "status": "READ_ONLY_TRANSPORT_EXECUTED",
                "external_writes_authorized": False,
                "production_certified": False,
            }
            receipt = self.audit.append(evidence)
            self._finish(body["tenant_id"], body["request_id"], "COMPLETED")
            return {
                "status": "READ_ONLY_TRANSPORT_EXECUTED",
                "result": result,
                "evidence": evidence,
                "audit_seq": receipt["seq"],
                "audit_sha256": receipt["hash"],
            }
        except Exception as exc:
            self._finish(body["tenant_id"], body["request_id"], "FAILED_CLOSED")
            if isinstance(exc, ComposioDenied):
                raise
            raise ComposioDenied("TRANSPORT_FAILED_CLOSED") from exc

    def audit_valid(self) -> bool:
        return self.audit.verify()
