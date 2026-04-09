from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import ActivityLog, CelonisConnection, CelonisUserToken, Client, EntityType
from foundry.schemas import (
    CelonisActionResult,
    CelonisPreflightBatchResult,
    CelonisConnectionOut,
    CelonisConnectionUpsert,
    CelonisExtractRequest,
    CelonisPreflightHistoryItem,
    CelonisImportRequest,
    CelonisPreflightResult,
    CelonisUserTokenStatus,
    CelonisUserTokenUpdate,
)
from foundry.settings import get_settings
from foundry.services.activity_log import log_activity, log_created, log_updated

router = APIRouter(prefix="/celonis", tags=["celonis"])


def _parse_services_or_default(raw_services: str | None) -> list[str]:
    default_services = list(CelonisGateway.SERVICE_DEFAULT_PROBES.keys())
    if not raw_services:
        return default_services

    requested = [item.strip().lower() for item in raw_services.split(",") if item.strip()]
    if not requested:
        return default_services

    invalid = [item for item in requested if item not in CelonisGateway.SERVICE_DEFAULT_PROBES]
    if invalid:
        allowed = ", ".join(default_services)
        invalid_display = ", ".join(invalid)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service values: {invalid_display}. Allowed values: {allowed}",
        )

    unique: list[str] = []
    for item in requested:
        if item not in unique:
            unique.append(item)
    return unique


def _get_connection_or_404(session: Session, client_id: UUID, organization_id: UUID):
    connection = session.exec(
        select(CelonisConnection).where(
            CelonisConnection.client_id == client_id,
            CelonisConnection.organization_id == organization_id,
        )
    ).first()
    if not connection or not connection.is_active:
        raise HTTPException(status_code=404, detail="Active Celonis connection not found for client")
    return connection


def _get_user_token(
    session: Session,
    *,
    organization_id: UUID,
    person_id: UUID,
) -> CelonisUserToken | None:
    return session.exec(
        select(CelonisUserToken).where(
            CelonisUserToken.organization_id == organization_id,
            CelonisUserToken.person_id == person_id,
        )
    ).first()


def _resolve_actor_token_override(session: Session, current_actor: CurrentActor) -> str | None:
    row = _get_user_token(
        session,
        organization_id=current_actor.organization.id,
        person_id=current_actor.person.id,
    )
    if row is None:
        return None
    token = row.token_value.strip()
    return token or None


def _token_override_kwargs(token_override: str | None) -> dict:
    if not token_override:
        return {}
    return {"token_override": token_override}


@router.get("/connections", response_model=list[CelonisConnectionOut])
def list_connections(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    rows = session.exec(
        select(CelonisConnection).where(
            CelonisConnection.organization_id == current_actor.organization.id
        )
    ).all()
    return sorted(rows, key=lambda row: row.updated_at or datetime.min, reverse=True)


@router.post("/connections/upsert", response_model=CelonisConnectionOut)
def upsert_connection(
    payload: CelonisConnectionUpsert,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    client = session.get(Client, payload.client_id)
    if not client or client.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=404, detail="Client not found")

    existing = session.exec(
        select(CelonisConnection).where(
            CelonisConnection.client_id == payload.client_id,
            CelonisConnection.organization_id == current_actor.organization.id,
        )
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
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"client_id": str(existing.client_id), "is_active": existing.is_active},
        )
        return existing

    row = CelonisConnection(
        organization_id=current_actor.organization.id,
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
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"client_id": str(row.client_id), "is_active": row.is_active},
    )
    return row


