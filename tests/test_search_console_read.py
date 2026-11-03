"""Search Console OAuth read adapter tests; no real Google credentials or requests.

Founding architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
"""
from __future__ import annotations

import json
import unittest

from imperial_plugins.search_console_read import (
    GoogleAccessError, SearchConsoleReadBridge, GOOGLE_SITES,
    GOOGLE_INSPECTION, request_google, sitemap_submission_preflight,
)
from imperial_plugins.indexing_mcp import ALLOWED_SITES


class FixtureTransport:
    def __init__(self, permissions=None):
        self.calls = []
        self.permissions = permissions or {"founder": "siteOwner", "company": "siteFullUser"}

    def __call__(self, method, url, token, body):
        assert token == "dummy-only-never-real"
        self.calls.append((method, url, body))
        if method == "GET" and url == GOOGLE_SITES:
            return 200, json.dumps({"siteEntry": [
                {"siteUrl": ALLOWED_SITES[k]["base"], "permissionLevel": v}
                for k, v in self.permissions.items()
            ]}).encode()
        if method == "GET" and url.endswith("/sitemaps"):
            for site in ALLOWED_SITES.values():
                if site["base"] in __import__("urllib").parse.unquote(url):
                    return 200, json.dumps({"sitemap": [
                        {"path": site["sitemap"], "lastSubmitted": "2026-10-30T00:00:00Z",
                         "isPending": False, "errors": "0", "warnings": "0"}
                    ]}).encode()
        if method == "POST" and url == GOOGLE_INSPECTION:
            return 200, json.dumps({"inspectionResult": {"indexStatusResult": {
                "verdict": "PASS", "coverageState": "Submitted and indexed",
                "indexingState": "INDEXING_ALLOWED",
                "lastCrawlTime": "2026-11-01T12:00:00Z",
            }}}).encode()
        raise AssertionError("Unexpected destination")


