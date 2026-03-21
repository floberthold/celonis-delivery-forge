"""Celonis Snapshot Service — pulls implementation artefacts from a remote tenant."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import (
    CelonisConnection,
    CelonisSnapshot,
    SnapshotChangeType,
    SnapshotDataModel,
    SnapshotJob,
    SnapshotKnowledgeModel,
    SnapshotPackage,
    SnapshotRunStatus,
    SnapshotTask,
)
from foundry.settings import get_settings

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def _content_hash(raw: dict) -> str:
    blob = json.dumps(raw, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _get_connection(session: Session, client_id: UUID) -> CelonisConnection | None:
    stmt = select(CelonisConnection).where(
        CelonisConnection.client_id == client_id,
        CelonisConnection.is_active == True,  # noqa: E712
    )
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


# ---------------------------------------------------------------------------
# Studio extraction helpers
# ---------------------------------------------------------------------------

def _extract_spaces(gw: CelonisGateway, base_url: str) -> list[dict]:
    try:
        result = gw.extract(tenant_base_url=base_url, source_path="/package-manager/api/spaces")
        if result.ok:
            data = json.loads(result.response_preview) if len(result.response_preview) < 100_000 else []
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _extract_packages(gw: CelonisGateway, base_url: str) -> list[dict]:
    try:
        result = gw.extract(tenant_base_url=base_url, source_path="/package-manager/api/packages")
        if result.ok:
            data = json.loads(result.response_preview) if len(result.response_preview) < 200_000 else []
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _extract_package_tasks(gw: CelonisGateway, base_url: str, package_key: str) -> list[dict]:
    try:
        path = f"/package-manager/api/packages/{package_key}/assets"
        result = gw.extract(tenant_base_url=base_url, source_path=path)
        if result.ok:
            data = json.loads(result.response_preview) if len(result.response_preview) < 500_000 else []
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _extract_data_models(gw: CelonisGateway, base_url: str) -> list[dict]:
    try:
        result = gw.extract(
            tenant_base_url=base_url,
            source_path="/process-mining/api/data-models",
        )
        if result.ok:
            raw = json.loads(result.response_preview) if len(result.response_preview) < 200_000 else {}
            items = raw if isinstance(raw, list) else raw.get("dataModels", raw.get("data", []))
            return _safe_list(items)
    except Exception:
        pass
    return []


def _extract_jobs(gw: CelonisGateway, base_url: str) -> list[dict]:
    try:
        result = gw.extract(
            tenant_base_url=base_url,
            source_path="/integration/api/v1/jobs",
        )
        if result.ok:
            raw = json.loads(result.response_preview) if len(result.response_preview) < 200_000 else {}
            items = raw if isinstance(raw, list) else raw.get("jobs", raw.get("data", []))
            return _safe_list(items)
    except Exception:
        pass
    return []


def _extract_knowledge_models(gw: CelonisGateway, base_url: str) -> list[dict]:
    try:
        result = gw.extract(
            tenant_base_url=base_url,
            source_path="/knowledge-model/api/knowledge-models",
        )
        if result.ok:
            raw = json.loads(result.response_preview) if len(result.response_preview) < 200_000 else {}
            items = raw if isinstance(raw, list) else raw.get("knowledgeModels", raw.get("data", []))
            return _safe_list(items)
    except Exception:
        pass
    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_snapshot(session: Session, *, client_id: UUID, triggered_by: UUID) -> CelonisSnapshot:
    """Trigger a full snapshot for a client and persist results."""
    conn = _get_connection(session, client_id)
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

        # ---- packages ----
        raw_packages = _extract_packages(gw, base_url)
        current_pkg_ids: set[str] = set()
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

            # ---- tasks inside package ----
            raw_tasks = _extract_package_tasks(gw, base_url, pkg_key)
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
        for dm in _extract_data_models(gw, base_url):
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

        # ---- jobs ----
        for job in _extract_jobs(gw, base_url):
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
        for km in _extract_knowledge_models(gw, base_url):
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

        # ---- finalize ----
        snap.status = SnapshotRunStatus.completed
        snap.finished_at = datetime.utcnow()
        snap.summary_json = {
            "packages": len(raw_packages),
            "data_models": len(_extract_data_models(gw, base_url)),
            "jobs": len(_extract_jobs(gw, base_url)),
            "knowledge_models": len(_extract_knowledge_models(gw, base_url)),
        }

        # Auto-generate a local export bundle + docs for every completed snapshot.
        try:
            from foundry.services.snapshot_export_service import build_snapshot_export

            export_result = build_snapshot_export(
                session,
                snapshot_id=snap.id,
                base_output_dir=Path(get_settings().uploads_dir) / "snapshot_exports",
            )
            snap.summary_json["export_bundle"] = {
                "bundle_path": export_result["bundle_path"],
                "docs_path": export_result["docs_path"],
                "generated_at": str(export_result["generated_at"]),
                "delta_counts": export_result.get("delta_counts"),
                "relationship_graph": export_result.get("relationship_graph"),
            }
        except Exception as export_exc:
            snap.summary_json["export_bundle_error"] = str(export_exc)

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