@router.get("/user-token", response_model=CelonisUserTokenStatus)
def get_user_token_status(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    row = _get_user_token(
        session,
        organization_id=current_actor.organization.id,
        person_id=current_actor.person.id,
    )
    if row is None or not row.token_value.strip():
        return CelonisUserTokenStatus(token_configured=False, updated_at=None)
    return CelonisUserTokenStatus(token_configured=True, updated_at=row.updated_at)


@router.put("/user-token", response_model=CelonisUserTokenStatus)
def put_user_token(
    payload: CelonisUserTokenUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    token_value = payload.token_value.strip()
    if not token_value:
        raise HTTPException(status_code=400, detail="token_value cannot be empty")

    row = _get_user_token(
        session,
        organization_id=current_actor.organization.id,
        person_id=current_actor.person.id,
    )
    now = datetime.utcnow()
    if row is None:
        row = CelonisUserToken(
            organization_id=current_actor.organization.id,
            person_id=current_actor.person.id,
            token_value=token_value,
            created_at=now,
            updated_at=now,
        )
    else:
        row.token_value = token_value
        row.updated_at = now

    session.add(row)
    session.commit()
    session.refresh(row)

    log_activity(
        session,
        entity_type=EntityType.person,
        entity_id=current_actor.person.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        action="person.celonis_user_token.updated",
        metadata={"token_present": True, "scope": "person+organization"},
    )
    return CelonisUserTokenStatus(token_configured=True, updated_at=row.updated_at)


@router.delete("/user-token", response_model=CelonisUserTokenStatus)
def delete_user_token(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    row = _get_user_token(
        session,
        organization_id=current_actor.organization.id,
        person_id=current_actor.person.id,
    )
    if row is not None:
        session.delete(row)
        session.commit()
        log_activity(
            session,
            entity_type=EntityType.person,
            entity_id=current_actor.person.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            action="person.celonis_user_token.updated",
            metadata={"token_present": False, "scope": "person+organization"},
        )
    return CelonisUserTokenStatus(token_configured=False, updated_at=None)


@router.post("/extract", response_model=CelonisActionResult)
def extract(
    payload: CelonisExtractRequest,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    settings = get_settings()
    connection = _get_connection_or_404(session, payload.client_id, current_actor.organization.id)
    token_override = _resolve_actor_token_override(session, current_actor)
    try:
        result = CelonisGateway(settings).extract(
            tenant_base_url=connection.tenant_base_url,
            source_path=payload.source_path,
            **_token_override_kwargs(token_override),
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
def import_data(
    payload: CelonisImportRequest,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    settings = get_settings()
    connection = _get_connection_or_404(session, payload.client_id, current_actor.organization.id)
    token_override = _resolve_actor_token_override(session, current_actor)
    try:
        result = CelonisGateway(settings).import_data(
            tenant_base_url=connection.tenant_base_url,
            target_path=payload.target_path,
            payload=payload.payload,
            **_token_override_kwargs(token_override),
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


@router.get("/connections/{client_id}/preflight", response_model=CelonisPreflightResult)
def preflight_connection(
    client_id: UUID,
    probe_path: str = "/",
    service: str = "core",
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    settings = get_settings()
    connection = _get_connection_or_404(session, client_id, current_actor.organization.id)
    token_override = _resolve_actor_token_override(session, current_actor)
    result = CelonisGateway(settings).preflight(
        tenant_base_url=connection.tenant_base_url,
        probe_path=probe_path,
        service=service,
        **_token_override_kwargs(token_override),
    )
    return CelonisPreflightResult(
        client_id=client_id,
        service=result.service,
        probe_path=result.probe_path,
        probe_url=result.probe_url,
        has_token=result.has_token,
        request_attempted=result.request_attempted,
        reachable=result.reachable,
        authenticated=result.authenticated,
        permission_status=result.permission_status,
        status_code=result.status_code,
        error=result.error,
        response_preview=result.response_preview,
    )


@router.post("/connections/{client_id}/preflight/batch", response_model=CelonisPreflightBatchResult)
def preflight_connection_batch(
    client_id: UUID,
    services: str | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    settings = get_settings()
    connection = _get_connection_or_404(session, client_id, current_actor.organization.id)
    selected_services = _parse_services_or_default(services)
    gateway = CelonisGateway(settings)
    token_override = _resolve_actor_token_override(session, current_actor)
    run_id = str(uuid4())
    run_ts = datetime.utcnow()

    results: list[CelonisPreflightResult] = []
    authorized_count = 0
    for service_name in selected_services:
        result = gateway.preflight(
            tenant_base_url=connection.tenant_base_url,
            probe_path="",
            service=service_name,
            **_token_override_kwargs(token_override),
        )
        if result.permission_status == "authorized":
            authorized_count += 1

        log_activity(
            session,
            entity_type=EntityType.celonis_connection,
            entity_id=connection.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            action="celonis_connection.preflight",
            metadata={
                "client_id": str(connection.client_id),
                "service": result.service,
                "probe_path": result.probe_path,
                "probe_url": result.probe_url,
                "has_token": result.has_token,
                "reachable": result.reachable,
                "authenticated": result.authenticated,
                "permission_status": result.permission_status,
                "status_code": result.status_code,
                "error": result.error,
                "source": "api_batch",
                "run_id": run_id,
            },
        )

        results.append(
            CelonisPreflightResult(
                client_id=client_id,
                service=result.service,
                probe_path=result.probe_path,
                probe_url=result.probe_url,
                has_token=result.has_token,
                request_attempted=result.request_attempted,
                reachable=result.reachable,
                authenticated=result.authenticated,
                permission_status=result.permission_status,
                status_code=result.status_code,
                error=result.error,
                response_preview=result.response_preview,
            )
        )

    total = len(results)
    return CelonisPreflightBatchResult(
        client_id=client_id,
        run_id=run_id,
        timestamp=run_ts,
        total=total,
        authorized_count=authorized_count,
        issue_count=total - authorized_count,
        results=results,
    )


@router.get("/connections/{client_id}/preflight/history", response_model=list[CelonisPreflightHistoryItem])
def preflight_connection_history(
    client_id: UUID,
    limit: int = 20,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")

    connection = _get_connection_or_404(session, client_id, current_actor.organization.id)
    rows = session.exec(
        select(ActivityLog).where(
            ActivityLog.organization_id == current_actor.organization.id,
            ActivityLog.entity_type == EntityType.celonis_connection,
            ActivityLog.entity_id == connection.id,
            ActivityLog.action == "celonis_connection.preflight",
        )
    ).all()

    sorted_rows = sorted(rows, key=lambda row: row.timestamp, reverse=True)[:limit]
    return [
        CelonisPreflightHistoryItem(
            timestamp=row.timestamp,
            actor_id=row.actor_id,
            service=str(row.metadata_json.get("service") or "core"),
            probe_path=str(row.metadata_json.get("probe_path") or "/"),
            probe_url=str(row.metadata_json.get("probe_url") or ""),
            has_token=bool(row.metadata_json.get("has_token", False)),
            reachable=bool(row.metadata_json.get("reachable", False)),
            authenticated=bool(row.metadata_json.get("authenticated", False)),
            permission_status=str(row.metadata_json.get("permission_status") or "unknown"),
            status_code=row.metadata_json.get("status_code"),
            error=row.metadata_json.get("error"),
            run_id=row.metadata_json.get("run_id"),
        )
        for row in sorted_rows
    ]
