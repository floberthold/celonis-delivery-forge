from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import CelonisDeploymentStatus, Client, Organization, Quest
from foundry.services.celonis.celonis_deployment_service import list_deployment_requests
from foundry.services.celonis.celonis_data_agent_service import list_data_agent_tools
from foundry.services.platform.feature_rollout import enabled_domains_for_org
from foundry.settings import get_settings

router = APIRouter(tags=["ui"])

_UI_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "ui" / "templates"
_templates = Jinja2Templates(directory=str(_UI_TEMPLATE_DIR))


def _org_clients(session: Session, organization_id: UUID) -> list[Client]:
    return list(session.exec(select(Client).where(Client.organization_id == organization_id)).all())


def _org_enabled_domains(organization: Organization) -> list[str]:
    settings = get_settings()
    return enabled_domains_for_org(settings.ui_rollout_config_path, organization.slug)


def _is_domain_enabled_for_org(organization: Organization, required_domain: str) -> bool:
    enabled_domains = _org_enabled_domains(organization)
    return "*" in enabled_domains or required_domain in enabled_domains


def _redirect_if_domain_disabled(
    organization: Organization,
    required_domain: str,
    *,
    fallback_path: str,
):
    if _is_domain_enabled_for_org(organization, required_domain):
        return None

    error_message = f"Feature domain '{required_domain}' is disabled for this organization"

    return RedirectResponse(
        url=f"{fallback_path}?err={quote_plus(error_message)}",
        status_code=303,
    )


@router.get("/methodology-ui")
def methodology_ui(
    request: Request,
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    mcp_tools = [
        {
            "name": tool.display_name,
            "purpose": tool.description,
            "status": "available",
        }
        for tool in list_data_agent_tools()
    ]
    return _templates.TemplateResponse(request, "agentic-methodology.html",
        {
            "request": request,
            "current_person": current_actor.person,
            "active_organization": current_actor.organization,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "mcp_tools": mcp_tools,
        },
    )


@router.get("/celonis-tool-hub-ui", include_in_schema=False)
def celonis_tool_hub_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    gated = _redirect_if_domain_disabled(
        current_actor.organization,
        "celonis-agent",
        fallback_path="/dashboard",
    )
    if gated:
        return gated

    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda c: c.name.lower(),
    )
    approved_deployments = [
        req
        for req in list_deployment_requests(session, organization_id=current_actor.organization.id)
        if req.status == CelonisDeploymentStatus.approved
    ]
    client_map = {str(c.id): c.name for c in clients}
    approved_deployment_rows = [
        {
            "id": req.id,
            "client_name": client_map.get(str(req.client_id), str(req.client_id)),
            "target_package_key": req.target_package_key,
            "target_package_name": req.target_package_name,
        }
        for req in approved_deployments
    ]
    quest_rows = list(
        session.exec(
            select(Quest)
            .where(Quest.organization_id == current_actor.organization.id)
            .order_by(Quest.created_at.desc())
        ).all()
    )[:20]
    return _templates.TemplateResponse(request, "celonis_tool_hub.html",
        {
            "request": request,
            "active_organization": current_actor.organization,
            "current_person": current_actor.person,
            "error_message": request.query_params.get("err"),
            "clients": clients,
            "approved_deployments": approved_deployment_rows,
            "quests": quest_rows,
            "tools": list_data_agent_tools(),
        },
    )

