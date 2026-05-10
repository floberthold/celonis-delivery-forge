from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


TOOL_ID = "agentic-code-analysis-mcp"
DEFAULT_METRICS_PATH = ".orchestration/code-analysis/latest_metrics.json"
DEFAULT_LLM_PROMPT_PATH = ".orchestration/code-analysis/next-improvements-prompt.md"

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".toml",
    ".ini",
    ".mako",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
    ".txt",
}

BASE_EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".venv-1",
    "venv",
    "node_modules",
    "dist",
    "build",
    "docs_site",
    ".orchestration",
    ".worktrees",
}

REPORT_FILES = [
    "CODE_ANALYSIS_SUMMARY.md",
    "DELIVERABLES_MANIFEST.md",
    "QUICK_REFERENCE.md",
    "READ_ME_FIRST.md",
    "REPOSITORY_ANALYSIS.md",
    "docs/code-analysis-complete-guide.md",
    "docs/code-quality-and-cleanup-roadmap.md",
    "docs/codebase-metrics-and-analysis.md",
    "docs/documentation-consolidation-plan.md",
    "docs/refactoring-ui-routes.md",
    "docs/service-layer-restructuring.md",
]


@dataclass
class ScanStats:
    text_files: int
    text_lines: int
    py_files: int
    py_lines: int
    top_dirs_by_lines: list[tuple[str, int]]
    top_py_files: list[tuple[str, int]]
    src_py_files: int
    src_py_lines: int
    tests_py_files: int
    tests_py_lines: int


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scan_repo(root: Path, active_view: bool) -> ScanStats:
    text_files = 0
    text_lines = 0
    py_files = 0
    py_lines = 0

    top_dirs: dict[str, int] = {}
    top_py: list[tuple[str, int]] = []
    src_py_files = 0
    src_py_lines = 0
    tests_py_files = 0
    tests_py_lines = 0

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)

        filtered_dirs = []
        for directory_name in dirnames:
            if directory_name in BASE_EXCLUDE_DIRS:
                continue
            if active_view and directory_name in {"external resources", "uploads"}:
                continue
            filtered_dirs.append(directory_name)
        dirnames[:] = filtered_dirs

        for filename in filenames:
            absolute_path = Path(dirpath) / filename
            relative_path = absolute_path.relative_to(root).as_posix()
            extension = absolute_path.suffix.lower()

            if extension not in TEXT_EXTENSIONS:
                continue

            if active_view and relative_path.startswith("data/generated/"):
                continue

            try:
                with absolute_path.open("r", encoding="utf-8", errors="ignore") as handle:
                    line_count = sum(1 for _ in handle)
            except OSError:
                continue

            top_key = relative_path.split("/")[0]
            top_dirs[top_key] = top_dirs.get(top_key, 0) + line_count
            text_files += 1
            text_lines += line_count

            if extension == ".py":
                py_files += 1
                py_lines += line_count
                top_py.append((relative_path, line_count))

                if relative_path.startswith("src/"):
                    src_py_files += 1
                    src_py_lines += line_count
                if relative_path.startswith("tests/"):
                    tests_py_files += 1
                    tests_py_lines += line_count

    top_dirs_sorted = sorted(top_dirs.items(), key=lambda item: item[1], reverse=True)[:12]
    top_py_sorted = sorted(top_py, key=lambda item: item[1], reverse=True)[:20]

    return ScanStats(
        text_files=text_files,
        text_lines=text_lines,
        py_files=py_files,
        py_lines=py_lines,
        top_dirs_by_lines=top_dirs_sorted,
        top_py_files=top_py_sorted,
        src_py_files=src_py_files,
        src_py_lines=src_py_lines,
        tests_py_files=tests_py_files,
        tests_py_lines=tests_py_lines,
    )


def _hotspot_lines(root: Path) -> int:
    hotspot = root / "src" / "foundry" / "api" / "routes" / "ui" / "__init__.py"
    if not hotspot.exists():
        return 0
    with hotspot.open("r", encoding="utf-8", errors="ignore") as handle:
        return sum(1 for _ in handle)


def _to_millions(value: int) -> str:
    return f"{value / 1_000_000:.2f}M"


