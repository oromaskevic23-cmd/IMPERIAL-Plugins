"""Public inventory fixture tests: immutable visibility boundary, no network."""
import unittest

from imperial_plugins.indexing_mcp import read_manifest
from imperial_plugins.public_inventory import (
    EXTRA_PUBLIC, InventoryDriftError, OWNER, validate_public_repositories,
)


def public_fixture():
    manifest = read_manifest()
    names = [p["name"] for p in manifest["projects"]] + sorted(EXTRA_PUBLIC)
    return [{"name": name, "owner": {"login": OWNER}, "private": False,
             "visibility": "public"} for name in names]


class InventoryTests(unittest.TestCase):
    def test_approved_23_projects_and_two_other_public(self):
        r = validate_public_repositories(public_fixture())
        self.assertEqual(r["public_repositories"], 25)
        self.assertEqual(r["public_projects"], 23)
        self.assertEqual(r["other_public_repositories"], 2)
        self.assertEqual(len(r["public_name_set_sha256"]), 64)
        self.assertEqual(r["google_indexed"], "UNVERIFIED")

    def test_unknown_public_repo_is_drift_not_autopublished(self):
        records = public_fixture()
        records.append({"name": "NEW-UNREVIEWED-PUBLIC", "private": False,
                        "owner": {"login": OWNER}})
        with self.assertRaisesRegex(InventoryDriftError, "DRIFT"):
            validate_public_repositories(records)

    def test_deleted_public_repo_is_drift(self):
        with self.assertRaisesRegex(InventoryDriftError, "DRIFT"):
            validate_public_repositories(public_fixture()[:-1])

    def test_unauthorized_foreign_repo_denied(self):
        data = public_fixture()
        data[0]["owner"]["login"] = "other"
        with self.assertRaisesRegex(InventoryDriftError, "FOREIGN"):
            validate_public_repositories(data)

    def test_private_details_ignored_without_leak(self):
        data = public_fixture()
        data.append({"name": "CLASSIFIED-DO-NOT-LOG",
                     "owner": {"login": OWNER}, "private": True,
                     "visibility": "private"})
        r = validate_public_repositories(data)
        self.assertEqual(r["private_repository_count"], "NOT_EXPOSED_BY_PUBLIC_API")
        self.assertNotIn("CLASSIFIED", str(r))

    def test_duplicate_public_rejected(self):
        data = public_fixture()
        data.append(data[0].copy())
        with self.assertRaisesRegex(InventoryDriftError, "DUPLICATE"):
            validate_public_repositories(data)

    def test_broken_manifest_or_wrong_schema_denied(self):
        for bad in (None, "x", [None], [{}]):
            with self.subTest(bad=bad), self.assertRaises(InventoryDriftError):
                validate_public_repositories(bad)


if __name__ == "__main__":
    unittest.main()
