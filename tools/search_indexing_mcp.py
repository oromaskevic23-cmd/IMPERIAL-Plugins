#!/usr/bin/env python3
"""Start the IMPERIAL Search Indexing MCP server on stdio.

Founding Architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
Read-only; no Google Search Console authorization is implicit.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imperial_plugins.indexing_mcp import main

if __name__ == "__main__":
    main()