def _replace_source_and_tests_table(text: str, src_files: int, src_lines: int, tests_files: int, tests_lines: int) -> str:
    text = re.sub(
        r"(\| \*\*Source Code\*\* \| )\d[\d,]*( \| )\d[\d,]*( \|)",
        rf"\g<1>{src_files:,}\g<2>{src_lines:,}\g<3>",
        text,
    )
    text = re.sub(
        r"(\| \*\*Tests\*\* \| )\d[\d,]*( \| )\d[\d,]*( \|)",
        rf"\g<1>{tests_files:,}\g<2>{tests_lines:,}\g<3>",
        text,
    )
    text = re.sub(
        r"Total Production Python: \d[\d,]* lines across \d[\d,]* files",
        f"Total Production Python: {src_lines:,} lines across {src_files:,} files",
        text,
    )
    return text


def _update_reports(root: Path, full_stats: ScanStats, active_stats: ScanStats, external_lines: int, hotspot_lines: int) -> dict:
    changed_files = []

    replacements = {
        "src/foundry/api/routes/ui.py": "src/foundry/api/routes/ui/__init__.py",
        "ui.py (9,810 lines)": f"ui/__init__.py ({hotspot_lines:,} lines)",
        "9,810 lines": f"{hotspot_lines:,} lines",
        "4.3M lines": f"{_to_millions(external_lines)} lines",
        "5.5M lines of Python code": f"{_to_millions(full_stats.text_lines)} text lines",
        "48,254 files": f"{full_stats.text_files:,} text files",
        "24.7M lines": f"{_to_millions(full_stats.text_lines)} text lines",
        "26,709 lines": f"{active_stats.src_py_lines:,} lines",
        "8,281 lines": f"{active_stats.tests_py_lines:,} lines",
        "9,810": f"{hotspot_lines:,}",
    }

    for relative_path in REPORT_FILES:
        path = root / relative_path
        if not path.exists():
            continue

        original = path.read_text(encoding="utf-8", errors="ignore")
        updated = original

        for old, new in replacements.items():
            updated = updated.replace(old, new)

        updated = _replace_source_and_tests_table(
            updated,
            src_files=active_stats.src_py_files,
            src_lines=active_stats.src_py_lines,
            tests_files=active_stats.tests_py_files,
            tests_lines=active_stats.tests_py_lines,
        )

        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed_files.append(relative_path)

    return {"changed_files": changed_files, "changed_count": len(changed_files)}


