#!/usr/bin/env python3
"""MOJON local stdio MCP server. No remote transport and no paid services."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imperial_plugins.mojon_mcp import main

if __name__ == "__main__":
    main()
