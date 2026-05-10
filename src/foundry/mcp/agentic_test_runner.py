from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


TOOL_ID = "agentic-user-test-runner-mcp"

SMOKE_TESTS = [
    "tests/test_methodology_ui.py",
    "tests/test_celonis_ui_route_presence.py",
]

CORE_TESTS = [
    "tests/test_methodology_ui.py",
    "tests/test_celonis_ui_route_presence.py",
    "tests/test_e2e_artifact_helpers.py",
    "tests/test_mcp_stub_modules.py",
]

E2E_TESTS = [
    "tests/e2e/test_dashboard_login_journey_playwright.py",
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_tests(suite: str, custom_tests: list[str], changed_files: list[str]) -> list[str]:
    if suite == "custom":
        return custom_tests
    if suite == "smoke":
        return SMOKE_TESTS
    if suite == "core":
        return CORE_TESTS
    if suite == "e2e":
        return E2E_TESTS

    combined = CORE_TESTS + E2E_TESTS
    if suite != "all":
        return combined

    if not changed_files:
        return combined

    selected: list[str] = []
    for changed in changed_files:
        normalized = changed.replace("\\", "/")
        if normalized.startswith("src/foundry/mcp/"):
            selected.extend(["tests/test_mcp_stub_modules.py", "tests/test_e2e_artifact_helpers.py"])
        if normalized.startswith("src/foundry/ui/templates/") or normalized.startswith("src/foundry/api/routes/ui.py"):
            selected.extend(["tests/test_methodology_ui.py", "tests/test_celonis_ui_route_presence.py"])

    if not selected:
        return combined
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(selected))


def _describe_payload() -> dict:
    return {
        "tool_id": TOOL_ID,
        "status": "ok",
        "mode": "live",
        "commands": ["describe", "health", "run"],
        "suites": ["smoke", "core", "e2e", "all", "custom"],
        "timestamp_utc": _now_utc(),
    }


def _run_tests(args: argparse.Namespace) -> tuple[dict, int]:
    artifacts_root = Path(args.artifacts_dir)
    artifacts_root.mkdir(parents=True, exist_ok=True)

    run_id = uuid4().hex
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    tests_to_run = _resolve_tests(args.suite, args.tests, args.changed_files)
    if not tests_to_run:
        payload = {
            "tool_id": TOOL_ID,
            "status": "error",
            "mode": "live",
            "run_id": run_id,
            "message": "No tests resolved for execution.",
            "timestamp_utc": _now_utc(),
        }
        return payload, 2

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = "src" if not existing_pythonpath else f"src{os.pathsep}{existing_pythonpath}"

    if args.suite in {"e2e", "all"}:
        env["RUN_PLAYWRIGHT_E2E"] = "1"
    if args.base_url:
        env["FORGE_E2E_BASE_URL"] = args.base_url
    env["FORGE_E2E_ARTIFACTS_DIR"] = str(artifacts_root)

    cmd = [sys.executable, "-m", "pytest", *tests_to_run, "-q", f"--maxfail={args.maxfail}"]

    start = time.time()
    started_at = _now_utc()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    duration_seconds = round(time.time() - start, 3)
    ended_at = _now_utc()

    status = "passed" if proc.returncode == 0 else "failed"
    runner_result = {
        "run_id": run_id,
        "suite": args.suite,
        "status": status,
        "returncode": proc.returncode,
        "tests": tests_to_run,
        "started_at_utc": started_at,
        "ended_at_utc": ended_at,
        "duration_seconds": duration_seconds,
        "command": cmd,
        "stdout_tail": proc.stdout[-8000:],
        "stderr_tail": proc.stderr[-8000:],
    }
    (run_dir / "runner_result.json").write_text(json.dumps(runner_result, indent=2), encoding="utf-8")

    payload = {
        "tool_id": TOOL_ID,
        "status": "ok",
        "mode": "live",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "suite": args.suite,
        "result": status,
        "returncode": proc.returncode,
        "tests_count": len(tests_to_run),
        "timestamp_utc": ended_at,
    }
    return payload, proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(prog=TOOL_ID)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("describe")
    subparsers.add_parser("health")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--suite", choices=["smoke", "core", "e2e", "all", "custom"], default="smoke")
    run_parser.add_argument("--tests", nargs="*", default=[])
    run_parser.add_argument("--changed-files", nargs="*", default=[])
    run_parser.add_argument("--maxfail", type=int, default=1)
    run_parser.add_argument("--artifacts-dir", default=".orchestration/test-runs")
    run_parser.add_argument("--base-url", default="")

    args = parser.parse_args()
    command = args.command or "describe"

    if command in {"describe", "health"}:
        payload = _describe_payload()
        payload["command"] = command
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")
        return 0

    if command == "run":
        payload, exit_code = _run_tests(args)
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")
        return exit_code

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
