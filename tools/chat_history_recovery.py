"""IMPERIAL Chat History Recovery CLI — offline, owner-supplied data only.

Founding Architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from imperial_plugins.chat_recovery import RecoveryError, build_index, recover


def main(argv=None):
    p = argparse.ArgumentParser(description="Private local ChatGPT export search (10 simulated sub-NCA specialists)")
    commands = p.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("index", help="Index user-supplied conversations.json")
    ingest.add_argument("--export", type=Path, required=True)
    ingest.add_argument("--database", type=Path, required=True,
                        help="New private unencrypted local SQLite file. Never commit it.")
    search = commands.add_parser("search", help="Search owner-provided export evidence")
    search.add_argument("--database", type=Path, required=True)
    search.add_argument("--query", required=True)
    cutoff = search.add_mutually_exclusive_group()
    cutoff.add_argument("--before", help="Owner-confirmed exclusive UTC date YYYY-MM-DD")
    cutoff.add_argument("--before-val-town", action="store_true",
                        help="Heuristic first user mention, NOT verified Val Town start")
    search.add_argument("--include-alternates", action="store_true")
    search.add_argument("--limit", type=int, default=10)
    args = p.parse_args(argv)
    try:
        if args.command == "index":
            result = build_index(args.export, args.database)
        else:
            result = recover(args.database,args.query,before=args.before,
                             before_val_town=args.before_val_town,
                             include_alternates=args.include_alternates,
                             limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (RecoveryError,OSError,ValueError) as exc:
        print("IMPERIAL_RECOVERY_DENIED: "+str(exc),file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
