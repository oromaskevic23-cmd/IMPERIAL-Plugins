"""Google Search Console scoped read connector; OAuth is externally provisioned.

Founding Architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
Repository contributors and third-party code provenance remain in Git history.

A valid Google OAuth access token must be supplied by a separate trusted host.
This module cannot acquire tokens, submit a sitemap, write to Google, or
claim that a successful URL audit proves any Google index status.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from .indexing_mcp import ALLOWED_SITES

GOOGLE_SITES = "https://www.googleapis.com/webmasters/v3/sites"
GOOGLE_INSPECTION = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
MAX_GOOGLE_BODY = 300_000
KNOWN_GOOGLE_PERMISSIONS = frozenset({
    "siteOwner", "siteFullUser", "siteRestrictedUser",
})


class GoogleAccessError(ValueError):
    """Google authorization, protocol or verification boundary failure."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GoogleAccessError("GOOGLE_REDIRECT_REJECTED")


def request_google(method: str, url: str, access_token: str,
                   body: dict | None = None) -> tuple[int, bytes]:
    """Host-side transport; no arbitrary URLs, redirect following or token logging."""
    allowed = (url == GOOGLE_SITES or
               url.startswith(GOOGLE_SITES + "/") or
               url == GOOGLE_INSPECTION)
    if not allowed or method not in {"GET", "POST"}:
        raise GoogleAccessError("GOOGLE_DESTINATION_DENIED")
    if method == "POST" and url != GOOGLE_INSPECTION:
        raise GoogleAccessError("GOOGLE_MUTATION_DENIED")
    if method == "GET" and body is not None:
        raise GoogleAccessError("GOOGLE_REQUEST_INVALID")
    if not isinstance(access_token, str) or not access_token.strip() or len(access_token) > 8192:
        raise GoogleAccessError("OAUTH_TOKEN_MISSING")
    payload = (json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
               if body is not None else None)
    req = urllib.request.Request(url, data=payload, method=method, headers={
        "Authorization": "Bearer " + access_token,
        "Accept": "application/json",
        "User-Agent": "IMPERIAL-Core-GSC-ReadBridge/0.1",
        **({"Content-Type": "application/json"} if body is not None else {}),
    })
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(req, timeout=12) as response:
            if response.status != 200:
                raise GoogleAccessError("GOOGLE_NON_200")
            if int(response.headers.get("Content-Length", "0")) > MAX_GOOGLE_BODY:
                raise GoogleAccessError("GOOGLE_RESPONSE_OVERSIZE")
            data = response.read(MAX_GOOGLE_BODY + 1)
            if len(data) > MAX_GOOGLE_BODY:
                raise GoogleAccessError("GOOGLE_RESPONSE_OVERSIZE")
            return response.status, data
    except urllib.error.HTTPError as exc:
        # Never print Google response bodies: they can contain private account data.
        if exc.code in (401, 403):
            raise GoogleAccessError("GOOGLE_AUTH_OR_PROPERTY_PERMISSION_DENIED") from None
        raise GoogleAccessError("GOOGLE_API_HTTP_ERROR_" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        if isinstance(exc, GoogleAccessError):
            raise
        raise GoogleAccessError("GOOGLE_TRANSPORT_FAILURE") from None


class SearchConsoleReadBridge:
    """Read an owner's actual Google API status for exactly two reviewed properties.

    Never called automatically by an MCP tool; the trusted operator must
    explicitly provide their own OAuth bearer token and ask for this operation.
    All results are constrained to two known public properties; no other
    property information is returned, even if the token has broader scope.
    """

    def __init__(self, *, access_token: str | None = None,
                 transport: Callable[[str, str, str, dict | None],
                                     tuple[int, bytes]] = request_google) -> None:
        self._token = access_token
        self._transport = transport

    def _read(self, method: str, url: str,
              body: dict | None = None) -> dict[str, Any]:
        if not isinstance(self._token, str) or not self._token.strip():
            raise GoogleAccessError("GOOGLE_OAUTH_NOT_CONNECTED")
        status, raw = self._transport(method, url, self._token, body)
        if status != 200 or not isinstance(raw, bytes) or len(raw) > MAX_GOOGLE_BODY:
            raise GoogleAccessError("GOOGLE_RESPONSE_REJECTED")
        try:
            obj = json.loads(raw)
        except (UnicodeDecodeError, ValueError, TypeError):
            raise GoogleAccessError("GOOGLE_BAD_JSON") from None
        if not isinstance(obj, dict):
            raise GoogleAccessError("GOOGLE_JSON_OBJECT_REQUIRED")
        return obj

    def check_property(self, site_id: str) -> dict[str, Any]:
        if not isinstance(site_id, str) or site_id not in ALLOWED_SITES:
            raise GoogleAccessError("SITE_NOT_ALLOWLISTED")
        entry = self._property_entry(site_id)
        return {
            "property": ALLOWED_SITES[site_id]["base"],
            "google_permission": entry["permissionLevel"],
            "status": "GOOGLE_API_PROPERTY_ACCESS_VERIFIED",
            "google_indexed": "UNVERIFIED",
        }

    def _property_entry(self, site_id: str) -> dict:
        if site_id not in ALLOWED_SITES:
            raise GoogleAccessError("SITE_NOT_ALLOWLISTED")
        response = self._read("GET", GOOGLE_SITES)
        entries = response.get("siteEntry", [])
        if not isinstance(entries, list) or len(entries) > 500:
            raise GoogleAccessError("GOOGLE_PROPERTY_RESPONSE_INVALID")
        target = ALLOWED_SITES[site_id]["base"]
        exact = [x for x in entries if isinstance(x, dict) and x.get("siteUrl") == target
                 and x.get("permissionLevel") in KNOWN_GOOGLE_PERMISSIONS]
        if len(exact) != 1:
            raise GoogleAccessError("GOOGLE_PROPERTY_ACCESS_NOT_VERIFIED")
        return exact[0]

    def list_submitted_sitemaps(self, site_id: str) -> dict[str, Any]:
        self._property_entry(site_id)
        site = ALLOWED_SITES[site_id]
        suffix = urllib.parse.quote(site["base"], safe="")
        result = self._read("GET", GOOGLE_SITES + "/" + suffix + "/sitemaps")
        entries = result.get("sitemap", [])
        if not isinstance(entries, list):
            raise GoogleAccessError("GOOGLE_SITEMAP_RESPONSE_INVALID")
        own = [x for x in entries if isinstance(x, dict) and
               x.get("path") == site["sitemap"]]
        return {
            "site_id": site_id,
            "site": site["base"],
            "expected_sitemap": site["sitemap"],
            "found_in_google_account": bool(own),
            "google_sitemap_entries": [{
                "path": x.get("path"), "isPending": x.get("isPending"),
                "isSitemapsIndex": x.get("isSitemapsIndex"),
                "lastSubmitted": x.get("lastSubmitted"),
                "lastDownloaded": x.get("lastDownloaded"),
                "warnings": x.get("warnings"), "errors": x.get("errors"),
            } for x in own],
            "url_indexed": "UNVERIFIED",
            "evidence": "GOOGLE_SEARCH_CONSOLE_API_RESPONSE",
        }

    def inspect_canonical(self, site_id: str, page: str) -> dict[str, Any]:
        if site_id not in ALLOWED_SITES:
            raise GoogleAccessError("SITE_NOT_ALLOWLISTED")
        site = ALLOWED_SITES[site_id]
        if not isinstance(page, str) or page not in (site["base"], site["catalog"]):
            raise GoogleAccessError("URL_NOT_ALLOWLISTED")
        self._property_entry(site_id)
        result = self._read("POST", GOOGLE_INSPECTION, {
            "inspectionUrl": page,
            "siteUrl": site["base"],
            "languageCode": "en-US",
        })
        inspection = result.get("inspectionResult")
        if not isinstance(inspection, dict):
            raise GoogleAccessError("GOOGLE_INSPECTION_RESULT_MISSING")
        indexed = inspection.get("indexStatusResult")
        if not isinstance(indexed, dict):
            raise GoogleAccessError("GOOGLE_INDEX_STATUS_UNAVAILABLE")
        return {
            "site_id": site_id,
            "inspection_url": page,
            "evidence": "GOOGLE_URL_INSPECTION_API_RESULT",
            "index_verdict": indexed.get("verdict", "UNSPECIFIED"),
            "coverage_state": indexed.get("coverageState"),
            "indexing_state": indexed.get("indexingState"),
            "last_crawl_time": indexed.get("lastCrawlTime"),
            "google_canonical": indexed.get("googleCanonical"),
            "user_canonical": indexed.get("userCanonical"),
            "note": "API-reported index state only; not a live-page indexability test.",
        }


def sitemap_submission_preflight(site_id: str) -> dict[str, str]:
    """Provide the exact reviewed Google API intent. Never execute it."""
    if site_id not in ALLOWED_SITES:
        raise GoogleAccessError("SITE_NOT_ALLOWLISTED")
    site = ALLOWED_SITES[site_id]
    endpoint = (
        GOOGLE_SITES + "/" + urllib.parse.quote(site["base"], safe="") +
        "/sitemaps/" + urllib.parse.quote(site["sitemap"], safe="")
    )
    return {
        "site_id": site_id,
        "method": "PUT",
        "endpoint": endpoint,
        "oauth_scope_required": "https://www.googleapis.com/auth/webmasters",
        "request_body": "NONE",
        "status": "INTENT_ONLY_OWNER_APPROVAL_REQUIRED",
        "google_submitted": "UNVERIFIED",
        "google_indexed": "UNVERIFIED",
    }
