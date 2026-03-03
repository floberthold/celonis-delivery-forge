from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import get_current_person
from foundry.db import get_session
from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import CelonisConnection, EntityType, Person
from foundry.schemas import (
    CelonisActionResult,
    CelonisConnectionOut,
    CelonisConnectionUpsert,
    CelonisExtractRequest,
    CelonisImportRequest,
)
from foundry.settings import get_settings
from foundry.services.activity_log import log_created, log_updated

router = APIRouter(prefix="/celonis", tags=["celonis"])


def _get_connection_or_404(session: Session, client_id):
    connection = session.exec(select(CelonisConnection).where(CelonisConnection.client_id == client_id)).first()
    if not connection or not connection.is_active:
        raise HTTPException(status_code=404, detail="Active Celonis connection not found for client")
    return connection


@router.get("/connections", response_model=list[CelonisConnectionOut])
def list_connections(session: Session = Depends(get_session)):
    rows = session.exec(select(CelonisConnection)).all()
    return sorted(rows, key=lambda row: row.updated_at or datetime.min, reverse=True)


@router.post("/connections/upsert", response_model=CelonisConnectionOut)
def upsert_connection(
    payload: CelonisConnectionUpsert,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    existing = session.exec(
        select(CelonisConnection).where(CelonisConnection.client_id == payload.client_id)
    ).first()
    if existing:
        existing.tenant_base_url = payload.tenant_base_url.strip()
        existing.is_active = payload.is_active
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)

        log_updated(
            session,
            entity_type=EntityType.celonis_connection,
            entity_id=existing.id,
            actor_id=current_person.id,
            metadata={"client_id": str(existing.client_id), "is_active": existing.is_active},
        )
        return existing

    row = CelonisConnection(
        client_id=payload.client_id,
        tenant_base_url=payload.tenant_base_url.strip(),
        is_active=payload.is_active,
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    log_created(
        session,
        entity_type=EntityType.celonis_connection,
        entity_id=row.id,
        actor_id=current_person.id,
        metadata={"client_id": str(row.client_id), "is_active": row.is_active},
    )
    return row


@router.post("/extract", response_model=CelonisActionResult)
def extract(payload: CelonisExtractRequest, session: Session = Depends(get_session)):
    settings = get_settings()
    connection = _get_connection_or_404(session, payload.client_id)
    try:
        result = CelonisGateway(settings).extract(
            tenant_base_url=connection.tenant_base_url,
            source_path=payload.source_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Celonis extract failed: {exc}") from exc

    return CelonisActionResult(
        client_id=payload.client_id,
        action=result.action,
        url=result.url,
        status_code=result.status_code,
        ok=result.ok,
        response_preview=result.response_preview,
    )


@router.post("/import", response_model=CelonisActionResult)
def import_data(payload: CelonisImportRequest, session: Session = Depends(get_session)):
    settings = get_settings()
    connection = _get_connection_or_404(session, payload.client_id)
    try:
        result = CelonisGateway(settings).import_data(
            tenant_base_url=connection.tenant_base_url,
            target_path=payload.target_path,
            payload=payload.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Celonis import failed: {exc}") from exc

    return CelonisActionResult(
        client_id=payload.client_id,
        action=result.action,
        url=result.url,
        status_code=result.status_code,
        ok=result.ok,
        response_preview=result.response_preview,
    )
