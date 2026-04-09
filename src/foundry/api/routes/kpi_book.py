from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org, get_session
from foundry.models import Client, KpiBookEntry
from foundry.schemas import KpiBookEntryCreate, KpiBookEntryOut, KpiBookEntryUpdate

router = APIRouter(prefix="/kpi-book", tags=["kpi-book"])


def _get_org_client(session: Session, client_id: UUID, organization_id: UUID) -> Client | None:
    client = session.get(Client, client_id)
    if not client or client.organization_id != organization_id:
        return None
    return client


def _get_org_kpi_book_entry(
    session: Session, entry_id: UUID, organization_id: UUID
) -> KpiBookEntry | None:
    entry = session.get(KpiBookEntry, entry_id)
    if entry is None:
        return None
    if _get_org_client(session, entry.client_id, organization_id) is None:
        return None
    return entry


@router.post("/", response_model=KpiBookEntryOut, status_code=201)
def create_entry(
    body: KpiBookEntryCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    org_id = current_actor.organization.id
    if _get_org_client(session, body.client_id, org_id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    entry = KpiBookEntry(**body.model_dump(), saved_by=current_actor.person.id)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/", response_model=list[KpiBookEntryOut])
def list_entries(
    client_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if _get_org_client(session, client_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    rows = session.exec(
        select(KpiBookEntry).where(KpiBookEntry.client_id == client_id)
    ).all()
    return sorted(rows, key=lambda row: row.created_at, reverse=True)


@router.patch("/{entry_id}", response_model=KpiBookEntryOut)
def update_entry(
    entry_id: UUID,
    body: KpiBookEntryUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    entry = _get_org_kpi_book_entry(session, entry_id, current_actor.organization.id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    from datetime import datetime
    entry.updated_at = datetime.utcnow()
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_entry(
    entry_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    entry = _get_org_kpi_book_entry(session, entry_id, current_actor.organization.id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    session.delete(entry)
    session.commit()
