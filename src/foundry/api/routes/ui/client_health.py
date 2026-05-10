from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Response, Request
from sqlmodel import Session

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import Client, EntityType, SensitivityLevel
from foundry.services.delivery.activity_log import log_activity, log_created, log_updated
from foundry.settings import get_settings
from .shared import redirect_ui as _redirect_ui

router = APIRouter(tags=["ui"])


@router.get("/client-health-ui")
def client_health_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from . import _client_health_context, templates

    return templates.TemplateResponse(request, "client_health.html",
        _client_health_context(request, session, current_actor),
    )


@router.post("/client-health-ui/create-client", include_in_schema=False)
def client_health_create_client(
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
            metadata={"sensitivity_level": client.sensitivity_level.value},
        )
        return _redirect_ui("/client-health-ui", ok=f"Client '{client.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/client-health-ui", err=f"Create client failed: {exc}")


@router.post("/client-health-ui/projects/{project_id}/celonis-links", include_in_schema=False)
def client_health_update_project_celonis_links(
    project_id: UUID,
    celonis_package_url: str = Form(""),
    celonis_app_url: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from . import _get_org_project, _normalize_http_url

    project = _get_org_project(session, project_id, current_actor.organization.id)
    if project is None:
        return _redirect_ui("/client-health-ui", err="Project not found")

    try:
        project.celonis_package_url = _normalize_http_url(celonis_package_url) or None
        project.celonis_app_url = _normalize_http_url(celonis_app_url) or None
        session.add(project)
        session.commit()
        session.refresh(project)
        log_updated(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={
                "celonis_package_url_set": bool(project.celonis_package_url),
                "celonis_app_url_set": bool(project.celonis_app_url),
            },
        )
        return _redirect_ui("/client-health-ui", ok=f"Celonis links updated for '{project.name}'")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/client-health-ui", err=f"Update Celonis links failed: {exc}")


@router.post("/client-health-ui/projects/{project_id}/celonis-token", include_in_schema=False)
def client_health_update_user_celonis_token(
    project_id: UUID,
    token_value: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from . import _get_org_person_celonis_token, _get_org_project, _upsert_org_person_celonis_token

    project = _get_org_project(session, project_id, current_actor.organization.id)
    if project is None:
        return _redirect_ui("/client-health-ui", err="Project not found")

    try:
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
            action_label = "saved"
        else:
            if existing is not None:
                session.delete(existing)
            action_label = "cleared"

        session.commit()
        log_activity(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            action="project.celonis_token.updated",
            metadata={"token_present": bool(cleaned), "scope": "person+organization"},
        )
        return _redirect_ui("/client-health-ui", ok=f"Celonis token {action_label} for your account")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/client-health-ui", err=f"Update Celonis token failed: {exc}")


@router.post("/client-health-ui/projects/{project_id}/celonis-uptime", include_in_schema=False)
def client_health_check_uptime(
    project_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from . import _get_org_active_celonis_connection, _get_org_person_celonis_token, _get_org_project

    project = _get_org_project(session, project_id, current_actor.organization.id)
    if project is None:
        return _redirect_ui("/client-health-ui", err="Project not found")

    connection = _get_org_active_celonis_connection(
        session,
        project.client_id,
        current_actor.organization.id,
    )
    if connection is None:
        return _redirect_ui("/client-health-ui", err="No active Celonis connection for this client")

    try:
        settings = get_settings()
        gateway = CelonisGateway(settings)
        user_token = _get_org_person_celonis_token(
            session,
            current_actor.organization.id,
            current_actor.person.id,
        )
        result = gateway.preflight(
            tenant_base_url=connection.tenant_base_url,
            probe_path="/",
            service="core",
            token_override=user_token.token_value if user_token else None,
        )

        log_activity(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            action="project.celonis_uptime_check",
            metadata={
                "probe_url": result.probe_url,
                "permission_status": result.permission_status,
                "status_code": result.status_code,
                "reachable": result.reachable,
                "authenticated": result.authenticated,
                "has_user_token": bool(user_token and user_token.token_value),
            },
        )

        message = (
            f"Uptime check: {result.permission_status}"
            + (f" (status {result.status_code})" if result.status_code is not None else "")
        )
        if result.reachable and result.permission_status in {"authorized", "forbidden", "unauthorized"}:
            return _redirect_ui("/client-health-ui", ok=message)
        return _redirect_ui("/client-health-ui", err=message)
    except Exception as exc:
        return _redirect_ui("/client-health-ui", err=f"Uptime check failed: {exc}")


@router.post("/client-health-ui/projects/{project_id}/celonis-metrics-download", include_in_schema=False)
def client_health_download_metrics(
    project_id: UUID,
    metrics_path: str = Form("/apps/api/packages"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from . import _get_org_active_celonis_connection, _get_org_person_celonis_token, _get_org_project

    project = _get_org_project(session, project_id, current_actor.organization.id)
    if project is None:
        return _redirect_ui("/client-health-ui", err="Project not found")

    connection = _get_org_active_celonis_connection(
        session,
        project.client_id,
        current_actor.organization.id,
    )
    if connection is None:
        return _redirect_ui("/client-health-ui", err="No active Celonis connection for this client")

    source_path = (metrics_path or "").strip() or "/apps/api/packages"

    try:
        settings = get_settings()
        gateway = CelonisGateway(settings)
        user_token = _get_org_person_celonis_token(
            session,
            current_actor.organization.id,
            current_actor.person.id,
        )
        result = gateway.extract_full(
            tenant_base_url=connection.tenant_base_url,
            source_path=source_path,
            token_override=user_token.token_value if user_token else None,
        )

        body = result.body or ""
        log_activity(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            action="project.celonis_metrics_download",
            metadata={
                "path": source_path,
                "status_code": result.status_code,
                "ok": result.ok,
                "payload_size": len(body),
                "has_user_token": bool(user_token and user_token.token_value),
            },
        )

        if not result.ok:
            return _redirect_ui(
                "/client-health-ui",
                err=f"Metrics download failed with status {result.status_code}",
            )

        filename_safe_project = re.sub(r"[^a-z0-9-]+", "-", project.name.lower()).strip("-") or "project"
        filename = f"celonis-metrics-{filename_safe_project}.json"
        return Response(
            content=body,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        return _redirect_ui("/client-health-ui", err=f"Metrics download failed: {exc}")

