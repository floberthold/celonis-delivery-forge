from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from foundry.models import CelonisSnapshot


_FAMILY_SPECS = [
    {
        "key": "spaces",
        "label": "Spaces",
        "count_key": "spaces",
        "coverage_key": "spaces",
        "pycelonis_domain": "studio.space",
    },
    {
        "key": "packages",
        "label": "Packages",
        "count_key": "packages",
        "coverage_key": "packages",
        "pycelonis_domain": "studio.content_node.package",
    },
    {
        "key": "package_assets",
        "label": "Package Assets",
        "count_from_task_types": True,
        "coverage_key": "package_assets",
        "pycelonis_domain": "studio.content_node.(kpi|view|analysis|skill|action_flow|annotation_builder)",
    },
    {
        "key": "data_models",
        "label": "Data Models",
        "count_key": "data_models",
        "coverage_key": "data_models",
        "pycelonis_domain": "data_integration.data_model",
    },
    {
        "key": "jobs",
        "label": "Jobs",
        "count_key": "jobs",
        "coverage_key": "jobs",
        "pycelonis_domain": "data_integration.job",
    },
    {
        "key": "knowledge_models",
        "label": "Knowledge Models",
        "count_key": "knowledge_models",
        "coverage_key": "knowledge_models",
        "pycelonis_domain": "studio.content_node.knowledge_model",
    },
    {
        "key": "apps",
        "label": "Apps",
        "count_key": "apps",
        "coverage_key": "apps",
        "pycelonis_domain": "apps",
    },
    {
        "key": "data_pools",
        "label": "Data Pools",
        "count_key": "data_pools",
        "coverage_key": "data_pools",
        "pycelonis_domain": "data_integration.data_pool",
    },
    {
        "key": "transformations",
        "label": "Transformations",
        "count_key": "transformations",
        "coverage_key": "transformations_global",
        "pycelonis_domain": "data_integration.task/transformation",
    },
]


def _as_int(value: Any) -> int:
    return value if isinstance(value, int) else 0


def _status_from(*, count: int, attempted: int, hits: int) -> str:
    if count > 0:
        return "covered"
    if attempted > 0 and hits == 0:
        return "permission-limited"
    return "empty"


def build_snapshot_coverage_report(snapshot: CelonisSnapshot) -> dict[str, Any]:
    summary_raw = snapshot.summary_json if isinstance(snapshot.summary_json, dict) else {}
    summary: dict[str, Any] = dict(summary_raw)

    task_types_raw = summary.get("task_types")
    task_types: dict[str, Any] = task_types_raw if isinstance(task_types_raw, dict) else {}

    coverage_raw = summary.get("coverage")
    coverage: dict[str, Any] = coverage_raw if isinstance(coverage_raw, dict) else {}

    families: list[dict[str, Any]] = []
    for spec in _FAMILY_SPECS:
        if spec.get("count_from_task_types"):
            count = sum(_as_int(value) for value in task_types.values())
        else:
            count = _as_int(summary.get(spec["count_key"]))

        cov_raw = coverage.get(spec["coverage_key"])
        cov: dict[str, Any] = cov_raw if isinstance(cov_raw, dict) else {}
        endpoints_attempted = _as_int(cov.get("endpoints_attempted"))
        endpoints_with_data = _as_int(cov.get("endpoints_with_data"))

        families.append(
            {
                "key": spec["key"],
                "label": spec["label"],
                "status": _status_from(
                    count=count,
                    attempted=endpoints_attempted,
                    hits=endpoints_with_data,
                ),
                "count": count,
                "endpoints_attempted": endpoints_attempted,
                "endpoints_with_data": endpoints_with_data,
                "pycelonis_domain": spec["pycelonis_domain"],
            }
        )

    covered = sum(1 for row in families if row["status"] == "covered")
    permission_limited = sum(1 for row in families if row["status"] == "permission-limited")
    empty = sum(1 for row in families if row["status"] == "empty")

    return {
        "snapshot_id": str(snapshot.id),
        "client_id": str(snapshot.client_id),
        "generated_at": datetime.utcnow().isoformat(),
        "statuses": {
            "covered": covered,
            "permission_limited": permission_limited,
            "empty": empty,
        },
        "task_types": task_types,
        "families": families,
        "raw_summary": summary,
    }


def build_snapshot_coverage_filename(snapshot_id: UUID) -> str:
    return f"snapshot_{snapshot_id}_coverage.json"
