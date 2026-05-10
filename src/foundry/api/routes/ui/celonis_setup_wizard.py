from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Form, Request
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import CelonisConnection, Client, EntityType, SensitivityLevel
from foundry.services.activity_log import log_activity, log_created
from foundry.settings import get_settings
from .shared import redirect_ui as _redirect_ui

router = APIRouter(tags=["ui"])


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except Exception as exc:
        raise ValueError(f"Invalid {field_name}") from exc


@router.get("/onboarding/celonis-setup")
def celonis_setup_wizard(
    request: Request,
    client_id: str = "",
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from . import _celonis_setup_context, _get_org_client, _org_clients, templates

    selected_client: Client | None = None
    org_clients = _org_clients(session, current_actor.organization.id)
    if client_id.strip():
        try:
            parsed_client_id = _parse_uuid(client_id, "client_id")
            selected_client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        except Exception:
            selected_client = None
    if selected_client is None and org_clients:
        selected_client = sorted(org_clients, key=lambda row: row.name.lower())[0]

    return templates.TemplateResponse(request, "celonis_setup_wizard.html",
        _celonis_setup_context(
            request,
            session,
            current_actor,
            selected_client=selected_client,
        ),
    )


@router.post("/onboarding/celonis-setup/create-client", include_in_schema=False)
def celonis_setup_create_client(
    name: str = Form(...),
    tenant_url: str = Form(...),
    sensitivity_level: str = Form("medium"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        client = Client(
            organization_id=current_actor.organization.id,
            name=name.strip(),
            tenant_url=tenant_url.strip(),
            sensitivity_level=SensitivityLevel(sensitivity_level),
        )
        session.add(client)
        session.commit()
        session.refresh(client)
        log_created(
            session,
            entity_type=EntityType.client,
            entity_id=client.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"source": "celonis_setup_wizard"},
        )
        return _redirect_ui(
            f"/onboarding/celonis-setup?client_id={client.id}",
            ok=f"Client '{client.name}' created",
        )
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/onboarding/celonis-setup", err=f"Create client failed: {exc}")


@router.post("/onboarding/celonis-setup/save-connection", include_in_schema=False)
def celonis_setup_save_connection(
    client_id: str = Form(...),
    tenant_base_url: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from . import _get_org_client

    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        if _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            return _redirect_ui("/onboarding/celonis-setup", err="Client not found")

        existing = session.exec(
            select(CelonisConnection).where(
                CelonisConnection.client_id == parsed_client_id,
                CelonisConnection.organization_id == current_actor.organization.id,
            )
        ).first()
        if existing is None:
            existing = CelonisConnection(
                organization_id=current_actor.organization.id,
                client_id=parsed_client_id,
                tenant_base_url=tenant_base_url.strip(),
                is_active=True,
            )
        else:
            existing.tenant_base_url = tenant_base_url.strip()
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        session.add(existing)
        session.commit()
        session.refresh(existing)
        return _redirect_ui(
            f"/onboarding/celonis-setup?client_id={parsed_client_id}",
            ok="Connection saved",
        )
    except Exception as exc:
        session.rollback()
        return _redirect_ui(
            f"/onboarding/celonis-setup?client_id={client_id}",
            err=f"Save connection failed: {exc}",
        )


@router.post("/onboarding/celonis-setup/save-token", include_in_schema=False)
def celonis_setup_save_token(
    client_id: str = Form(...),
    token_value: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from . import _get_org_client, _get_org_person_celonis_token, _upsert_org_person_celonis_token

    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        if _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            return _redirect_ui("/onboarding/celonis-setup", err="Client not found")

        cleaned = token_value.strip()
        existing = _get_org_person_celonis_token(
            session,
            current_actor.organization.id,
            current_actor.person.id,
        )
        if cleaned:
            _upsert_org_person_celonis_token(
                session,
                current_actor.organization.id,
                current_actor.person.id,
                cleaned,
            )
            label = "Token saved"
        else:
            if existing is not None:
                session.delete(existing)
            label = "Token cleared"
        session.commit()
        return _redirect_ui(f"/onboarding/celonis-setup?client_id={parsed_client_id}", ok=label)
    except Exception as exc:
        session.rollback()
        return _redirect_ui(
            f"/onboarding/celonis-setup?client_id={client_id}",
            err=f"Save token failed: {exc}",
        )


@router.post("/onboarding/celonis-setup/run-preflight", include_in_schema=False)
def celonis_setup_run_preflight(
    client_id: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from . import _get_org_active_celonis_connection, _get_org_client, _get_org_person_celonis_token

    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        if client is None:
            return _redirect_ui("/onboarding/celonis-setup", err="Client not found")

        connection = _get_org_active_celonis_connection(
            session,
            parsed_client_id,
            current_actor.organization.id,
        )
        if connection is None:
            return _redirect_ui(
                f"/onboarding/celonis-setup?client_id={parsed_client_id}",
                err="No active Celonis connection for selected client",
            )

        services = list(CelonisGateway.SERVICE_DEFAULT_PROBES.keys())
        user_token = _get_org_person_celonis_token(
            session,
            current_actor.organization.id,
            current_actor.person.id,
        )
        token_override = user_token.token_value if user_token else None
        gateway = CelonisGateway(get_settings())
        run_id = str(uuid4())
        authorized_count = 0
        for service_name in services:
            result = gateway.preflight(
                tenant_base_url=connection.tenant_base_url,
                probe_path="",
                service=service_name,
                token_override=token_override,
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
                    "source": "setup_wizard",
                    "run_id": run_id,
                },
            )
        total = len(services)
        if authorized_count == total:
            return _redirect_ui(
                f"/onboarding/celonis-setup?client_id={parsed_client_id}",
                ok=f"Preflight complete: all {total} services authorized (run {run_id})",
            )
        if authorized_count > 0:
            return _redirect_ui(
                f"/onboarding/celonis-setup?client_id={parsed_client_id}",
                ok=(
                    "Preflight complete with limited scope: "
                    f"{authorized_count}/{total} services authorized (run {run_id})"
                ),
            )
        return _redirect_ui(
            f"/onboarding/celonis-setup?client_id={parsed_client_id}",
            err=f"Preflight found {total - authorized_count}/{total} service issues (run {run_id})",
        )
    except Exception as exc:
        session.rollback()
        return _redirect_ui(
            f"/onboarding/celonis-setup?client_id={client_id}",
            err=f"Preflight failed: {exc}",
        )


