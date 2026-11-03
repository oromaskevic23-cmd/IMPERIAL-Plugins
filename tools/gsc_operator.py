"""Owner-operated read-only Search Console verifier.

Usage: run in an authorized private host with a short-lived OAuth token
provided via the runtime environment, never entered in chat or committed.
"""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imperial_plugins.search_console_read import (
    GoogleAccessError, SearchConsoleReadBridge, sitemap_submission_preflight,
)
from imperial_plugins.indexing_mcp import ALLOWED_SITES


def main():
    parser = argparse.ArgumentParser(description="IMPERIAL Google property preflight")
    parser.add_argument("--site", choices=sorted(ALLOWED_SITES), required=True)
    parser.add_argument("--check", choices=("property", "sitemap", "home", "catalog", "plan"),
                        default="property")
    args = parser.parse_args()
    if args.check == "plan":
        result = sitemap_submission_preflight(args.site)
    else:
        reader = SearchConsoleReadBridge(
            access_token=os.environ.get("IMPERIAL_GSC_ACCESS_TOKEN"))
        try:
            if args.check == "property":
                result = reader.check_property(args.site)
            elif args.check == "sitemap":
                result = reader.list_submitted_sitemaps(args.site)
            else:
                page = ALLOWED_SITES[args.site]["base" if args.check == "home"
                                              else "catalog"]
                result = reader.inspect_canonical(args.site, page)
        except GoogleAccessError as exc:
            result = {"status": "BLOCKED", "reason": str(exc),
                      "google_indexed": "UNVERIFIED"}
            print(json.dumps(result))
            return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
