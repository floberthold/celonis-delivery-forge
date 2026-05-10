from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_seed(profile: str, dry_run: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        ".\\scripts\\seed_profile_data.ps1",
        "-Profile",
        profile,
    ]
    if dry_run:
        cmd.append("-DryRun")

    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Seed strategy script is PowerShell-first")
def test_profile_seed_strategy_dry_run_full_profile_lists_steps() -> None:
    result = _run_seed("full", dry_run=True)
    assert result.returncode == 0, result.stderr or result.stdout
    output = f"{result.stdout}\n{result.stderr}"

    assert "Profile seed strategy" in output
    assert "Profile: full" in output
    assert "python scripts/seed_use_cases.py" in output
    assert "python scripts/seed_forum_insights.py" in output


@pytest.mark.skipif(sys.platform != "win32", reason="Seed strategy script is PowerShell-first")
def test_profile_seed_strategy_rejects_unknown_profile() -> None:
    result = _run_seed("does-not-exist", dry_run=True)
    assert result.returncode != 0
    output = f"{result.stdout}\n{result.stderr}"
    assert "not found in seed plan" in output
