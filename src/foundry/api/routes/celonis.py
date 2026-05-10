from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.contracts import build_error_detail
from foundry.db import get_session
from foundry.error_codes import (
    CELONIS_DEPLOYMENT_CLIENT_MISMATCH,
    CELONIS_DEPLOYMENT_NOT_APPROVED,
    CELONIS_DEPLOYMENT_PACKAGE_MISMATCH,
    CELONIS_DEPLOYMENT_REQUEST_INVALID,
    CELONIS_DEPLOYMENT_REQUEST_NOT_FOUND,
    CELONIS_DEPLOYMENT_REQUEST_REQUIRED,
    CELONIS_ORG_SCOPE_MISMATCH,
    CELONIS_QUEST_NOT_FOUND,
    CELONIS_TOKEN_REQUIRED,
    CELONIS_TOOL_INVOCATION_ERROR,
    CELONIS_TOOL_NOT_FOUND,
    CELONIS_TOOL_UPSTREAM_ERROR,
)
from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import (
    ActivityLog,
    CelonisConnection,
    CelonisDeploymentRequest,
    CelonisDeploymentStatus,
    CelonisUserToken,
    Client,
    EntityType,
)
from foundry.schemas import (
    CelonisActionResult,
    CelonisDataAgentCatalogOut,
    CelonisDataAgentInvokeRequest,
    CelonisDataAgentInvokeResult,
    CelonisDataAgentToolOut,
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
from foundry.services.celonis_contracts import CelonisDataAgentInvocationContract
from foundry.services.celonis_data_agent_service import (
    CelonisDataAgentError,
    get_data_agent_tool_definition,
    invoke_data_agent_tool,
    list_data_agent_tools,
)
from foundry.services.quest_service import get_org_quest

router = APIRouter(prefix="/celonis", tags=["celonis"])


def _error_detail(*, error_code: str, message: str, request_id: str) -> dict[str, str]:
    return build_error_detail(
        error_code=error_code,
        message=message,
        request_id=request_id,
    ).model_dump()


def _raise_http_error(*, status_code: int, error_code: str, message: str, request_id: str) -> None:
    raise HTTPException(
        status_code=status_code,
        detail=_error_detail(error_code=error_code, message=message, request_id=request_id),
    )


@router.get("/data-agent/tools", response_model=CelonisDataAgentCatalogOut)
def list_data_agent_tool_catalog(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    token_configured = _resolve_actor_token_override(session, current_actor) is not None
    tools = [
        CelonisDataAgentToolOut(
            key=tool.key,
            display_name=tool.display_name,
            description=tool.description,
            required_inputs=list(tool.required_inputs),
            optional_inputs=list(tool.optional_inputs),
            read_only=tool.read_only,
            requires_user_token=tool.requires_user_token,
            requires_approved_deployment=tool.requires_approved_deployment,
            capability_group=tool.capability_group,
            source=tool.source,
        )
        for tool in list_data_agent_tools()
    ]
    return CelonisDataAgentCatalogOut(
        tool_count=len(tools),
        token_configured=token_configured,
        tools=tools,
    )


@router.post("/data-agent/tools/{tool_key}/invoke", response_model=CelonisDataAgentInvokeResult)
def invoke_data_agent_tool_route(
    tool_key: str,
    payload: CelonisDataAgentInvokeRequest,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    request_id = str(uuid4())
    tool_definition = get_data_agent_tool_definition(tool_key)
    if tool_definition is None:
        _raise_http_error(
            status_code=404,
            error_code=CELONIS_TOOL_NOT_FOUND,
            message="Celonis data-agent tool not found",
            request_id=request_id,
        )

    if payload.organization_id is not None and payload.organization_id != current_actor.organization.id:
        _raise_http_error(
            status_code=400,
            error_code=CELONIS_ORG_SCOPE_MISMATCH,
            message="organization_id does not match current actor organization",
            request_id=request_id,
        )

    connection = _get_connection_or_404(session, payload.client_id, current_actor.organization.id)
    token_override = _resolve_actor_token_override(session, current_actor)
    if not token_override:
        _raise_http_error(
            status_code=400,
            error_code=CELONIS_TOKEN_REQUIRED,
            message="Delegated Celonis user token required for data-agent tool invocation",
            request_id=request_id,
        )

    linked_quest = None
    if payload.quest_id is not None:
        linked_quest = get_org_quest(session, payload.quest_id, current_actor.organization.id)
        if linked_quest is None:
            _raise_http_error(
                status_code=404,
                error_code=CELONIS_QUEST_NOT_FOUND,
                message="Quest not found",
                request_id=request_id,
            )

    deployment_request = None
    deployment_request_id_for_contract = None
    if tool_definition.requires_approved_deployment:
        raw_deployment_request_id = payload.inputs.get("deployment_request_id")
        if not isinstance(raw_deployment_request_id, str) or not raw_deployment_request_id.strip():
            _raise_http_error(
                status_code=400,
                error_code=CELONIS_DEPLOYMENT_REQUEST_REQUIRED,
                message="Approved deployment_request_id required for Studio write tools",
                request_id=request_id,
            )
        try:
            deployment_request_id = UUID(raw_deployment_request_id.strip())
        except ValueError:
            _raise_http_error(
                status_code=400,
                error_code=CELONIS_DEPLOYMENT_REQUEST_INVALID,
                message="deployment_request_id must be a valid UUID",
                request_id=request_id,
            )
        deployment_request_id_for_contract = deployment_request_id
        deployment_request = session.get(CelonisDeploymentRequest, deployment_request_id)
        if deployment_request is None or deployment_request.organization_id != current_actor.organization.id:
            _raise_http_error(
                status_code=404,
                error_code=CELONIS_DEPLOYMENT_REQUEST_NOT_FOUND,
                message="Deployment request not found",
                request_id=request_id,
            )
        if deployment_request.client_id != payload.client_id:
            _raise_http_error(
                status_code=400,
                error_code=CELONIS_DEPLOYMENT_CLIENT_MISMATCH,
                message="Deployment request client does not match invocation client",
                request_id=request_id,
            )
        if deployment_request.status != CelonisDeploymentStatus.approved:
            _raise_http_error(
                status_code=400,
                error_code=CELONIS_DEPLOYMENT_NOT_APPROVED,
                message="Studio write tools require an approved deployment request",
                request_id=request_id,
            )
        package_key = payload.inputs.get("package_key")
        if isinstance(package_key, str) and package_key.strip() and deployment_request.target_package_key:
            if package_key.strip() != deployment_request.target_package_key:
                _raise_http_error(
                    status_code=400,
                    error_code=CELONIS_DEPLOYMENT_PACKAGE_MISMATCH,
                    message="Invocation package_key does not match approved deployment request",
                    request_id=request_id,
                )

    try:
        result = invoke_data_agent_tool(
            get_settings(),
            tenant_base_url=connection.tenant_base_url,
            token_override=token_override,
            tool_key=tool_key,
            inputs=payload.inputs,
        )
    except CelonisDataAgentError as exc:
        _raise_http_error(
            status_code=400,
            error_code=CELONIS_TOOL_INVOCATION_ERROR,
            message=str(exc),
            request_id=request_id,
        )
    except Exception as exc:
        _raise_http_error(
            status_code=502,
            error_code=CELONIS_TOOL_UPSTREAM_ERROR,
            message=f"Celonis data-agent invocation failed: {exc}",
            request_id=request_id,
        )

    invocation_contract = CelonisDataAgentInvocationContract(
        request_id=request_id,
        organization_id=current_actor.organization.id,
        client_id=payload.client_id,
        tenant_base_url=connection.tenant_base_url,
        tool_key=tool_key,
        inputs=payload.inputs,
        actor_person_id=current_actor.person.id,
        quest_id=payload.quest_id,
        deployment_request_id=deployment_request_id_for_contract,
    )
    metadata = invocation_contract.to_activity_metadata(
        input_keys=sorted(payload.inputs.keys()),
        read_only=tool_definition.read_only,
        requires_user_token=tool_definition.requires_user_token,
        requires_approved_deployment=tool_definition.requires_approved_deployment,
        capability_group=tool_definition.capability_group,
    )

    log_activity(
        session,
        entity_type=EntityType.celonis_connection,
        entity_id=connection.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        action="celonis_data_agent.tool_invoked",
        metadata=metadata,
    )
    if linked_quest is not None:
        log_activity(
            session,
            entity_type=EntityType.quest,
            entity_id=linked_quest.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            action="quest.celonis_data_agent_tool_invoked",
            metadata=metadata,
        )
    if deployment_request is not None:
        log_activity(
            session,
            entity_type=EntityType.celonis_deployment_request,
            entity_id=deployment_request.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            action="celonis_deployment_request.studio_write_tool_invoked",
            metadata=metadata,
        )

    return CelonisDataAgentInvokeResult(
        client_id=payload.client_id,
        tool_key=tool_key,
        request_id=request_id,
        ok=True,
        source=tool_definition.source,
        token_configured=True,
        quest_id=payload.quest_id,
        data=result,
    )


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
    request_id = str(uuid4())
    settings = get_settings()
    if payload.organization_id is not None and payload.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=400, detail="organization_id does not match current actor organization")
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

    log_activity(
        session,
        entity_type=EntityType.celonis_connection,
        entity_id=connection.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        action="celonis.extract",
        metadata={
            "request_id": request_id,
            "client_id": str(payload.client_id),
            "source_path": payload.source_path,
            "url": result.url,
            "status_code": result.status_code,
            "ok": result.ok,
        },
    )

    return CelonisActionResult(
        client_id=payload.client_id,
        request_id=request_id,
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
    request_id = str(uuid4())
    settings = get_settings()
    if payload.organization_id is not None and payload.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=400, detail="organization_id does not match current actor organization")
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

    log_activity(
        session,
        entity_type=EntityType.celonis_connection,
        entity_id=connection.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        action="celonis.import",
        metadata={
            "request_id": request_id,
            "client_id": str(payload.client_id),
            "target_path": payload.target_path,
            "url": result.url,
            "status_code": result.status_code,
            "ok": result.ok,
        },
    )

    return CelonisActionResult(
        client_id=payload.client_id,
        request_id=request_id,
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
