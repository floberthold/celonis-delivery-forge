import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urlparse
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
from markupsafe import Markup, escape
from sqlmodel import Session, select

from foundry.api.deps import AUTH_COOKIE_NAME, get_current_person, get_current_person_optional
from foundry.db import engine, get_session
from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import (
    ActivityLog,
    Asset,
    AssetMembership,
    AssetStatus,
    AssetType,
    CelonisConnection,
    Client,
    DecisionType,
    EntityType,
    GlobalRole,
    MembershipRole,
    Person,
    Project,
    ProjectMembership,
    ProjectStatus,
    ReviewArtifact,
    ReviewComment,
    ReviewDecision,
    ReviewRequest,
    ReviewStatus,
    SensitivityLevel,
    Template,
    TemplateInstantiation,
    TemplateLibrary,
    Todo,
    TodoPriority,
    TodoStatus,
    TemplateScope,
    TemplateStorageType,
)
from foundry.schemas import (
    ReviewDecisionCreate,
    ReviewRequestCreate,
    TemplateInstantiateCreate,
)
from foundry.settings import get_settings
from foundry.security import create_access_token, hash_password, verify_password
from foundry.services.project_service import ProjectService
from foundry.services.review_service import ReviewService
from foundry.services.activity_log import log_activity, log_created, log_updated
from foundry.services.template_service import TemplateService

router = APIRouter(tags=["ui"])
UI_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "ui" / "templates"


def _docu_dir() -> Path | None:
    candidates: list[Path] = [Path(__file__).resolve().parents[4] / "docu"]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "docu")
    candidates.append(Path.cwd() / "docu")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None



def _template_auth_context(request: Request) -> dict:
    with Session(engine) as session:
        person = get_current_person_optional(request=request, token=None, session=session)
    return {"current_person": person}


templates = Jinja2Templates(
    directory=str(UI_TEMPLATE_DIR),
    context_processors=[_template_auth_context],
)
loaders = [FileSystemLoader(str(UI_TEMPLATE_DIR))]
docu_template_dir = _docu_dir()
if docu_template_dir:
    loaders.insert(0, FileSystemLoader(str(docu_template_dir)))
templates.env.loader = ChoiceLoader(loaders)


def _normalize_http_url(value: str | None) -> str:
    if not value:
        return ""
    candidate = value.strip()
    if not candidate:
        return ""
    parsed = urlparse(candidate)
    if not parsed.scheme:
        candidate = f"https://{candidate}"
        parsed = urlparse(candidate)
    if parsed.scheme.lower() not in {"http", "https"}:
        return ""
    return candidate


def _clickable_url(value: str | None) -> Markup:
    if not value:
        return Markup("-")
    label = value.strip()
    if not label:
        return Markup("-")
    href = _normalize_http_url(label)
    if not href:
        return Markup(escape(label))
    return Markup(
        f'<a href="{escape(href)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>'
    )


templates.env.filters["normalized_url"] = _normalize_http_url
templates.env.filters["clickable_url"] = _clickable_url


def _redirect_dashboard(*, ok: str | None = None, err: str | None = None) -> RedirectResponse:
    if ok:
        return RedirectResponse(url=f"/dashboard?ok={quote_plus(ok)}", status_code=303)
    if err:
        return RedirectResponse(url=f"/dashboard?err={quote_plus(err)}", status_code=303)
    return RedirectResponse(url="/dashboard", status_code=303)


def _redirect_ui(path: str, *, ok: str | None = None, err: str | None = None) -> RedirectResponse:
    if ok:
        return RedirectResponse(url=f"{path}?ok={quote_plus(ok)}", status_code=303)
    if err:
        return RedirectResponse(url=f"{path}?err={quote_plus(err)}", status_code=303)
    return RedirectResponse(url=path, status_code=303)


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError(f"Invalid UUID for {field_name}") from exc


def _parse_optional_uuid(value: str | None, field_name: str) -> UUID | None:
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    return _parse_uuid(candidate, field_name)


def _parse_optional_datetime(value: str | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    try:
        return datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"Invalid datetime for {field_name}") from exc


def _parse_json_object(value: str, *, field_name: str) -> dict:
    if not value.strip():
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return parsed


def _normalize_redirect_path(path: str | None, fallback: str) -> str:
    if not path:
        return fallback
    candidate = path.strip()
    if not candidate.startswith("/"):
        return fallback
    return candidate


def _redirect_login(*, err: str | None = None) -> RedirectResponse:
    if err:
        return RedirectResponse(url=f"/login?err={quote_plus(err)}", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


def _validate_todo_scope(*, person_id: UUID | None, client_id: UUID | None, project_id: UUID | None) -> None:
    selected = sum(1 for value in [person_id, client_id, project_id] if value is not None)
    if selected != 1:
        raise ValueError("Exactly one of person_id, client_id, project_id is required")


def _timeline_by_entity_keys(
    session: Session,
    entity_keys: list[tuple[EntityType, UUID]],
) -> list[dict]:
    unique_keys = sorted(set(entity_keys), key=lambda item: (item[0].value, str(item[1])))
    if not unique_keys:
        return []

    key_set = set(unique_keys)
    rows = [
        row
        for row in session.exec(select(ActivityLog)).all()
        if (row.entity_type, row.entity_id) in key_set
    ]
    rows.sort(key=lambda row: row.timestamp, reverse=True)

    people = list(session.exec(select(Person)).all())
    person_name_by_id = {person.id: person.name for person in people}

    return [
        {
            "id": row.id,
            "timestamp": row.timestamp,
            "action": row.action,
            "entity_type": row.entity_type.value,
            "entity_id": row.entity_id,
            "actor_id": row.actor_id,
            "actor_name": person_name_by_id.get(row.actor_id, "Unknown"),
            "metadata_json": row.metadata_json,
        }
        for row in rows
    ]


def _dashboard_context(request: Request, session: Session) -> dict:
    clients = sorted(session.exec(select(Client)).all(), key=lambda row: row.created_at, reverse=True)
    projects = sorted(session.exec(select(Project)).all(), key=lambda row: row.created_at, reverse=True)
    assets = sorted(session.exec(select(Asset)).all(), key=lambda row: row.created_at, reverse=True)
    reviews = sorted(
        session.exec(select(ReviewRequest)).all(), key=lambda row: row.created_at, reverse=True
    )
    timeline = sorted(session.exec(select(ActivityLog)).all(), key=lambda row: row.timestamp, reverse=True)
    people = sorted(session.exec(select(Person)).all(), key=lambda row: row.created_at, reverse=True)
    memberships = session.exec(select(ProjectMembership)).all()
    celonis_connections = sorted(
        session.exec(select(CelonisConnection)).all(), key=lambda row: row.updated_at, reverse=True
    )
    connection_by_client = {row.client_id: row for row in celonis_connections}

    return {
        "request": request,
        "ok_message": request.query_params.get("ok"),
        "error_message": request.query_params.get("err"),
        "clients_count": len(clients),
        "projects_count": len(projects),
        "assets_count": len(assets),
        "reviews_count": len(reviews),
        "timeline_count": len(timeline),
        "clients": clients[:10],
        "projects": projects[:10],
        "assets": assets[:10],
        "reviews": reviews[:10],
        "timeline": timeline[:10],
        "form_clients": clients,
        "form_projects": projects,
        "form_assets": assets,
        "form_reviews": reviews,
        "form_people": people,
        "form_memberships": memberships,
        "celonis_connections": celonis_connections,
        "connection_by_client": connection_by_client,
        "sensitivity_options": [row.value for row in SensitivityLevel],
        "project_status_options": [row.value for row in ProjectStatus],
        "asset_type_options": [row.value for row in AssetType],
        "membership_role_options": [row.value for row in MembershipRole],
        "global_role_options": [row.value for row in GlobalRole],
    }


@router.get("/")
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=307)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error_message": request.query_params.get("err"),
        },
    )