def _generate_llm_prompt(
    root: Path,
    active_stats: ScanStats,
    full_stats: ScanStats,
    external_lines: int,
    hotspot_lines: int,
    output_path: Path,
) -> None:
    top_py_lines = "\n".join(
        f"- {path}: {lines:,}"
        for path, lines in active_stats.top_py_files[:12]
    )
    top_dir_lines = "\n".join(
        f"- {name}: {lines:,}"
        for name, lines in active_stats.top_dirs_by_lines[:10]
    )

    content = f"""# LLM Prompt: Next Improvements for Celonis Delivery Forge

Use this prompt in Copilot/LLM to get prioritized next-step suggestions.

---

You are reviewing a refactored codebase and must suggest the next best improvements.
Prioritize defects, complexity risk, maintainability risk, and missing tests.

## Repository Baseline (auto-generated)
- Full text files: {full_stats.text_files:,}
- Full text lines: {full_stats.text_lines:,}
- Active text files: {active_stats.text_files:,}
- Active text lines: {active_stats.text_lines:,}
- Active Python files: {active_stats.py_files:,}
- Active Python lines: {active_stats.py_lines:,}
- External resources lines: {external_lines:,}
- Primary UI hotspot: src/foundry/api/routes/ui/__init__.py ({hotspot_lines:,} lines)

## Active Top Directories by Lines
{top_dir_lines}

## Active Largest Python Files
{top_py_lines}

## Existing Goal
Re-run code analysis and report generation reliably across agents, then decide what to improve next.

## Required Output
1. Top 10 improvements ranked by severity and ROI.
2. For each item: why it matters, affected file(s), and a safe incremental implementation plan.
3. Test plan additions required before and after each change.
4. Any regressions to watch for in UI routing, service domain boundaries, and tool-hub contracts.
5. A one-sprint and two-sprint execution split.

Keep recommendations concrete and implementation-ready.
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def _build_payload(
    root: Path,
    full_stats: ScanStats,
    active_stats: ScanStats,
    external_lines: int,
    hotspot_lines: int,
    updated_reports: dict | None,
    metrics_path: Path,
    llm_prompt_path: Path,
) -> dict:
    return {
        "tool_id": TOOL_ID,
        "status": "ok",
        "mode": "live",
        "timestamp_utc": _now_utc(),
        "repo_root": str(root),
        "full_view": {
            "text_files": full_stats.text_files,
            "text_lines": full_stats.text_lines,
            "python_files": full_stats.py_files,
            "python_lines": full_stats.py_lines,
            "top_dirs_by_lines": full_stats.top_dirs_by_lines,
        },
        "active_view": {
            "text_files": active_stats.text_files,
            "text_lines": active_stats.text_lines,
            "python_files": active_stats.py_files,
            "python_lines": active_stats.py_lines,
            "src_python_files": active_stats.src_py_files,
            "src_python_lines": active_stats.src_py_lines,
            "tests_python_files": active_stats.tests_py_files,
            "tests_python_lines": active_stats.tests_py_lines,
            "top_dirs_by_lines": active_stats.top_dirs_by_lines,
            "top_python_files": active_stats.top_py_files,
        },
        "external_resources_lines": external_lines,
        "hotspot": {
            "path": "src/foundry/api/routes/ui/__init__.py",
            "lines": hotspot_lines,
        },
        "artifacts": {
            "metrics_json": str(metrics_path),
            "llm_prompt": str(llm_prompt_path),
        },
        "reports_update": updated_reports or {"changed_files": [], "changed_count": 0},
    }


def _write_metrics_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _describe_payload() -> dict:
    return {
        "tool_id": TOOL_ID,
        "status": "ok",
        "mode": "live",
        "commands": ["describe", "health", "run"],
        "timestamp_utc": _now_utc(),
        "report_files": REPORT_FILES,
        "message": "Re-runs codebase analysis, refreshes report metrics, and emits an LLM next-improvements brief.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog=TOOL_ID)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("describe")
    subparsers.add_parser("health")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--repo-root", default=".")
    run_parser.add_argument("--metrics-json", default=DEFAULT_METRICS_PATH)
    run_parser.add_argument("--llm-prompt", default=DEFAULT_LLM_PROMPT_PATH)
    run_parser.add_argument("--update-reports", dest="update_reports", action="store_true", default=True)
    run_parser.add_argument("--no-update-reports", dest="update_reports", action="store_false")
    run_parser.add_argument("--emit-llm-brief", dest="emit_llm_brief", action="store_true", default=True)
    run_parser.add_argument("--no-emit-llm-brief", dest="emit_llm_brief", action="store_false")

    args = parser.parse_args()
    command = args.command or "describe"

    if command in {"describe", "health"}:
        payload = _describe_payload()
        payload["command"] = command
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")
        return 0

    if command != "run":
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

    root = Path(args.repo_root).resolve()
    metrics_path = (root / args.metrics_json).resolve()
    llm_prompt_path = (root / args.llm_prompt).resolve()

    full_stats = _scan_repo(root, active_view=False)
    active_stats = _scan_repo(root, active_view=True)
    external_lines = dict(full_stats.top_dirs_by_lines).get("external resources", 0)
    hotspot_lines = _hotspot_lines(root)

    updated_reports = None
    if args.update_reports:
        updated_reports = _update_reports(
            root,
            full_stats=full_stats,
            active_stats=active_stats,
            external_lines=external_lines,
            hotspot_lines=hotspot_lines,
        )

    if args.emit_llm_brief:
        _generate_llm_prompt(
            root,
            active_stats=active_stats,
            full_stats=full_stats,
            external_lines=external_lines,
            hotspot_lines=hotspot_lines,
            output_path=llm_prompt_path,
        )

    payload = _build_payload(
        root=root,
        full_stats=full_stats,
        active_stats=active_stats,
        external_lines=external_lines,
        hotspot_lines=hotspot_lines,
        updated_reports=updated_reports,
        metrics_path=metrics_path,
        llm_prompt_path=llm_prompt_path,
    )
    _write_metrics_json(metrics_path, payload)

    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
