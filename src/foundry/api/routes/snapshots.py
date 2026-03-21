from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org, get_session
from foundry.models import (
    Client,
    CelonisSnapshot,
    SnapshotDataModel,
    SnapshotJob,
    SnapshotKnowledgeModel,
    SnapshotPackage,
    SnapshotTask,
)
from foundry.schemas import (
    CelonisSnapshotOut,
    SnapshotExportOut,
    SnapshotReplayPlanOut,
    CelonisSnapshotTriggerRequest,
    SnapshotDataModelOut,
    SnapshotJobOut,
    SnapshotKnowledgeModelOut,
    SnapshotPackageOut,
    SnapshotTaskOut,
)
from foundry.services.snapshot_export_service import (
    build_snapshot_delta_report,
    build_snapshot_export,
    build_snapshot_replay_plan,
)
from foundry.services.snapshot_service import run_snapshot
from foundry.settings import get_settings

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


def _get_org_client(session: Session, client_id: UUID, organization_id: UUID) -> Client | None:
    client = session.get(Client, client_id)
    if not client or client.organization_id != organization_id:
        return None
    return client


def _get_org_snapshot(
    session: Session, snapshot_id: UUID, organization_id: UUID
) -> CelonisSnapshot | None:
    snap = session.get(CelonisSnapshot, snapshot_id)
    if snap is None:
        return None
    if _get_org_client(session, snap.client_id, organization_id) is None:
        return None
    return snap


@router.post("/trigger", response_model=CelonisSnapshotOut, status_code=status.HTTP_202_ACCEPTED)
def trigger_snapshot(
    body: CelonisSnapshotTriggerRequest,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if _get_org_client(session, body.client_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    snap = run_snapshot(session, client_id=body.client_id, triggered_by=current_actor.person.id)
    return snap


@router.get("/", response_model=list[CelonisSnapshotOut])
def list_snapshots(
    client_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if _get_org_client(session, client_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    rows = session.exec(
        select(CelonisSnapshot).where(CelonisSnapshot.client_id == client_id)
    ).all()
    return sorted(rows, key=lambda row: row.created_at, reverse=True)


@router.get("/{snapshot_id}", response_model=CelonisSnapshotOut)
def get_snapshot(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snap


@router.get("/{snapshot_id}/packages", response_model=list[SnapshotPackageOut])
def list_snapshot_packages(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return session.exec(
        select(SnapshotPackage).where(SnapshotPackage.snapshot_id == snapshot_id)
    ).all()


@router.get("/{snapshot_id}/tasks", response_model=list[SnapshotTaskOut])
def list_snapshot_tasks(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return session.exec(
        select(SnapshotTask).where(SnapshotTask.snapshot_id == snapshot_id)
    ).all()


@router.get("/{snapshot_id}/data-models", response_model=list[SnapshotDataModelOut])
def list_snapshot_data_models(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return session.exec(
        select(SnapshotDataModel).where(SnapshotDataModel.snapshot_id == snapshot_id)
    ).all()


@router.get("/{snapshot_id}/jobs", response_model=list[SnapshotJobOut])
def list_snapshot_jobs(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return session.exec(
        select(SnapshotJob).where(SnapshotJob.snapshot_id == snapshot_id)
    ).all()


@router.get("/{snapshot_id}/knowledge-models", response_model=list[SnapshotKnowledgeModelOut])
def list_snapshot_knowledge_models(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return session.exec(
        select(SnapshotKnowledgeModel).where(SnapshotKnowledgeModel.snapshot_id == snapshot_id)
    ).all()


@router.post("/{snapshot_id}/export", response_model=SnapshotExportOut)
def export_snapshot_bundle(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    output_dir = get_settings().uploads_dir
    result = build_snapshot_export(
        session,
        snapshot_id=snapshot_id,
        base_output_dir=Path(output_dir) / "snapshot_exports",
    )
    return result


@router.get("/{snapshot_id}/delta")
def get_snapshot_delta(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return build_snapshot_delta_report(session, snapshot_id=snapshot_id)


@router.get("/{snapshot_id}/replay-plan", response_model=SnapshotReplayPlanOut)
def get_snapshot_replay_plan(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return build_snapshot_replay_plan(session, snapshot_id=snapshot_id)


@router.get("/{snapshot_id}/export/download")
def download_snapshot_bundle(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    output_dir = get_settings().uploads_dir
    result = build_snapshot_export(
        session,
        snapshot_id=snapshot_id,
        base_output_dir=Path(output_dir) / "snapshot_exports",
    )
    return FileResponse(
        path=result["bundle_path"],
        filename=f"snapshot_{snapshot_id}.zip",
        media_type="application/zip",
    )
