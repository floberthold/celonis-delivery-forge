from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_stub_server(tool_id: str, purpose: str) -> int:
    """Provide a minimal executable MCP-style CLI contract for planned tools."""
    parser = argparse.ArgumentParser(prog=tool_id)
    parser.add_argument(
        "command",
        nargs="?",
        default="describe",
        choices=["describe", "health"],
        help="Stub command to execute.",
    )
    args = parser.parse_args()

    payload = {
        "tool_id": tool_id,
        "status": "ok",
        "mode": "stub",
        "purpose": purpose,
        "command": args.command,
        "timestamp_utc": _utc_now(),
        "message": "Stub MCP entrypoint is operational; implementation is pending.",
    }
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    return 0
