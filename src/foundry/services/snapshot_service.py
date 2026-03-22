"""Celonis Snapshot Service — pulls implementation artefacts from a remote tenant."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from sqlmodel import Session, select

from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import (
    CelonisConnection,
    CelonisSnapshot,
    SnapshotChangeType,
    SnapshotApp,
    SnapshotDataModel,
    SnapshotDataPool,
    SnapshotJob,
    SnapshotKnowledgeModel,
    SnapshotPackage,
    SnapshotRunStatus,
    SnapshotSpace,
    SnapshotTask,
    SnapshotTransformation,
)
from foundry.settings import get_settings
from foundry.services.snapshot_git_service import materialize_celonis_snapshot_git_history

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _content_hash(raw: dict) -> str:
    blob = json.dumps(raw, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _get_connection(
    session: Session,
    client_id: UUID,
    *,
    organization_id: UUID | None = None,
) -> CelonisConnection | None:
    filters = [
        CelonisConnection.client_id == client_id,
        CelonisConnection.is_active == True,  # noqa: E712
    ]
    if organization_id is not None:
        filters.append(CelonisConnection.organization_id == organization_id)
    stmt = select(CelonisConnection).where(*filters)
    return session.exec(stmt).first()


def _prev_task_hashes(session: Session, client_id: UUID) -> dict[str, str]:
    """Return {task_id: content_hash} from the most recent completed snapshot."""
    rows = session.exec(
        select(CelonisSnapshot).where(
            CelonisSnapshot.client_id == client_id,
            CelonisSnapshot.status == SnapshotRunStatus.completed,
        )
    ).all()
    prev = sorted(rows, key=lambda row: row.created_at, reverse=True)[0] if rows else None
    if prev is None:
        return {}
    tasks = session.exec(
        select(SnapshotTask).where(SnapshotTask.snapshot_id == prev.id)
    ).all()
    return {t.task_id: t.content_hash or "" for t in tasks}


def _prev_package_ids(session: Session, client_id: UUID) -> set[str]:
    rows = session.exec(
        select(CelonisSnapshot).where(
            CelonisSnapshot.client_id == client_id,
            CelonisSnapshot.status == SnapshotRunStatus.completed,
        )
    ).all()
    prev = sorted(rows, key=lambda row: row.created_at, reverse=True)[0] if rows else None
    if prev is None:
        return set()
    pkgs = session.exec(
        select(SnapshotPackage).where(SnapshotPackage.snapshot_id == prev.id)
    ).all()
    return {p.package_id for p in pkgs}


def _prev_entity_ids(
    session: Session,
    client_id: UUID,
    model_class,
    id_attr: str,
) -> set[str]:
    """Return the set of entity IDs from the most-recent completed snapshot."""
    rows = session.exec(
        select(CelonisSnapshot).where(
            CelonisSnapshot.client_id == client_id,
            CelonisSnapshot.status == SnapshotRunStatus.completed,
        )
    ).all()
    prev = sorted(rows, key=lambda row: row.created_at, reverse=True)[0] if rows else None
    if prev is None:
        return set()
    entities = session.exec(
        select(model_class).where(model_class.snapshot_id == prev.id)  # type: ignore[attr-defined]
    ).all()
    return {str(getattr(e, id_attr)) for e in entities}


# ---------------------------------------------------------------------------
# Studio extraction helpers
# ---------------------------------------------------------------------------

_LIST_FALLBACK_KEYS = (
    "items",
    "results",
    "value",
    "content",
)


def _extract_items(payload: Any, list_keys: tuple[str, ...]) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in (*list_keys, *_LIST_FALLBACK_KEYS):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _next_query(payload: dict[str, Any], page_number: int) -> dict[str, Any] | None:
    token = payload.get("nextPageToken") or payload.get("next_page_token")
    if isinstance(token, str) and token.strip():
        return {"pageToken": token.strip()}

    cursor = payload.get("nextCursor") or payload.get("cursor")
    if isinstance(cursor, str) and cursor.strip():
        return {"cursor": cursor.strip()}

    current_page = payload.get("page") or payload.get("pageNumber")
    total_pages = payload.get("totalPages") or payload.get("pageCount")
    if isinstance(current_page, int) and isinstance(total_pages, int) and current_page < total_pages:
        return {"page": current_page + 1}

    has_next = payload.get("hasNext")
    if has_next is True:
        return {"page": page_number + 1}

    return None


def _fetch_endpoint_items(
    gw: CelonisGateway,
    base_url: str,
    path: str,
    *,
    list_keys: tuple[str, ...],
    token_override: str | None = None,
    max_pages: int = 50,
) -> tuple[list[dict], bool]:
    items: list[dict] = []
    query: dict[str, Any] = {}
    page_number = 1

    for _ in range(max_pages):
        endpoint = path
        if query:
            endpoint = f"{path}?{urlencode(query)}"
        extract_kwargs: dict[str, Any] = {}
        if token_override:
            extract_kwargs["token_override"] = token_override
        result = gw.extract_full(
            tenant_base_url=base_url,
            source_path=endpoint,
            **extract_kwargs,
        )
        if not result.ok or not result.body:
            break

        payload = json.loads(result.body)
        items.extend(_extract_items(payload, list_keys))
        payload_dict = _safe_dict(payload)
        if not payload_dict:
            break

        next_q = _next_query(payload_dict, page_number)
        if not next_q:
            break
        query = next_q
        page_number += 1

    return items, bool(items)


def _collect_entities(
    gw: CelonisGateway,
    base_url: str,
    *,
    endpoints: tuple[str, ...],
    list_keys: tuple[str, ...] = (),
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    merged: list[dict] = []
    attempted = 0
    successful = 0
    for endpoint in endpoints:
        attempted += 1
        rows, ok = _fetch_endpoint_items(
            gw,
            base_url,
            endpoint,
            list_keys=list_keys,
            token_override=token_override,
        )
        if ok:
            successful += 1
            merged.extend(rows)
    return merged, {"endpoints_attempted": attempted, "endpoints_with_data": successful}


def _dedupe_by_preferred_keys(rows: list[dict], preferred_keys: tuple[str, ...]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        key_value = ""
        for key in preferred_keys:
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                key_value = f"{key}:{value.strip()}"
                break
        if not key_value:
            key_value = json.dumps(row, sort_keys=True, default=str)
        if key_value in seen:
            continue
        seen.add(key_value)
        out.append(row)
    return out

def _extract_spaces(
    gw: CelonisGateway,
    base_url: str,
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    rows, stats = _collect_entities(
        gw,
        base_url,
        endpoints=("/package-manager/api/spaces", "/studio/api/spaces"),
        list_keys=("spaces", "data"),
        token_override=token_override,
    )
    return _dedupe_by_preferred_keys(rows, ("id", "key", "name")), stats


def _extract_packages(
    gw: CelonisGateway,
    base_url: str,
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    rows, stats = _collect_entities(
        gw,
        base_url,
        endpoints=("/package-manager/api/packages",),
        list_keys=("packages", "data"),
        token_override=token_override,
    )
    return _dedupe_by_preferred_keys(rows, ("id", "key", "name")), stats


def _extract_package_tasks(
    gw: CelonisGateway,
    base_url: str,
    package_key: str,
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    rows, stats = _collect_entities(
        gw,
        base_url,
        endpoints=(f"/package-manager/api/packages/{package_key}/assets",),
        list_keys=("assets", "items", "data"),
        token_override=token_override,
    )
    return _dedupe_by_preferred_keys(rows, ("id", "key", "name")), stats


def _extract_data_models(
    gw: CelonisGateway,
    base_url: str,
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    rows, stats = _collect_entities(
        gw,
        base_url,
        endpoints=("/process-mining/api/data-models", "/integration/api/v1/data-models"),
        list_keys=("dataModels", "data"),
        token_override=token_override,
    )
    return _dedupe_by_preferred_keys(rows, ("id", "name")), stats


def _extract_jobs(
    gw: CelonisGateway,
    base_url: str,
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    rows, stats = _collect_entities(
        gw,
        base_url,
        endpoints=("/integration/api/v1/jobs", "/integration/api/jobs"),
        list_keys=("jobs", "data"),
        token_override=token_override,
    )
    return _dedupe_by_preferred_keys(rows, ("id", "name")), stats


def _extract_knowledge_models(
    gw: CelonisGateway,
    base_url: str,
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    rows, stats = _collect_entities(
        gw,
        base_url,
        endpoints=("/knowledge-model/api/knowledge-models", "/semantic-layer/api/knowledge-models"),
        list_keys=("knowledgeModels", "data"),
        token_override=token_override,
    )
    return _dedupe_by_preferred_keys(rows, ("id", "key", "name")), stats


def _extract_apps(
    gw: CelonisGateway,
    base_url: str,
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    rows, stats = _collect_entities(
        gw,
        base_url,
        endpoints=("/apps/api/packages", "/apps/api/apps"),
        list_keys=("packages", "apps", "data"),
        token_override=token_override,
    )
    return _dedupe_by_preferred_keys(rows, ("id", "key", "name")), stats


def _extract_data_pools(
    gw: CelonisGateway,
    base_url: str,
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    rows, stats = _collect_entities(
        gw,
        base_url,
        endpoints=("/integration/api/pools", "/integration/api/v1/pools"),
        list_keys=("pools", "data"),
        token_override=token_override,
    )
    return _dedupe_by_preferred_keys(rows, ("id", "name")), stats


def _extract_transformations(
    gw: CelonisGateway,
    base_url: str,
    pool_id: str | None = None,
    token_override: str | None = None,
) -> tuple[list[dict], dict[str, int]]:
    endpoints = (
        f"/integration/api/v1/pools/{pool_id}/transformations",
        f"/integration/api/pools/{pool_id}/transformations",
    ) if pool_id else (
        "/integration/api/v1/transformations",
        "/integration/api/transformations",
    )
    rows, stats = _collect_entities(
        gw,
        base_url,
        endpoints=endpoints,
        list_keys=("transformations", "data"),
        token_override=token_override,
    )
    return _dedupe_by_preferred_keys(rows, ("id", "name")), stats


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_snapshot(
    session: Session,
    *,
    client_id: UUID,
    triggered_by: UUID,
    organization_id: UUID | None = None,
    token_override: str | None = None,
) -> CelonisSnapshot:
    """Trigger a full snapshot for a client and persist results."""
    conn = _get_connection(session, client_id, organization_id=organization_id)
    if conn is None:
        raise ValueError(f"No active Celonis connection for client {client_id}")

    snap = CelonisSnapshot(
        client_id=client_id,
        triggered_by=triggered_by,
        status=SnapshotRunStatus.running,
        started_at=datetime.utcnow(),
    )
    session.add(snap)
    session.commit()
    session.refresh(snap)

    try:
        gw = CelonisGateway(get_settings())
        base_url = conn.tenant_base_url

        prev_hashes = _prev_task_hashes(session, client_id)
        prev_pkg_ids = _prev_package_ids(session, client_id)
        prev_space_ids = _prev_entity_ids(session, client_id, SnapshotSpace, "space_id")
        prev_app_ids = _prev_entity_ids(session, client_id, SnapshotApp, "app_id")
        prev_pool_ids = _prev_entity_ids(session, client_id, SnapshotDataPool, "pool_id")
        prev_transformation_ids = _prev_entity_ids(session, client_id, SnapshotTransformation, "transformation_id")

        # Fetch everything in parallel (sequential for simplicity; all are independent)
        raw_spaces, spaces_stats = _extract_spaces(gw, base_url, token_override=token_override)
        raw_packages, packages_stats = _extract_packages(gw, base_url, token_override=token_override)
        raw_data_models, data_models_stats = _extract_data_models(gw, base_url, token_override=token_override)
        raw_jobs, jobs_stats = _extract_jobs(gw, base_url, token_override=token_override)
        raw_knowledge_models, kms_stats = _extract_knowledge_models(gw, base_url, token_override=token_override)
        raw_apps, apps_stats = _extract_apps(gw, base_url, token_override=token_override)
        raw_pools, pools_stats = _extract_data_pools(gw, base_url, token_override=token_override)

        # Global transformations endpoint (falls back gracefully)
        raw_transformations_global, transformations_global_stats = _extract_transformations(
            gw,
            base_url,
            token_override=token_override,
        )

        # Per-pool transformations (for tenants where global endpoint is empty)
        per_pool_transformations: list[dict] = []
        transformation_pool_endpoint_hits = 0
        transformation_pool_endpoint_attempts = 0
        if not raw_transformations_global:
            for pool in raw_pools:
                pid = str(pool.get("id", ""))
                if pid:
                    tf_rows, tf_stats = _extract_transformations(
                        gw,
                        base_url,
                        pid,
                        token_override=token_override,
                    )
                    per_pool_transformations.extend(tf_rows)
                    transformation_pool_endpoint_attempts += tf_stats["endpoints_attempted"]
                    transformation_pool_endpoint_hits += tf_stats["endpoints_with_data"]
        raw_transformations = _dedupe_by_preferred_keys(
            raw_transformations_global or per_pool_transformations,
            ("id", "name"),
        )

        # ---- spaces ----
        for space in raw_spaces:
            space_id = str(space.get("id", ""))
            if not space_id:
                continue
            change = SnapshotChangeType.added if space_id not in prev_space_ids else SnapshotChangeType.unchanged
            session.add(SnapshotSpace(
                snapshot_id=snap.id,
                client_id=client_id,
                space_id=space_id,
                name=space.get("name") or space_id,
                change_type=change,
                raw_json=space,
            ))

        # ---- packages ----
        current_pkg_ids: set[str] = set()
        task_type_counts: dict[str, int] = {}
        package_assets_endpoint_attempts = 0
        package_assets_endpoint_hits = 0
        for pkg in raw_packages:
            pkg_id = str(pkg.get("id", pkg.get("key", "")))
            if not pkg_id:
                continue
            pkg_key = pkg.get("key") or pkg_id
            current_pkg_ids.add(pkg_id)
            change = SnapshotChangeType.added if pkg_id not in prev_pkg_ids else SnapshotChangeType.unchanged
            record = SnapshotPackage(
                snapshot_id=snap.id,
                client_id=client_id,
                package_id=pkg_id,
                name=pkg.get("name") or pkg.get("title") or pkg_id,
                key=pkg_key,
                space_id=str(pkg.get("spaceId", "")) or None,
                space_name=pkg.get("spaceName") or None,
                change_type=change,
                raw_json=pkg,
            )
            session.add(record)

            # ---- tasks/assets inside package ----
            # Every asset type (KPI, VIEW, ANALYSIS, KNOWLEDGE_MODEL_LINK,
            # ACTION_FLOW, ACTION_SKILL, ANNOTATION_BUILDER, SIMULATION_RESULT…)
            # is captured here under SnapshotTask with task_type preserving the type string.
            raw_tasks, task_stats = _extract_package_tasks(
                gw,
                base_url,
                pkg_key,
                token_override=token_override,
            )
            package_assets_endpoint_attempts += task_stats["endpoints_attempted"]
            package_assets_endpoint_hits += task_stats["endpoints_with_data"]
            for task in raw_tasks:
                task_id = str(task.get("id", task.get("key", "")))
                if not task_id:
                    continue
                h = _content_hash(task)
                prev_h = prev_hashes.get(task_id)
                if prev_h is None:
                    task_change = SnapshotChangeType.added
                elif prev_h != h:
                    task_change = SnapshotChangeType.modified
                else:
                    task_change = SnapshotChangeType.unchanged
                task_type = task.get("type") or task.get("assetType") or "unknown"
                task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
                pql = task.get("pqlQuery") or task.get("formulaQuery") or task.get("query") or None
                session.add(SnapshotTask(
                    snapshot_id=snap.id,
                    client_id=client_id,
                    package_id=pkg_id,
                    task_id=task_id,
                    name=task.get("name") or task.get("title") or task_id,
                    task_type=task_type,
                    description=task.get("description") or None,
                    pql_formula=pql,
                    change_type=task_change,
                    content_hash=h,
                    raw_json=task,
                ))

        # ---- data models ----
        for dm in raw_data_models:
            dm_id = str(dm.get("id", ""))
            if not dm_id:
                continue
            session.add(SnapshotDataModel(
                snapshot_id=snap.id,
                client_id=client_id,
                data_model_id=dm_id,
                name=dm.get("name") or dm_id,
                space_id=str(dm.get("spaceId", "")) or None,
                space_name=dm.get("spaceName") or None,
                change_type=SnapshotChangeType.unchanged,
                raw_json=dm,
            ))

        # ---- jobs (data integration / extraction jobs) ----
        for job in raw_jobs:
            job_id = str(job.get("id", ""))
            if not job_id:
                continue
            session.add(SnapshotJob(
                snapshot_id=snap.id,
                client_id=client_id,
                job_id=job_id,
                name=job.get("name") or job_id,
                pool_id=str(job.get("poolId", "")) or None,
                pool_name=job.get("poolName") or None,
                change_type=SnapshotChangeType.unchanged,
                raw_json=job,
            ))

        # ---- knowledge models ----
        for km in raw_knowledge_models:
            km_id = str(km.get("id", ""))
            if not km_id:
                continue
            session.add(SnapshotKnowledgeModel(
                snapshot_id=snap.id,
                client_id=client_id,
                km_id=km_id,
                name=km.get("name") or km_id,
                space_id=str(km.get("spaceId", "")) or None,
                space_name=km.get("spaceName") or None,
                change_type=SnapshotChangeType.unchanged,
                raw_json=km,
            ))

        # ---- apps ----
        for app in raw_apps:
            app_id = str(app.get("id", app.get("key", "")))
            if not app_id:
                continue
            change = SnapshotChangeType.added if app_id not in prev_app_ids else SnapshotChangeType.unchanged
            session.add(SnapshotApp(
                snapshot_id=snap.id,
                client_id=client_id,
                app_id=app_id,
                name=app.get("name") or app.get("title") or app_id,
                space_id=str(app.get("spaceId", "")) or None,
                space_name=app.get("spaceName") or None,
                package_key=app.get("packageKey") or app.get("key") or None,
                change_type=change,
                raw_json=app,
            ))

        # ---- data pools ----
        for pool in raw_pools:
            pool_id = str(pool.get("id", ""))
            if not pool_id:
                continue
            change = SnapshotChangeType.added if pool_id not in prev_pool_ids else SnapshotChangeType.unchanged
            session.add(SnapshotDataPool(
                snapshot_id=snap.id,
                client_id=client_id,
                pool_id=pool_id,
                name=pool.get("name") or pool_id,
                change_type=change,
                raw_json=pool,
            ))

        # ---- transformations ----
        for tf in raw_transformations:
            tf_id = str(tf.get("id", ""))
            if not tf_id:
                continue
            change = SnapshotChangeType.added if tf_id not in prev_transformation_ids else SnapshotChangeType.unchanged
            session.add(SnapshotTransformation(
                snapshot_id=snap.id,
                client_id=client_id,
                transformation_id=tf_id,
                name=tf.get("name") or tf_id,
                pool_id=str(tf.get("poolId", "")) or None,
                pool_name=tf.get("poolName") or None,
                change_type=change,
                raw_json=tf,
            ))

        # ---- finalize ----
        snap.status = SnapshotRunStatus.completed
        snap.finished_at = datetime.utcnow()
        updated_summary = {
            "spaces": len(raw_spaces),
            "packages": len(raw_packages),
            "data_models": len(raw_data_models),
            "jobs": len(raw_jobs),
            "knowledge_models": len(raw_knowledge_models),
            "apps": len(raw_apps),
            "data_pools": len(raw_pools),
            "transformations": len(raw_transformations),
            "task_types": task_type_counts,
            "coverage": {
                "spaces": spaces_stats,
                "packages": packages_stats,
                "package_assets": {
                    "endpoints_attempted": package_assets_endpoint_attempts,
                    "endpoints_with_data": package_assets_endpoint_hits,
                },
                "data_models": data_models_stats,
                "jobs": jobs_stats,
                "knowledge_models": kms_stats,
                "apps": apps_stats,
                "data_pools": pools_stats,
                "transformations_global": transformations_global_stats,
                "transformations_by_pool": {
                    "endpoints_attempted": transformation_pool_endpoint_attempts,
                    "endpoints_with_data": transformation_pool_endpoint_hits,
                },
            },
        }
        snap.summary_json = updated_summary

        # Auto-generate a local export bundle + docs for every completed snapshot.
        try:
            from foundry.services.snapshot_export_service import build_snapshot_export

            export_result = build_snapshot_export(
                session,
                snapshot_id=snap.id,
                base_output_dir=Path(get_settings().uploads_dir) / "snapshot_exports",
            )
            updated_summary["export_bundle"] = {
                "bundle_path": export_result["bundle_path"],
                "docs_path": export_result["docs_path"],
                "generated_at": str(export_result["generated_at"]),
                "delta_counts": export_result.get("delta_counts"),
                "relationship_graph": export_result.get("relationship_graph"),
            }
        except Exception as export_exc:
            updated_summary["export_bundle_error"] = str(export_exc)

        try:
            updated_summary["git_history"] = materialize_celonis_snapshot_git_history(
                session,
                snapshot_id=snap.id,
                base_output_dir=Path(get_settings().uploads_dir) / "git_history",
            )
        except Exception as git_exc:
            updated_summary["git_history_error"] = str(git_exc)

        snap.summary_json = updated_summary

        session.add(snap)
        session.commit()
        session.refresh(snap)

    except Exception as exc:
        snap.status = SnapshotRunStatus.failed
        snap.finished_at = datetime.utcnow()
        snap.error_message = str(exc)
        session.add(snap)
        session.commit()
        session.refresh(snap)
        raise

    return snap
