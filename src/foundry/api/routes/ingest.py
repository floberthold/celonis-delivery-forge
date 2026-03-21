from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import (
    AssetSnapshot,
    AssetSource,
    EntityType,
    IngestFinding,
    IngestFindingSeverity,
    IngestRun,
    IngestRunStatus,
    Person,
)
from foundry.schemas import (
    AssetSnapshotCreate,
    AssetSnapshotOut,
    AssetSourceCreate,
    AssetSourceOut,
    AssetSourceUpdate,
    CodeDropIngestRequest,
    CodeDropIngestResult,
    IngestFindingCreate,
    IngestFindingOut,
    IngestRunCreate,
    IngestRunOut,
    IngestRunUpdate,
    RepoSyncIngestRequest,
)
from foundry.services.activity_log import log_created, log_updated
from foundry.services.ingest_service import execute_code_drop_ingest, execute_repo_sync_ingest
from foundry.settings import get_settings

router = APIRouter(prefix="/ingest", tags=["ingest"])
settings = get_settings()


def _get_org_source(session: Session, source_id: UUID, organization_id: UUID) -> AssetSource | None:
    return session.exec(
        select(AssetSource).where(
            AssetSource.id == source_id,
            AssetSource.organization_id == organization_id,
        )
    ).first()


def _get_org_snapshot(session: Session, snapshot_id: UUID, organization_id: UUID) -> AssetSnapshot | None:
    snapshot = session.get(AssetSnapshot, snapshot_id)
    if snapshot is None:
        return None
    if _get_org_source(session, snapshot.asset_source_id, organization_id) is None:
        return None
    return snapshot


def _get_org_run(session: Session, run_id: UUID, organization_id: UUID) -> IngestRun | None:
    run = session.get(IngestRun, run_id)
    if run is None:
        return None
    if _get_org_source(session, run.asset_source_id, organization_id) is None:
        return None
    return run