@router.post("/login", include_in_schema=False)
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next_path: str = Form("/dashboard"),
    session: Session = Depends(get_session),
):
    person = session.exec(select(Person).where(Person.email == email.strip().lower())).first()
    if not person or not verify_password(password, person.hashed_password):
        return _redirect_login(err="Invalid credentials")

    token = create_access_token(str(person.id))
    target_path = _normalize_redirect_path(next_path, "/dashboard")
    response = RedirectResponse(url=target_path, status_code=303)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=get_settings().jwt_expire_minutes * 60,
        path="/",
    )
    return response


@router.post("/logout", include_in_schema=False)
def logout() -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return response


@router.get("/dashboard")
def dashboard(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse("dashboard.html", _dashboard_context(request, session))


@router.post("/dashboard/create-client", include_in_schema=False)
def dashboard_create_client(
    name: str = Form(...),
    tenant_url: str = Form(...),
    sensitivity_level: str = Form("medium"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        client = Client(
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
            actor_id=current_person.id,
            metadata={"sensitivity_level": client.sensitivity_level.value},
        )
        return _redirect_dashboard(ok=f"Client '{client.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Create client failed: {exc}")


@router.post("/dashboard/create-person", include_in_schema=False)
def dashboard_create_person(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role_global: str = Form("member"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        person = Person(
            name=name.strip(),
            email=email.strip().lower(),
            hashed_password=hash_password(password),
            role_global=GlobalRole(role_global),
        )
        session.add(person)
        session.commit()
        session.refresh(person)
        log_created(
            session,
            entity_type=EntityType.person,
            entity_id=person.id,
            actor_id=current_person.id,
            metadata={"email": person.email, "role_global": person.role_global.value},
        )
        return _redirect_dashboard(ok=f"Person '{person.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Create person failed: {exc}")


@router.post("/dashboard/create-project", include_in_schema=False)
def dashboard_create_project(
    name: str = Form(...),
    client_id: str = Form(...),
    status: str = Form("planned"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        project = Project(
            name=name.strip(),
            client_id=_parse_uuid(client_id, "client_id"),
            status=ProjectStatus(status),
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        log_created(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_person.id,
            metadata={"client_id": str(project.client_id), "status": project.status.value},
        )
        return _redirect_dashboard(ok=f"Project '{project.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Create project failed: {exc}")


@router.post("/dashboard/create-membership", include_in_schema=False)
def dashboard_create_membership(
    project_id: str = Form(...),
    person_id: str = Form(...),
    role: str = Form("contributor"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        membership = ProjectMembership(
            project_id=_parse_uuid(project_id, "project_id"),
            person_id=_parse_uuid(person_id, "person_id"),
            role=MembershipRole(role),
        )
        session.add(membership)
        session.commit()
        session.refresh(membership)
        log_created(
            session,
            entity_type=EntityType.membership,
            entity_id=membership.id,
            actor_id=current_person.id,
            metadata={
                "project_id": str(membership.project_id),
                "person_id": str(membership.person_id),
                "role": membership.role.value,
            },
        )
        return _redirect_dashboard(ok="Project membership created")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Create membership failed: {exc}")


@router.post("/dashboard/create-asset", include_in_schema=False)
def dashboard_create_asset(
    name: str = Form(...),
    asset_type: str = Form(...),
    project_id: str = Form(...),
    client_id: str = Form(...),
    celonis_url: str = Form(""),
    asset_identifier: str = Form(""),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        asset = Asset(
            name=name.strip(),
            type=AssetType(asset_type),
            project_id=_parse_uuid(project_id, "project_id"),
            client_id=_parse_uuid(client_id, "client_id"),
            celonis_url=celonis_url.strip() or None,
            asset_identifier=asset_identifier.strip() or None,
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)
        log_created(
            session,
            entity_type=EntityType.asset,
            entity_id=asset.id,
            actor_id=current_person.id,
            metadata={
                "type": asset.type.value,
                "project_id": str(asset.project_id),
                "client_id": str(asset.client_id),
            },
        )
        return _redirect_dashboard(ok=f"Asset '{asset.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Create asset failed: {exc}")


@router.post("/dashboard/create-review", include_in_schema=False)
def dashboard_create_review(
    asset_id: str = Form(...),
    project_id: str = Form(...),
    author_id: str = Form(...),
    reviewer_id: str = Form(...),
    change_summary: str = Form(...),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        payload = ReviewRequestCreate(
            asset_id=_parse_uuid(asset_id, "asset_id"),
            project_id=_parse_uuid(project_id, "project_id"),
            author_id=_parse_uuid(author_id, "author_id"),
            reviewer_id=_parse_uuid(reviewer_id, "reviewer_id"),
            change_summary=change_summary.strip(),
        )
        review = ReviewService.submit_for_review(session, payload)
        log_created(
            session,
            entity_type=EntityType.review,
            entity_id=review.id,
            actor_id=current_person.id,
            metadata={"asset_id": str(review.asset_id), "project_id": str(review.project_id)},
        )
        return _redirect_dashboard(ok="Review submitted")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Submit review failed: {exc}")


@router.post("/dashboard/review-decision", include_in_schema=False)
def dashboard_review_decision(
    review_id: str = Form(...),
    reviewer_id: str = Form(...),
    decision: str = Form(...),
    note: str = Form(""),
    snippet_worthy: str | None = Form(None),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        payload = ReviewDecisionCreate(
            review_id=_parse_uuid(review_id, "review_id"),
            reviewer_id=_parse_uuid(reviewer_id, "reviewer_id"),
            decision=DecisionType(decision),
            note=note.strip() or None,
            snippet_worthy=snippet_worthy is not None,
        )
        review = ReviewService.decide_review(session, payload)
        log_updated(
            session,
            entity_type=EntityType.review,
            entity_id=review.id,
            actor_id=current_person.id,
            metadata={"decision": payload.decision.value, "status": review.status.value},
        )
        return _redirect_dashboard(ok="Review decision applied")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Review decision failed: {exc}")


@router.post("/dashboard/celonis-connection", include_in_schema=False)
def dashboard_celonis_connection(
    client_id: str = Form(...),
    tenant_base_url: str = Form(...),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        existing = session.exec(
            select(CelonisConnection).where(CelonisConnection.client_id == parsed_client_id)
        ).first()
        if existing:
            existing.tenant_base_url = tenant_base_url.strip()
            existing.is_active = True
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
            return _redirect_dashboard(ok="Celonis connection updated")

        row = CelonisConnection(client_id=parsed_client_id, tenant_base_url=tenant_base_url.strip())
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
        return _redirect_dashboard(ok="Celonis connection created")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Celonis connection failed: {exc}")


@router.post("/dashboard/celonis-extract", include_in_schema=False)
def dashboard_celonis_extract(
    client_id: str = Form(...),
    source_path: str = Form("/process-mining/api/teams"),
    session: Session = Depends(get_session),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        connection = session.exec(
            select(CelonisConnection).where(CelonisConnection.client_id == parsed_client_id)
        ).first()
        if connection is None or not connection.is_active:
            return _redirect_dashboard(err="No active Celonis connection for selected client")

        result = CelonisGateway(get_settings()).extract(
            tenant_base_url=connection.tenant_base_url,
            source_path=source_path,
        )
        if result.ok:
            return _redirect_dashboard(ok=f"Extract ok ({result.status_code}) from {result.url}")
        return _redirect_dashboard(err=f"Extract failed ({result.status_code}) from {result.url}")
    except Exception as exc:
        return _redirect_dashboard(err=f"Celonis extract failed: {exc}")


@router.post("/dashboard/celonis-import", include_in_schema=False)
def dashboard_celonis_import(
    client_id: str = Form(...),
    target_path: str = Form("/process-mining/api/teams"),
    payload_json: str = Form('{"name":"foundry-import"}'),
    session: Session = Depends(get_session),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        connection = session.exec(
            select(CelonisConnection).where(CelonisConnection.client_id == parsed_client_id)
        ).first()
        if connection is None or not connection.is_active:
            return _redirect_dashboard(err="No active Celonis connection for selected client")

        payload = json.loads(payload_json) if payload_json.strip() else {}
        if not isinstance(payload, dict):
            return _redirect_dashboard(err="Payload must be a JSON object")

        result = CelonisGateway(get_settings()).import_data(
            tenant_base_url=connection.tenant_base_url,
            target_path=target_path,
            payload=payload,
        )
        if result.ok:
            return _redirect_dashboard(ok=f"Import ok ({result.status_code}) to {result.url}")
        return _redirect_dashboard(err=f"Import failed ({result.status_code}) to {result.url}")
    except Exception as exc:
        return _redirect_dashboard(err=f"Celonis import failed: {exc}")


@router.get("/projects-ui")
def projects_ui(request: Request, session: Session = Depends(get_session)):
    projects = sorted(session.exec(select(Project)).all(), key=lambda row: row.created_at, reverse=True)
    clients = list(session.exec(select(Client)).all())
    memberships = list(session.exec(select(ProjectMembership)).all())

    client_name_by_id = {client.id: client.name for client in clients}
    membership_total_by_project: dict = {}
    membership_active_by_project: dict = {}
    for membership in memberships:
        membership_total_by_project[membership.project_id] = (
            membership_total_by_project.get(membership.project_id, 0) + 1
        )
        if membership.end_date is None:
            membership_active_by_project[membership.project_id] = (
                membership_active_by_project.get(membership.project_id, 0) + 1
            )

    rows = [
        {
            "id": project.id,
            "name": project.name,
            "client_id": project.client_id,
            "status": project.status.value,
            "client_name": client_name_by_id.get(project.client_id, "Unknown"),
            "membership_summary": (
                f"{membership_active_by_project.get(project.id, 0)} active / "
                f"{membership_total_by_project.get(project.id, 0)} total"
            ),
            "created_at": project.created_at,
        }
        for project in projects
    ]

    return templates.TemplateResponse(
        "projects.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_id": request.query_params.get("edit"),
            "rows": rows,
            "clients": clients,
            "project_status_options": [row.value for row in ProjectStatus],
        },
    )


@router.post("/projects-ui/create", include_in_schema=False)
def projects_ui_create(
    name: str = Form(...),
    client_id: str = Form(...),
    status: str = Form("planned"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        project = Project(
            name=name.strip(),
            client_id=_parse_uuid(client_id, "client_id"),
            status=ProjectStatus(status),
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        log_created(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_person.id,
            metadata={"client_id": str(project.client_id), "status": project.status.value},
        )
        return _redirect_ui("/projects-ui", ok=f"Project '{project.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/projects-ui", err=f"Create project failed: {exc}")


@router.post("/projects-ui/update", include_in_schema=False)
def projects_ui_update(
    project_id: str = Form(...),
    name: str = Form(...),
    client_id: str = Form(...),
    status: str = Form(...),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        project = session.get(Project, parsed_project_id)
        if not project:
            return _redirect_ui("/projects-ui", err="Project not found")

        parsed_status = ProjectStatus(status)
        if parsed_status == ProjectStatus.active:
            ProjectService.ensure_can_be_active(session, parsed_project_id)
        if parsed_status == ProjectStatus.closed:
            ProjectService.ensure_can_be_closed(session, parsed_project_id)

        project.name = name.strip()
        project.client_id = _parse_uuid(client_id, "client_id")
        project.status = parsed_status
        session.add(project)
        session.commit()
        session.refresh(project)
        log_updated(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_person.id,
            metadata={"client_id": str(project.client_id), "status": project.status.value},
        )
        return _redirect_ui("/projects-ui", ok="Project updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/projects-ui", err=f"Update project failed: {exc}")


@router.post("/projects-ui/delete", include_in_schema=False)
def projects_ui_delete(project_id: str = Form(...), session: Session = Depends(get_session)):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        project = session.get(Project, parsed_project_id)
        if not project:
            return _redirect_ui("/projects-ui", err="Project not found")

        has_memberships = session.exec(
            select(ProjectMembership).where(ProjectMembership.project_id == parsed_project_id)
        ).first()
        if has_memberships:
            return _redirect_ui("/projects-ui", err="Cannot delete project with memberships")

        has_assets = session.exec(select(Asset).where(Asset.project_id == parsed_project_id)).first()
        if has_assets:
            return _redirect_ui("/projects-ui", err="Cannot delete project with assets")

        has_reviews = session.exec(
            select(ReviewRequest).where(ReviewRequest.project_id == parsed_project_id)
        ).first()
        if has_reviews:
            return _redirect_ui("/projects-ui", err="Cannot delete project with reviews")

        has_todos = session.exec(select(Todo).where(Todo.project_id == parsed_project_id)).first()
        if has_todos:
            return _redirect_ui("/projects-ui", err="Cannot delete project with todos")

        session.delete(project)
        session.commit()
        return _redirect_ui("/projects-ui", ok="Project deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/projects-ui", err=f"Delete project failed: {exc}")


@router.get("/assets-ui")
def assets_ui(request: Request, session: Session = Depends(get_session)):
    assets = sorted(session.exec(select(Asset)).all(), key=lambda row: row.created_at, reverse=True)
    projects = list(session.exec(select(Project)).all())
    clients = list(session.exec(select(Client)).all())

    project_name_by_id = {project.id: project.name for project in projects}
    client_name_by_id = {client.id: client.name for client in clients}

    rows = [
        {
            "id": asset.id,
            "name": asset.name,
            "type": asset.type.value,
            "status": asset.status.value,
            "project_id": asset.project_id,
            "client_id": asset.client_id,
            "celonis_url": asset.celonis_url,
            "asset_identifier": asset.asset_identifier,
            "project_name": project_name_by_id.get(asset.project_id, "Unknown"),
            "client_name": client_name_by_id.get(asset.client_id, "Unknown"),
            "created_at": asset.created_at,
        }
        for asset in assets
    ]

    return templates.TemplateResponse(
        "assets.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_id": request.query_params.get("edit"),
            "rows": rows,
            "projects": projects,
            "clients": clients,
            "asset_type_options": [row.value for row in AssetType],
            "asset_status_options": [row.value for row in AssetStatus],
        },
    )


@router.post("/assets-ui/create", include_in_schema=False)
def assets_ui_create(
    name: str = Form(...),
    asset_type: str = Form(...),
    status: str = Form("draft"),
    project_id: str = Form(...),
    client_id: str = Form(...),
    celonis_url: str = Form(""),
    asset_identifier: str = Form(""),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        asset = Asset(
            name=name.strip(),
            type=AssetType(asset_type),
            status=AssetStatus(status),
            project_id=_parse_uuid(project_id, "project_id"),
            client_id=_parse_uuid(client_id, "client_id"),
            celonis_url=celonis_url.strip() or None,
            asset_identifier=asset_identifier.strip() or None,
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)
        log_created(
            session,
            entity_type=EntityType.asset,
            entity_id=asset.id,
            actor_id=current_person.id,
            metadata={
                "type": asset.type.value,
                "project_id": str(asset.project_id),
                "client_id": str(asset.client_id),
            },
        )
        return _redirect_ui("/assets-ui", ok=f"Asset '{asset.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/assets-ui", err=f"Create asset failed: {exc}")


@router.post("/assets-ui/update", include_in_schema=False)
def assets_ui_update(
    asset_id: str = Form(...),
    name: str = Form(...),
    asset_type: str = Form(...),
    status: str = Form(...),
    project_id: str = Form(...),
    client_id: str = Form(...),
    celonis_url: str = Form(""),
    asset_identifier: str = Form(""),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        asset = session.get(Asset, _parse_uuid(asset_id, "asset_id"))
        if not asset:
            return _redirect_ui("/assets-ui", err="Asset not found")

        asset.name = name.strip()
        asset.type = AssetType(asset_type)
        asset.status = AssetStatus(status)
        asset.project_id = _parse_uuid(project_id, "project_id")
        asset.client_id = _parse_uuid(client_id, "client_id")
        asset.celonis_url = celonis_url.strip() or None
        asset.asset_identifier = asset_identifier.strip() or None
        session.add(asset)
        session.commit()
        session.refresh(asset)
        log_updated(
            session,
            entity_type=EntityType.asset,
            entity_id=asset.id,
            actor_id=current_person.id,
            metadata={
                "type": asset.type.value,
                "project_id": str(asset.project_id),
                "client_id": str(asset.client_id),
            },
        )
        return _redirect_ui("/assets-ui", ok="Asset updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/assets-ui", err=f"Update asset failed: {exc}")


@router.post("/assets-ui/delete", include_in_schema=False)
def assets_ui_delete(asset_id: str = Form(...), session: Session = Depends(get_session)):
    try:
        parsed_asset_id = _parse_uuid(asset_id, "asset_id")
        asset = session.get(Asset, parsed_asset_id)
        if not asset:
            return _redirect_ui("/assets-ui", err="Asset not found")

        has_memberships = session.exec(
            select(AssetMembership).where(AssetMembership.asset_id == parsed_asset_id)
        ).first()
        if has_memberships:
            return _redirect_ui("/assets-ui", err="Cannot delete asset with memberships")

        has_reviews = session.exec(
            select(ReviewRequest).where(ReviewRequest.asset_id == parsed_asset_id)
        ).first()
        if has_reviews:
            return _redirect_ui("/assets-ui", err="Cannot delete asset with reviews")

        session.delete(asset)
        session.commit()
        return _redirect_ui("/assets-ui", ok="Asset deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/assets-ui", err=f"Delete asset failed: {exc}")


@router.get("/reviews-ui")
def reviews_ui(request: Request, session: Session = Depends(get_session)):
    reviews = sorted(
        session.exec(select(ReviewRequest)).all(), key=lambda row: row.created_at, reverse=True
    )
    assets = list(session.exec(select(Asset)).all())
    projects = list(session.exec(select(Project)).all())
    people = list(session.exec(select(Person)).all())

    asset_name_by_id = {asset.id: asset.name for asset in assets}
    project_name_by_id = {project.id: project.name for project in projects}
    person_name_by_id = {person.id: person.name for person in people}

    rows = [
        {
            "id": review.id,
            "asset_id": review.asset_id,
            "project_id": review.project_id,
            "author_id": review.author_id,
            "reviewer_id": review.reviewer_id,
            "asset_name": asset_name_by_id.get(review.asset_id, "Unknown"),
            "project_name": project_name_by_id.get(review.project_id, "Unknown"),
            "author_name": person_name_by_id.get(review.author_id, "Unknown"),
            "reviewer_name": person_name_by_id.get(review.reviewer_id, "Unknown"),
            "status": review.status.value,
            "change_summary": review.change_summary,
            "snippet_worthy": review.snippet_worthy,
            "created_at": review.created_at,
            "submitted_at": review.submitted_at,
            "decision_at": review.decision_at,
        }
        for review in reviews
    ]

    return templates.TemplateResponse(
        "reviews.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_id": request.query_params.get("edit"),
            "rows": rows,
            "assets": assets,
            "projects": projects,
            "people": people,
            "review_status_options": [row.value for row in ReviewStatus],
        },
    )


@router.post("/reviews-ui/create", include_in_schema=False)
def reviews_ui_create(
    asset_id: str = Form(...),
    project_id: str = Form(...),
    author_id: str = Form(...),
    reviewer_id: str = Form(...),
    change_summary: str = Form(...),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        payload = ReviewRequestCreate(
            asset_id=_parse_uuid(asset_id, "asset_id"),
            project_id=_parse_uuid(project_id, "project_id"),
            author_id=_parse_uuid(author_id, "author_id"),
            reviewer_id=_parse_uuid(reviewer_id, "reviewer_id"),
            change_summary=change_summary.strip(),
        )
        review = ReviewService.submit_for_review(session, payload)
        log_created(
            session,
            entity_type=EntityType.review,
            entity_id=review.id,
            actor_id=current_person.id,
            metadata={"asset_id": str(review.asset_id), "project_id": str(review.project_id)},
        )
        return _redirect_ui("/reviews-ui", ok="Review created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/reviews-ui", err=f"Create review failed: {exc}")


@router.post("/reviews-ui/update", include_in_schema=False)
def reviews_ui_update(
    review_id: str = Form(...),
    asset_id: str = Form(...),
    project_id: str = Form(...),
    author_id: str = Form(...),
    reviewer_id: str = Form(...),
    status: str = Form(...),
    change_summary: str = Form(...),
    snippet_worthy: str | None = Form(None),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        review = session.get(ReviewRequest, _parse_uuid(review_id, "review_id"))
        if not review:
            return _redirect_ui("/reviews-ui", err="Review not found")

        review.asset_id = _parse_uuid(asset_id, "asset_id")
        review.project_id = _parse_uuid(project_id, "project_id")
        review.author_id = _parse_uuid(author_id, "author_id")
        review.reviewer_id = _parse_uuid(reviewer_id, "reviewer_id")
        review.status = ReviewStatus(status)
        review.change_summary = change_summary.strip()
        review.snippet_worthy = snippet_worthy is not None
        session.add(review)
        session.commit()
        session.refresh(review)
        log_updated(
            session,
            entity_type=EntityType.review,
            entity_id=review.id,
            actor_id=current_person.id,
            metadata={"status": review.status.value, "snippet_worthy": review.snippet_worthy},
        )
        return _redirect_ui("/reviews-ui", ok="Review updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/reviews-ui", err=f"Update review failed: {exc}")


@router.post("/reviews-ui/delete", include_in_schema=False)
def reviews_ui_delete(review_id: str = Form(...), session: Session = Depends(get_session)):
    try:
        parsed_review_id = _parse_uuid(review_id, "review_id")
        review = session.get(ReviewRequest, parsed_review_id)
        if not review:
            return _redirect_ui("/reviews-ui", err="Review not found")

        has_artifacts = session.exec(
            select(ReviewArtifact).where(ReviewArtifact.review_request_id == parsed_review_id)
        ).first()
        if has_artifacts:
            return _redirect_ui("/reviews-ui", err="Cannot delete review with artifacts")

        has_comments = session.exec(
            select(ReviewComment).where(ReviewComment.review_request_id == parsed_review_id)
        ).first()
        if has_comments:
            return _redirect_ui("/reviews-ui", err="Cannot delete review with comments")

        has_decisions = session.exec(
            select(ReviewDecision).where(ReviewDecision.review_request_id == parsed_review_id)
        ).first()
        if has_decisions:
            return _redirect_ui("/reviews-ui", err="Cannot delete review with decisions")

        session.delete(review)
        session.commit()
        return _redirect_ui("/reviews-ui", ok="Review deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/reviews-ui", err=f"Delete review failed: {exc}")


@router.get("/people-ui")
def people_ui(request: Request, session: Session = Depends(get_session)):
    people = sorted(session.exec(select(Person)).all(), key=lambda row: row.created_at, reverse=True)
    rows = [
        {
            "id": person.id,
            "name": person.name,
            "email": person.email,
            "role_global": person.role_global.value,
            "created_at": person.created_at,
        }
        for person in people
    ]
    return templates.TemplateResponse(
        "people.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_id": request.query_params.get("edit"),
            "rows": rows,
            "global_role_options": [row.value for row in GlobalRole],
        },
    )


@router.post("/people-ui/create", include_in_schema=False)
def people_ui_create(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role_global: str = Form("member"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        person = Person(
            name=name.strip(),
            email=email.strip().lower(),
            hashed_password=hash_password(password),
            role_global=GlobalRole(role_global),
        )
        session.add(person)
        session.commit()
        session.refresh(person)
        log_created(
            session,
            entity_type=EntityType.person,
            entity_id=person.id,
            actor_id=current_person.id,
            metadata={"email": person.email, "role_global": person.role_global.value},
        )
        return _redirect_ui("/people-ui", ok=f"Person '{person.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/people-ui", err=f"Create person failed: {exc}")


@router.post("/people-ui/update", include_in_schema=False)
def people_ui_update(
    person_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    role_global: str = Form(...),
    password: str = Form(""),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        parsed_person_id = _parse_uuid(person_id, "person_id")
        person = session.get(Person, parsed_person_id)
        if not person:
            return _redirect_ui("/people-ui", err="Person not found")

        person.name = name.strip()
        person.email = email.strip().lower()
        person.role_global = GlobalRole(role_global)
        if password.strip():
            person.hashed_password = hash_password(password)
        session.add(person)
        session.commit()
        session.refresh(person)
        log_updated(
            session,
            entity_type=EntityType.person,
            entity_id=person.id,
            actor_id=current_person.id,
            metadata={"email": person.email, "role_global": person.role_global.value},
        )
        return _redirect_ui("/people-ui", ok="Person updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/people-ui", err=f"Update person failed: {exc}")


@router.post("/people-ui/delete", include_in_schema=False)
def people_ui_delete(person_id: str = Form(...), session: Session = Depends(get_session)):
    try:
        parsed_person_id = _parse_uuid(person_id, "person_id")
        person = session.get(Person, parsed_person_id)
        if not person:
            return _redirect_ui("/people-ui", err="Person not found")

        membership_ref = session.exec(
            select(ProjectMembership).where(ProjectMembership.person_id == parsed_person_id)
        ).first() or session.exec(
            select(AssetMembership).where(AssetMembership.person_id == parsed_person_id)
        ).first()
        review_ref = session.exec(
            select(ReviewRequest).where(
                (ReviewRequest.author_id == parsed_person_id)
                | (ReviewRequest.reviewer_id == parsed_person_id)
            )
        ).first()
        comment_ref = session.exec(
            select(ReviewComment).where(ReviewComment.author_id == parsed_person_id)
        ).first()
        decision_ref = session.exec(
            select(ReviewDecision).where(ReviewDecision.reviewer_id == parsed_person_id)
        ).first()
        activity_ref = session.exec(
            select(ActivityLog).where(ActivityLog.actor_id == parsed_person_id)
        ).first()
        todo_ref = session.exec(
            select(Todo).where(
                (Todo.created_by == parsed_person_id)
                | (Todo.assignee_id == parsed_person_id)
                | (Todo.person_id == parsed_person_id)
            )
        ).first()

        if membership_ref or review_ref or comment_ref or decision_ref or activity_ref or todo_ref:
            return _redirect_ui("/people-ui", err="Cannot delete person with existing references")

        session.delete(person)
        session.commit()
        return _redirect_ui("/people-ui", ok="Person deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/people-ui", err=f"Delete person failed: {exc}")


@router.get("/clients-ui")
def clients_ui(request: Request, session: Session = Depends(get_session)):
    clients = sorted(session.exec(select(Client)).all(), key=lambda row: row.created_at, reverse=True)
    rows = [
        {
            "id": client.id,
            "name": client.name,
            "tenant_url": client.tenant_url,
            "sensitivity_level": client.sensitivity_level.value,
            "created_at": client.created_at,
        }
        for client in clients
    ]
    return templates.TemplateResponse(
        "clients.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_id": request.query_params.get("edit"),
            "rows": rows,
            "sensitivity_options": [row.value for row in SensitivityLevel],
        },
    )


@router.post("/clients-ui/create", include_in_schema=False)
def clients_ui_create(
    name: str = Form(...),
    tenant_url: str = Form(...),
    sensitivity_level: str = Form("medium"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        client = Client(
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
            actor_id=current_person.id,
            metadata={"sensitivity_level": client.sensitivity_level.value},
        )
        return _redirect_ui("/clients-ui", ok=f"Client '{client.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/clients-ui", err=f"Create client failed: {exc}")


@router.post("/clients-ui/update", include_in_schema=False)
def clients_ui_update(
    client_id: str = Form(...),
    name: str = Form(...),
    tenant_url: str = Form(...),
    sensitivity_level: str = Form(...),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        client = session.get(Client, _parse_uuid(client_id, "client_id"))
        if not client:
            return _redirect_ui("/clients-ui", err="Client not found")

        client.name = name.strip()
        client.tenant_url = tenant_url.strip()
        client.sensitivity_level = SensitivityLevel(sensitivity_level)
        session.add(client)
        session.commit()
        session.refresh(client)
        log_updated(
            session,
            entity_type=EntityType.client,
            entity_id=client.id,
            actor_id=current_person.id,
            metadata={"sensitivity_level": client.sensitivity_level.value},
        )
        return _redirect_ui("/clients-ui", ok="Client updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/clients-ui", err=f"Update client failed: {exc}")


@router.post("/clients-ui/delete", include_in_schema=False)
def clients_ui_delete(client_id: str = Form(...), session: Session = Depends(get_session)):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        client = session.get(Client, parsed_client_id)
        if not client:
            return _redirect_ui("/clients-ui", err="Client not found")

        project_ref = session.exec(select(Project).where(Project.client_id == parsed_client_id)).first()
        asset_ref = session.exec(select(Asset).where(Asset.client_id == parsed_client_id)).first()
        connection_ref = session.exec(
            select(CelonisConnection).where(CelonisConnection.client_id == parsed_client_id)
        ).first()
        todo_ref = session.exec(select(Todo).where(Todo.client_id == parsed_client_id)).first()

        if project_ref or asset_ref or connection_ref or todo_ref:
            return _redirect_ui("/clients-ui", err="Cannot delete client with existing references")

        session.delete(client)
        session.commit()
        return _redirect_ui("/clients-ui", ok="Client deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/clients-ui", err=f"Delete client failed: {exc}")


@router.post("/todos-ui/create", include_in_schema=False)
def todos_ui_create(
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    due_at: str = Form(""),
    assignee_id: str = Form(""),
    created_by: str = Form(...),
    person_id: str = Form(""),
    client_id: str = Form(""),
    project_id: str = Form(""),
    redirect_to: str = Form("/dashboard"),
    session: Session = Depends(get_session),
):
    target_path = _normalize_redirect_path(redirect_to, "/dashboard")
    try:
        parsed_person_id = _parse_optional_uuid(person_id, "person_id")
        parsed_client_id = _parse_optional_uuid(client_id, "client_id")
        parsed_project_id = _parse_optional_uuid(project_id, "project_id")
        _validate_todo_scope(
            person_id=parsed_person_id,
            client_id=parsed_client_id,
            project_id=parsed_project_id,
        )

        todo = Todo(
            title=title.strip(),
            description=description.strip() or None,
            priority=TodoPriority(priority),
            due_at=_parse_optional_datetime(due_at, "due_at"),
            assignee_id=_parse_optional_uuid(assignee_id, "assignee_id"),
            created_by=_parse_uuid(created_by, "created_by"),
            person_id=parsed_person_id,
            client_id=parsed_client_id,
            project_id=parsed_project_id,
        )
        session.add(todo)
        session.commit()

        metadata = {
            "person_id": str(todo.person_id) if todo.person_id else None,
            "client_id": str(todo.client_id) if todo.client_id else None,
            "project_id": str(todo.project_id) if todo.project_id else None,
            "status": todo.status.value,
            "priority": todo.priority.value,
        }
        session.add(
            ActivityLog(
                entity_type=EntityType.todo,
                entity_id=todo.id,
                actor_id=todo.created_by,
                action="todo.created",
                metadata_json=metadata,
            )
        )
        session.commit()
        return _redirect_ui(target_path, ok="Todo created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Create todo failed: {exc}")


@router.post("/todos-ui/update", include_in_schema=False)
def todos_ui_update(
    todo_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    status: str = Form("open"),
    priority: str = Form("medium"),
    due_at: str = Form(""),
    assignee_id: str = Form(""),
    redirect_to: str = Form("/dashboard"),
    session: Session = Depends(get_session),
):
    target_path = _normalize_redirect_path(redirect_to, "/dashboard")
    try:
        parsed_todo_id = _parse_uuid(todo_id, "todo_id")
        todo = session.get(Todo, parsed_todo_id)
        if not todo:
            return _redirect_ui(target_path, err="Todo not found")

        todo.title = title.strip()
        todo.description = description.strip() or None
        todo.status = TodoStatus(status)
        todo.priority = TodoPriority(priority)
        todo.due_at = _parse_optional_datetime(due_at, "due_at")
        todo.assignee_id = _parse_optional_uuid(assignee_id, "assignee_id")
        todo.updated_at = datetime.utcnow()
        if todo.status == TodoStatus.done:
            todo.completed_at = datetime.utcnow()
        else:
            todo.completed_at = None

        session.add(todo)
        session.commit()

        session.add(
            ActivityLog(
                entity_type=EntityType.todo,
                entity_id=todo.id,
                actor_id=todo.created_by,
                action="todo.updated",
                metadata_json={
                    "status": todo.status.value,
                    "priority": todo.priority.value,
                },
            )
        )
        session.commit()
        return _redirect_ui(target_path, ok="Todo updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Update todo failed: {exc}")


@router.post("/todos-ui/delete", include_in_schema=False)
def todos_ui_delete(
    todo_id: str = Form(...),
    redirect_to: str = Form("/dashboard"),
    session: Session = Depends(get_session),
):
    target_path = _normalize_redirect_path(redirect_to, "/dashboard")
    try:
        parsed_todo_id = _parse_uuid(todo_id, "todo_id")
        todo = session.get(Todo, parsed_todo_id)
        if not todo:
            return _redirect_ui(target_path, err="Todo not found")

        actor_id = todo.created_by
        session.delete(todo)
        session.commit()

        session.add(
            ActivityLog(
                entity_type=EntityType.todo,
                entity_id=parsed_todo_id,
                actor_id=actor_id,
                action="todo.deleted",
                metadata_json={},
            )
        )
        session.commit()
        return _redirect_ui(target_path, ok="Todo deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Delete todo failed: {exc}")


@router.get("/people-ui/{person_id}/overview")
def person_overview_ui(person_id: str, request: Request, session: Session = Depends(get_session)):
    try:
        parsed_person_id = _parse_uuid(person_id, "person_id")
    except ValueError as exc:
        return _redirect_ui("/people-ui", err=str(exc))

    person = session.get(Person, parsed_person_id)
    if not person:
        return _redirect_ui("/people-ui", err="Person not found")

    memberships = list(
        session.exec(select(ProjectMembership).where(ProjectMembership.person_id == parsed_person_id)).all()
    )
    project_ids = {membership.project_id for membership in memberships}
    all_projects = list(session.exec(select(Project)).all())
    projects = [project for project in all_projects if project.id in project_ids] if project_ids else []
    client_ids = {project.client_id for project in projects}

    asset_memberships = list(
        session.exec(select(AssetMembership).where(AssetMembership.person_id == parsed_person_id)).all()
    )
    direct_asset_ids = {membership.asset_id for membership in asset_memberships}
    all_assets = list(session.exec(select(Asset)).all())
    project_assets = [asset for asset in all_assets if asset.project_id in project_ids] if project_ids else []
    direct_assets = [asset for asset in all_assets if asset.id in direct_asset_ids] if direct_asset_ids else []
    asset_by_id = {asset.id: asset for asset in [*project_assets, *direct_assets]}
    assets = sorted(asset_by_id.values(), key=lambda row: row.created_at, reverse=True)

    reviews = list(
        session.exec(
            select(ReviewRequest).where(
                (ReviewRequest.author_id == parsed_person_id) | (ReviewRequest.reviewer_id == parsed_person_id)
            )
        ).all()
    )
    review_ids = {review.id for review in reviews}

    all_todos = list(session.exec(select(Todo)).all())
    todos = [
        row
        for row in all_todos
        if row.person_id == parsed_person_id
        or row.assignee_id == parsed_person_id
        or (row.project_id in project_ids if row.project_id else False)
        or (row.client_id in client_ids if row.client_id else False)
    ]
    todos.sort(key=lambda row: row.created_at, reverse=True)
    todo_ids = {todo.id for todo in todos}

    entity_keys: list[tuple[EntityType, UUID]] = [(EntityType.person, parsed_person_id)]
    entity_keys.extend((EntityType.membership, row.id) for row in memberships)
    entity_keys.extend((EntityType.project, row.id) for row in projects)
    entity_keys.extend((EntityType.client, client_id_value) for client_id_value in client_ids)
    entity_keys.extend((EntityType.asset, row.id) for row in assets)
    entity_keys.extend((EntityType.review, review_id) for review_id in review_ids)
    entity_keys.extend((EntityType.todo, todo_id) for todo_id in todo_ids)
    timeline_rows = _timeline_by_entity_keys(session, entity_keys)

    project_name_by_id = {project.id: project.name for project in projects}
    project_status_by_id = {project.id: project.status.value for project in projects}
    project_client_id_by_project_id = {project.id: project.client_id for project in projects}
    all_clients = list(session.exec(select(Client)).all())
    client_name_by_id = {client.id: client.name for client in all_clients if client.id in client_ids}
    people = list(session.exec(select(Person)).all())
    person_name_by_id = {row.id: row.name for row in people}
    asset_name_by_id = {asset.id: asset.name for asset in assets}

    todo_rows = [
        {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "status": row.status.value,
            "priority": row.priority.value,
            "due_at": row.due_at,
            "assignee_id": row.assignee_id,
            "assignee_name": person_name_by_id.get(row.assignee_id, "-") if row.assignee_id else "-",
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in todos
    ]
    membership_rows = [
        {
            "project_id": membership.project_id,
            "project_name": project_name_by_id.get(membership.project_id, "-"),
            "client_name": client_name_by_id.get(project_client_id_by_project_id[membership.project_id], "-")
            if membership.project_id in project_client_id_by_project_id
            else "-",
            "status": project_status_by_id.get(membership.project_id, "-"),
            "role": membership.role.value,
            "start_date": membership.start_date,
        }
        for membership in memberships
    ]

    return templates.TemplateResponse(
        "person_overview.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_todo_id": request.query_params.get("edit_todo"),
            "person": person,
            "memberships": memberships,
            "membership_rows": membership_rows,
            "projects": projects,
            "assets": assets,
            "reviews": reviews,
            "todo_rows": todo_rows,
            "timeline_rows": timeline_rows,
            "project_name_by_id": project_name_by_id,
            "client_name_by_id": client_name_by_id,
            "person_name_by_id": person_name_by_id,
            "asset_name_by_id": asset_name_by_id,
            "people": people,
            "todo_status_options": [row.value for row in TodoStatus],
            "todo_priority_options": [row.value for row in TodoPriority],
        },
    )


@router.get("/clients-ui/{client_id}/overview")
def client_overview_ui(client_id: str, request: Request, session: Session = Depends(get_session)):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
    except ValueError as exc:
        return _redirect_ui("/clients-ui", err=str(exc))

    client = session.get(Client, parsed_client_id)
    if not client:
        return _redirect_ui("/clients-ui", err="Client not found")

    projects = list(session.exec(select(Project).where(Project.client_id == parsed_client_id)).all())
    project_ids = {project.id for project in projects}
    assets = list(session.exec(select(Asset).where(Asset.client_id == parsed_client_id)).all())
    asset_ids = {asset.id for asset in assets}
    all_memberships = list(session.exec(select(ProjectMembership)).all())
    memberships = [row for row in all_memberships if row.project_id in project_ids] if project_ids else []
    person_ids = {membership.person_id for membership in memberships}

    all_reviews = list(session.exec(select(ReviewRequest)).all())
    reviews = [
        row
        for row in all_reviews
        if row.project_id in project_ids or row.asset_id in asset_ids
    ]
    person_ids.update(review.author_id for review in reviews)
    person_ids.update(review.reviewer_id for review in reviews)

    all_people = list(session.exec(select(Person)).all())
    people = [row for row in all_people if row.id in person_ids] if person_ids else []
    person_name_by_id = {person.id: person.name for person in people}

    all_todos = list(session.exec(select(Todo)).all())
    todos = [
        row
        for row in all_todos
        if row.client_id == parsed_client_id or (row.project_id in project_ids if row.project_id else False)
    ]
    todos.sort(key=lambda row: row.created_at, reverse=True)
    todo_ids = {todo.id for todo in todos}

    entity_keys: list[tuple[EntityType, UUID]] = [(EntityType.client, parsed_client_id)]
    entity_keys.extend((EntityType.project, row.id) for row in projects)
    entity_keys.extend((EntityType.membership, row.id) for row in memberships)
    entity_keys.extend((EntityType.asset, row.id) for row in assets)
    entity_keys.extend((EntityType.review, row.id) for row in reviews)
    entity_keys.extend((EntityType.person, person_id_value) for person_id_value in person_ids)
    entity_keys.extend((EntityType.todo, todo_id) for todo_id in todo_ids)
    timeline_rows = _timeline_by_entity_keys(session, entity_keys)

    project_name_by_id = {project.id: project.name for project in projects}
    asset_name_by_id = {asset.id: asset.name for asset in assets}
    all_people_name_by_id = {person.id: person.name for person in all_people}

    todo_rows = [
        {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "status": row.status.value,
            "priority": row.priority.value,
            "due_at": row.due_at,
            "assignee_id": row.assignee_id,
            "assignee_name": all_people_name_by_id.get(row.assignee_id, "-") if row.assignee_id else "-",
            "project_id": row.project_id,
            "project_name": project_name_by_id.get(row.project_id, "-") if row.project_id else "-",
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in todos
    ]

    return templates.TemplateResponse(
        "client_overview.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_todo_id": request.query_params.get("edit_todo"),
            "client": client,
            "projects": projects,
            "assets": assets,
            "reviews": reviews,
            "people": people,
            "memberships": memberships,
            "todo_rows": todo_rows,
            "timeline_rows": timeline_rows,
            "person_name_by_id": person_name_by_id,
            "project_name_by_id": project_name_by_id,
            "asset_name_by_id": asset_name_by_id,
            "all_people": all_people,
            "todo_status_options": [row.value for row in TodoStatus],
            "todo_priority_options": [row.value for row in TodoPriority],
        },
    )


@router.get("/projects-ui/{project_id}/overview")
def project_overview_ui(project_id: str, request: Request, session: Session = Depends(get_session)):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
    except ValueError as exc:
        return _redirect_ui("/projects-ui", err=str(exc))

    project = session.get(Project, parsed_project_id)
    if not project:
        return _redirect_ui("/projects-ui", err="Project not found")

    client = session.get(Client, project.client_id)
    memberships = list(
        session.exec(select(ProjectMembership).where(ProjectMembership.project_id == parsed_project_id)).all()
    )
    person_ids = {membership.person_id for membership in memberships}
    all_people = list(session.exec(select(Person)).all())
    people = [row for row in all_people if row.id in person_ids] if person_ids else []
    person_name_by_id = {person.id: person.name for person in people}

    assets = list(session.exec(select(Asset).where(Asset.project_id == parsed_project_id)).all())
    asset_ids = {asset.id for asset in assets}
    reviews = list(session.exec(select(ReviewRequest).where(ReviewRequest.project_id == parsed_project_id)).all())
    for review in reviews:
        person_ids.add(review.author_id)
        person_ids.add(review.reviewer_id)

    todos = list(session.exec(select(Todo).where(Todo.project_id == parsed_project_id)).all())
    todos.sort(key=lambda row: row.created_at, reverse=True)
    todo_ids = {todo.id for todo in todos}

    entity_keys: list[tuple[EntityType, UUID]] = [(EntityType.project, parsed_project_id)]
    entity_keys.append((EntityType.client, project.client_id))
    entity_keys.extend((EntityType.membership, row.id) for row in memberships)
    entity_keys.extend((EntityType.asset, asset_id) for asset_id in asset_ids)
    entity_keys.extend((EntityType.review, review.id) for review in reviews)
    entity_keys.extend((EntityType.person, person_id_value) for person_id_value in person_ids)
    entity_keys.extend((EntityType.todo, todo_id) for todo_id in todo_ids)
    timeline_rows = _timeline_by_entity_keys(session, entity_keys)

    asset_name_by_id = {asset.id: asset.name for asset in assets}
    all_people_name_by_id = {person.id: person.name for person in all_people}
    todo_rows = [
        {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "status": row.status.value,
            "priority": row.priority.value,
            "due_at": row.due_at,
            "assignee_id": row.assignee_id,
            "assignee_name": all_people_name_by_id.get(row.assignee_id, "-") if row.assignee_id else "-",
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in todos
    ]

    return templates.TemplateResponse(
        "project_overview.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_todo_id": request.query_params.get("edit_todo"),
            "project": project,
            "client": client,
            "memberships": memberships,
            "people": people,
            "assets": assets,
            "reviews": reviews,
            "todo_rows": todo_rows,
            "timeline_rows": timeline_rows,
            "person_name_by_id": person_name_by_id,
            "asset_name_by_id": asset_name_by_id,
            "all_people": all_people,
            "todo_status_options": [row.value for row in TodoStatus],
            "todo_priority_options": [row.value for row in TodoPriority],
        },
    )


@router.get("/templates-ui")
def templates_ui(request: Request, session: Session = Depends(get_session)):
    libraries = sorted(
        session.exec(select(TemplateLibrary)).all(), key=lambda row: row.created_at, reverse=True
    )
    templates_rows = sorted(
        session.exec(select(Template)).all(), key=lambda row: row.created_at, reverse=True
    )
    instantiations = sorted(
        session.exec(select(TemplateInstantiation)).all(),
        key=lambda row: row.created_at,
        reverse=True,
    )
    clients = sorted(session.exec(select(Client)).all(), key=lambda row: row.created_at, reverse=True)
    projects = sorted(session.exec(select(Project)).all(), key=lambda row: row.created_at, reverse=True)
    people = sorted(session.exec(select(Person)).all(), key=lambda row: row.created_at, reverse=True)

    library_name_by_id = {library.id: library.name for library in libraries}
    rows = [
        {
            "id": row.id,
            "title": row.title,
            "library_id": row.library_id,
            "library_name": library_name_by_id.get(row.library_id, "Unknown"),
            "category": row.category,
            "storage_type": row.storage_type.value,
            "storage_url": row.storage_url,
            "requires_review": row.requires_review,
            "is_active": row.is_active,
            "created_at": row.created_at,
        }
        for row in templates_rows
    ]

    return templates.TemplateResponse(
        "templates.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "rows": rows,
            "libraries": libraries,
            "clients": clients,
            "projects": projects,
            "people": people,
            "instantiations": instantiations[:20],
            "template_scope_options": [row.value for row in TemplateScope],
            "template_storage_options": [row.value for row in TemplateStorageType],
        },
    )


@router.post("/templates-ui/create-library", include_in_schema=False)
def templates_ui_create_library(
    name: str = Form(...),
    scope: str = Form("global_scope"),
    client_id: str = Form(""),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        parsed_scope = TemplateScope(scope)
        parsed_client_id = _parse_uuid(client_id, "client_id") if client_id.strip() else None
        library = TemplateLibrary(
            name=name.strip(),
            scope=parsed_scope,
            client_id=parsed_client_id,
        )
        session.add(library)
        session.commit()
        session.refresh(library)
        log_created(
            session,
            entity_type=EntityType.template,
            entity_id=library.id,
            actor_id=current_person.id,
            metadata={
                "scope": library.scope.value,
                "client_id": str(library.client_id) if library.client_id else None,
            },
        )
        return _redirect_ui("/templates-ui", ok=f"Library '{library.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/templates-ui", err=f"Create library failed: {exc}")


@router.post("/templates-ui/create-template", include_in_schema=False)
def templates_ui_create_template(
    library_id: str = Form(...),
    title: str = Form(...),
    category: str = Form(...),
    storage_type: str = Form(...),
    storage_url: str = Form(...),
    created_by: str = Form(...),
    description: str = Form(""),
    requires_review: str | None = Form(None),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        template = Template(
            library_id=_parse_uuid(library_id, "library_id"),
            title=title.strip(),
            category=category.strip(),
            description=description.strip() or None,
            storage_type=TemplateStorageType(storage_type),
            storage_url=storage_url.strip(),
            created_by=_parse_uuid(created_by, "created_by"),
            requires_review=requires_review is not None,
        )
        session.add(template)
        session.commit()
        session.refresh(template)
        log_created(
            session,
            entity_type=EntityType.template,
            entity_id=template.id,
            actor_id=current_person.id,
            metadata={"library_id": str(template.library_id), "category": template.category},
        )
        return _redirect_ui("/templates-ui", ok=f"Template '{template.title}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/templates-ui", err=f"Create template failed: {exc}")


@router.post("/templates-ui/instantiate", include_in_schema=False)
def templates_ui_instantiate(
    template_id: str = Form(...),
    project_id: str = Form(...),
    client_id: str = Form(...),
    author_id: str = Form(...),
    reviewer_id: str = Form(...),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        template = session.get(Template, _parse_uuid(template_id, "template_id"))
        if not template or not template.is_active:
            return _redirect_ui("/templates-ui", err="Template not found or inactive")

        instantiation = TemplateService.instantiate_template(
            session,
            template=template,
            payload=TemplateInstantiateCreate(
                project_id=_parse_uuid(project_id, "project_id"),
                client_id=_parse_uuid(client_id, "client_id"),
                author_id=_parse_uuid(author_id, "author_id"),
                reviewer_id=_parse_uuid(reviewer_id, "reviewer_id"),
            ),
        )
        log_created(
            session,
            entity_type=EntityType.template_instantiation,
            entity_id=instantiation.id,
            actor_id=current_person.id,
            metadata={"template_id": str(template.id), "project_id": str(instantiation.project_id)},
        )
        return _redirect_ui("/templates-ui", ok="Template instantiated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/templates-ui", err=f"Template instantiation failed: {exc}")


@router.get("/timeline-ui")
def timeline_ui(request: Request, session: Session = Depends(get_session)):
    rows = sorted(session.exec(select(ActivityLog)).all(), key=lambda row: row.timestamp, reverse=True)
    people = list(session.exec(select(Person)).all())

    return templates.TemplateResponse(
        "timeline.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_id": request.query_params.get("edit"),
            "rows": rows,
            "people": people,
            "entity_type_options": [row.value for row in EntityType],
        },
    )


@router.post("/timeline-ui/create", include_in_schema=False)
def timeline_ui_create(
    action: str = Form(...),
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    actor_id: str = Form(...),
    metadata_json: str = Form("{}"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        row = ActivityLog(
            action=action.strip(),
            entity_type=EntityType(entity_type),
            entity_id=_parse_uuid(entity_id, "entity_id"),
            actor_id=_parse_uuid(actor_id, "actor_id"),
            metadata_json=_parse_json_object(metadata_json, field_name="metadata_json"),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        log_activity(
            session,
            entity_type=row.entity_type,
            entity_id=row.id,
            actor_id=current_person.id,
            action="timeline_entry.created",
            metadata={"target_entity_id": str(row.entity_id), "target_action": row.action},
        )
        return _redirect_ui("/timeline-ui", ok="Timeline event created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/timeline-ui", err=f"Create timeline event failed: {exc}")


@router.post("/timeline-ui/update", include_in_schema=False)
def timeline_ui_update(
    log_id: str = Form(...),
    action: str = Form(...),
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    actor_id: str = Form(...),
    metadata_json: str = Form("{}"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        row = session.get(ActivityLog, _parse_uuid(log_id, "log_id"))
        if not row:
            return _redirect_ui("/timeline-ui", err="Timeline entry not found")

        row.action = action.strip()
        row.entity_type = EntityType(entity_type)
        row.entity_id = _parse_uuid(entity_id, "entity_id")
        row.actor_id = _parse_uuid(actor_id, "actor_id")
        row.metadata_json = _parse_json_object(metadata_json, field_name="metadata_json")
        session.add(row)
        session.commit()
        session.refresh(row)
        log_activity(
            session,
            entity_type=row.entity_type,
            entity_id=row.id,
            actor_id=current_person.id,
            action="timeline_entry.updated",
            metadata={"target_entity_id": str(row.entity_id), "target_action": row.action},
        )
        return _redirect_ui("/timeline-ui", ok="Timeline event updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/timeline-ui", err=f"Update timeline event failed: {exc}")


@router.post("/timeline-ui/delete", include_in_schema=False)
def timeline_ui_delete(
    log_id: str = Form(...),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        row = session.get(ActivityLog, _parse_uuid(log_id, "log_id"))
        if not row:
            return _redirect_ui("/timeline-ui", err="Timeline entry not found")
        deleted_row_id = row.id
        deleted_entity_type = row.entity_type
        deleted_entity_id = row.entity_id
        deleted_action = row.action
        session.delete(row)
        session.commit()
        log_activity(
            session,
            entity_type=deleted_entity_type,
            entity_id=deleted_row_id,
            actor_id=current_person.id,
            action="timeline_entry.deleted",
            metadata={"target_entity_id": str(deleted_entity_id), "target_action": deleted_action},
        )
        return _redirect_ui("/timeline-ui", ok="Timeline event deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/timeline-ui", err=f"Delete timeline event failed: {exc}")


@router.get("/docu/user.html")
def docu_user(request: Request):
    return templates.TemplateResponse("user.html", {"request": request})


@router.get("/docu/developer.html")
def docu_developer(request: Request):
    return templates.TemplateResponse("developer.html", {"request": request})


@router.get("/tenant-ui")
def tenant_ui(request: Request):
    tenant_url = request.query_params.get("url") or "https://id.celonis.cloud/user/ui/login"
    return templates.TemplateResponse(
        "tenant.html",
        {
            "request": request,
            "tenant_url": tenant_url,
        },
    )