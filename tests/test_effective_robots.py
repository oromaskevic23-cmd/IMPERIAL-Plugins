"""Effective host-root robots tests. Never make network requests."""
import unittest
from imperial_plugins.effective_robots import (
    HOST_ROBOTS, RobotsAuditError, audit_effective_robots,
)


class HostRobotsTests(unittest.TestCase):
    def test_missing_root_is_default_allow_not_project_robots(self):
        result = audit_effective_robots(404, b"")
        self.assertTrue(result["status"].startswith("PASS"))
        self.assertEqual(result["http_status"], 404)
        self.assertFalse(result["project_path_robots_are_effective"])
        self.assertEqual(result["google_indexed"], "UNVERIFIED")
        self.assertEqual(result["effective_robots_url"], HOST_ROBOTS)

    def test_allow_all_root(self):
        result = audit_effective_robots(200, b"User-agent: *\nAllow: /\n")
        self.assertEqual(result["policy"], "HOST_ROOT_ROBOTS_PARSED")

    def test_host_root_explicit_denial_rejected(self):
        for robots in (
            b"User-agent: *\nDisallow: /\n",
            b"User-agent: Googlebot\nDisallow: /Capital-Core-Public/\n",
            b"User-agent: *\nDisallow: /oromaskevic23-cmd/\n",
        ):
            with self.subTest(robots=robots), self.assertRaisesRegex(
                RobotsAuditError, "DENIES"
            ):
                audit_effective_robots(200, robots)

    def test_non_200_404_ambiguous_fail_closed(self):
        for status in (2000, 301, 403, 429, 500, 503):
            with self.subTest(status=status), self.assertRaises(RobotsAuditError):
                audit_effective_robots(status, b"")

    def test_oversize_and_encoding_errors(self):
        for body in (b"x" * 512_001, b"\xff"):
            with self.subTest(length=len(body)), self.assertRaises(RobotsAuditError):
                audit_effective_robots(200, body)

    def test_bad_types_fail_closed(self):
        for status, body in (("404", b""), (200, "User-agent: *"), (None, None)):
            with self.subTest(status=status), self.assertRaises(RobotsAuditError):
                audit_effective_robots(status, body)


if __name__ == "__main__":
    unittest.main()
