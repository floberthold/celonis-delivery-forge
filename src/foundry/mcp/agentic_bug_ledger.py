from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


TOOL_ID = "agentic-bug-ledger-mcp"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_runs(artifacts_dir: Path) -> list[dict]:
    if not artifacts_dir.exists():
        return []

    runs: list[dict] = []
    for child in artifacts_dir.iterdir():
        if not child.is_dir():
            continue
        run_metadata = _read_json(child / "run_metadata.json")
        runner_result = _read_json(child / "runner_result.json")
        bug_ledger = _read_json(child / "bug_ledger.json")
        bugs = bug_ledger.get("bugs", []) if isinstance(bug_ledger, dict) else []
        runs.append(
            {
                "run_id": child.name,
                "path": str(child),
                "run_metadata": run_metadata,
                "runner_result": runner_result,
                "bugs": bugs,
                "mtime": child.stat().st_mtime,
            }
        )
    runs.sort(key=lambda item: item["mtime"], reverse=True)
    return runs


def _describe_payload(command: str) -> dict:
    return {
        "tool_id": TOOL_ID,
        "status": "ok",
        "mode": "live",
        "command": command,
        "commands": ["describe", "health", "summarize", "latest"],
        "timestamp_utc": _now_utc(),
    }


def _summarize(runs: list[dict], limit: int) -> dict:
    bugs: list[dict] = []
    for run in runs:
        for bug in run["bugs"]:
            entry = dict(bug)
            entry["run_id"] = run["run_id"]
            journey_id = run["run_metadata"].get("journey_id") or run["runner_result"].get("suite")
            entry["journey_id"] = journey_id
            bugs.append(entry)

    by_severity = Counter(str(bug.get("severity", "unknown")) for bug in bugs)
    recent = bugs[: max(limit, 0)]

    return {
        "tool_id": TOOL_ID,
        "status": "ok",
        "mode": "live",
        "command": "summarize",
        "runs_total": len(runs),
        "bugs_total": len(bugs),
        "bugs_by_severity": dict(by_severity),
        "recent_bugs": recent,
        "timestamp_utc": _now_utc(),
    }


def _latest(runs: list[dict]) -> dict:
    if not runs:
        return {
            "tool_id": TOOL_ID,
            "status": "ok",
            "mode": "live",
            "command": "latest",
            "latest": None,
            "timestamp_utc": _now_utc(),
        }

    top = runs[0]
    return {
        "tool_id": TOOL_ID,
        "status": "ok",
        "mode": "live",
        "command": "latest",
        "latest": {
            "run_id": top["run_id"],
            "path": top["path"],
            "bugs_count": len(top["bugs"]),
            "run_metadata": top["run_metadata"],
            "runner_result": {
                "status": top["runner_result"].get("status"),
                "suite": top["runner_result"].get("suite"),
                "returncode": top["runner_result"].get("returncode"),
            },
            "bugs": top["bugs"],
        },
        "timestamp_utc": _now_utc(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog=TOOL_ID)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("describe")
    subparsers.add_parser("health")

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--artifacts-dir", default=".orchestration/test-runs")
    summarize.add_argument("--limit", type=int, default=20)

    latest = subparsers.add_parser("latest")
    latest.add_argument("--artifacts-dir", default=".orchestration/test-runs")

    args = parser.parse_args()
    command = args.command or "describe"

    if command in {"describe", "health"}:
        payload = _describe_payload(command)
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")
        return 0

    if command in {"summarize", "latest"}:
        runs = _load_runs(Path(args.artifacts_dir))
        payload = _summarize(runs, args.limit) if command == "summarize" else _latest(runs)
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")
        return 0

    payload = {
        "tool_id": TOOL_ID,
        "status": "error",
        "mode": "live",
        "message": f"Unsupported command: {command}",
        "timestamp_utc": _now_utc(),
    }
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
