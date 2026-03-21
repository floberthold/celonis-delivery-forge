#!/usr/bin/env python
"""Seed forum insights and move them to triaged in one run.

Usage:
  .\\.venv\\Scripts\\python scripts\\seed_forum_insights.py \
    --base-url http://127.0.0.1:8000 \
    --created-by <person-uuid> \
    --actor-id <person-uuid>
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from urllib import error, request


def _request_json(method: str, url: str, payload: dict | None = None) -> dict:
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    req = request.Request(url=url, method=method.upper(), data=body, headers=headers)
    try:
        with request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {method} {url}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Connection error for {method} {url}: {exc.reason}") from exc


def _week_label() -> str:
    now = datetime.now(timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _seed_rows() -> list[dict]:
    return [
        {
            "topic": "ML Workbench",
            "thread_title": "Notebook scheduling fails after environment upgrade",
            "source_url": "https://support.celonis.com/s/su-search#searchString=MLWB",
            "problem_summary": "Users report scheduled notebook runs failing after runtime image updates.",
            "proposed_action": "Add preflight checks for runtime/image compatibility before scheduling runs.",
            "impact_score": 4,
            "confidence_score": 3,
        },
        {
            "topic": "Data Integration",
            "thread_title": "Extractor retry behavior unclear on transient API failures",
            "source_url": "https://support.celonis.com/s/su-search#searchString=data%20integration",
            "problem_summary": "Forum questions indicate inconsistent expectations around retry windows.",
            "proposed_action": "Document and expose retry policy defaults in integration diagnostics.",
            "impact_score": 4,
            "confidence_score": 4,
        },
        {
            "topic": "Data Jobs and Scheduling",
            "thread_title": "Job chain timing drift across timezones",
            "source_url": "https://support.celonis.com/s/su-search#searchString=schedule",
            "problem_summary": "Teams see execution offsets when schedules are moved across regional admins.",
            "proposed_action": "Track timezone metadata per schedule and validate on update.",
            "impact_score": 3,
            "confidence_score": 3,
        },
        {
            "topic": "Process Mining and OCPM",
            "thread_title": "Object-centric model joins create unexpected duplicates",
            "source_url": "https://support.celonis.com/s/su-search#searchString=OCPM",
            "problem_summary": "Multiple users struggle with duplicate records from object link modeling.",
            "proposed_action": "Add modeling checklist and duplicate-detection diagnostics in intake review.",
            "impact_score": 5,
            "confidence_score": 3,
        },
        {
            "topic": "Governance and Permissions",
            "thread_title": "Role scope confusion for cross-space reviews",
            "source_url": "https://support.celonis.com/s/su-search#searchString=permissions",
            "problem_summary": "Forum posts show repeated confusion about reviewer rights in multi-space setups.",
            "proposed_action": "Introduce permission preflight and clear role mismatch hints.",
            "impact_score": 4,
            "confidence_score": 4,
        },
        {
            "topic": "PQL and Performance",
            "thread_title": "Slow KPIs with nested CASE over large event logs",
            "source_url": "https://support.celonis.com/s/su-search#searchString=PQL%20performance",
            "problem_summary": "Performance degradation appears when complex PQL patterns are used at scale.",
            "proposed_action": "Collect and publish reusable optimization snippets for high-cost KPI patterns.",
            "impact_score": 5,
            "confidence_score": 4,
        },
        {
            "topic": "Studio and Package Operations",
            "thread_title": "Package publish rollback expectations",
            "source_url": "https://support.celonis.com/s/su-search#searchString=Studio%20package",
            "problem_summary": "Users ask for safer rollback patterns after failed package promotion.",
            "proposed_action": "Add runbook guidance and approval checkpoint before publish operations.",
            "impact_score": 3,
            "confidence_score": 3,
        },
        {
            "topic": "Data Integration",
            "thread_title": "Incremental load watermark handling with late-arriving data",
            "source_url": "https://support.celonis.com/s/su-search#searchString=incremental%20load",
            "problem_summary": "Late-arriving records are missed in several integration patterns discussed.",
            "proposed_action": "Capture a watermark strategy template and validation checks.",
            "impact_score": 4,
            "confidence_score": 3,
        },
        {
            "topic": "ML Workbench",
            "thread_title": "Dependency pinning for reproducible notebook runs",
            "source_url": "https://support.celonis.com/s/su-search#searchString=notebook%20dependency",
            "problem_summary": "Reproducibility issues surface when dependency versions drift between runs.",
            "proposed_action": "Store dependency lock metadata with each execution summary.",
            "impact_score": 4,
            "confidence_score": 4,
        },
        {
            "topic": "Governance and Permissions",
            "thread_title": "Audit trail requirements for production fixes",
            "source_url": "https://support.celonis.com/s/su-search#searchString=audit",
            "problem_summary": "Support threads emphasize traceability for urgent production changes.",
            "proposed_action": "Require changelog metadata and actor attribution on every status transition.",
            "impact_score": 5,
            "confidence_score": 4,
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed and triage forum insights via API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--created-by", required=True, help="UUID of the creating person")
    parser.add_argument("--actor-id", required=True, help="UUID used for triage update activity")
    parser.add_argument("--owner-id", default=None)
    parser.add_argument("--reviewer-id", default=None)
    parser.add_argument("--target-week", default=_week_label())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = _seed_rows()
    if args.dry_run:
        print(f"Dry run: would create {len(rows)} insights for target week {args.target_week}.")
        for idx, row in enumerate(rows, start=1):
            print(f"{idx:02d}. {row['topic']} | {row['thread_title']}")
        return 0

    base_url = args.base_url.rstrip("/")
    created_ids: list[str] = []

    for row in rows:
        create_payload = {
            **row,
            "created_by": args.created_by,
            "owner_id": args.owner_id,
            "reviewer_id": args.reviewer_id,
            "target_week": args.target_week,
        }
        created = _request_json("POST", f"{base_url}/forum-insights/", create_payload)
        insight_id = created["id"]

        _request_json(
            "PATCH",
            f"{base_url}/forum-insights/{insight_id}",
            {
                "status": "triaged",
                "actor_id": args.actor_id,
                "last_reviewed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        created_ids.append(insight_id)
        print(f"Created and triaged insight: {insight_id} | {row['thread_title']}")

    print(f"Done. Seeded and triaged {len(created_ids)} forum insights.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())