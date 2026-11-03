"""Approval-gated sitemap submission reference.

This module requires an independent host-supplied approval verifier and Google
OAuth; it does not acquire access or grant authority. No automatic retries.
Founding Architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Callable
from urllib.parse import quote

from .indexing_mcp import ALLOWED_SITES
from .search_console_read import GoogleAccessError, SearchConsoleReadBridge, GOOGLE_SITES


@dataclass(frozen=True)
class SitemapIntent:
    site_id: str
    operation_id: str
    owner_proof_ref: str
    qa_proof_ref: str
    policy_version: str

    def canonical(self) -> bytes:
        return json.dumps(self.__dict__, sort_keys=True, separators=(",", ":")).encode()


class SubmissionGate:
    """Local fail-closed reference. Host must supply its own trusted verifier."""

    def __init__(self, database_path: str | Path, *,
                 approval_verifier: Callable[[bytes, str], bool] | None = None):
        self.database_path = str(database_path)
        self.approval_verifier = approval_verifier
        with sqlite3.connect(self.database_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS submissions(
                operation_id TEXT PRIMARY KEY,
                site_id TEXT NOT NULL,
                intent_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                provider_http_status INTEGER
            )""")

    def submit(self, intent: SitemapIntent, reader: SearchConsoleReadBridge,
               *, send: Callable[[str, str, str], int] | None = None) -> dict:
        if not isinstance(intent, SitemapIntent):
            raise GoogleAccessError("INVALID_INTENT")
        if intent.site_id not in ALLOWED_SITES:
            raise GoogleAccessError("UNREVIEWED_PROPERTY")
        for value in (intent.operation_id, intent.owner_proof_ref,
                      intent.qa_proof_ref, intent.policy_version):
            if not isinstance(value, str) or not 3 <= len(value) <= 128:
                raise GoogleAccessError("INCOMPLETE_APPROVAL_EVIDENCE")
        if (self.approval_verifier is None or
            self.approval_verifier(intent.canonical(), intent.owner_proof_ref) is not True):
            raise GoogleAccessError("OWNER_APPROVAL_NOT_VERIFIED")
        if not isinstance(reader, SearchConsoleReadBridge):
            raise GoogleAccessError("GOOGLE_READER_REQUIRED")
        info = reader.check_property(intent.site_id)
        if info["google_permission"] not in ("siteOwner", "siteFullUser"):
            raise GoogleAccessError("GOOGLE_WRITE_PERMISSION_NOT_VERIFIED")
        if send is None:
            raise GoogleAccessError("PRIVATE_WRITE_TRANSPORT_NOT_CONNECTED")
        site = ALLOWED_SITES[intent.site_id]
        endpoint = GOOGLE_SITES + "/" + quote(site["base"], safe="") + "/sitemaps/" + quote(site["sitemap"], safe="")
        digest = hashlib.sha256(intent.canonical()).hexdigest()
        with sqlite3.connect(self.database_path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT status FROM submissions WHERE operation_id=?",
                                  (intent.operation_id,)).fetchone()
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
