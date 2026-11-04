"""Canonical public GitHub inventory drift checker — no write operations.

Founder and final architectural authority: Alexander Nikolaevich Romaskevich.
This lists only publicly visible repositories, never private identifiers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

from .indexing_mcp import read_manifest

OWNER = "oromaskevic23-cmd"
API_ROOT = f"https://api.github.com/users/{OWNER}/repos"
EXTRA_PUBLIC = frozenset({
    "oromaskevic23-cmd",
    "IMPERIAL-Core-US-HoldCo-Founder-Control-Blueprint",
})
MAX_PAGE_BYTES = 500_000


class InventoryDriftError(ValueError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise InventoryDriftError("PUBLIC_INVENTORY_REDIRECT_DENIED")


def fetch_public_repositories() -> list[dict]:
    """Read the public user endpoint only; abort on failed/paginated fetch."""
    opener = urllib.request.build_opener(_NoRedirect())
    results: list[dict] = []
    for page in range(1, 6):
        url = API_ROOT + f"?type=owner&per_page=100&page={page}"
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "IMPERIAL-Core-Public-Inventory-Guard/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        try:
            with opener.open(request, timeout=15) as response:
                if response.status != 200:
                    raise InventoryDriftError("GITHUB_PUBLIC_API_NOT_200")
                if int(response.headers.get("Content-Length", "0")) > MAX_PAGE_BYTES:
                    raise InventoryDriftError("GITHUB_PUBLIC_RESPONSE_OVERSIZE")
                raw = response.read(MAX_PAGE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise InventoryDriftError("GITHUB_PUBLIC_API_HTTP_" + str(exc.code)) from None
        except (TimeoutError, urllib.error.URLError):
            raise InventoryDriftError("GITHUB_PUBLIC_API_UNAVAILABLE") from None
        if len(raw) > MAX_PAGE_BYTES:
            raise InventoryDriftError("GITHUB_PUBLIC_RESPONSE_OVERSIZE")
        try:
            data = json.loads(raw)
        except (UnicodeDecodeError, ValueError):
            raise InventoryDriftError("GITHUB_PUBLIC_API_INVALID_JSON") from None
        if not isinstance(data, list) or len(data) > 100:
            raise InventoryDriftError("GITHUB_PUBLIC_API_INVALID_COLLECTION")
        results.extend(data)
        if len(data) < 100:
            return results
    raise InventoryDriftError("GITHUB_PUBLIC_INVENTORY_PAGINATION_EXCEEDED")


def validate_public_repositories(repositories: list[dict]) -> dict:
    """Compare live public names against a dated approved 23-project registry."""
    if not isinstance(repositories, list):
        raise InventoryDriftError("GITHUB_PUBLIC_INVENTORY_INVALID")
    names: list[str] = []
    for entry in repositories:
        if not isinstance(entry, dict):
            raise InventoryDriftError("GITHUB_PUBLIC_INVENTORY_INVALID")
        # Never process, persist or display private repository names.
        if entry.get("private") is True or entry.get("visibility") == "private":
            continue
        owner = entry.get("owner", {})
        if not isinstance(owner, dict) or owner.get("login") != OWNER:
            raise InventoryDriftError("FOREIGN_REPOSITORY_DENIED")
        name = entry.get("name")
        if not isinstance(name, str) or not name or "/" in name:
            raise InventoryDriftError("GITHUB_PUBLIC_REPOSITORY_NAME_INVALID")
        names.append(name)
    if len(set(names)) != len(names):
        raise InventoryDriftError("GITHUB_PUBLIC_DUPLICATE_REPOSITORY")
    manifest = read_manifest()
    expected_projects = {p["name"] for p in manifest["projects"]}
    expected_public = expected_projects | EXTRA_PUBLIC
    current_public = set(names)
    if current_public != expected_public:
        # Return only counts to logs; do not silently expose newly made projects.
        raise InventoryDriftError(
            "PUBLIC_REPOSITORY_REGISTRY_DRIFT: "
            f"expected={len(expected_public)},current={len(current_public)},"
            f"missing={len(expected_public-current_public)},"
            f"new={len(current_public-expected_public)}"
        )
    if len(expected_projects) != 23 or len(expected_public) != 25:
        raise InventoryDriftError("PUBLIC_REPOSITORY_SNAPSHOT_SCHEMA_DRIFT")
    digest = hashlib.sha256(
        json.dumps(sorted(names), separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "status": "PASS_LIVE_PUBLIC_REPO_INVENTORY",
        "owner": OWNER,
        "public_repositories": 25,
        "public_projects": 23,
        "other_public_repositories": 2,
        "public_name_set_sha256": digest,
        "private_repository_count": "NOT_EXPOSED_BY_PUBLIC_API",
        "google_indexed": "UNVERIFIED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True)
    parser.parse_args()
    result = validate_public_repositories(fetch_public_repositories())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryDriftError as exc:
        print("INVENTORY_CHECK_FAILED:", str(exc))
        raise SystemExit(1)
