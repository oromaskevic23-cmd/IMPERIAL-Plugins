"""IMPERIAL Search Indexing MCP — scoped public-web verification tools.

Founding architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
Implementation contributors: recorded in Git history. Third-party rights respected.

Implements JSON-RPC 2.0 MCP stdio; legacy 2025-11-25 and modern
2026-07-28. Read-only, source-evidence-first. No Google account access,
Search Console submission, indexing claim, private repository retrieval,
API credential handling, live worker dispatch or crawler spoofing.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

MCP_LEGACY = "2025-11-25"
MCP_MODERN = "2026-07-28"
VERSIONS = (MCP_MODERN, MCP_LEGACY)
VERSION_META = "io.modelcontextprotocol/protocolVersion"
CAPABILITIES_META = "io.modelcontextprotocol/clientCapabilities"
SERVER_INFO_META = "io.modelcontextprotocol/serverInfo"
SERVER_INFO = {"name": "imperial-search-indexing-mcp", "version": "0.1.0"}
MANIFEST = Path(__file__).resolve().parents[2] / "data" / "search-indexing-public.json"
MAX_BYTES = 1_200_000
MAX_RPC_BYTES = 131_072


class AuditError(ValueError):
    """Public site check was rejected or failed; never convert to Google PASS."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AuditError("HTTP redirect is not permitted for allowlisted checks")


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.scripts: list[str] = []
        self._script = False
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "link":
            self.links.append({k: v or "" for k, v in a.items()})
        if tag == "script" and a.get("type") == "application/ld+json":
            self._script = True
            self._text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script:
            self.scripts.append("".join(self._text))
            self._script = False

    def handle_data(self, data: str) -> None:
        if self._script:
            self._text.append(data)


def read_manifest() -> dict[str, Any]:
    result = json.loads(MANIFEST.read_text(encoding="utf-8"))
    projects = result.get("projects", [])
    if len(projects) != 23 or len({p["url"] for p in projects}) != 23:
        raise AuditError("invalid or drifted public project snapshot")
    for project in projects:
        if not project["url"].startswith("https://github.com/oromaskevic23-cmd/"):
            raise AuditError("unexpected external repository in public manifest")
    return result


