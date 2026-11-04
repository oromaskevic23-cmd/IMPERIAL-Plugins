#!/usr/bin/env python3
"""Fail-closed check for a known bundled-AI-quota relay anti-pattern.

This is a narrow automated preventive test, not a full legal/security audit.
No credentials, network calls, or external dependencies are needed.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go"}
SELF = "security/provider_quota_relay_gate.py"

BUNDLED_AI = re.compile(r"\bValTownOpenAI\b")
OPENAI_COMPATIBLE = re.compile(r"/v1/(?:models|chat/completions)\b")
SERVER_ENTRYPOINT = re.compile(
    r"\b(?:Deno\.serve|serve\s*\(|FastAPI\s*\(|app\.(?:get|post)|router\.(?:get|post)|createServer\s*\()"
)


def violations(files: dict[str, str]) -> list[str]:
    """A provider-native bundled allowance and external compatible server must not coexist."""
    provider_files = sorted(name for name, body in files.items() if BUNDLED_AI.search(body))
    endpoint_files = sorted(
        name for name, body in files.items()
        if OPENAI_COMPATIBLE.search(body) and SERVER_ENTRYPOINT.search(body)
    )
    if not provider_files or not endpoint_files:
        return []
    return [
        "Bundled ValTownOpenAI quota appears together with an OpenAI-compatible "
        "served API in source. Block release until the relay is removed or "
        "provider permission is independently established.",
        "Provider references: " + ", ".join(provider_files),
        "Hosted relay references: " + ", ".join(endpoint_files),
    ]


def tracked_sources(root: Path) -> dict[str, str]:
    cp = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    result = {}
    for name in cp.stdout.decode("utf-8").split("\x00"):
        if not name or name == SELF or Path(name).suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        path = root / name
        if not path.is_file() or path.is_symlink():
            continue
        try:
            result[name] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise RuntimeError("Non-UTF8 tracked source file: " + name)
    return result


def self_test() -> None:
    assert not violations({"safe.ts": "fetch('/v1/chat/completions')"})
    assert not violations({"safe.ts": "const client = new ValTownOpenAI()"})
    assert violations({
        "provider.ts": "const client = new ValTownOpenAI();",
        "server.ts": "Deno.serve((r) => r.url.includes('/v1/chat/completions'))",
    })
    assert violations({"relay.ts": "Deno.serve(()=>new ValTownOpenAI()); // /v1/models"})
    print("4 provider-relay gate self-tests: PASS")


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return 0
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    try:
        issues = violations(tracked_sources(root))
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"PROVIDER_RELAY_GATE_ERROR: {exc}", file=sys.stderr)
        return 2
    if issues:
        for issue in issues:
            print("PROVIDER_RELAY_BLOCK: " + issue, file=sys.stderr)
        return 1
    print("PROVIDER_RELAY_GATE_PASS (known ValTownOpenAI relay pattern only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
