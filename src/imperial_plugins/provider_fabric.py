"""Original IMPERIAL Core provider request fabric.

Copyright (c) 2026 Alexander Nikolaevich Romaskevich (RomaskevicH).

Builds validated requests for five external capabilities. No foreign repository
is cloned, forked or vendored. This module never executes an HTTP request.
The privileged server worker must authenticate and authorize the request with
real Guardian Core, AI Passport and Approval Gateway before sending anything.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

_ALNUM = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_HOST = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?$")
_ALLOWED_ACTIONS = frozenset({
    "perplexity.research", "firecrawl.scrape", "posthog.capture",
    "playwright.e2e", "composio.discover"
})


class ProviderRequestDenied(ValueError):
    """Invalid scope, unsupported action, untrusted URL or unapproved effect."""


def _canonical(obj: dict) -> bytes:
    try:
        raw = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProviderRequestDenied("NON_JSON_PAYLOAD") from exc
    if len(raw) > 16384:
        raise ProviderRequestDenied("PAYLOAD_TOO_LARGE")
    return raw


def _public_url(value: object, allowed_hosts: frozenset[str]) -> str:
    if type(value) is not str or not 12 <= len(value) <= 2048:
        raise ProviderRequestDenied("URL_INVALID")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname or ""
        port = parsed.port
    except ValueError as exc:
        raise ProviderRequestDenied("URL_INVALID") from exc
    host = hostname.lower().rstrip(".")
    if (parsed.scheme != "https" or not host or not _HOST.fullmatch(host)
        or host not in allowed_hosts or parsed.username or parsed.password
        or port not in (None, 443) or parsed.fragment):
        raise ProviderRequestDenied("PUBLIC_URL_SCOPE_DENIED")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ProviderRequestDenied("IP_LITERAL_DENIED")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ProviderRequestDenied("INTERNAL_HOST_DENIED")
    return value


@dataclass(frozen=True)
class PreparedProviderRequest:
    action: str
    target: str
    method: str
    payload: bytes
    requires_external_authorization: bool
    requires_vendor_credentials: bool
    potentially_billable: bool
    source_sha256: str
    runtime_execution_authorized: bool = False

    def as_evidence(self) -> dict:
        """Only safe plan metadata; never return credentials or request bodies."""
        return {
            "action": self.action, "endpoint": self.target, "method": self.method,
            "payload_sha256": self.source_sha256,
            "external_effects": self.requires_external_authorization,
            "credentials_required": self.requires_vendor_credentials,
            "potentially_billable": self.potentially_billable,
            "runtime_execution_authorized": False,
            "independent_qa_verified": False,
        }


def _plan(action: str, target: str, payload: dict, *, billable: bool = True,
          credentials: bool = True, method: str = "POST") -> PreparedProviderRequest:
    raw = _canonical(payload)
    return PreparedProviderRequest(
        action=action, target=target, method=method, payload=raw,
        requires_external_authorization=True,
        requires_vendor_credentials=credentials,
        potentially_billable=billable,
        source_sha256=hashlib.sha256(raw).hexdigest(),
    )


def prepare_provider_action(action: str, arguments: dict,
                            *, approved_public_hosts: frozenset[str] = frozenset(),
                            posthog_region: str = "eu") -> PreparedProviderRequest:
    """Produce a bounded, inspectable request. Never sends data or invokes tools.

    approved_public_hosts must be configured by the server operator; there is
    no permissive default. The resulting payload is untrusted until a separate
    signed action permit authorizes the precise SHA-256, tenant and scope.
    """
    if (type(action) is not str or action not in _ALLOWED_ACTIONS
        or type(arguments) is not dict):
        raise ProviderRequestDenied("UNKNOWN_PROVIDER_ACTION")
    if action == "perplexity.research":
        if set(arguments) != {"question"}:
            raise ProviderRequestDenied("QUESTION_SCHEMA_DENIED")
        question = arguments["question"]
        if type(question) is not str or not 8 <= len(question) <= 3000:
            raise ProviderRequestDenied("QUESTION_BOUNDS_DENIED")
        return _plan(action, "https://api.perplexity.ai/chat/completions",
                     {"model": "sonar", "messages": [
                         {"role": "user", "content": question}
                     ]})
    if action == "firecrawl.scrape":
        if set(arguments) != {"url"} or type(approved_public_hosts) is not frozenset:
            raise ProviderRequestDenied("URL_SCHEMA_DENIED")
        allowed = frozenset(x.lower() for x in approved_public_hosts
                            if type(x) is str)
        url = _public_url(arguments["url"], allowed)
        return _plan(action, "https://api.firecrawl.dev/v2/scrape",
                     {"url": url, "formats": ["markdown"], "onlyMainContent": True})
    if action == "posthog.capture":
        if (set(arguments) != {"event", "distinct_id_sha256", "properties"}
            or posthog_region not in {"eu", "us"}):
            raise ProviderRequestDenied("ANALYTICS_SCHEMA_DENIED")
        event, identifier, props = (
            arguments["event"], arguments["distinct_id_sha256"],
            arguments["properties"])
        if (type(event) is not str or not _ALNUM.fullmatch(event)
            or type(identifier) is not str or not _SHA.fullmatch(identifier)
            or type(props) is not dict or len(props) > 10):
            raise ProviderRequestDenied("ANALYTICS_PII_OR_SCHEMA_DENIED")
        # Expose only approved, deliberately low-cardinality aggregate keys.
        allowed_fields = {"app_version", "surface", "result", "step", "experiment"}
        if (not set(props).issubset(allowed_fields)
            or any(type(v) is not str or not 1 <= len(v) <= 64
                   for v in props.values())):
            raise ProviderRequestDenied("ANALYTICS_PROPERTIES_DENIED")
        return _plan(action, f"https://{posthog_region}.i.posthog.com/i/v0/e/",
                     {"event": event, "distinct_id": identifier,
                      "properties": props}, billable=True)
    if action == "playwright.e2e":
        if arguments != {"suite": "constructor-browser-acceptance"}:
            raise ProviderRequestDenied("BROWSER_SUITE_NOT_APPROVED")
        # This is a bounded orchestration descriptor; actual Chromium runs
        # in CONSTRUCTOR-AI's owned flagship-browser.yml GitHub Actions job.
        return _plan(action, "CONSTRUCTOR-AI:e2e/browser-acceptance.mjs",
                     {"suite": "constructor-browser-acceptance",
                      "isolation": "ci-staging", "command": [
                          "node", "e2e/browser-acceptance.mjs"]},
                     credentials=False, billable=False, method="LOCAL")
    if action == "composio.discover":
        if set(arguments) != {"query"}:
            raise ProviderRequestDenied("MCP_SCHEMA_DENIED")
        query = arguments["query"]
        if type(query) is not str or not 8 <= len(query) <= 160:
            raise ProviderRequestDenied("MCP_QUERY_BOUNDS_DENIED")
        # MCP tool discovery only. NO tool execution or OAuth provisioning.
        return _plan(action, "https://connect.composio.dev/mcp",
                     {"jsonrpc": "2.0", "id": "search-1",
                      "method": "tools/call", "params": {
                          "name": "COMPOSIO_SEARCH_TOOLS",
                          "arguments": {"query": query}}},
                     billable=False)
    raise ProviderRequestDenied("UNKNOWN_PROVIDER_ACTION")
