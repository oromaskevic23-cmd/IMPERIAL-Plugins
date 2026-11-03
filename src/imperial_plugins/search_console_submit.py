"""Approval-gated sitemap submission reference.

This module requires an independent host-supplied approval verifier and Google
OAuth; it does not acquire access or grant authority. No automatic retries.
Founding Architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import time
from pathlib import Path
import sqlite3
from typing import Callable
import urllib.error
import urllib.request
from urllib.parse import quote

from .indexing_mcp import ALLOWED_SITES, audit_public_site, _NoRedirect
from .search_console_read import GoogleAccessError, SearchConsoleReadBridge, GOOGLE_SITES


@dataclass(frozen=True)
class SitemapIntent:
    site_id: str
    operation_id: str
    owner_proof_ref: str
    qa_proof_ref: str
    policy_version: str
    issued_at: int
    expires_at: int

    def canonical(self) -> bytes:
        return json.dumps(self.__dict__, sort_keys=True, separators=(",", ":")).encode()


def request_google_sitemap_put(method: str, endpoint: str, access_token: str) -> int:
    """Real Google transport, called only from a private host after all gates."""
    allowed = {
        GOOGLE_SITES + "/" + quote(site["base"], safe="") +
        "/sitemaps/" + quote(site["sitemap"], safe="")
        for site in ALLOWED_SITES.values()
    }
    if method != "PUT" or endpoint not in allowed:
        raise GoogleAccessError("GOOGLE_SUBMISSION_DESTINATION_DENIED")
    if not isinstance(access_token, str) or not access_token.strip() or len(access_token) > 8192:
        raise GoogleAccessError("GOOGLE_OAUTH_NOT_CONNECTED")
    req = urllib.request.Request(endpoint, method="PUT", headers={
        "Authorization": "Bearer " + access_token,
        "Accept": "application/json",
        "User-Agent": "IMPERIAL-Core-GSC-SubmissionGate/0.1",
    })
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(req, timeout=12) as response:
            if response.status not in (200, 204):
                raise GoogleAccessError("GOOGLE_SUBMISSION_UNCONFIRMED")
            if len(response.read(1025)) > 1024:
                raise GoogleAccessError("GOOGLE_RESPONSE_OVERSIZE")
            return response.status
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise GoogleAccessError("GOOGLE_WRITE_PERMISSION_DENIED") from None
        raise GoogleAccessError("GOOGLE_SUBMISSION_RESPONSE_ERROR") from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise GoogleAccessError("GOOGLE_SUBMISSION_TRANSPORT_FAILED") from None


class SubmissionGate:
    """Local fail-closed reference. Host must supply its own trusted verifier."""

    def __init__(self, database_path: str | Path, *,
                 approval_verifier: Callable[[bytes, str], bool] | None = None,
                 qa_verifier: Callable[[bytes, str], bool] | None = None,
                 site_auditor: Callable[[str], dict] = audit_public_site,
                 kill_switch: bool = True):
        self.database_path = str(database_path)
        self.approval_verifier = approval_verifier
        self.qa_verifier = qa_verifier
        self.kill_switch = kill_switch
        self.site_auditor = site_auditor
        with sqlite3.connect(self.database_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS submissions(
                operation_id TEXT PRIMARY KEY,
                site_id TEXT NOT NULL UNIQUE,
                intent_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                provider_http_status INTEGER
            )""")

    def submit(self, intent: SitemapIntent, reader: SearchConsoleReadBridge,
               *, send: Callable[[str, str, str], int] | None = None,
               now: int | None = None) -> dict:
        if self.kill_switch or os.environ.get("IMPERIAL_OWNER_KILL_SWITCH", "1") != "0":
            raise GoogleAccessError("OWNER_KILL_SWITCH")
        if not isinstance(intent, SitemapIntent):
            raise GoogleAccessError("INVALID_INTENT")
        if intent.site_id not in ALLOWED_SITES:
            raise GoogleAccessError("UNREVIEWED_PROPERTY")
        for value in (intent.operation_id, intent.owner_proof_ref,
                      intent.qa_proof_ref, intent.policy_version):
            if not isinstance(value, str) or not 3 <= len(value) <= 128:
                raise GoogleAccessError("INCOMPLETE_APPROVAL_EVIDENCE")
        clock = int(time.time()) if now is None else now
        if (type(intent.issued_at) is not int or type(intent.expires_at) is not int
            or type(clock) is not int or intent.issued_at > clock + 30
            or intent.expires_at <= clock
            or intent.expires_at - intent.issued_at > 600):
            raise GoogleAccessError("PERMIT_EXPIRED_OR_INVALID")
        if (self.approval_verifier is None or
            self.approval_verifier(intent.canonical(), intent.owner_proof_ref) is not True):
            raise GoogleAccessError("OWNER_APPROVAL_NOT_VERIFIED")
        if (self.qa_verifier is None or
            self.qa_verifier(intent.canonical(), intent.qa_proof_ref) is not True):
            raise GoogleAccessError("INDEPENDENT_QA_NOT_VERIFIED")
        if not isinstance(reader, SearchConsoleReadBridge):
            raise GoogleAccessError("GOOGLE_READER_REQUIRED")
        info = reader.check_property(intent.site_id)
        if info["google_permission"] not in ("siteOwner", "siteFullUser"):
            raise GoogleAccessError("GOOGLE_WRITE_PERMISSION_NOT_VERIFIED")
        if send is None:
            raise GoogleAccessError("PRIVATE_WRITE_TRANSPORT_NOT_CONNECTED")
        site_audit = self.site_auditor(intent.site_id)
        if (not isinstance(site_audit, dict) or site_audit.get("site_id") != intent.site_id
            or site_audit.get("public_http_audit") != "PASS"):
            raise GoogleAccessError("PUBLIC_SITEMAP_AUDIT_REQUIRED")
        site = ALLOWED_SITES[intent.site_id]
        endpoint = GOOGLE_SITES + "/" + quote(site["base"], safe="") + "/sitemaps/" + quote(site["sitemap"], safe="")
        digest = hashlib.sha256(intent.canonical()).hexdigest()
        with sqlite3.connect(self.database_path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT status FROM submissions WHERE operation_id=? OR site_id=?",
                                  (intent.operation_id, intent.site_id)).fetchone()
            if previous is not None:
                raise GoogleAccessError("REPLAY_OR_UNKNOWN_OUTCOME_REQUIRES_RECONCILIATION")
            db.execute("INSERT INTO submissions VALUES (?,?,?,?,NULL)",
                       (intent.operation_id, intent.site_id, digest, "PREPARED"))
            db.commit()
        try:
            status = send("PUT", endpoint, reader._token)
        except Exception:
            with sqlite3.connect(self.database_path) as db:
                db.execute("UPDATE submissions SET status='NEEDS_RECONCILIATION' WHERE operation_id=?",
                           (intent.operation_id,))
            raise GoogleAccessError("SUBMISSION_OUTCOME_UNKNOWN") from None
        if type(status) is not int or status not in (200, 204):
            with sqlite3.connect(self.database_path) as db:
                db.execute("UPDATE submissions SET status='NEEDS_RECONCILIATION' WHERE operation_id=?",
                           (intent.operation_id,))
            raise GoogleAccessError("GOOGLE_SUBMISSION_NOT_CONFIRMED")
        with sqlite3.connect(self.database_path) as db:
            db.execute("UPDATE submissions SET status='GOOGLE_SITEMAP_SUBMITTED', provider_http_status=? WHERE operation_id=?",
                       (status, intent.operation_id))
        return {
            "status": "GOOGLE_SITEMAP_SUBMITTED",
            "site_id": intent.site_id,
            "sitemap": site["sitemap"],
            "operation_id": intent.operation_id,
            "google_http_status": status,
            "google_indexed": "UNVERIFIED",
            "evidence": "PROVIDER_HTTP_RESPONSE_NOT_INDEXING",
        }
