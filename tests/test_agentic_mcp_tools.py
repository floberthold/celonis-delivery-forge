from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _tool_env() -> dict[str, str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = "src" if not existing_pythonpath else f"src{os.pathsep}{existing_pythonpath}"
    return env


def test_agentic_test_runner_executes_pytest_and_writes_artifacts(tmp_path) -> None:
    artifacts_dir = tmp_path / "runs"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "foundry.mcp.agentic_test_runner",
            "run",
            "--suite",
            "custom",
            "--tests",
            "tests/test_e2e_artifact_helpers.py",
            "--artifacts-dir",
            str(artifacts_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
        env=_tool_env(),
    )

    payload = json.loads(proc.stdout)
    assert payload["status"] == "ok"
    assert payload["mode"] == "live"
    assert payload["result"] == "passed"

    run_id = payload["run_id"]
    run_result_path = artifacts_dir / run_id / "runner_result.json"
    assert run_result_path.exists()

    run_result = json.loads(run_result_path.read_text(encoding="utf-8"))
    assert run_result["status"] == "passed"
    assert "tests/test_e2e_artifact_helpers.py" in run_result["tests"]


def test_agentic_bug_ledger_summarizes_runs(tmp_path) -> None:
    artifacts_dir = tmp_path / "runs"
    run_one = artifacts_dir / "run-one"
    run_two = artifacts_dir / "run-two"
    run_one.mkdir(parents=True, exist_ok=True)
    run_two.mkdir(parents=True, exist_ok=True)

    (run_one / "run_metadata.json").write_text(
        json.dumps({"run_id": "run-one", "journey_id": "journey-a", "status": "failed"}, indent=2),
        encoding="utf-8",
    )
    (run_one / "bug_ledger.json").write_text(
        json.dumps(
            {
                "bugs": [
                    {
                        "id": "BUG-0001",
                        "severity": "P1",
                        "expected_behavior": "x",
                        "observed_behavior": "y",
                        "route": "/a",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (run_two / "run_metadata.json").write_text(
        json.dumps({"run_id": "run-two", "journey_id": "journey-b", "status": "passed"}, indent=2),
        encoding="utf-8",
    )
    (run_two / "bug_ledger.json").write_text(
        json.dumps(
            {
                "bugs": [
                    {
                        "id": "BUG-0002",
                        "severity": "P2",
                        "expected_behavior": "m",
                        "observed_behavior": "n",
                        "route": "/b",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summarize_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "foundry.mcp.agentic_bug_ledger",
            "summarize",
            "--artifacts-dir",
            str(artifacts_dir),
            "--limit",
            "10",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=_tool_env(),
    )
    summary_payload = json.loads(summarize_proc.stdout)
    assert summary_payload["status"] == "ok"
    assert summary_payload["mode"] == "live"
    assert summary_payload["runs_total"] == 2
    assert summary_payload["bugs_total"] == 2
    assert summary_payload["bugs_by_severity"]["P1"] == 1
    assert summary_payload["bugs_by_severity"]["P2"] == 1

    latest_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "foundry.mcp.agentic_bug_ledger",
            "latest",
            "--artifacts-dir",
            str(artifacts_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
        env=_tool_env(),
    )
    latest_payload = json.loads(latest_proc.stdout)
    assert latest_payload["status"] == "ok"
    assert latest_payload["mode"] == "live"
    assert latest_payload["latest"] is not None
