from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


MODULE_NAME = "foundry.mcp.agentic_code_analysis"


def _run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = "src" if not existing_pythonpath else f"src{os.pathsep}{existing_pythonpath}"
    return subprocess.run(
        [sys.executable, "-m", MODULE_NAME, *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )


def test_code_analysis_mcp_describe_and_health() -> None:
    for command in ["describe", "health"]:
        proc = _run_cmd([command])
        payload = json.loads(proc.stdout)
        assert payload["status"] == "ok"
        assert payload["mode"] == "live"
        assert payload["command"] == command


def test_code_analysis_mcp_run_no_report_updates(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics.json"
    prompt_path = tmp_path / "llm_prompt.md"

    proc = _run_cmd(
        [
            "run",
            "--repo-root",
            ".",
            "--metrics-json",
            str(metrics_path),
            "--llm-prompt",
            str(prompt_path),
            "--no-update-reports",
        ]
    )
    payload = json.loads(proc.stdout)

    assert payload["status"] == "ok"
    assert payload["tool_id"] == "agentic-code-analysis-mcp"
    assert metrics_path.exists()
    assert prompt_path.exists()

    metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics_payload["active_view"]["python_lines"] > 0
    assert metrics_payload["hotspot"]["path"] == "src/foundry/api/routes/ui/__init__.py"