class SearchConsoleTests(unittest.TestCase):
    def setUp(self):
        self.transport = FixtureTransport()
        self.reader = SearchConsoleReadBridge(
            access_token="dummy-only-never-real", transport=self.transport)

    def test_without_oauth_fails_closed(self):
        reader = SearchConsoleReadBridge(access_token=None, transport=self.transport)
        with self.assertRaisesRegex(GoogleAccessError, "NOT_CONNECTED"):
            reader.check_property("founder")
        self.assertEqual(self.transport.calls, [])

    def test_exact_property_and_real_permission(self):
        found = self.reader.check_property("founder")
        self.assertEqual(found["google_permission"], "siteOwner")
        self.assertEqual(found["google_indexed"], "UNVERIFIED")
        self.assertEqual(len(self.transport.calls), 1)

    def test_unknown_or_other_property_denied_without_network(self):
        for value in ("attacker", "http://localhost/", "../", ""):
            with self.subTest(value=value), self.assertRaises(GoogleAccessError):
                self.reader.check_property(value)
        self.assertEqual(self.transport.calls, [])

    def test_account_other_than_owner_denied(self):
        reader = SearchConsoleReadBridge(
            access_token="dummy-only-never-real",
            transport=FixtureTransport(permissions={"founder": "siteUnverifiedUser"}))
        with self.assertRaisesRegex(GoogleAccessError, "NOT_VERIFIED"):
            reader.list_submitted_sitemaps("founder")

    def test_missing_property_denied_even_with_token(self):
        reader = SearchConsoleReadBridge(
            access_token="dummy-only-never-real",
            transport=FixtureTransport(permissions={"company": "siteOwner"}))
        with self.assertRaises(GoogleAccessError):
            reader.inspect_canonical("founder", ALLOWED_SITES["founder"]["base"])

    def test_sitemap_status_only_from_google_response(self):
        result = self.reader.list_submitted_sitemaps("company")
        self.assertEqual(result["evidence"], "GOOGLE_SEARCH_CONSOLE_API_RESPONSE")
        self.assertEqual(result["url_indexed"], "UNVERIFIED")
        self.assertTrue(result["found_in_google_account"])
        self.assertEqual(len(self.transport.calls), 2)
        self.assertEqual(self.transport.calls[0][0], "GET")
        self.assertEqual(self.transport.calls[1][0], "GET")

    def test_inspection_exact_canonical_only(self):
        page = ALLOWED_SITES["founder"]["catalog"]
        result = self.reader.inspect_canonical("founder", page)
        self.assertEqual(result["index_verdict"], "PASS")
        self.assertEqual(result["evidence"], "GOOGLE_URL_INSPECTION_API_RESULT")
        self.assertEqual(len(self.transport.calls), 2)
        self.assertEqual(self.transport.calls[1][0], "POST")
        self.assertEqual(self.transport.calls[1][2]["inspectionUrl"], page)

    def test_inspection_rejects_any_unreviewed_page(self):
        for page in ("http://127.0.0.1", "https://evil.example/",
                     ALLOWED_SITES["founder"]["base"] + "admin"):
            with self.subTest(page=page), self.assertRaises(GoogleAccessError):
                self.reader.inspect_canonical("founder", page)
        self.assertEqual(self.transport.calls, [])

    def test_submit_is_never_executed_by_preflight(self):
        plan = sitemap_submission_preflight("company")
        self.assertEqual(plan["method"], "PUT")
        self.assertIn("%3A%2F%2F", plan["endpoint"])
        self.assertEqual(plan["status"], "INTENT_ONLY_OWNER_APPROVAL_REQUIRED")
        self.assertEqual(plan["google_submitted"], "UNVERIFIED")
        self.assertEqual(self.transport.calls, [])

    def test_wrong_transport_destination_and_write_denied(self):
        with self.assertRaises(GoogleAccessError):
            request_google("PUT", GOOGLE_SITES, "dummy-only-never-real")
        with self.assertRaises(GoogleAccessError):
            request_google("POST", GOOGLE_SITES, "dummy-only-never-real")
        with self.assertRaises(GoogleAccessError):
            request_google("GET", "https://localhost/admin", "dummy-only-never-real")

    def test_google_endpoint_allowlist_rejects_extra_paths(self):
        for extra_path in ("/unreviewed/sitemaps", "/../sites", "/owner/private"):
            with self.subTest(extra_path=extra_path), self.assertRaises(GoogleAccessError):
                request_google("GET", GOOGLE_SITES + extra_path, "dummy-only-never-real")

    def test_operator_cli_blocks_without_real_oauth(self):
        import os
        import subprocess
        import sys
        from pathlib import Path
        repo = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env.pop("IMPERIAL_GSC_ACCESS_TOKEN", None)
        cmd = [sys.executable, str(repo / "tools/gsc_operator.py"),
               "--site", "founder", "--check", "property"]
        output = subprocess.run(cmd, cwd=repo, env=env, capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(output.returncode, 2)
        result = json.loads(output.stdout)
        self.assertEqual(result["reason"], "GOOGLE_OAUTH_NOT_CONNECTED")
        self.assertEqual(result["google_indexed"], "UNVERIFIED")

    def test_operator_cli_only_returns_submission_preflight(self):
        import subprocess
        import sys
        from pathlib import Path
        repo = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, str(repo / "tools/gsc_operator.py"),
             "--site", "company", "--check", "plan"],
            cwd=repo, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "INTENT_ONLY_OWNER_APPROVAL_REQUIRED")
        self.assertEqual(payload["google_submitted"], "UNVERIFIED")

    def test_malformed_google_response_denied(self):
        reader = SearchConsoleReadBridge(
            access_token="dummy-only-never-real",
            transport=lambda *_: (200, b"not json"))
        with self.assertRaises(GoogleAccessError):
            reader.check_property("company")


if __name__ == "__main__":
    unittest.main()
