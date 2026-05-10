from __future__ import annotations

import json
import os
import subprocess
import sys


MODULES = [
    "foundry.mcp.agentic_test_runner",
    "foundry.mcp.agentic_bug_ledger",
    "foundry.mcp.agentic_evidence",
    "foundry.mcp.agentic_deployment_readiness",
]


def test_mcp_stub_modules_are_executable() -> None:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = "src" if not existing_pythonpath else f"src{os.pathsep}{existing_pythonpath}"

    for module_name in MODULES:
        proc = subprocess.run(
            [sys.executable, "-m", module_name, "health"],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        payload = json.loads(proc.stdout)
        assert payload["status"] == "ok"
        assert payload["mode"] in {"stub", "live"}
        assert payload["command"] == "health"