def _public_get(url: str) -> bytes:
    """Fetch only server-selected URLs; redirects and oversized bodies fail closed."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "IMPERIAL-Core-IndexingMCP/0.1 (public site verification)",
        "Accept": "text/html,application/xml,text/xml,text/plain",
    })
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(req, timeout=12) as response:
            if response.status != 200:
                raise AuditError("public endpoint did not return HTTP 200")
            if response.headers.get("Content-Length") and int(
                response.headers["Content-Length"]
            ) > MAX_BYTES:
                raise AuditError("public endpoint exceeds bounded response limit")
            data = response.read(MAX_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise AuditError("public endpoint unavailable or unsafe") from exc
    if len(data) > MAX_BYTES:
        raise AuditError("public endpoint exceeds bounded response limit")
    return data


def _site(manifest: dict[str, Any], site_id: str) -> dict[str, str]:
    if site_id not in ("founder", "company"):
        raise AuditError("site_id must be founder or company")
    return manifest["sites"][site_id]


def _canonical_and_items(html: bytes, catalog: str, expected: list[str]) -> dict[str, Any]:
    try:
        parser = _PageParser()
        parser.feed(html.decode("utf-8"))
        canonical = [x.get("href") for x in parser.links if x.get("rel") == "canonical"]
        if canonical != [catalog]:
            raise AuditError("catalog self-canonical missing or inconsistent")
        itemlists: list[dict[str, Any]] = []
        for raw in parser.scripts:
            data = json.loads(raw)
            nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
            itemlists.extend(n for n in nodes if isinstance(n, dict) and
                             n.get("@type") == "ItemList")
        if len(itemlists) != 1:
            raise AuditError("catalog ItemList metadata missing or ambiguous")
        entries = itemlists[0].get("itemListElement", [])
        listed = [v.get("url") for v in entries]
        if (len(listed) != len(expected) or set(listed) != set(expected) or
            len(set(listed)) != len(listed) or
            itemlists[0].get("numberOfItems") != len(expected)):
            raise AuditError("published structured project catalog drifted")
        return {"canonical_valid": True, "public_projects": len(listed),
                "structured_data_matches_manifest": True}
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, AttributeError) as exc:
        raise AuditError("invalid public catalog HTML or structured data") from exc


def _sitemap(data: bytes, base: str, catalog: str) -> dict[str, Any]:
    if b"<!DOCTYPE" in data.upper():
        raise AuditError("DOCTYPE in XML rejected")
    try:
        root = ET.fromstring(data)
        namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        urls = [(v.text or "").strip() for v in root.findall(
            namespace + "url/" + namespace + "loc"
        )]
    except ET.ParseError as exc:
        raise AuditError("invalid sitemap XML") from exc
    if not urls or len(urls) != len(set(urls)):
        raise AuditError("missing or duplicate sitemap URLs")
    if catalog not in urls or base not in urls:
        raise AuditError("canonical landing page or project catalog missing from sitemap")
    if any(not u.startswith(base) for u in urls):
        raise AuditError("sitemap has URL outside this site's canonical path")
    return {"sitemap_url_count": len(urls), "unique_canonical_urls": True,
            "catalog_in_sitemap": True}


def audit_public_site(site_id: str, *,
                      getter: Callable[[str], bytes] = _public_get) -> dict[str, Any]:
    """Real public HTTP checks, no Google Search Console or Googlebot claims."""
    m = read_manifest()
    site = _site(m, site_id)
    expected = [p["url"] for p in m["projects"]]
    # No client-provided URL reaches the network; only manifest URLs are fetched.
    urls = [site["base"], site["catalog"], site["sitemap"], site["robots"]]
    if len(set(urls)) != 4 or any(
        not u.startswith(site["base"]) for u in urls
    ):
        raise AuditError("unsafe or duplicate allowlisted URL")
    responses = {url: getter(url) for url in urls}
    robots = responses[site["robots"]].decode("utf-8").lower()
    if "disallow: /" in robots or (
        "sitemap: " + site["sitemap"].lower()
    ) not in robots:
        raise AuditError("robots.txt denies crawling or sitemap is not declared")
    checks = _sitemap(responses[site["sitemap"]], site["base"], site["catalog"])
    checks.update(_canonical_and_items(responses[site["catalog"]],
                                       site["catalog"], expected))
    return {
        "site_id": site_id,
        "public_http_audit": "PASS",
        "urls_checked": urls,
        "checks": checks,
        "google_search_console_verified": "UNVERIFIED",
        "google_indexed": "UNVERIFIED",
        "note": "HTTP and source metadata evidence only, not actual Google indexing.",
    }


def status() -> dict[str, Any]:
    m = read_manifest()
    return {
        "project_count": len(m["projects"]),
        "excluded_private_count": m["excluded_private_count"],
        "catalog_evidence": m["source_evidence"],
        "google": m["google_status"],
        "public_sites": sorted(m["sites"]),
        "scope": "source snapshot; not live Google Search Console or search ranking",
    }


def list_public_projects() -> dict[str, Any]:
    m = read_manifest()
    return {
        "status": "PUBLIC_GITHUB_SNAPSHOT",
        "as_of": m["updated"],
        "projects": m["projects"],
        "count": len(m["projects"]),
        "google_indexed": "UNVERIFIED",
    }


def search_console_plan() -> dict[str, Any]:
    m = read_manifest()
    return {
        "action": "HUMAN_AUTHORIZED_SEARCH_CONSOLE_SUBMISSION_REQUIRED",
        "properties": [
            {"site_id": k, "url_prefix_property": v["base"],
             "sitemap": v["sitemap"], "catalog_url": v["catalog"]}
            for k, v in sorted(m["sites"].items())
        ],
        "submission_status": "NOT_VERIFIED",
        "ownership_status": "NOT_VERIFIED",
        "indexing_status": "NOT_VERIFIED",
        "notes": [
            "Verify URL-prefix properties in the intended Google account.",
            "Submit each sitemap via Search Console after verification.",
            "Review Google's URL Inspection and Pages report independently.",
            "Generic project pages are not eligible for the restricted Google Indexing API.",
        ],
    }


NO_ARGUMENTS = {"type": "object", "properties": {}, "additionalProperties": False}
SITE_ARGUMENT = {
    "type": "object",
    "properties": {"site_id": {"type": "string", "enum": ["founder", "company"]}},
    "required": ["site_id"],
    "additionalProperties": False,
}
TOOLS = [
    {"name": "imperial.indexing_status",
     "title": "Public indexing evidence",
     "description": "Read the verified source snapshot and explicitly unverified Google indexing status.",
     "inputSchema": NO_ARGUMENTS, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "imperial.list_public_projects",
     "title": "Public project registry",
     "description": "Return the 23 verified public project repositories and evidence limits; never private ones.",
     "inputSchema": NO_ARGUMENTS, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "imperial.audit_published_site",
     "title": "Verify published public site",
     "description": "Check HTTP, sitemap, robots, canonical and JSON-LD for founder or company public site. No Google indexing claim.",
     "inputSchema": SITE_ARGUMENT, "annotations": {"readOnlyHint": True, "openWorldHint": True}},
    {"name": "imperial.search_console_plan",
     "title": "Google Search Console plan",
     "description": "Get URL-prefix property and sitemap submission instructions; cannot submit without authorization.",
     "inputSchema": NO_ARGUMENTS, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
]
EXECUTORS: dict[str, Callable[..., dict[str, Any]]] = {
    "imperial.indexing_status": status,
    "imperial.list_public_projects": list_public_projects,
    "imperial.audit_published_site": audit_public_site,
    "imperial.search_console_plan": search_console_plan,
}


class IndexingMCPServer:
    def __init__(self) -> None:
        self.legacy_initialized = False

    @staticmethod
    def _error(id_value: Any, code: int, message: str,
               data: dict[str, Any] | None = None) -> dict[str, Any]:
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": id_value, "error": error}

    @staticmethod
    def _result(id_value: Any, payload: dict[str, Any], modern: bool) -> dict[str, Any]:
        if modern:
            payload = dict(payload, resultType="complete", _meta={
                SERVER_INFO_META: SERVER_INFO
            })
        return {"jsonrpc": "2.0", "id": id_value, "result": payload}

    def dispatch(self, message: Any) -> dict[str, Any] | None:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return self._error(None, -32600, "Invalid JSON-RPC request")
        method = message.get("method")
        if not isinstance(method, str):
            return self._error(message.get("id"), -32600, "Invalid method")
        if "id" not in message:
            # All notifications are one-way. No tools may be executed by a notification.
            return None
        ident = message["id"]
        if isinstance(ident, bool) or not (ident is None or isinstance(ident, (str, int))):
            return self._error(None, -32600, "Invalid JSON-RPC id")
        params = message.get("params", {})
        if not isinstance(params, dict):
            return self._error(ident, -32602, "Invalid params")
        if method == "initialize":
            version = params.get("protocolVersion", MCP_LEGACY)
            if version != MCP_LEGACY:
                version = MCP_LEGACY
            self.legacy_initialized = True
            return self._result(ident, {"protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO}, False)
        meta = params.get("_meta")
        modern = isinstance(meta, dict) and VERSION_META in meta
        if modern:
            version = meta.get(VERSION_META)
            if version != MCP_MODERN:
                return self._error(ident, -32022, "Unsupported protocol version",
                                   {"requested": version, "supported": list(VERSIONS)})
            if not isinstance(meta.get(CAPABILITIES_META), dict):
                return self._error(ident, -32602, "Missing client capabilities")
            info = meta.get("io.modelcontextprotocol/clientInfo")
            if info is not None and not isinstance(info, dict):
                return self._error(ident, -32602, "Invalid client info")
        elif not self.legacy_initialized:
            return self._error(ident, -32602, "Initialize legacy MCP or supply modern request _meta")
        if method == "server/discover":
            if not modern:
                return self._error(ident, -32601, "Method not supported in legacy MCP")
            return self._result(ident, {
                "supportedVersions": list(VERSIONS),
                "capabilities": {"tools": {"listChanged": False}},
                "instructions": "Public source-indexing audit only; no Google Search Console authorization or submission.",
                "ttlMs": 0, "cacheScope": "public",
            }, True)
        if method == "ping":
            return self._result(ident, {}, modern)
        if method == "tools/list":
            if params.get("cursor"):
                return self._error(ident, -32602, "Invalid cursor")
            result: dict[str, Any] = {"tools": TOOLS}
            if modern:
                result.update({"ttlMs": 0, "cacheScope": "public"})
            return self._result(ident, result, modern)
        if method == "tools/call":
            name = params.get("name")
            fn = EXECUTORS.get(name) if isinstance(name, str) else None
            if fn is None:
                return self._error(ident, -32602, "Unknown tool")
            args = params.get("arguments", {})
            if not isinstance(args, dict):
                return self._error(ident, -32602, "Tool arguments must be an object")
            expected = {"site_id"} if name == "imperial.audit_published_site" else set()
            if set(args) != expected:
                return self._result(ident, {"content": [{"type": "text",
                    "text": "Tool argument mismatch: unexpected or missing fields"}],
                    "isError": True}, modern)
            try:
                outcome = fn(**args)
                return self._result(ident, {"content": [{
                    "type": "text", "text": json.dumps(outcome, ensure_ascii=False,
                                                       sort_keys=True)}],
                    "isError": False}, modern)
            except (AuditError, ValueError, KeyError, TypeError) as exc:
                return self._result(ident, {"content": [{
                    "type": "text", "text": "Public verification failed: " + str(exc)}],
                    "isError": True}, modern)
            except Exception:
                return self._result(ident, {"content": [{
                    "type": "text", "text": "Public verification failed: internal error"}],
                    "isError": True}, modern)
        return self._error(ident, -32601, "Method not found")


def main() -> None:
    server = IndexingMCPServer()
    # stdout must carry only JSON-RPC frames; never print incidental logs here.
    for line in sys.stdin.buffer:
        if len(line) > MAX_RPC_BYTES:
            response = IndexingMCPServer._error(None, -32600, "Oversize request")
        else:
            try:
                request = json.loads(line)
                response = server.dispatch(request)
            except (ValueError, UnicodeDecodeError):
                response = IndexingMCPServer._error(None, -32700, "Parse error")
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":"),
                                        ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
