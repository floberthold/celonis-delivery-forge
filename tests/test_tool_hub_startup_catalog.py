from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / ".orchestration" / "tool-hub" / "catalog.json"
STATE_PATH = REPO_ROOT / ".orchestration" / "tool-hub" / "state.json"


def _run_start(mode: str, profile: str, *, registry_path: str | None = None, profiles_path: str | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        ".\\START.ps1",
        "-Mode",
        mode,
        "-Profile",
        profile,
        "-SkipDependencyInstall",
    ]

    if registry_path:
        cmd.extend(["-RegistryPath", registry_path])
    if profiles_path:
        cmd.extend(["-ProfilesPath", profiles_path])

    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Tool hub startup scripts are PowerShell-first")
def test_start_dry_run_writes_catalog_with_health_probe_and_activation_phase() -> None:
    result = _run_start("dry-run", "full")
    assert result.returncode == 0, result.stderr or result.stdout
    assert CATALOG_PATH.exists()

    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8-sig"))
    tools = payload.get("tools", [])

    assert payload.get("mode") == "dry-run"
    assert payload.get("profile") == "full"
    assert isinstance(tools, list)
    assert tools
    assert all(int(tool.get("activation_phase", 0)) >= 1 for tool in tools)
    assert all(
        isinstance(tool.get("health_probe"), dict) and bool(tool.get("health_probe", {}).get("type"))
        for tool in tools
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Tool hub startup scripts are PowerShell-first")
def test_start_status_mode_returns_without_running_state() -> None:
    result = _run_start("status", "full")
    assert result.returncode == 0, result.stderr or result.stdout
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "No running state found." in combined_output or "running" in combined_output.lower()


@pytest.mark.skipif(sys.platform != "win32", reason="Tool hub startup scripts are PowerShell-first")
def test_start_status_mode_prints_profile_health_summary() -> None:
    backup_catalog = CATALOG_PATH.read_text(encoding="utf-8-sig") if CATALOG_PATH.exists() else None
    backup_state = STATE_PATH.read_text(encoding="utf-8-sig") if STATE_PATH.exists() else None

    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        catalog_payload = {
            "profile": "pilot-core",
            "tools": [
                {
                    "id": "foundry-api",
                    "domain": "core-platform",
                    "enabled": True,
                    "activation_phase": 1,
                },
                {
                    "id": "local-wiki-query-api",
                    "domain": "knowledge-hub",
                    "enabled": False,
                    "activation_phase": 1,
                },
            ],
        }
        state_payload = {
            "started_at_utc": "2026-05-10T00:00:00Z",
            "tools": [
                {
                    "id": "foundry-api",
                    "pid": os.getpid(),
                    "repo_path": ".",
                    "log_file": "dummy.log",
                }
            ],
        }

        CATALOG_PATH.write_text(json.dumps(catalog_payload), encoding="utf-8")
        STATE_PATH.write_text(json.dumps(state_payload), encoding="utf-8")

        result = _run_start("status", "pilot-core")
        assert result.returncode == 0, result.stderr or result.stdout
        combined_output = f"{result.stdout}\n{result.stderr}"
        assert "Profile health summary" in combined_output
        assert "core-platform" in combined_output
        assert "Process state" in combined_output
    finally:
        if backup_catalog is None:
            CATALOG_PATH.unlink(missing_ok=True)
        else:
            CATALOG_PATH.write_text(backup_catalog, encoding="utf-8")

        if backup_state is None:
            STATE_PATH.unlink(missing_ok=True)
        else:
            STATE_PATH.write_text(backup_state, encoding="utf-8")


@pytest.mark.skipif(sys.platform != "win32", reason="Tool hub startup scripts are PowerShell-first")
def test_dry_run_applies_profile_max_activation_phase_filter() -> None:
    fixture_dir = REPO_ROOT / ".orchestration" / "tool-hub" / "test-fixtures" / uuid4().hex
    fixture_dir.mkdir(parents=True, exist_ok=True)

    registry_relative = str(fixture_dir.relative_to(REPO_ROOT) / "registry.json").replace("\\", "/")
    profiles_relative = str(fixture_dir.relative_to(REPO_ROOT) / "profiles.json").replace("\\", "/")

    registry_payload = {
        "schema_version": 1,
        "tools": [
            {
                "id": "phase-one-tool",
                "display_name": "Phase One Tool",
                "domain": "core-platform",
                "repo_path": ".",
                "enabled": True,
                "shell": "powershell",
                "command": "Write-Output 'phase-one'",
                "health_probe": {"type": "process"},
                "activation_phase": 1,
            },
            {
                "id": "phase-two-tool",
                "display_name": "Phase Two Tool",
                "domain": "core-platform",
                "repo_path": ".",
                "enabled": True,
                "shell": "powershell",
                "command": "Write-Output 'phase-two'",
                "health_probe": {"type": "process"},
                "activation_phase": 2,
            },
        ],
    }
    profiles_payload = {
        "schema_version": 1,
        "profiles": [
            {
                "id": "phase-one-only",
                "include_domains": ["core-platform"],
                "max_activation_phase": 1,
                "exclude_tool_ids": [],
            }
        ],
    }

    (fixture_dir / "registry.json").write_text(json.dumps(registry_payload), encoding="utf-8")
    (fixture_dir / "profiles.json").write_text(json.dumps(profiles_payload), encoding="utf-8")

    result = _run_start(
        "dry-run",
        "phase-one-only",
        registry_path=registry_relative,
        profiles_path=profiles_relative,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8-sig"))
    tools = {tool["id"]: tool for tool in payload.get("tools", [])}

    assert tools["phase-one-tool"]["enabled"] is True
    assert tools["phase-two-tool"]["enabled"] is False

    shutil.rmtree(fixture_dir, ignore_errors=True)
