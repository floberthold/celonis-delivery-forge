#!/usr/bin/env python
"""Append or update one Weekly Intake Log row in the forum roadmap file.

Usage:
  .\\.venv\\Scripts\\python scripts\\update_forum_intake_log.py \
    --week 2026-W13 \
    --reviewer "Delivery Forge team" \
    --search-terms "MLWB, integration, performance, governance" \
    --threads-scanned 10 \
    --ideas-added 10 \
    --blockers "none"
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def _week_label() -> str:
    now = datetime.now(timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _normalize_cell(value: str) -> str:
    return value.replace("|", "/").strip()


def _build_row(
    *, week: str, reviewer: str, search_terms: str, threads_scanned: int, ideas_added: int, blockers: str
) -> str:
    return (
        f"| {week} | {_normalize_cell(reviewer)} | {_normalize_cell(search_terms)} "
        f"| {threads_scanned} | {ideas_added} | {_normalize_cell(blockers)} |"
    )


def _update_intake_table(content: str, new_row: str, week: str) -> str:
    marker = "## Weekly Intake Log"
    marker_idx = content.find(marker)
    if marker_idx == -1:
        raise RuntimeError("Could not find '## Weekly Intake Log' section.")

    lines = content.splitlines()

    start = None
    for i, line in enumerate(lines):
        if line.strip() == marker:
            start = i
            break
    if start is None:
        raise RuntimeError("Could not locate intake log section line index.")

    table_start = None
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("| Week | Reviewer | Search Terms | Threads Scanned | Ideas Added | Blockers |"):
            table_start = i
            break
    if table_start is None:
        raise RuntimeError("Could not find intake log table header.")

    data_start = table_start + 2
    data_end = data_start
    while data_end < len(lines) and lines[data_end].startswith("|"):
        data_end += 1

    week_prefix = f"| {week} |"
    updated = False
    for i in range(data_start, data_end):
        if lines[i].startswith(week_prefix):
            lines[i] = new_row
            updated = True
            break

    if not updated:
        lines.insert(data_end, new_row)

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Weekly Intake Log row in forum roadmap.")
    parser.add_argument(
        "--roadmap-path",
        default="docs/celonis-forum-insights-roadmap.md",
        help="Path to forum roadmap markdown file.",
    )
    parser.add_argument("--week", default=_week_label())
    parser.add_argument("--reviewer", default="Delivery Forge team")
    parser.add_argument("--search-terms", required=True)
    parser.add_argument("--threads-scanned", type=int, required=True)
    parser.add_argument("--ideas-added", type=int, required=True)
    parser.add_argument("--blockers", default="none")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.threads_scanned < 0 or args.ideas_added < 0:
        raise RuntimeError("threads-scanned and ideas-added must be >= 0")

    roadmap_path = Path(args.roadmap_path)
    if not roadmap_path.exists():
        raise RuntimeError(f"Roadmap file not found: {roadmap_path}")

    new_row = _build_row(
        week=args.week,
        reviewer=args.reviewer,
        search_terms=args.search_terms,
        threads_scanned=args.threads_scanned,
        ideas_added=args.ideas_added,
        blockers=args.blockers,
    )

    original = roadmap_path.read_text(encoding="utf-8")
    updated = _update_intake_table(original, new_row, args.week)

    if args.dry_run:
        print("Dry run: would write row:")
        print(new_row)
        return 0

    roadmap_path.write_text(updated, encoding="utf-8")
    print(f"Updated intake log row for week {args.week}: {roadmap_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())