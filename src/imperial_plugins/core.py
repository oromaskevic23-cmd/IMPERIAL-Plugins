"""Pure-Python, deny-by-default IMPERIAL plugin authorization reference.

No dynamic imports, subprocesses, network access or plugin execution.
HMAC represents a single trust domain, NOT the future asymmetric AI Passport PKI.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sqlite3
import time
from pathlib import Path

CAPABILITIES = frozenset({"read:public", "simulate:task", "route:internal"})
NAME_PATTERN = re.compile(r"^imperial\.[a-z][a-z0-9-]{2,63}$")
AGENT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
MAX_TOKEN_AGE = 3600
SKEW_SECONDS = 30


def canonical(value: dict) -> bytes:
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sign_claims(claims: dict, key: bytes, purpose: str) -> dict:
    """Issuer-side utility; privileged signing key must never reach plugins."""
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("signing key must be at least 32 bytes")
    if purpose not in {"passport", "approval"}:
        raise ValueError("unrecognized signing purpose")
    mac = hmac.new(key, purpose.encode() + b":" + canonical(claims),
                   hashlib.sha256).hexdigest()
    return {"claims": claims, "signature": mac}


def _verify_token(token: object, key: bytes, purpose: str) -> dict | None:
    if not isinstance(token, dict):
        return None
    claims, sig = token.get("claims"), token.get("signature")
    if not isinstance(claims, dict) or not isinstance(sig, str) or len(sig) != 64:
        return None
    try:
        expected = sign_claims(claims, key, purpose)["signature"]
        if hmac.compare_digest(sig, expected):
            return claims
    except (ValueError, TypeError, OverflowError):
        pass
    return None


def validate_manifest(manifest: object) -> dict:
    """Validate data only; a manifest never confers execution permission."""
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    if set(manifest) != {"id", "version", "capabilities", "description"}:
        raise ValueError("unexpected or missing manifest fields")
    name, version, caps, description = (
        manifest["id"], manifest["version"], manifest["capabilities"],
        manifest["description"]
    )
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        raise ValueError("invalid plugin id")
    if not isinstance(version, str) or not re.fullmatch(
        r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version
    ):
        raise ValueError("invalid semantic version")
    if (not isinstance(caps, list) or not caps or
        any(not isinstance(c, str) or c not in CAPABILITIES for c in caps) or
        len(caps) != len(set(caps))):
        raise ValueError("invalid capabilities")
    if not isinstance(description, str) or not (1 <= len(description) <= 300):
        raise ValueError("invalid description")
    return dict(manifest)


class GuardianCore:
    """Evaluate one request under a configured issuer and an owner-controlled gate.

    A disabled kill switch does not authorize anything by itself.
    """
    def __init__(self, passport_key: bytes, approval_key: bytes,
                 *, trusted_issuer: str = "IMPERIAL Core", kill_switch: bool = True):
        if len(passport_key) < 32 or len(approval_key) < 32:
            raise ValueError("separate keys >= 32 bytes required")
        if hmac.compare_digest(passport_key, approval_key):
            raise ValueError("passport and approval signing keys must differ")
        self.passport_key = passport_key
        self.approval_key = approval_key
        self.trusted_issuer = trusted_issuer
        self.kill_switch = kill_switch

    def evaluate(self, manifest: dict, request: dict, *, now: int | None = None) -> dict:
        def deny(reason: str) -> dict:
            return {"allowed": False, "reason": reason}
        # An explicit local test opt-out is the only accepted disabled value.
        # Unknown values must never silently turn a requested emergency stop off.
        switch_value = os.getenv("IMPERIAL_OWNER_KILL_SWITCH")
        if self.kill_switch or (switch_value is not None and switch_value != "0"):
            return deny("owner_kill_switch")
        try:
            checked = validate_manifest(manifest)
        except (TypeError, ValueError):
            return deny("manifest_invalid")
        if not isinstance(request, dict):
            return deny("request_invalid")
        action = request.get("action")
        task_id = request.get("task_id")
        if type(action) is not str or action not in CAPABILITIES or action not in checked["capabilities"]:
            return deny("capability_denied")
        if not isinstance(task_id, str) or not AGENT_PATTERN.fullmatch(task_id):
            return deny("task_invalid")
        now = int(time.time()) if now is None else int(now)
        claims = _verify_token(request.get("ai_passport"), self.passport_key, "passport")
        if not claims or set(claims) != {"agent_id", "issuer", "issued_at", "expires_at"}:
            return deny("passport_invalid")
        agent_id, issued, expiry = claims.get("agent_id"), claims.get("issued_at"), claims.get("expires_at")
        if (not isinstance(agent_id, str) or not AGENT_PATTERN.fullmatch(agent_id)
            or claims.get("issuer") != self.trusted_issuer
            or type(issued) is not int or type(expiry) is not int
            or issued > now + SKEW_SECONDS or expiry <= now
            or expiry - issued > MAX_TOKEN_AGE or expiry <= issued):
            return deny("passport_expired_or_untrusted")
        if request.get("agent_id") != agent_id:
            return deny("passport_agent_mismatch")
        if action != "read:public":
            approval = _verify_token(request.get("approval"), self.approval_key, "approval")
            if not approval or set(approval) != {
                "issuer", "agent_id", "task_id", "action", "expires_at"}:
                return deny("approval_required")
            if (approval.get("issuer") != "OWNER"
                or approval.get("agent_id") != agent_id
                or approval.get("task_id") != task_id
                or approval.get("action") != action
                or type(approval.get("expires_at")) is not int
                or not now < approval["expires_at"] <= now + MAX_TOKEN_AGE):
                return deny("approval_scope_or_expiry")
        return {"allowed": True, "reason": "policy_passed", "action": action}


class AuditLedger:
    """Local durable hash chain; not immutable against DB administrator compromise."""
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS events(
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                previous_hash TEXT NOT NULL,
                event_json TEXT NOT NULL,
                hash TEXT NOT NULL UNIQUE
            )""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    @staticmethod
    def _hash(previous: str, value: str) -> str:
        return hashlib.sha256((previous + value).encode("utf-8")).hexdigest()

    def append(self, event: dict) -> dict:
        payload = canonical(event).decode("utf-8")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            last = db.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
            previous = last[0] if last else "0" * 64
            digest = self._hash(previous, payload)
            row = db.execute("INSERT INTO events(previous_hash,event_json,hash) VALUES(?,?,?)",
                             (previous, payload, digest))
            db.commit()
            return {"seq": row.lastrowid, "previous_hash": previous, "hash": digest}

    def verify(self) -> bool:
        with self._connect() as db:
            rows = db.execute("SELECT seq,previous_hash,event_json,hash FROM events ORDER BY seq").fetchall()
        previous = "0" * 64
        for expected_seq, (seq, link, payload, digest) in enumerate(rows, 1):
            if (seq != expected_seq or link != previous
                or not hmac.compare_digest(self._hash(link, payload), digest)):
                return False
            previous = digest
        return True
