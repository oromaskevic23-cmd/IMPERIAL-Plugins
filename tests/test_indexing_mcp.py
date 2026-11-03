"""Regression and adversarial tests for IMPERIAL Search Indexing MCP.

Founding Architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
No network is required; real HTTP checks are separately executable.
"""
from __future__ import annotations

import json
from unittest import TestCase
import unittest
from unittest.mock import patch

from imperial_plugins.indexing_mcp import (
    AuditError, IndexingMCPServer, MCP_LEGACY, MCP_MODERN,
    CAPABILITIES_META, VERSION_META,
    audit_public_site, list_public_projects, read_manifest,
    search_console_plan, status, _public_get, _sitemap,
)


def envelope(method: str, ident=1, args=None, modern=False):
    params = args.copy() if args else {}
    if modern:
        params["_meta"] = {
            VERSION_META: MCP_MODERN,
            CAPABILITIES_META: {},
            "io.modelcontextprotocol/clientInfo": {"name": "test-client", "version": "1.0.0"},
        }
    return {"jsonrpc": "2.0", "id": ident, "method": method, "params": params}


def fake_endpoints(site_id: str):
    m = read_manifest()
    site = m["sites"][site_id]
    items = [
        {"@type": "ListItem", "position": i + 1, "url": v["url"]}
        for i, v in enumerate(m["projects"])
    ]
    doc = {"@context": "https://schema.org", "@graph": [
        {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items},
    ]}
    html = ("<!doctype html><html><head><link rel='canonical' href='" +
            site["catalog"] + "'><script type='application/ld+json'>" +
            json.dumps(doc) + "</script></head><body><h1>Projects</h1></body></html>")
    # HTMLParser handles single-quoted link attributes.
    site_xml = ("<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/"
                "schemas/sitemap/0.9'><url><loc>" + site["base"] +
                "</loc></url><url><loc>" + site["catalog"] +
                "</loc></url></urlset>")
    return {
        site["base"]: b"<html><title>Home</title></html>",
        site["catalog"]: html.encode(),
        site["sitemap"]: site_xml.encode(),
        site["robots"]: ("User-agent: *\nAllow: /\nSitemap: " +
                         site["sitemap"] + "\n").encode(),
    }


class ProjectScope(TestCase):
    def test_snapshot_is_exactly_public(self):
        m = read_manifest()
        self.assertEqual(len(m["projects"]), 23)
        self.assertEqual(m["excluded_private_count"], 7)
        self.assertEqual(m["google_status"]["url_indexed"], "UNVERIFIED")
        self.assertFalse(any("Private" in p["url"] for p in m["projects"]))

    def test_all_tools_read_only_and_no_external_submission(self):
        server = IndexingMCPServer()
        response = server.dispatch(envelope("tools/list", modern=True))
        tools = response["result"]["tools"]
        self.assertEqual(len(tools), 4)
        self.assertTrue(all(t["annotations"]["readOnlyHint"] for t in tools))
        self.assertFalse(any("submit" in t["name"].lower() for t in tools))

    def test_explicit_google_evidence_absence(self):
        self.assertEqual(status()["google"]["sitemap_submitted"], "UNVERIFIED")
        self.assertEqual(list_public_projects()["google_indexed"], "UNVERIFIED")
        self.assertEqual(search_console_plan()["submission_status"], "NOT_VERIFIED")
        self.assertEqual(len(search_console_plan()["properties"]), 2)


class AuditSites(TestCase):
    def test_two_realistic_site_snapshots(self):
        for site in ("founder", "company"):
            with self.subTest(site=site):
                responses = fake_endpoints(site)
                r = audit_public_site(site, getter=responses.__getitem__)
                self.assertEqual(r["public_http_audit"], "PASS")
                self.assertEqual(r["checks"]["public_projects"], 23)
                self.assertEqual(r["checks"]["sitemap_url_count"], 2)
                self.assertEqual(r["google_indexed"], "UNVERIFIED")

    def test_refuses_arbitrary_site_input_and_no_fetch(self):
        called = []
        for value in ("localhost", "http://127.0.0.1/admin", "../", "company/../../"):
            with self.subTest(site=value), self.assertRaises(AuditError):
                audit_public_site(value, getter=lambda x: called.append(x))
        self.assertEqual(called, [])

    def test_does_not_claim_google_when_catalog_drifted(self):
        r = fake_endpoints("founder")
        site = read_manifest()["sites"]["founder"]
        r[site["catalog"]] = r[site["catalog"]].replace(
            b'"numberOfItems": 23', b'"numberOfItems": 900',
        )
        with self.assertRaises(AuditError):
            audit_public_site("founder", getter=r.__getitem__)

    def test_missing_self_canonical_is_rejected(self):
        r = fake_endpoints("company")
        site = read_manifest()["sites"]["company"]
        r[site["catalog"]] = r[site["catalog"]].replace(b"rel='canonical'", b"rel='alternate'")
        with self.assertRaises(AuditError):
            audit_public_site("company", getter=r.__getitem__)

    def test_foreign_sitemap_url_is_rejected(self):
        r = fake_endpoints("company")
        site = read_manifest()["sites"]["company"]
        r[site["sitemap"]] = r[site["sitemap"]].replace(
            site["catalog"].encode(), b"http://localhost/private")
        with self.assertRaises(AuditError):
            audit_public_site("company", getter=r.__getitem__)

    def test_xml_dtd_and_duplicate_are_rejected(self):
        b = read_manifest()["sites"]["founder"]["base"]
        c = read_manifest()["sites"]["founder"]["catalog"]
        with self.assertRaises(AuditError):
            _sitemap(b"<!DOCTYPE foo><urlset></urlset>", b, c)
        with self.assertRaises(AuditError):
            _sitemap(
                ("<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
                 "<url><loc>" + c + "</loc></url>"
                 "<url><loc>" + c + "</loc></url></urlset>").encode(),
                b, c)

    def test_robots_crawl_denial_is_rejected(self):
        r = fake_endpoints("founder")
        site = read_manifest()["sites"]["founder"]
        r[site["robots"]] += b"Disallow: /\n"
        with self.assertRaises(AuditError):
            audit_public_site("founder", getter=r.__getitem__)

    def test_http_redirects_rejected(self):
        with patch("imperial_plugins.indexing_mcp.urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = __import__("urllib").error.HTTPError(
                "https://example.org/", 302, "Found", {}, None)
            with self.assertRaises(AuditError):
                _public_get("https://oromaskevic23-cmd.github.io/oromaskevic23-cmd/")


