"""Effective, host-root robots.txt audit for GitHub Pages project-path sites.

A /project/robots.txt is not the effective crawler policy. Googlebot checks
https://host/robots.txt, with behavior depending on the HTTP response.
This reports public crawl-policy evidence, never Google indexing.
"""
from __future__ import annotations

import argparse
import json
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import urllib.error
import urllib.request

from .indexing_mcp import ALLOWED_SITES

HOST_ROBOTS = "https://oromaskevic23-cmd.github.io/robots.txt"
MAX_BYTES = 512_000


class RobotsAuditError(ValueError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RobotsAuditError("HOST_ROBOTS_REDIRECT_UNREVIEWED")


def fetch_root_robots():
    """Returns status plus bytes; no other URL may be fetched."""
    opener = urllib.request.build_opener(_NoRedirect())
    request = urllib.request.Request(HOST_ROBOTS, headers={
        "User-Agent": "IMPERIAL-Core-Effective-Robots-Check/1.0",
        "Accept": "text/plain",
    })
    try:
        with opener.open(request, timeout=12) as response:
            if response.status != 200:
                raise RobotsAuditError("HOST_ROBOTS_HTTP_UNEXPECTED")
            if int(response.headers.get("Content-Length", "0")) > MAX_BYTES:
                raise RobotsAuditError("HOST_ROBOTS_RESPONSE_TOO_LARGE")
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise RobotsAuditError("HOST_ROBOTS_RESPONSE_TOO_LARGE")
            return 200, data
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return 404, b""
        raise RobotsAuditError("HOST_ROBOTS_UNVERIFIABLE_HTTP_" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError):
        raise RobotsAuditError("HOST_ROBOTS_NETWORK_UNVERIFIABLE") from None


def audit_effective_robots(status: int, raw: bytes) -> dict:
    """Offline check with injected root-host HTTP evidence."""
    if type(status) is not int or not isinstance(raw, bytes):
        raise RobotsAuditError("HOST_ROBOTS_BAD_EVIDENCE")
    if status == 404:
        policy = "NO_HOST_ROOT_ROBOTS_HTTP_404"
        allowed = True
    elif status == 200:
        if len(raw) > MAX_BYTES:
            raise RobotsAuditError("HOST_ROBOTS_RESPONSE_TOO_LARGE")
        try:
            body = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise RobotsAuditError("HOST_ROBOTS_NOT_UTF8") from None
        parser = RobotFileParser()
        parser.parse(body.splitlines())
        allowed = all(
            parser.can_fetch("Googlebot", site["base"]) and
            parser.can_fetch("*", site["catalog"])
            for site in ALLOWED_SITES.values()
        )
        policy = "HOST_ROOT_ROBOTS_PARSED"
    else:
        raise RobotsAuditError("HOST_ROOT_ROBOTS_HTTP_UNVERIFIABLE")
    if not allowed:
        raise RobotsAuditError("HOST_ROOT_ROBOTS_DENIES_IMPERIAL_PUBLIC_PAGE")
    return {
        "status": "PASS_EFFECTIVE_HOST_ROBOTS",
        "effective_robots_url": HOST_ROBOTS,
        "http_status": status,
        "policy": policy,
        "sites_checked": sorted(ALLOWED_SITES),
        "project_path_robots_are_effective": False,
        "notes": "Conservative Python robots parser; not Googlebot or URL Inspection proof.",
        "google_indexed": "UNVERIFIED",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", required=True, action="store_true")
    p.parse_args()
    result = audit_effective_robots(*fetch_root_robots())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RobotsAuditError as exc:
        print("HOST_ROBOTS_AUDIT_FAILED:", str(exc))
        raise SystemExit(1)
