"""Tests for original provider request fabric; never contact external services."""
import hashlib
import json
import unittest
from imperial_plugins.provider_fabric import (
    PreparedProviderRequest, ProviderRequestDenied, prepare_provider_action
)


class ProviderFabricTests(unittest.TestCase):
    def test_research_request(self):
        p = prepare_provider_action("perplexity.research",
                                    {"question": "Check an official public specification"})
        self.assertIsInstance(p, PreparedProviderRequest)
        self.assertIn("api.perplexity.ai", p.target)
        self.assertEqual(json.loads(p.payload)["model"], "sonar")
        self.assertTrue(p.potentially_billable)
        self.assertFalse(p.runtime_execution_authorized)
        self.assertEqual(p.source_sha256, hashlib.sha256(p.payload).hexdigest())
        self.assertNotIn("question", str(p.as_evidence()))

    def test_firecrawl_only_explicit_public_hosts(self):
        with self.assertRaises(ProviderRequestDenied):
            prepare_provider_action("firecrawl.scrape", {"url": "https://example.org/page"})
        p = prepare_provider_action(
            "firecrawl.scrape", {"url": "https://example.org/page"},
            approved_public_hosts=frozenset({"example.org"}))
        self.assertEqual(p.target, "https://api.firecrawl.dev/v2/scrape")
        self.assertEqual(json.loads(p.payload)["url"], "https://example.org/page")
        for url in ("https://localhost/x", "http://example.org/x",
                    "https://127.0.0.1/x", "https://example.org.evil.net/x",
                    "https://alice:password@example.org/x",
                    "https://example.org:8443/x",
                    "https://example.org/x#fragment"):
            with self.subTest(url=url), self.assertRaises(ProviderRequestDenied):
                prepare_provider_action("firecrawl.scrape", {"url": url},
                    approved_public_hosts=frozenset({"example.org", "localhost", "127.0.0.1"}))

    def test_posthog_minimal_pseudonymous_events(self):
        p = prepare_provider_action("posthog.capture", {
            "event": "build_completed", "distinct_id_sha256": "a" * 64,
            "properties": {"result": "pass", "surface": "constructor_ai"},
        }, posthog_region="eu")
        self.assertEqual(p.target, "https://eu.i.posthog.com/i/v0/e/")
        self.assertEqual(json.loads(p.payload)["event"], "build_completed")
        for bad in ({"email": "person@example.com"}, {"secret": "token"},
                    {"result": "X" * 100}, {"ip": "1.2.3.4"}):
            with self.subTest(bad=bad), self.assertRaises(ProviderRequestDenied):
                prepare_provider_action("posthog.capture", {
                    "event": "build_completed", "distinct_id_sha256": "a" * 64,
                    "properties": bad
                })

    def test_playwright_is_pinned_to_owned_ci_suite(self):
        p = prepare_provider_action("playwright.e2e", {
            "suite": "constructor-browser-acceptance"})
        self.assertEqual(p.method, "LOCAL")
        self.assertFalse(p.requires_vendor_credentials)
        self.assertIn("CONSTRUCTOR-AI", p.target)
        with self.assertRaises(ProviderRequestDenied):
            prepare_provider_action("playwright.e2e",
                                    {"suite": "run-arbitrary-shell-command"})

    def test_composio_only_discovery_not_execution(self):
        p = prepare_provider_action("composio.discover", {
            "query": "Find a read-only calendar list action"})
        payload = json.loads(p.payload)
        self.assertEqual(payload["params"]["name"], "COMPOSIO_SEARCH_TOOLS")
        self.assertEqual(payload["method"], "tools/call")
        for action in ("composio.execute", "composio.delete",
                       "composio.connect", "other.unknown"):
            with self.subTest(action=action), self.assertRaises(ProviderRequestDenied):
                prepare_provider_action(action, {"query": "Delete all records"})

    def test_readiness_is_not_authorization(self):
        plans = [
            prepare_provider_action("perplexity.research", {"question": "An approved question"}),
            prepare_provider_action("posthog.capture", {
                "event": "task_completed", "distinct_id_sha256": "b"*64,
                "properties": {"result": "pass"}
            }),
            prepare_provider_action("playwright.e2e", {
                "suite": "constructor-browser-acceptance"}),
            prepare_provider_action("composio.discover", {
                "query": "Find a read only file list"}),
        ]
        for plan in plans:
            e = plan.as_evidence()
            self.assertFalse(e["runtime_execution_authorized"])
            self.assertFalse(e["independent_qa_verified"])
            self.assertTrue(e["external_effects"])
            self.assertEqual(e["payload_sha256"], plan.source_sha256)

    def test_reject_injection_and_invalid_schema(self):
        for action, args in (
            ("firecrawl.scrape", {"url": "file:///etc/passwd"}),
            ("firecrawl.scrape", {"url": "https://example.org", "force": True}),
            ("posthog.capture", {"event": "x"}),
            ("composio.discover", {"query": "x"}),
            ("perplexity.research", {"question": 123}),
        ):
            with self.subTest(action=action, args=args), self.assertRaises(
                    ProviderRequestDenied):
                prepare_provider_action(action, args)


if __name__ == "__main__":
    unittest.main()