@router.post("/sources", response_model=AssetSourceOut)
def create_source(
    payload: AssetSourceCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    source = AssetSource(
        **payload.model_dump(exclude={"organization_id"}),
        organization_id=current_actor.organization.id,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    log_created(
        session,
        entity_type=EntityType.asset_source,
        entity_id=source.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"name": source.name, "kind": source.kind.value, "provider": source.provider},
    )
    return source


@router.get("/sources", response_model=list[AssetSourceOut])
def list_sources(
    active_only: bool = True,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    stmt = select(AssetSource).where(AssetSource.organization_id == current_actor.organization.id)
    if active_only:
        stmt = stmt.where(AssetSource.is_active.is_(True))
    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return rows


@router.patch("/sources/{source_id}", response_model=AssetSourceOut)
def update_source(
    source_id: UUID,
    payload: AssetSourceUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    source = _get_org_source(session, source_id, current_actor.organization.id)
    if not source:
        raise HTTPException(status_code=404, detail="Asset source not found")

    updates = payload.model_dump(exclude_unset=True)
    for field_name, field_value in updates.items():
        setattr(source, field_name, field_value)

    source.updated_at = datetime.utcnow()
    session.add(source)
    session.commit()
    session.refresh(source)

    log_updated(
        session,
        entity_type=EntityType.asset_source,
        entity_id=source.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"updated_fields": sorted(updates.keys())},
    )
    return source


@router.post("/sources/{source_id}/snapshots", response_model=AssetSnapshotOut)
def create_snapshot(
    source_id: UUID,
    payload: AssetSnapshotCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    source = _get_org_source(session, source_id, current_actor.organization.id)
    if not source:
        raise HTTPException(status_code=404, detail="Asset source not found")

    snapshot = AssetSnapshot(asset_source_id=source_id, **payload.model_dump())
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    log_created(
        session,
        entity_type=EntityType.asset_snapshot,
        entity_id=snapshot.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"source_id": str(source_id), "version_label": snapshot.version_label},
    )
    return snapshot


@router.get("/sources/{source_id}/snapshots", response_model=list[AssetSnapshotOut])
def list_snapshots(
    source_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    source = _get_org_source(session, source_id, current_actor.organization.id)
    if not source:
        raise HTTPException(status_code=404, detail="Asset source not found")

    rows = list(session.exec(select(AssetSnapshot).where(AssetSnapshot.asset_source_id == source_id)).all())
    rows.sort(key=lambda row: row.received_at, reverse=True)
    return rows


@router.post("/runs", response_model=IngestRunOut)
def create_run(
    payload: IngestRunCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    source = _get_org_source(session, payload.asset_source_id, current_actor.organization.id)
    if not source:
        raise HTTPException(status_code=404, detail="Asset source not found")

    if payload.asset_snapshot_id:
        snapshot = _get_org_snapshot(session, payload.asset_snapshot_id, current_actor.organization.id)
        if not snapshot or snapshot.asset_source_id != payload.asset_source_id:
            raise HTTPException(status_code=400, detail="Snapshot does not belong to the source")

    run = IngestRun(**payload.model_dump(), triggered_by=current_actor.person.id)
    session.add(run)
    session.commit()
    session.refresh(run)

    log_created(
        session,
        entity_type=EntityType.ingest_run,
        entity_id=run.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"source_id": str(run.asset_source_id), "status": run.status.value},
    )
    return run


@router.get("/runs", response_model=list[IngestRunOut])
def list_runs(
    asset_source_id: UUID | None = None,
    status: IngestRunStatus | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    org_source_ids = {
        row.id
        for row in session.exec(
            select(AssetSource).where(AssetSource.organization_id == current_actor.organization.id)
        ).all()
    }

    if asset_source_id and asset_source_id not in org_source_ids:
        raise HTTPException(status_code=404, detail="Asset source not found")

    stmt = select(IngestRun)
    if org_source_ids:
        stmt = stmt.where(IngestRun.asset_source_id.in_(org_source_ids))
    else:
        return []
    if asset_source_id:
        stmt = stmt.where(IngestRun.asset_source_id == asset_source_id)
    if status:
        stmt = stmt.where(IngestRun.status == status)

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.created_at, reverse=True)
    return rows[:limit]


@router.patch("/runs/{run_id}", response_model=IngestRunOut)
def update_run(
    run_id: UUID,
    payload: IngestRunUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    run = _get_org_run(session, run_id, current_actor.organization.id)
    if not run:
        raise HTTPException(status_code=404, detail="Ingest run not found")

    updates = payload.model_dump(exclude_unset=True)
    for field_name, field_value in updates.items():
        setattr(run, field_name, field_value)

    if run.status in {IngestRunStatus.completed, IngestRunStatus.failed, IngestRunStatus.canceled} and not run.finished_at:
        run.finished_at = datetime.utcnow()

    session.add(run)
    session.commit()
    session.refresh(run)

    log_updated(
        session,
        entity_type=EntityType.ingest_run,
        entity_id=run.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"updated_fields": sorted(updates.keys())},
    )
    return run


@router.post("/runs/{run_id}/findings", response_model=IngestFindingOut)
def add_finding(
    run_id: UUID,
    payload: IngestFindingCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    run = _get_org_run(session, run_id, current_actor.organization.id)
    if not run:
        raise HTTPException(status_code=404, detail="Ingest run not found")

    finding = IngestFinding(ingest_run_id=run_id, **payload.model_dump())
    session.add(finding)
    session.commit()
    session.refresh(finding)

    log_created(
        session,
        entity_type=EntityType.ingest_finding,
        entity_id=finding.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"run_id": str(run_id), "severity": finding.severity.value, "is_blocking": finding.is_blocking},
    )
    return finding


@router.get("/runs/{run_id}/findings", response_model=list[IngestFindingOut])
def list_findings(
    run_id: UUID,
    severity: IngestFindingSeverity | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    run = _get_org_run(session, run_id, current_actor.organization.id)
    if not run:
        raise HTTPException(status_code=404, detail="Ingest run not found")

    stmt = select(IngestFinding).where(IngestFinding.ingest_run_id == run_id)
    if severity:
        stmt = stmt.where(IngestFinding.severity == severity)

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.created_at, reverse=True)
    return rows


@router.post("/code-drop/execute", response_model=CodeDropIngestResult)
def execute_code_drop(
    payload: CodeDropIngestRequest,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    source = _get_org_source(session, payload.asset_source_id, current_actor.organization.id)
    if not source:
        raise HTTPException(status_code=404, detail="Asset source not found")

    try:
        snapshot, run, findings = execute_code_drop_ingest(
            session=session,
            source=source,
            drop_path=payload.drop_path,
            triggered_by=current_actor.person.id,
            uploads_dir=settings.uploads_dir,
            version_label=payload.version_label,
            source_ref=payload.source_ref,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_created(
        session,
        entity_type=EntityType.asset_snapshot,
        entity_id=snapshot.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={
            "source_id": str(source.id),
            "version_label": snapshot.version_label,
            "manifest_path": snapshot.manifest_path,
        },
    )
    log_created(
        session,
        entity_type=EntityType.ingest_run,
        entity_id=run.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={
            "source_id": str(source.id),
            "snapshot_id": str(snapshot.id),
            "status": run.status.value,
            "findings_total": run.metrics_json.get("findings_total", 0),
            "findings_blocking": run.metrics_json.get("findings_blocking", 0),
        },
    )

    return CodeDropIngestResult(snapshot=snapshot, run=run, findings=findings)


@router.post("/repo-sync/execute", response_model=CodeDropIngestResult)
def execute_repo_sync(
    payload: RepoSyncIngestRequest,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    source = _get_org_source(session, payload.asset_source_id, current_actor.organization.id)
    if not source:
        raise HTTPException(status_code=404, detail="Asset source not found")

    try:
        snapshot, run, findings = execute_repo_sync_ingest(
            session=session,
            source=source,
            local_repo_path=payload.local_repo_path,
            triggered_by=current_actor.person.id,
            uploads_dir=settings.uploads_dir,
            branch=payload.branch,
            tag=payload.tag,
            commit_sha=payload.commit_sha,
            version_label=payload.version_label,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_created(
        session,
        entity_type=EntityType.asset_snapshot,
        entity_id=snapshot.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={
            "source_id": str(source.id),
            "version_label": snapshot.version_label,
            "source_ref": snapshot.source_ref,
            "manifest_path": snapshot.manifest_path,
            "ingest_mode": snapshot.summary_json.get("ingest_mode"),
            "provenance": snapshot.summary_json.get("provenance", {}),
        },
    )
    log_created(
        session,
        entity_type=EntityType.ingest_run,
        entity_id=run.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={
            "source_id": str(source.id),
            "snapshot_id": str(snapshot.id),
            "status": run.status.value,
            "findings_total": run.metrics_json.get("findings_total", 0),
            "findings_blocking": run.metrics_json.get("findings_blocking", 0),
        },
    )

    return CodeDropIngestResult(snapshot=snapshot, run=run, findings=findings)
