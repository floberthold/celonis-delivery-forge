from pathlib import Path
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org, get_session
from foundry.api.routes.celonis import _resolve_actor_token_override
from foundry.models import (
    Client,
    CelonisSnapshot,
    SnapshotDataModel,
    SnapshotJob,
    SnapshotKnowledgeModel,
    SnapshotPackage,
    SnapshotTask,
    SnapshotTaskDetail,
)
from foundry.schemas import (
    CelonisSnapshotOut,
    SnapshotExportOut,
    SnapshotGitHistoryOut,
    SnapshotReplayPlanOut,
    CelonisSnapshotTriggerRequest,
    SnapshotDataModelOut,
    SnapshotJobOut,
    SnapshotKnowledgeModelOut,
    SnapshotPackageOut,
    SnapshotTaskDetailOut,
    SnapshotTaskOut,
)
from foundry.services.snapshot_export_service import (
    build_snapshot_delta_report,
    build_snapshot_export,
    build_snapshot_replay_plan,
)
from foundry.services.snapshot_coverage_service import (
    build_snapshot_coverage_filename,
    build_snapshot_coverage_report,
)
from foundry.services.snapshot_git_service import materialize_celonis_snapshot_git_history
from foundry.services.snapshot_service import preflight_snapshot_endpoints, run_snapshot
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


@router.get("/preflight/{client_id}")
def preflight_client_endpoints(
    client_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    """Probe every snapshot family endpoint for a client without persisting anything.

    Returns per-endpoint diagnostics (HTTP status, response shape, detected list key)
    so you can identify why a full snapshot returns zero results.
    """
    if _get_org_client(session, client_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        token_override = _resolve_actor_token_override(session, current_actor)
        result = preflight_snapshot_endpoints(
            session,
            client_id=client_id,
            organization_id=current_actor.organization.id,
            token_override=token_override or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(content=result)


@router.post("/trigger", response_model=CelonisSnapshotOut, status_code=status.HTTP_202_ACCEPTED)
def trigger_snapshot(
    body: CelonisSnapshotTriggerRequest,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if _get_org_client(session, body.client_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        token_override = _resolve_actor_token_override(session, current_actor)
        run_kwargs: dict = {}
        if token_override:
            run_kwargs["token_override"] = token_override
        snap = run_snapshot(
            session,
            client_id=body.client_id,
            triggered_by=current_actor.person.id,
            organization_id=current_actor.organization.id,
            **run_kwargs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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


@router.get("/{snapshot_id}/task-details", response_model=list[SnapshotTaskDetailOut])
def list_snapshot_task_details(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return session.exec(
        select(SnapshotTaskDetail).where(SnapshotTaskDetail.snapshot_id == snapshot_id)
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
    settings = get_settings()
    output_dir = getattr(settings, "generated_dir", settings.uploads_dir)
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


@router.get("/{snapshot_id}/coverage")
def get_snapshot_coverage_report(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return build_snapshot_coverage_report(snap)


@router.get("/{snapshot_id}/coverage/download")
def download_snapshot_coverage_report(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    payload = build_snapshot_coverage_report(snap)
    filename = build_snapshot_coverage_filename(snapshot_id)
    return Response(
        content=json.dumps(payload, indent=2, default=str),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{snapshot_id}/export/download")
def download_snapshot_bundle(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    settings = get_settings()
    output_dir = getattr(settings, "generated_dir", settings.uploads_dir)
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


@router.post("/{snapshot_id}/git-history", response_model=SnapshotGitHistoryOut)
def materialize_snapshot_git_history(
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    snap = _get_org_snapshot(session, snapshot_id, current_actor.organization.id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    settings = get_settings()
    output_dir = getattr(settings, "generated_dir", settings.uploads_dir)
    result = materialize_celonis_snapshot_git_history(
        session,
        snapshot_id=snapshot_id,
        base_output_dir=Path(output_dir) / "git_history",
    )
    snap.summary_json = {**snap.summary_json, "git_history": result}
    session.add(snap)
    session.commit()
    session.refresh(snap)
    return result
