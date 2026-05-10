from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import Client, EntityType, KpiDefinition, KpiVersion, Project
from foundry.schemas import KpiCreate, KpiOut, KpiStatusUpdate, KpiUpdate, KpiVersionCreate
from foundry.services.activity_log import log_created, log_updated

router = APIRouter(prefix="/kpis", tags=["kpis"])


def _get_org_client(session: Session, client_id: UUID, organization_id: UUID) -> Client | None:
    client = session.get(Client, client_id)
    if not client or client.organization_id != organization_id:
        return None
    return client


def _get_org_project(session: Session, project_id: UUID, organization_id: UUID) -> Project | None:
    project = session.get(Project, project_id)
    if not project or project.organization_id != organization_id:
        return None
    return project


def _get_org_kpi(session: Session, kpi_id: UUID, organization_id: UUID) -> KpiDefinition | None:
    kpi = session.get(KpiDefinition, kpi_id)
    if not kpi:
        return None
    project = _get_org_project(session, kpi.project_id, organization_id)
    client = _get_org_client(session, kpi.client_id, organization_id)
    if project is None or client is None:
        return None
    return kpi


@router.get("/", response_model=list[KpiOut])
def list_kpis(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    org_id = current_actor.organization.id
    rows = [
        row
        for row in session.exec(select(KpiDefinition)).all()
        if _get_org_project(session, row.project_id, org_id) is not None
        and _get_org_client(session, row.client_id, org_id) is not None
    ]
    return sorted(rows, key=lambda r: r.created_at, reverse=True)


@router.get("/{kpi_id}", response_model=KpiOut)
def get_kpi(
    kpi_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    return kpi


@router.post("/", response_model=KpiOut)
def create_kpi(
    payload: KpiCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    org_id = current_actor.organization.id
    project = _get_org_project(session, payload.project_id, org_id)
    client = _get_org_client(session, payload.client_id, org_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if project.client_id != client.id:
        raise HTTPException(status_code=400, detail="Project does not belong to client")

    kpi = KpiDefinition(**payload.model_dump())
    session.add(kpi)
    session.commit()
    session.refresh(kpi)
    log_created(
        session,
        entity_type=EntityType.kpi_definition,
        entity_id=kpi.id,
        actor_id=current_actor.person.id,
        organization_id=org_id,
        metadata={"project_id": str(kpi.project_id), "client_id": str(kpi.client_id)},
    )
    return kpi


@router.patch("/{kpi_id}", response_model=KpiOut)
def update_kpi(
    kpi_id: UUID,
    payload: KpiUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    org_id = current_actor.organization.id
    kpi = _get_org_kpi(session, kpi_id, org_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")

    update_data = payload.model_dump(exclude_unset=True)
    next_project_id = update_data.get("project_id", kpi.project_id)
    next_client_id = update_data.get("client_id", kpi.client_id)
    project = _get_org_project(session, next_project_id, org_id)
    client = _get_org_client(session, next_client_id, org_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if project.client_id != client.id:
        raise HTTPException(status_code=400, detail="Project does not belong to client")

    for key, value in update_data.items():
        setattr(kpi, key, value)
    kpi.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(kpi)
    session.commit()
    session.refresh(kpi)
    log_updated(
        session,
        entity_type=EntityType.kpi_definition,
        entity_id=kpi.id,
        actor_id=current_actor.person.id,
        organization_id=org_id,
        metadata={"fields": list(update_data.keys())},
    )
    return kpi


@router.post("/{kpi_id}/status", response_model=KpiOut)
def update_kpi_status(
    kpi_id: UUID,
    payload: KpiStatusUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    kpi.status = payload.status
    kpi.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(kpi)
    session.commit()
    session.refresh(kpi)
    log_updated(
        session,
        entity_type=EntityType.kpi_definition,
        entity_id=kpi.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"status": kpi.status.value},
    )
    return kpi


@router.post("/{kpi_id}/versions", response_model=KpiVersion)
def save_kpi_version(
    kpi_id: UUID,
    payload: KpiVersionCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    existing = session.exec(select(KpiVersion).where(KpiVersion.kpi_id == kpi_id)).all()
    next_version = max((v.version for v in existing), default=0) + 1
    version = KpiVersion(
        kpi_id=kpi_id,
        version=next_version,
        pql_formula=payload.pql_formula,
        change_note=payload.change_note,
        author_id=current_actor.person.id,
    )
    session.add(version)
    kpi.pql_formula = payload.pql_formula
    kpi.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(kpi)
    session.commit()
    session.refresh(version)
    log_created(
        session,
        entity_type=EntityType.kpi_version,
        entity_id=version.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"kpi_id": str(kpi_id), "version": next_version},
    )
    return version


@router.get("/{kpi_id}/versions", response_model=list[KpiVersion])
def list_kpi_versions(
    kpi_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    rows = session.exec(select(KpiVersion).where(KpiVersion.kpi_id == kpi_id)).all()
    return sorted(rows, key=lambda v: v.version, reverse=True)


@router.delete("/{kpi_id}", status_code=204)
def delete_kpi(
    kpi_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    for v in session.exec(select(KpiVersion).where(KpiVersion.kpi_id == kpi_id)).all():
        session.delete(v)
    session.delete(kpi)
    session.commit()