class Protocol(TestCase):
    def test_modern_discover(self):
        r = IndexingMCPServer().dispatch(envelope("server/discover", modern=True))
        self.assertEqual(r["result"]["resultType"], "complete")
        self.assertIn(MCP_MODERN, r["result"]["supportedVersions"])
        self.assertIn(MCP_LEGACY, r["result"]["supportedVersions"])
        self.assertEqual(r["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"],
                         "imperial-search-indexing-mcp")

    def test_modern_tool_list_and_call(self):
        s = IndexingMCPServer()
        response = s.dispatch(envelope("tools/list", modern=True))
        self.assertEqual(response["result"]["cacheScope"], "public")
        response = s.dispatch(envelope(
            "tools/call", args={"name": "imperial.indexing_status", "arguments": {}},
            modern=True,
        ))
        self.assertFalse(response["result"]["isError"])
        output = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(output["project_count"], 23)
        self.assertEqual(output["google"]["url_indexed"], "UNVERIFIED")

    def test_legacy_handshake_and_calls(self):
        s = IndexingMCPServer()
        before = s.dispatch(envelope("tools/list"))
        self.assertEqual(before["error"]["code"], -32602)
        initialized = s.dispatch(envelope("initialize", args={
            "protocolVersion": MCP_LEGACY, "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        }))
        self.assertEqual(initialized["result"]["protocolVersion"], MCP_LEGACY)
        self.assertNotIn("resultType", initialized["result"])
        r = s.dispatch(envelope("tools/list"))
        self.assertEqual(len(r["result"]["tools"]), 4)
        self.assertNotIn("resultType", r["result"])

    def test_malformed_caps_and_unsupported_version(self):
        s = IndexingMCPServer()
        m = envelope("tools/list", modern=True)
        del m["params"]["_meta"][CAPABILITIES_META]
        self.assertEqual(s.dispatch(m)["error"]["code"], -32602)
        m = envelope("tools/list", modern=True)
        m["params"]["_meta"][VERSION_META] = "2099-01-01"
        err = s.dispatch(m)["error"]
        self.assertEqual(err["code"], -32022)
        self.assertEqual(err["data"]["requested"], "2099-01-01")

    def test_unknown_tool_and_unknown_method(self):
        s = IndexingMCPServer()
        self.assertEqual(s.dispatch(envelope("banana", modern=True))["error"]["code"], -32601)
        self.assertEqual(s.dispatch(envelope(
            "tools/call", args={"name": "imperial.root_access", "arguments": {}},
            modern=True))["error"]["code"], -32602)

    def test_invalid_site_and_unexpected_arg_are_tool_errors(self):
        s = IndexingMCPServer()
        r = s.dispatch(envelope("tools/call", args={
            "name": "imperial.audit_published_site",
            "arguments": {"site_id": "http://169.254.169.254/"},
        }, modern=True))
        self.assertTrue(r["result"]["isError"])
        r2 = s.dispatch(envelope("tools/call", args={
            "name": "imperial.indexing_status",
            "arguments": {"secret": "do not use"},
        }, modern=True))
        self.assertTrue(r2["result"]["isError"])

    def test_notifications_never_execute(self):
        s = IndexingMCPServer()
        msg = envelope("tools/call", args={
            "name": "imperial.audit_published_site",
            "arguments": {"site_id": "founder"},
        }, modern=True)
        del msg["id"]
        self.assertIsNone(s.dispatch(msg))

    def test_invalid_rpc_fails_closed(self):
        s = IndexingMCPServer()
        self.assertEqual(s.dispatch([])["error"]["code"], -32600)
        self.assertEqual(s.dispatch({"jsonrpc": "2.0", "id": 1,
                                     "method": "tools/list", "params": []})["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
