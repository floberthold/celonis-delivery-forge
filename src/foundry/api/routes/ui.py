import json
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlsplit, urlunsplit
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
from markupsafe import Markup, escape
from sqlmodel import Session, select

from foundry.api.deps import (
    AUTH_COOKIE_NAME,
    CurrentActor,
    get_current_actor_with_org,
    get_current_person,
    get_current_person_optional,
)
from foundry.db import engine, get_session
from foundry.integrations.celonis_import import CelonisGateway
from foundry.integrations.gitlab_gateway import GitLabGateway
from foundry.models import (
    ActivityLog,
    Asset,
    AssetMembership,
    AssetStatus,
    AssetType,
    Agent,
    CelonisConnection,
    CelonisSnapshot,
    Client,
    DecisionType,
    DeliveryFile,
    EntityType,
    FileSource,
    GitLabPipelineRun,
    GitLabRepo,
    GlobalRole,
    KpiBookEntry,
    KpiDefinition,
    KpiStatus,
    KpiVersion,
    MembershipRole,
    OrganizationMembership,
    OrganizationRole,
    Person,
    Quest,
    QuestAssignment,
    QuestObjective,
    QuestPriority,
    QuestSource,
    QuestStatus,
    Project,
    ProjectMembership,
    ProjectStatus,
    ReviewArtifact,
    ReviewComment,
    ReviewDecision,
    ReviewRequest,
    ReviewStatus,
    SensitivityLevel,
    SnapshotDataModel,
    SnapshotJob,
    SnapshotKnowledgeModel,
    SnapshotPackage,
    SnapshotRunStatus,
    SnapshotTask,
    Template,
    TemplateInstantiation,
    TemplateLibrary,
    LibraryType,
    Todo,
    TodoComment,
    TodoDocument,
    TodoDocumentSource,
    TodoLink,
    TodoPriority,
    TodoStatus,
    TodoTag,
    TemplateScope,
    TemplateStorageType,
)
from foundry.schemas import (
    KpiBookEntryCreate,
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
from foundry.services.todo_service import (
    delete_todo_with_children,
    make_document_url,
    normalize_tag_name,
    remove_document_file,
    render_markdown,
    store_uploaded_document,
)
from foundry.services.snapshot_export_service import (
    build_snapshot_delta_report,
    build_snapshot_export,
    build_snapshot_replay_plan,
)
from foundry.services.quest_service import (
    create_assignment as create_assignment_service,
    create_objective as create_objective_service,
    create_quest as create_quest_service,
    delete_assignment as delete_assignment_service,
    delete_objective as delete_objective_service,
    delete_quest as delete_quest_service,
    get_org_quest as get_org_quest_service,
    list_assignments as list_assignments_service,
    list_objectives as list_objectives_service,
    pause_quest as pause_quest_service,
    replace_quest as replace_quest_service,
    reprioritize_quest as reprioritize_quest_service,
    update_assignment as update_assignment_service,
    update_objective as update_objective_service,
    update_quest as update_quest_service,
)

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
templates.env.filters["render_markdown"] = render_markdown


def _with_query_params(path: str, **params: str | None) -> str:
    parts = urlsplit(path)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for key, value in params.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value
    return urlunsplit(("", "", parts.path or "/", urlencode(query), parts.fragment))


def _redirect_dashboard(*, ok: str | None = None, err: str | None = None) -> RedirectResponse:
    if ok:
        return RedirectResponse(url=_with_query_params("/dashboard", ok=ok), status_code=303)
    if err:
        return RedirectResponse(url=_with_query_params("/dashboard", err=err), status_code=303)
    return RedirectResponse(url="/dashboard", status_code=303)


def _redirect_ui(path: str, *, ok: str | None = None, err: str | None = None) -> RedirectResponse:
    if ok:
        return RedirectResponse(url=_with_query_params(path, ok=ok), status_code=303)
    if err:
        return RedirectResponse(url=_with_query_params(path, err=err), status_code=303)
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


def _store_uploaded_delivery_file(upload_file: UploadFile) -> tuple[str, int]:
    settings = get_settings()
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    allowed_extensions = {".pdf", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"}
    allowed_mime_types = {
        "application/pdf",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "application/csv",
        "application/octet-stream",
    }

    original_name = (upload_file.filename or "file").strip() or "file"
    source_path = Path(original_name)
    suffix = source_path.suffix.lower()
    if suffix not in allowed_extensions:
        raise ValueError(
            "Unsupported file extension. Allowed: "
            + ", ".join(sorted(allowed_extensions))
        )

    mime_type = (upload_file.content_type or "").lower()
    if mime_type and mime_type not in allowed_mime_types:
        raise ValueError(f"Unsupported content type: {mime_type}")

    upload_file.file.seek(0, 2)
    file_size_bytes = upload_file.file.tell()
    upload_file.file.seek(0)
    if file_size_bytes > settings.delivery_file_max_upload_bytes:
        raise ValueError(
            f"File exceeds max allowed size of {settings.delivery_file_max_upload_bytes} bytes"
        )

    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", source_path.stem).strip("-._") or "file"
    safe_suffix = re.sub(r"[^A-Za-z0-9.]+", "", source_path.suffix)[:16]
    stored_filename = f"{uuid4().hex}_{safe_stem[:48]}{safe_suffix}"
    destination = uploads_dir / stored_filename

    upload_file.file.seek(0)
    with destination.open("wb") as handle:
        shutil.copyfileobj(upload_file.file, handle)

    return stored_filename, destination.stat().st_size


def _redirect_login(*, err: str | None = None) -> RedirectResponse:
    if err:
        return RedirectResponse(url=f"/login?err={quote_plus(err)}", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


def _validate_todo_scope(*, person_id: UUID | None, client_id: UUID | None, project_id: UUID | None) -> None:
    selected = sum(1 for value in [person_id, client_id, project_id] if value is not None)
    if selected != 1:
        raise ValueError("Exactly one of person_id, client_id, project_id is required")


def _parse_todo_scope_ref(scope_ref: str | None) -> tuple[UUID | None, UUID | None, UUID | None]:
    if not scope_ref or not scope_ref.strip():
        return None, None, None
    raw_value = scope_ref.strip()
    try:
        scope_kind, scope_id = raw_value.split(":", 1)
    except ValueError as exc:
        raise ValueError("Invalid todo scope reference") from exc

    parsed_scope_id = _parse_uuid(scope_id, "scope_id")
    if scope_kind == "person":
        return parsed_scope_id, None, None
    if scope_kind == "client":
        return None, parsed_scope_id, None
    if scope_kind == "project":
        return None, None, parsed_scope_id
    raise ValueError("Invalid todo scope type")


def _resolve_todo_scope(
    *,
    scope_ref: str | None,
    person_id: str | None,
    client_id: str | None,
    project_id: str | None,
) -> tuple[UUID | None, UUID | None, UUID | None]:
    scoped_person_id, scoped_client_id, scoped_project_id = _parse_todo_scope_ref(scope_ref)
    parsed_person_id = scoped_person_id or _parse_optional_uuid(person_id, "person_id")
    parsed_client_id = scoped_client_id or _parse_optional_uuid(client_id, "client_id")
    parsed_project_id = scoped_project_id or _parse_optional_uuid(project_id, "project_id")
    _validate_todo_scope(
        person_id=parsed_person_id,
        client_id=parsed_client_id,
        project_id=parsed_project_id,
    )
    return parsed_person_id, parsed_client_id, parsed_project_id


def _todo_activity_metadata(todo: Todo) -> dict:
    return {
        "title": todo.title,
        "person_id": str(todo.person_id) if todo.person_id else None,
        "client_id": str(todo.client_id) if todo.client_id else None,
        "project_id": str(todo.project_id) if todo.project_id else None,
        "assignee_id": str(todo.assignee_id) if todo.assignee_id else None,
        "status": todo.status.value,
        "priority": todo.priority.value,
        "has_long_description": bool(todo.long_description_markdown and todo.long_description_markdown.strip()),
    }


def _org_clients(session: Session, organization_id: UUID) -> list[Client]:
    return list(session.exec(select(Client).where(Client.organization_id == organization_id)).all())


def _org_people(session: Session, organization_id: UUID) -> list[Person]:
    memberships = list(
        session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id
            )
        ).all()
    )
    if not memberships:
        return []
    person_ids = {membership.person_id for membership in memberships}
    return [
        row
        for row in session.exec(select(Person)).all()
        if row.id in person_ids
    ]


def _org_agents(session: Session, organization_id: UUID) -> list[Agent]:
    return list(session.exec(select(Agent).where(Agent.organization_id == organization_id)).all())


def _org_projects(session: Session, organization_id: UUID) -> list[Project]:
    return list(session.exec(select(Project).where(Project.organization_id == organization_id)).all())


def _org_assets(session: Session, organization_id: UUID) -> list[Asset]:
    return list(session.exec(select(Asset).where(Asset.organization_id == organization_id)).all())


def _org_reviews(session: Session, organization_id: UUID) -> list[ReviewRequest]:
    project_ids = [project.id for project in _org_projects(session, organization_id)]
    if not project_ids:
        return []
    project_id_set = set(project_ids)
    return [
        row
        for row in session.exec(select(ReviewRequest)).all()
        if row.project_id in project_id_set
    ]


def _org_todos(session: Session, organization_id: UUID) -> list[Todo]:
    return list(session.exec(select(Todo).where(Todo.organization_id == organization_id)).all())


def _org_quests(session: Session, organization_id: UUID) -> list[Quest]:
    return list(session.exec(select(Quest).where(Quest.organization_id == organization_id)).all())


def _org_activity_logs(session: Session, organization_id: UUID) -> list[ActivityLog]:
    return list(
        session.exec(select(ActivityLog).where(ActivityLog.organization_id == organization_id)).all()
    )


def _org_celonis_connections(session: Session, organization_id: UUID) -> list[CelonisConnection]:
    return list(
        session.exec(
            select(CelonisConnection).where(CelonisConnection.organization_id == organization_id)
        ).all()
    )


def _org_template_libraries(session: Session, organization_id: UUID) -> list[TemplateLibrary]:
    return list(
        session.exec(
            select(TemplateLibrary).where(TemplateLibrary.organization_id == organization_id)
        ).all()
    )


def _org_templates(session: Session, organization_id: UUID) -> list[Template]:
    return list(session.exec(select(Template).where(Template.organization_id == organization_id)).all())


def _org_template_instantiations(session: Session, organization_id: UUID) -> list[TemplateInstantiation]:
    return list(
        session.exec(
            select(TemplateInstantiation).where(
                TemplateInstantiation.organization_id == organization_id
            )
        ).all()
    )


def _delivery_file_in_org(
    row: DeliveryFile,
    *,
    org_library_ids: set[UUID],
    org_client_ids: set[UUID],
    org_project_ids: set[UUID],
    org_person_ids: set[UUID],
) -> bool:
    return bool(
        (row.library_id and row.library_id in org_library_ids)
        or (row.client_id and row.client_id in org_client_ids)
        or (row.project_id and row.project_id in org_project_ids)
        or (row.uploaded_by and row.uploaded_by in org_person_ids)
    )


def _org_delivery_files(session: Session, organization_id: UUID) -> list[DeliveryFile]:
    org_libraries = _org_template_libraries(session, organization_id)
    org_clients = _org_clients(session, organization_id)
    org_projects = _org_projects(session, organization_id)
    org_people = _org_people(session, organization_id)
    org_library_ids = {row.id for row in org_libraries}
    org_client_ids = {row.id for row in org_clients}
    org_project_ids = {row.id for row in org_projects}
    org_person_ids = {row.id for row in org_people}
    return [
        row
        for row in session.exec(select(DeliveryFile)).all()
        if _delivery_file_in_org(
            row,
            org_library_ids=org_library_ids,
            org_client_ids=org_client_ids,
            org_project_ids=org_project_ids,
            org_person_ids=org_person_ids,
        )
    ]


def _org_kpis(session: Session, organization_id: UUID) -> list[KpiDefinition]:
    org_project_ids = {row.id for row in _org_projects(session, organization_id)}
    if not org_project_ids:
        return []
    return [
        row
        for row in session.exec(select(KpiDefinition)).all()
        if row.project_id in org_project_ids
    ]


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


def _get_org_asset(session: Session, asset_id: UUID, organization_id: UUID) -> Asset | None:
    asset = session.get(Asset, asset_id)
    if not asset or asset.organization_id != organization_id:
        return None
    return asset


def _get_org_review(session: Session, review_id: UUID, organization_id: UUID) -> ReviewRequest | None:
    review = session.get(ReviewRequest, review_id)
    if not review:
        return None
    if _get_org_project(session, review.project_id, organization_id) is None:
        return None
    return review


def _get_org_todo(session: Session, todo_id: UUID, organization_id: UUID) -> Todo | None:
    todo = session.get(Todo, todo_id)
    if not todo or todo.organization_id != organization_id:
        return None
    return todo


def _get_org_quest(session: Session, quest_id: UUID, organization_id: UUID) -> Quest | None:
    quest = session.get(Quest, quest_id)
    if not quest or quest.organization_id != organization_id:
        return None
    return quest


def _get_org_template_library(
    session: Session, library_id: UUID, organization_id: UUID
) -> TemplateLibrary | None:
    library = session.get(TemplateLibrary, library_id)
    if not library or library.organization_id != organization_id:
        return None
    return library


def _get_org_template(session: Session, template_id: UUID, organization_id: UUID) -> Template | None:
    template = session.get(Template, template_id)
    if not template or template.organization_id != organization_id:
        return None
    return template


def _get_org_kpi(session: Session, kpi_id: UUID, organization_id: UUID) -> KpiDefinition | None:
    kpi = session.get(KpiDefinition, kpi_id)
    if not kpi:
        return None
    if _get_org_project(session, kpi.project_id, organization_id) is None:
        return None
    if _get_org_client(session, kpi.client_id, organization_id) is None:
        return None
    return kpi


def _get_org_activity_log(
    session: Session, log_id: UUID, organization_id: UUID
) -> ActivityLog | None:
    row = session.get(ActivityLog, log_id)
    if not row or row.organization_id != organization_id:
        return None
    return row


def _get_org_membership(
    session: Session, person_id: UUID, organization_id: UUID
) -> OrganizationMembership | None:
    return session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.person_id == person_id,
        )
    ).first()


def _timeline_by_entity_keys(
    session: Session,
    entity_keys: list[tuple[EntityType, UUID]],
    organization_id: UUID | None = None,
) -> list[dict]:
    unique_keys = sorted(set(entity_keys), key=lambda item: (item[0].value, str(item[1])))
    if not unique_keys:
        return []

    key_set = set(unique_keys)
    rows = [
        row
        for row in session.exec(select(ActivityLog)).all()
        if (row.entity_type, row.entity_id) in key_set
        and (organization_id is None or row.organization_id == organization_id)
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


def _dashboard_context(request: Request, session: Session, current_actor: CurrentActor) -> dict:
    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    projects = sorted(
        _org_projects(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    assets = sorted(
        _org_assets(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    reviews = sorted(
        _org_reviews(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    timeline = sorted(
        _org_activity_logs(session, current_actor.organization.id),
        key=lambda row: row.timestamp,
        reverse=True,
    )
    people = sorted(session.exec(select(Person)).all(), key=lambda row: row.created_at, reverse=True)
    memberships = session.exec(select(ProjectMembership)).all()
    celonis_connections = sorted(
        _org_celonis_connections(session, current_actor.organization.id),
        key=lambda row: row.updated_at,
        reverse=True,
    )
    connection_by_client = {row.client_id: row for row in celonis_connections}
    person_name_by_id = {row.id: row.name for row in people}
    client_name_by_id = {row.id: row.name for row in clients}

    celonis_preflight_history: list[dict] = []
    for row in timeline:
        if row.action != "celonis_connection.preflight":
            continue

        metadata = row.metadata_json or {}
        raw_client_id = metadata.get("client_id")
        client_name = "Unknown client"
        if raw_client_id:
            try:
                client_name = client_name_by_id.get(UUID(str(raw_client_id)), "Unknown client")
            except ValueError:
                client_name = "Unknown client"

        celonis_preflight_history.append(
            {
                "timestamp": row.timestamp,
                "actor_name": person_name_by_id.get(row.actor_id, "Unknown"),
                "client_name": client_name,
                "service": metadata.get("service", "core"),
                "permission_status": metadata.get("permission_status", "unknown"),
                "status_code": metadata.get("status_code"),
                "run_id": metadata.get("run_id"),
            }
        )
        if len(celonis_preflight_history) >= 12:
            break

    return {
        "request": request,
        "active_organization": current_actor.organization,
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
        "celonis_preflight_history": celonis_preflight_history,
        "connection_by_client": connection_by_client,
        "sensitivity_options": [row.value for row in SensitivityLevel],
        "project_status_options": [row.value for row in ProjectStatus],
        "asset_type_options": [row.value for row in AssetType],
        "membership_role_options": [row.value for row in MembershipRole],
        "global_role_options": [row.value for row in GlobalRole],
    }


def _orchestration_context(request: Request, session: Session, current_actor: CurrentActor) -> dict:
    clients = _org_clients(session, current_actor.organization.id)
    projects = _org_projects(session, current_actor.organization.id)
    quests = _org_quests(session, current_actor.organization.id)
    people = _org_people(session, current_actor.organization.id)
    agents = _org_agents(session, current_actor.organization.id)

    projects_by_id = {row.id: row for row in projects}

    open_statuses = {QuestStatus.draft, QuestStatus.suggested, QuestStatus.accepted, QuestStatus.active, QuestStatus.blocked}
    open_quests = [row for row in quests if row.status in open_statuses]
    active_quests = [row for row in quests if row.status == QuestStatus.active]
    blocked_quests = [row for row in quests if row.status == QuestStatus.blocked]

    pressure_by_project: dict[UUID, dict[str, int | str]] = {}
    for row in open_quests:
        if row.project_id is None:
            continue
        project = projects_by_id.get(row.project_id)
        if project is None:
            continue
        project_pressure = pressure_by_project.setdefault(
            row.project_id,
            {
                "project_name": project.name,
                "open_count": 0,
                "high_count": 0,
            },
        )
        project_pressure["open_count"] = int(project_pressure["open_count"]) + 1
        if row.priority in {QuestPriority.high, QuestPriority.critical}:
            project_pressure["high_count"] = int(project_pressure["high_count"]) + 1

    hotspots = sorted(
        pressure_by_project.values(),
        key=lambda item: (int(item["high_count"]), int(item["open_count"])),
        reverse=True,
    )[:6]

    person_name_by_id = {row.id: row.name for row in people}
    agent_name_by_id = {row.id: row.name for row in agents}

    objectives_by_quest_id: dict[UUID, list[QuestObjective]] = {}
    assignments_by_quest_id: dict[UUID, list[QuestAssignment]] = {}
    for row in open_quests:
        objectives_by_quest_id[row.id] = list_objectives_service(session, quest_id=row.id)
        assignments_by_quest_id[row.id] = list_assignments_service(session, quest_id=row.id)

    quest_rows: list[dict[str, object]] = []
    for row in sorted(open_quests, key=lambda item: item.created_at, reverse=True)[:10]:
        quest_status = row.status.value

        project_name = "Unscoped"
        if row.project_id and row.project_id in projects_by_id:
            project_name = projects_by_id[row.project_id].name

        objective_rows = [
            {
                "id": objective.id,
                "title": objective.title,
                "details": objective.details,
                "is_done": objective.is_done,
                "sort_order": objective.sort_order,
            }
            for objective in objectives_by_quest_id.get(row.id, [])
        ]

        assignment_rows = []
        for assignment in assignments_by_quest_id.get(row.id, []):
            assignment_rows.append(
                {
                    "id": assignment.id,
                    "agent_name": (
                        agent_name_by_id.get(assignment.agent_id) if assignment.agent_id else None
                    ),
                    "assignee_name": (
                        person_name_by_id.get(assignment.assignee_person_id)
                        if assignment.assignee_person_id
                        else None
                    ),
                    "role": assignment.role,
                    "state": assignment.state,
                }
            )

        quest_rows.append(
            {
                "id": row.id,
                "title": row.title,
                "project_name": project_name,
                "priority": row.priority.value,
                "status": quest_status,
                "source": row.source.value,
                "can_override": row.status not in {QuestStatus.archived, QuestStatus.done},
                "objectives": objective_rows,
                "assignments": assignment_rows,
            }
        )

    units = []
    for row in sorted(people, key=lambda item: item.name.lower())[:8]:
        if row.role_global == GlobalRole.admin:
            unit_type = "guardian"
        else:
            unit_type = "builder"
        units.append({"name": row.name, "unit_type": unit_type, "role": row.role_global.value})

    selected_quest_action = (request.query_params.get("quest_action") or "").strip()
    selected_quest_actor_id = (request.query_params.get("quest_actor_id") or "").strip()

    quest_activity = sorted(
        [
            row
            for row in _org_activity_logs(session, current_actor.organization.id)
            if row.entity_type == EntityType.quest
        ],
        key=lambda row: row.timestamp,
        reverse=True,
    )

    if selected_quest_action:
        quest_activity = [row for row in quest_activity if row.action == selected_quest_action]

    if selected_quest_actor_id:
        quest_activity = [
            row
            for row in quest_activity
            if str(row.actor_id) == selected_quest_actor_id
        ]

    quest_timeline_actions = sorted(
        {
            row.action
            for row in _org_activity_logs(session, current_actor.organization.id)
            if row.entity_type == EntityType.quest
        }
    )
    quest_timeline_actors = sorted(
        [
            {
                "id": str(person.id),
                "name": person.name,
            }
            for person in people
        ],
        key=lambda row: row["name"].lower(),
    )

    quest_activity = quest_activity[:14]

    quest_timeline_rows = [
        {
            "timestamp": row.timestamp,
            "actor_name": person_name_by_id.get(row.actor_id, "Unknown"),
            "action": row.action,
            "title": (row.metadata_json or {}).get("title") or "Quest",
            "status": (row.metadata_json or {}).get("status"),
            "priority": (row.metadata_json or {}).get("priority"),
        }
        for row in quest_activity
    ]

    return {
        "request": request,
        "active_organization": current_actor.organization,
        "ok_message": request.query_params.get("ok"),
        "error_message": request.query_params.get("err"),
        "clients_count": len(clients),
        "projects_count": len(projects),
        "agents_count": len(people),
        "open_quests_count": len(open_quests),
        "active_quests_count": len(active_quests),
        "blocked_quests_count": len(blocked_quests),
        "hotspots": hotspots,
        "quest_rows": quest_rows,
        "quest_timeline_rows": quest_timeline_rows,
        "quest_timeline_actions": quest_timeline_actions,
        "quest_timeline_actors": quest_timeline_actors,
        "selected_quest_action": selected_quest_action,
        "selected_quest_actor_id": selected_quest_actor_id,
        "units": units,
        "form_projects": sorted(projects, key=lambda row: row.name.lower()),
        "form_people": sorted(people, key=lambda row: row.name.lower()),
        "form_agents": sorted(agents, key=lambda row: row.name.lower()),
        "quest_priority_options": [row.value for row in QuestPriority],
        "assignment_state_options": ["assigned", "in_progress", "blocked", "done"],
        "quest_status_options": [row.value for row in QuestStatus],
        "override_policy": "Full user control enabled",
    }


def _client_health_context(request: Request, session: Session, current_actor: CurrentActor) -> dict:
    now = datetime.utcnow()
    stale_review_cutoff = now - timedelta(days=7)
    workflow_window_cutoff = now - timedelta(days=7)

    clients = sorted(_org_clients(session, current_actor.organization.id), key=lambda row: row.name.lower())
    projects = sorted(_org_projects(session, current_actor.organization.id), key=lambda row: row.name.lower())
    assets = _org_assets(session, current_actor.organization.id)
    reviews = _org_reviews(session, current_actor.organization.id)
    todos = _org_todos(session, current_actor.organization.id)
    memberships = list(session.exec(select(ProjectMembership)).all())
    activity_rows = _org_activity_logs(session, current_actor.organization.id)
    celonis_connections = _org_celonis_connections(session, current_actor.organization.id)

    assets_by_project: dict[UUID, list[Asset]] = {}
    for row in assets:
        assets_by_project.setdefault(row.project_id, []).append(row)

    reviews_by_project: dict[UUID, list[ReviewRequest]] = {}
    review_project_by_id: dict[UUID, UUID] = {}
    for row in reviews:
        reviews_by_project.setdefault(row.project_id, []).append(row)
        review_project_by_id[row.id] = row.project_id

    todos_by_project: dict[UUID, list[Todo]] = {}
    todo_project_by_id: dict[UUID, UUID] = {}
    for row in todos:
        if row.project_id is None:
            continue
        todos_by_project.setdefault(row.project_id, []).append(row)
        todo_project_by_id[row.id] = row.project_id

    active_membership_count_by_project: dict[UUID, int] = {}
    for row in memberships:
        if row.start_date > now:
            continue
        if row.end_date is not None and row.end_date < now:
            continue
        active_membership_count_by_project[row.project_id] = (
            active_membership_count_by_project.get(row.project_id, 0) + 1
        )

    last_activity_by_project: dict[UUID, datetime] = {}
    for row in activity_rows:
        if row.entity_type != EntityType.project:
            continue
        current = last_activity_by_project.get(row.entity_id)
        if current is None or row.timestamp > current:
            last_activity_by_project[row.entity_id] = row.timestamp

    connection_by_client = {row.client_id: row for row in celonis_connections}
    client_name_by_id = {row.id: row.name for row in clients}

    project_rows: list[dict] = []
    critical_pm_count = 0
    critical_dev_count = 0

    for project in sorted(projects, key=lambda row: (client_name_by_id.get(row.client_id, "").lower(), row.name.lower())):
        project_assets = assets_by_project.get(project.id, [])
        project_reviews = reviews_by_project.get(project.id, [])
        project_todos = todos_by_project.get(project.id, [])

        pending_reviews = sum(
            1
            for row in project_reviews
            if row.status in {ReviewStatus.submitted, ReviewStatus.in_review}
        )
        stale_reviews = sum(
            1
            for row in project_reviews
            if row.status == ReviewStatus.in_review
            and ((row.submitted_at or row.created_at) < stale_review_cutoff)
        )

        open_todos = sum(1 for row in project_todos if row.status != TodoStatus.done)
        overdue_high_prio_todos = sum(
            1
            for row in project_todos
            if row.status != TodoStatus.done
            and row.priority == TodoPriority.high
            and row.due_at is not None
            and row.due_at < now
        )

        asset_total = len(project_assets)
        assets_approved = sum(1 for row in project_assets if row.status == AssetStatus.approved)
        asset_approval_rate = (assets_approved / asset_total) if asset_total else 0.0

        extractors_total = sum(1 for row in project_assets if row.type == AssetType.extractor)
        extractors_healthy = sum(
            1
            for row in project_assets
            if row.type == AssetType.extractor and row.status == AssetStatus.approved
        )
        data_models_total = sum(1 for row in project_assets if row.type == AssetType.data_model)
        data_models_healthy = sum(
            1
            for row in project_assets
            if row.type == AssetType.data_model and row.status == AssetStatus.approved
        )
        action_flows_total = sum(1 for row in project_assets if row.type == AssetType.action_flow)
        action_flows_healthy = sum(
            1
            for row in project_assets
            if row.type == AssetType.action_flow and row.status == AssetStatus.approved
        )
        ml_jobs_total = sum(1 for row in project_assets if row.type == AssetType.ml_job)
        deprecated_assets = sum(1 for row in project_assets if row.status == AssetStatus.deprecated)

        technical_total = extractors_total + data_models_total + action_flows_total
        technical_healthy = extractors_healthy + data_models_healthy + action_flows_healthy

        if technical_total == 0:
            pipeline_health = "n/a"
        elif technical_healthy == technical_total:
            pipeline_health = "healthy"
        elif technical_healthy == 0:
            pipeline_health = "critical"
        else:
            pipeline_health = "warning"

        connection = connection_by_client.get(project.client_id)
        connection_active = bool(connection and connection.is_active)
        uptime_status = "healthy" if connection_active else "warning"

        workflow_runs_7d = 0
        for row in activity_rows:
            if row.timestamp < workflow_window_cutoff:
                continue
            if row.entity_type == EntityType.review:
                if review_project_by_id.get(row.entity_id) == project.id and row.action.startswith("review."):
                    workflow_runs_7d += 1
            elif row.entity_type == EntityType.todo:
                if todo_project_by_id.get(row.entity_id) == project.id and row.action.startswith("todo."):
                    workflow_runs_7d += 1

        approved_review_count = sum(1 for row in project_reviews if row.status == ReviewStatus.approved)
        decided_review_count = sum(
            1
            for row in project_reviews
            if row.status in {ReviewStatus.approved, ReviewStatus.changes_requested, ReviewStatus.closed}
        )
        review_approval_rate = (approved_review_count / decided_review_count) if decided_review_count else 0.0

        if overdue_high_prio_todos > 0:
            pm_health = "critical"
        elif open_todos > 0 or pending_reviews > 0 or not connection_active:
            pm_health = "warning"
        else:
            pm_health = "healthy"

        if deprecated_assets > 0 or stale_reviews > 0:
            dev_health = "critical"
        elif not connection_active or (technical_total > 0 and technical_healthy < technical_total):
            dev_health = "warning"
        else:
            dev_health = "healthy"

        if pm_health == "critical":
            critical_pm_count += 1
        if dev_health == "critical":
            critical_dev_count += 1

        project_rows.append(
            {
                "client_id": project.client_id,
                "client_name": client_name_by_id.get(project.client_id, "Unknown client"),
                "project_id": project.id,
                "project_name": project.name,
                "project_status": project.status.value,
                "member_count": active_membership_count_by_project.get(project.id, 0),
                "open_todos": open_todos,
                "overdue_high_prio_todos": overdue_high_prio_todos,
                "pending_reviews": pending_reviews,
                "asset_total": asset_total,
                "assets_approved": assets_approved,
                "asset_approval_rate": asset_approval_rate,
                "last_activity": last_activity_by_project.get(project.id),
                "pm_health": pm_health,
                "connection_active": connection_active,
                "uptime_status": uptime_status,
                "pipeline_health": pipeline_health,
                "workflow_runs_7d": workflow_runs_7d,
                "extractors_total": extractors_total,
                "extractors_healthy": extractors_healthy,
                "data_models_total": data_models_total,
                "data_models_healthy": data_models_healthy,
                "action_flows_total": action_flows_total,
                "action_flows_healthy": action_flows_healthy,
                "ml_jobs_total": ml_jobs_total,
                "deprecated_assets": deprecated_assets,
                "stale_reviews": stale_reviews,
                "review_approval_rate": review_approval_rate,
                "dev_health": dev_health,
            }
        )

    health_rank = {"healthy": 0, "warning": 1, "critical": 2}

    def _worst_health(rows: list[dict], key: str) -> str:
        if not rows:
            return "healthy"
        return max((row[key] for row in rows), key=lambda value: health_rank.get(value, 0))

    def _aggregate_pipeline_health(rows: list[dict]) -> str:
        if not rows:
            return "n/a"
        non_na = [row["pipeline_health"] for row in rows if row["pipeline_health"] != "n/a"]
        if not non_na:
            return "n/a"
        if "critical" in non_na:
            return "critical"
        if "warning" in non_na:
            return "warning"
        return "healthy"

    projects_by_client: dict[UUID, list[dict]] = {}
    for row in project_rows:
        projects_by_client.setdefault(row["client_id"], []).append(row)

    rows_with_rollups: list[dict] = []
    for client in clients:
        client_project_rows = projects_by_client.get(client.id, [])

        asset_total = sum(row["asset_total"] for row in client_project_rows)
        assets_approved = sum(row["assets_approved"] for row in client_project_rows)
        last_activity = max((row["last_activity"] for row in client_project_rows if row["last_activity"]), default=None)
        uptime_status = "healthy" if client_project_rows and all(row["connection_active"] for row in client_project_rows) else "warning"
        pipeline_health = _aggregate_pipeline_health(client_project_rows)

        rows_with_rollups.append(
            {
                "row_kind": "client_summary",
                "client_id": client.id,
                "client_name": client.name,
                "project_count": len(client_project_rows),
                "project_id": None,
                "project_name": "Portfolio summary",
                "project_status": f"{len(client_project_rows)} projects",
                "member_count": sum(row["member_count"] for row in client_project_rows),
                "open_todos": sum(row["open_todos"] for row in client_project_rows),
                "overdue_high_prio_todos": sum(row["overdue_high_prio_todos"] for row in client_project_rows),
                "pending_reviews": sum(row["pending_reviews"] for row in client_project_rows),
                "asset_total": asset_total,
                "assets_approved": assets_approved,
                "asset_approval_rate": (assets_approved / asset_total) if asset_total else 0.0,
                "last_activity": last_activity,
                "pm_health": _worst_health(client_project_rows, "pm_health"),
                "connection_active": all(row["connection_active"] for row in client_project_rows) if client_project_rows else False,
                "uptime_status": uptime_status,
                "pipeline_health": pipeline_health,
                "workflow_runs_7d": sum(row["workflow_runs_7d"] for row in client_project_rows),
                "extractors_total": sum(row["extractors_total"] for row in client_project_rows),
                "extractors_healthy": sum(row["extractors_healthy"] for row in client_project_rows),
                "data_models_total": sum(row["data_models_total"] for row in client_project_rows),
                "data_models_healthy": sum(row["data_models_healthy"] for row in client_project_rows),
                "action_flows_total": sum(row["action_flows_total"] for row in client_project_rows),
                "action_flows_healthy": sum(row["action_flows_healthy"] for row in client_project_rows),
                "ml_jobs_total": sum(row["ml_jobs_total"] for row in client_project_rows),
                "deprecated_assets": sum(row["deprecated_assets"] for row in client_project_rows),
                "stale_reviews": sum(row["stale_reviews"] for row in client_project_rows),
                "review_approval_rate": 0.0,
                "dev_health": _worst_health(client_project_rows, "dev_health"),
            }
        )

        for project_row in client_project_rows:
            row_with_kind = dict(project_row)
            row_with_kind["row_kind"] = "project"
            rows_with_rollups.append(row_with_kind)

    return {
        "request": request,
        "ok_message": request.query_params.get("ok"),
        "error_message": request.query_params.get("err"),
        "rows": rows_with_rollups,
        "clients_count": len(clients),
        "projects_count": len(projects),
        "critical_pm_count": critical_pm_count,
        "critical_dev_count": critical_dev_count,
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
def dashboard(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    return templates.TemplateResponse(
        "dashboard.html",
        _dashboard_context(request, session, current_actor),
    )


@router.get("/orchestration-ui")
def orchestration_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    return templates.TemplateResponse(
        "orchestration.html",
        _orchestration_context(request, session, current_actor),
    )


@router.post("/orchestration-ui/quests/create", include_in_schema=False)
def orchestration_create_quest(
    title: str = Form(...),
    description: str = Form(""),
    project_id: str = Form(""),
    priority: str = Form("medium"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_project_id = _parse_optional_uuid(project_id, "project_id")
        if parsed_project_id and _get_org_project(session, parsed_project_id, current_actor.organization.id) is None:
            return _redirect_ui("/orchestration-ui", err="Project not found in your organization")

        quest = create_quest_service(
            session,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            data={
                "title": title.strip(),
                "description": description.strip() or None,
                "project_id": parsed_project_id,
                "source": QuestSource.user_authored,
                "priority": QuestPriority(priority),
                "status": QuestStatus.suggested,
                "owner_person_id": current_actor.person.id,
            },
            default_owner_person_id=current_actor.person.id,
        )
        return _redirect_ui("/orchestration-ui", ok=f"Quest '{quest.title}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Create quest failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/edit", include_in_schema=False)
def orchestration_edit_quest(
    quest_id: UUID,
    title: str = Form(...),
    status: str = Form("suggested"),
    priority: str = Form("medium"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        update_quest_service(
            session,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            quest=quest,
            updates={
                "title": title.strip(),
                "status": QuestStatus(status),
                "priority": QuestPriority(priority),
            },
        )
        return _redirect_ui("/orchestration-ui", ok="Quest updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Edit quest failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/pause", include_in_schema=False)
def orchestration_pause_quest(
    quest_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        pause_quest_service(
            session,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            quest=quest,
        )
        return _redirect_ui("/orchestration-ui", ok="Quest paused")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Pause quest failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/reprioritize", include_in_schema=False)
def orchestration_reprioritize_quest(
    quest_id: UUID,
    priority: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        reprioritize_quest_service(
            session,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            quest=quest,
            priority=QuestPriority(priority),
        )
        return _redirect_ui("/orchestration-ui", ok="Quest reprioritized")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Reprioritize quest failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/replace", include_in_schema=False)
def orchestration_replace_quest(
    quest_id: UUID,
    title: str = Form(...),
    priority: str = Form("medium"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        replace_quest_service(
            session,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            quest=quest,
            title=title.strip(),
            description=quest.description,
            priority=QuestPriority(priority),
        )
        return _redirect_ui("/orchestration-ui", ok="Quest replaced")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Replace quest failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/delete", include_in_schema=False)
def orchestration_delete_quest(
    quest_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        quest_title = quest.title
        delete_quest_service(
            session,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            quest=quest,
        )
        return _redirect_ui("/orchestration-ui", ok=f"Quest '{quest_title}' deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Delete quest failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/objectives/create", include_in_schema=False)
def orchestration_create_objective(
    quest_id: UUID,
    title: str = Form(...),
    details: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        create_objective_service(
            session,
            quest=quest,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            title=title.strip(),
            details=details.strip() or None,
            sort_order=None,
        )
        return _redirect_ui("/orchestration-ui", ok="Objective added")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Add objective failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/objectives/{objective_id}/toggle", include_in_schema=False)
def orchestration_toggle_objective(
    quest_id: UUID,
    objective_id: UUID,
    is_done: str = Form("false"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        update_objective_service(
            session,
            quest=quest,
            objective_id=objective_id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            updates={"is_done": is_done.strip().lower() == "true"},
        )
        return _redirect_ui("/orchestration-ui", ok="Objective updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Update objective failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/objectives/{objective_id}/delete", include_in_schema=False)
def orchestration_delete_objective(
    quest_id: UUID,
    objective_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        delete_objective_service(
            session,
            quest=quest,
            objective_id=objective_id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
        )
        return _redirect_ui("/orchestration-ui", ok="Objective deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Delete objective failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/assignments/create", include_in_schema=False)
def orchestration_create_assignment(
    quest_id: UUID,
    assignee_person_id: str = Form(""),
    agent_id: str = Form(""),
    role: str = Form(""),
    state: str = Form("assigned"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        create_assignment_service(
            session,
            quest=quest,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            assignee_person_id=_parse_optional_uuid(assignee_person_id, "assignee_person_id"),
            agent_id=_parse_optional_uuid(agent_id, "agent_id"),
            role=role.strip() or None,
            state=state.strip() or "assigned",
        )
        return _redirect_ui("/orchestration-ui", ok="Assignment created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Create assignment failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/assignments/{assignment_id}/state", include_in_schema=False)
def orchestration_update_assignment(
    quest_id: UUID,
    assignment_id: UUID,
    state: str = Form("assigned"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        update_assignment_service(
            session,
            quest=quest,
            assignment_id=assignment_id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            updates={"state": state.strip() or "assigned"},
        )
        return _redirect_ui("/orchestration-ui", ok="Assignment updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Update assignment failed: {exc}")


@router.post("/orchestration-ui/quests/{quest_id}/assignments/{assignment_id}/delete", include_in_schema=False)
def orchestration_delete_assignment(
    quest_id: UUID,
    assignment_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    quest = get_org_quest_service(session, quest_id, current_actor.organization.id)
    if quest is None:
        return _redirect_ui("/orchestration-ui", err="Quest not found")

    try:
        delete_assignment_service(
            session,
            quest=quest,
            assignment_id=assignment_id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
        )
        return _redirect_ui("/orchestration-ui", ok="Assignment deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/orchestration-ui", err=f"Delete assignment failed: {exc}")


@router.get("/client-health-ui")
def client_health_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    return templates.TemplateResponse(
        "client_health.html",
        _client_health_context(request, session, current_actor),
    )


@router.post("/dashboard/create-client", include_in_schema=False)
def dashboard_create_client(
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        normalized_email = email.strip().lower()
        person = session.exec(select(Person).where(Person.email == normalized_email)).first()
        created = False
        if person is None:
            person = Person(
                name=name.strip(),
                email=normalized_email,
                hashed_password=hash_password(password),
                role_global=GlobalRole(role_global),
            )
            session.add(person)
            session.commit()
            session.refresh(person)
            created = True

        membership = _get_org_membership(session, person.id, current_actor.organization.id)
        if membership is None:
            membership = OrganizationMembership(
                organization_id=current_actor.organization.id,
                person_id=person.id,
                role=OrganizationRole.member,
            )
            session.add(membership)
            session.commit()

        log_created(
            session,
            entity_type=EntityType.person,
            entity_id=person.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"email": person.email, "role_global": person.role_global.value},
        )
        if created:
            return _redirect_dashboard(ok=f"Person '{person.name}' created")
        return _redirect_dashboard(ok=f"Person '{person.name}' added to organization")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Create person failed: {exc}")


@router.post("/dashboard/create-project", include_in_schema=False)
def dashboard_create_project(
    name: str = Form(...),
    client_id: str = Form(...),
    status: str = Form("planned"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        if _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            raise ValueError("Client not found")

        project = Project(
            organization_id=current_actor.organization.id,
            name=name.strip(),
            client_id=parsed_client_id,
            status=ProjectStatus(status),
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        log_created(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        if _get_org_project(session, parsed_project_id, current_actor.organization.id) is None:
            raise ValueError("Project not found")

        membership = ProjectMembership(
            project_id=parsed_project_id,
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
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        parsed_client_id = _parse_uuid(client_id, "client_id")
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        if project is None:
            raise ValueError("Project not found")
        if client is None:
            raise ValueError("Client not found")
        if project.client_id != client.id:
            raise ValueError("Project does not belong to the specified client")

        asset = Asset(
            organization_id=current_actor.organization.id,
            name=name.strip(),
            type=AssetType(asset_type),
            project_id=parsed_project_id,
            client_id=parsed_client_id,
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
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        payload = ReviewRequestCreate(
            asset_id=_parse_uuid(asset_id, "asset_id"),
            project_id=_parse_uuid(project_id, "project_id"),
            author_id=_parse_uuid(author_id, "author_id"),
            reviewer_id=_parse_uuid(reviewer_id, "reviewer_id"),
            change_summary=change_summary.strip(),
        )
        review = ReviewService.submit_for_review(
            session,
            payload,
            organization_id=current_actor.organization.id,
        )
        log_created(
            session,
            entity_type=EntityType.review,
            entity_id=review.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        payload = ReviewDecisionCreate(
            review_id=_parse_uuid(review_id, "review_id"),
            reviewer_id=_parse_uuid(reviewer_id, "reviewer_id"),
            decision=DecisionType(decision),
            note=note.strip() or None,
            snippet_worthy=snippet_worthy is not None,
        )
        review = ReviewService.decide_review(
            session,
            payload,
            organization_id=current_actor.organization.id,
        )
        log_updated(
            session,
            entity_type=EntityType.review,
            entity_id=review.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        if _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            return _redirect_dashboard(err="Client not found")

        existing = session.exec(
            select(CelonisConnection).where(
                CelonisConnection.client_id == parsed_client_id,
                CelonisConnection.organization_id == current_actor.organization.id,
            )
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
                actor_id=current_actor.person.id,
                organization_id=current_actor.organization.id,
                metadata={"client_id": str(existing.client_id), "is_active": existing.is_active},
            )
            return _redirect_dashboard(ok="Celonis connection updated")

        row = CelonisConnection(
            organization_id=current_actor.organization.id,
            client_id=parsed_client_id,
            tenant_base_url=tenant_base_url.strip(),
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
        return _redirect_dashboard(ok="Celonis connection created")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Celonis connection failed: {exc}")


@router.post("/dashboard/celonis-extract", include_in_schema=False)
def dashboard_celonis_extract(
    client_id: str = Form(...),
    source_path: str = Form("/process-mining/api/teams"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        connection = session.exec(
            select(CelonisConnection).where(
                CelonisConnection.client_id == parsed_client_id,
                CelonisConnection.organization_id == current_actor.organization.id,
            )
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


@router.post("/dashboard/celonis-preflight", include_in_schema=False)
def dashboard_celonis_preflight(
    client_id: str = Form(...),
    service: str = Form("core"),
    probe_path: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        connection = session.exec(
            select(CelonisConnection).where(
                CelonisConnection.client_id == parsed_client_id,
                CelonisConnection.organization_id == current_actor.organization.id,
            )
        ).first()
        if connection is None or not connection.is_active:
            return _redirect_dashboard(err="No active Celonis connection for selected client")

        result = CelonisGateway(get_settings()).preflight(
            tenant_base_url=connection.tenant_base_url,
            probe_path=probe_path,
            service=service,
        )
        log_activity(
            session,
            entity_type=EntityType.celonis_connection,
            entity_id=connection.id,
            actor_id=current_actor.person.id,
            action="celonis_connection.preflight",
            organization_id=current_actor.organization.id,
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
            },
        )
        if not result.has_token:
            return _redirect_dashboard(err=result.error or "Celonis API token is not configured")
        if result.permission_status == "authorized":
            return _redirect_dashboard(
                ok=(
                    f"Preflight authorized ({result.status_code}) [{result.service}] "
                    f"at {result.probe_url}"
                )
            )
        if result.reachable:
            return _redirect_dashboard(
                err=(
                    f"Preflight {result.permission_status} ({result.status_code}) "
                    f"[{result.service}] at {result.probe_url}"
                )
            )
        return _redirect_dashboard(err=f"Preflight failed: {result.error or 'unknown error'}")
    except Exception as exc:
        return _redirect_dashboard(err=f"Celonis preflight failed: {exc}")


@router.post("/dashboard/celonis-preflight-batch", include_in_schema=False)
def dashboard_celonis_preflight_batch(
    client_id: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        connection = session.exec(
            select(CelonisConnection).where(
                CelonisConnection.client_id == parsed_client_id,
                CelonisConnection.organization_id == current_actor.organization.id,
            )
        ).first()
        if connection is None or not connection.is_active:
            return _redirect_dashboard(err="No active Celonis connection for selected client")

        services = list(CelonisGateway.SERVICE_DEFAULT_PROBES.keys())
        gateway = CelonisGateway(get_settings())
        run_id = str(uuid4())
        authorized_count = 0

        for service_name in services:
            result = gateway.preflight(
                tenant_base_url=connection.tenant_base_url,
                probe_path="",
                service=service_name,
            )
            if result.permission_status == "authorized":
                authorized_count += 1

            log_activity(
                session,
                entity_type=EntityType.celonis_connection,
                entity_id=connection.id,
                actor_id=current_actor.person.id,
                action="celonis_connection.preflight",
                organization_id=current_actor.organization.id,
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
                    "source": "dashboard_batch",
                    "run_id": run_id,
                },
            )

        total = len(services)
        issue_count = total - authorized_count
        if issue_count == 0:
            return _redirect_dashboard(
                ok=f"Batch preflight passed for all {total} services (run {run_id})"
            )
        return _redirect_dashboard(
            err=(
                f"Batch preflight found {issue_count}/{total} service issues "
                f"(run {run_id})"
            )
        )
    except Exception as exc:
        return _redirect_dashboard(err=f"Celonis batch preflight failed: {exc}")


@router.post("/dashboard/celonis-import", include_in_schema=False)
def dashboard_celonis_import(
    client_id: str = Form(...),
    target_path: str = Form("/process-mining/api/teams"),
    payload_json: str = Form('{"name":"foundry-import"}'),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        connection = session.exec(
            select(CelonisConnection).where(
                CelonisConnection.client_id == parsed_client_id,
                CelonisConnection.organization_id == current_actor.organization.id,
            )
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
def projects_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    projects = sorted(
        _org_projects(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    clients = _org_clients(session, current_actor.organization.id)
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
            "salesforce_url": project.salesforce_url,
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
    salesforce_url: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        if _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            raise ValueError("Client not found")

        project = Project(
            organization_id=current_actor.organization.id,
            name=name.strip(),
            client_id=parsed_client_id,
            status=ProjectStatus(status),
            salesforce_url=_normalize_http_url(salesforce_url) or None,
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        log_created(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    salesforce_url: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        if not project:
            return _redirect_ui("/projects-ui", err="Project not found")

        parsed_client_id = _parse_uuid(client_id, "client_id")
        if _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            return _redirect_ui("/projects-ui", err="Client not found")

        parsed_status = ProjectStatus(status)
        if parsed_status == ProjectStatus.active:
            ProjectService.ensure_can_be_active(session, parsed_project_id)
        if parsed_status == ProjectStatus.closed:
            ProjectService.ensure_can_be_closed(session, parsed_project_id)

        project.name = name.strip()
        project.client_id = parsed_client_id
        project.status = parsed_status
        project.salesforce_url = _normalize_http_url(salesforce_url) or None
        session.add(project)
        session.commit()
        session.refresh(project)
        log_updated(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"client_id": str(project.client_id), "status": project.status.value},
        )
        return _redirect_ui("/projects-ui", ok="Project updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/projects-ui", err=f"Update project failed: {exc}")


@router.post("/projects-ui/delete", include_in_schema=False)
def projects_ui_delete(
    project_id: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
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
def assets_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    assets = sorted(
        _org_assets(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    projects = _org_projects(session, current_actor.organization.id)
    clients = _org_clients(session, current_actor.organization.id)

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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        parsed_client_id = _parse_uuid(client_id, "client_id")
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        if project is None:
            raise ValueError("Project not found")
        if client is None:
            raise ValueError("Client not found")
        if project.client_id != client.id:
            raise ValueError("Project does not belong to the specified client")

        asset = Asset(
            organization_id=current_actor.organization.id,
            name=name.strip(),
            type=AssetType(asset_type),
            status=AssetStatus(status),
            project_id=parsed_project_id,
            client_id=parsed_client_id,
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
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_asset_id = _parse_uuid(asset_id, "asset_id")
        asset = _get_org_asset(session, parsed_asset_id, current_actor.organization.id)
        if not asset:
            return _redirect_ui("/assets-ui", err="Asset not found")

        parsed_project_id = _parse_uuid(project_id, "project_id")
        parsed_client_id = _parse_uuid(client_id, "client_id")
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        if project is None:
            return _redirect_ui("/assets-ui", err="Project not found")
        if client is None:
            return _redirect_ui("/assets-ui", err="Client not found")
        if project.client_id != client.id:
            return _redirect_ui("/assets-ui", err="Project does not belong to the specified client")

        asset.name = name.strip()
        asset.type = AssetType(asset_type)
        asset.status = AssetStatus(status)
        asset.project_id = parsed_project_id
        asset.client_id = parsed_client_id
        asset.celonis_url = celonis_url.strip() or None
        asset.asset_identifier = asset_identifier.strip() or None
        session.add(asset)
        session.commit()
        session.refresh(asset)
        log_updated(
            session,
            entity_type=EntityType.asset,
            entity_id=asset.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
def assets_ui_delete(
    asset_id: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_asset_id = _parse_uuid(asset_id, "asset_id")
        asset = _get_org_asset(session, parsed_asset_id, current_actor.organization.id)
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
def reviews_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    reviews = sorted(
        _org_reviews(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    assets = _org_assets(session, current_actor.organization.id)
    projects = _org_projects(session, current_actor.organization.id)
    people = sorted(
        _org_people(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )

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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_asset_id = _parse_uuid(asset_id, "asset_id")
        parsed_project_id = _parse_uuid(project_id, "project_id")
        parsed_author_id = _parse_uuid(author_id, "author_id")
        parsed_reviewer_id = _parse_uuid(reviewer_id, "reviewer_id")

        asset = _get_org_asset(session, parsed_asset_id, current_actor.organization.id)
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        if asset is None:
            return _redirect_ui("/reviews-ui", err="Asset not found")
        if project is None:
            return _redirect_ui("/reviews-ui", err="Project not found")
        org_people = {row.id for row in _org_people(session, current_actor.organization.id)}
        if parsed_author_id not in org_people or parsed_reviewer_id not in org_people:
            return _redirect_ui(
                "/reviews-ui",
                err="Author and reviewer must belong to the active organization",
            )

        payload = ReviewRequestCreate(
            asset_id=parsed_asset_id,
            project_id=parsed_project_id,
            author_id=parsed_author_id,
            reviewer_id=parsed_reviewer_id,
            change_summary=change_summary.strip(),
        )
        review = ReviewService.submit_for_review(
            session,
            payload,
            organization_id=current_actor.organization.id,
        )
        log_created(
            session,
            entity_type=EntityType.review,
            entity_id=review.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_review_id = _parse_uuid(review_id, "review_id")
        review = _get_org_review(session, parsed_review_id, current_actor.organization.id)
        if not review:
            return _redirect_ui("/reviews-ui", err="Review not found")

        parsed_asset_id = _parse_uuid(asset_id, "asset_id")
        parsed_project_id = _parse_uuid(project_id, "project_id")
        parsed_author_id = _parse_uuid(author_id, "author_id")
        parsed_reviewer_id = _parse_uuid(reviewer_id, "reviewer_id")

        asset = _get_org_asset(session, parsed_asset_id, current_actor.organization.id)
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        if asset is None:
            return _redirect_ui("/reviews-ui", err="Asset not found")
        if project is None:
            return _redirect_ui("/reviews-ui", err="Project not found")
        org_people = {row.id for row in _org_people(session, current_actor.organization.id)}
        if parsed_author_id not in org_people or parsed_reviewer_id not in org_people:
            return _redirect_ui(
                "/reviews-ui",
                err="Author and reviewer must belong to the active organization",
            )

        review.asset_id = parsed_asset_id
        review.project_id = parsed_project_id
        review.author_id = parsed_author_id
        review.reviewer_id = parsed_reviewer_id
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
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"status": review.status.value, "snippet_worthy": review.snippet_worthy},
        )
        return _redirect_ui("/reviews-ui", ok="Review updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/reviews-ui", err=f"Update review failed: {exc}")


@router.post("/reviews-ui/delete", include_in_schema=False)
def reviews_ui_delete(
    review_id: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_review_id = _parse_uuid(review_id, "review_id")
        review = _get_org_review(session, parsed_review_id, current_actor.organization.id)
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
def people_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    memberships = list(
        session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == current_actor.organization.id
            )
        ).all()
    )
    membership_by_person_id = {row.person_id: row for row in memberships}
    people = sorted(
        _org_people(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    rows = [
        {
            "id": person.id,
            "name": person.name,
            "email": person.email,
            "role_global": person.role_global.value,
            "role_org": membership_by_person_id[person.id].role.value
            if person.id in membership_by_person_id
            else "member",
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        normalized_email = email.strip().lower()
        person = session.exec(select(Person).where(Person.email == normalized_email)).first()
        created = False
        if person is None:
            person = Person(
                name=name.strip(),
                email=normalized_email,
                hashed_password=hash_password(password),
                role_global=GlobalRole(role_global),
            )
            session.add(person)
            session.commit()
            session.refresh(person)
            created = True

        membership = _get_org_membership(session, person.id, current_actor.organization.id)
        if membership is None:
            membership = OrganizationMembership(
                organization_id=current_actor.organization.id,
                person_id=person.id,
                role=OrganizationRole.member,
            )
            session.add(membership)
            session.commit()

        log_created(
            session,
            entity_type=EntityType.person,
            entity_id=person.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"email": person.email, "role_global": person.role_global.value},
        )
        if created:
            return _redirect_ui("/people-ui", ok=f"Person '{person.name}' created")
        return _redirect_ui("/people-ui", ok=f"Person '{person.name}' added to organization")
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_person_id = _parse_uuid(person_id, "person_id")
        person = session.get(Person, parsed_person_id)
        if not person:
            return _redirect_ui("/people-ui", err="Person not found")
        membership = _get_org_membership(session, parsed_person_id, current_actor.organization.id)
        if membership is None:
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
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"email": person.email, "role_global": person.role_global.value},
        )
        return _redirect_ui("/people-ui", ok="Person updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/people-ui", err=f"Update person failed: {exc}")


@router.post("/people-ui/delete", include_in_schema=False)
def people_ui_delete(
    person_id: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_person_id = _parse_uuid(person_id, "person_id")
        person = session.get(Person, parsed_person_id)
        if not person:
            return _redirect_ui("/people-ui", err="Person not found")
        membership = _get_org_membership(session, parsed_person_id, current_actor.organization.id)
        if membership is None:
            return _redirect_ui("/people-ui", err="Person not found")

        org_projects = _org_projects(session, current_actor.organization.id)
        org_project_ids = {row.id for row in org_projects}
        org_assets = _org_assets(session, current_actor.organization.id)
        org_asset_ids = {row.id for row in org_assets}
        org_reviews = _org_reviews(session, current_actor.organization.id)
        org_review_ids = {row.id for row in org_reviews}
        org_todos = _org_todos(session, current_actor.organization.id)
        org_todo_ids = {row.id for row in org_todos}

        membership_ref = session.exec(
            select(ProjectMembership).where(
                ProjectMembership.person_id == parsed_person_id,
                ProjectMembership.project_id.in_(org_project_ids),
            )
        ).first() or session.exec(
            select(AssetMembership).where(
                AssetMembership.person_id == parsed_person_id,
                AssetMembership.asset_id.in_(org_asset_ids),
            )
        ).first()
        review_ref = next(
            (
                row
                for row in org_reviews
                if row.author_id == parsed_person_id or row.reviewer_id == parsed_person_id
            ),
            None,
        )
        comment_ref = session.exec(
            select(ReviewComment).where(
                ReviewComment.author_id == parsed_person_id,
                ReviewComment.review_request_id.in_(org_review_ids),
            )
        ).first()
        decision_ref = session.exec(
            select(ReviewDecision).where(
                ReviewDecision.reviewer_id == parsed_person_id,
                ReviewDecision.review_request_id.in_(org_review_ids),
            )
        ).first()
        activity_ref = session.exec(
            select(ActivityLog).where(
                ActivityLog.actor_id == parsed_person_id,
                ActivityLog.organization_id == current_actor.organization.id,
            )
        ).first()
        todo_comment_ref = session.exec(
            select(TodoComment).where(
                TodoComment.author_id == parsed_person_id,
                TodoComment.todo_id.in_(org_todo_ids),
            )
        ).first()
        todo_document_ref = session.exec(
            select(TodoDocument).where(
                TodoDocument.uploaded_by == parsed_person_id,
                TodoDocument.todo_id.in_(org_todo_ids),
            )
        ).first()
        todo_ref = next(
            (
                row
                for row in org_todos
                if row.created_by == parsed_person_id
                or row.assignee_id == parsed_person_id
                or row.person_id == parsed_person_id
            ),
            None,
        )

        if (
            membership_ref
            or review_ref
            or comment_ref
            or decision_ref
            or activity_ref
            or todo_comment_ref
            or todo_document_ref
            or todo_ref
        ):
            return _redirect_ui(
                "/people-ui",
                err="Cannot remove person from organization with existing organization references",
            )

        session.delete(membership)
        session.commit()
        return _redirect_ui("/people-ui", ok="Person removed from organization")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/people-ui", err=f"Delete person failed: {exc}")


@router.get("/clients-ui")
def clients_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    rows = [
        {
            "id": client.id,
            "name": client.name,
            "tenant_url": client.tenant_url,
            "sensitivity_level": client.sensitivity_level.value,
            "salesforce_url": client.salesforce_url,
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
    salesforce_url: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        client = Client(
            organization_id=current_actor.organization.id,
            name=name.strip(),
            tenant_url=tenant_url.strip(),
            sensitivity_level=SensitivityLevel(sensitivity_level),
            salesforce_url=_normalize_http_url(salesforce_url) or None,
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
    salesforce_url: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        if not client:
            return _redirect_ui("/clients-ui", err="Client not found")

        client.name = name.strip()
        client.tenant_url = tenant_url.strip()
        client.sensitivity_level = SensitivityLevel(sensitivity_level)
        client.salesforce_url = _normalize_http_url(salesforce_url) or None
        session.add(client)
        session.commit()
        session.refresh(client)
        log_updated(
            session,
            entity_type=EntityType.client,
            entity_id=client.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"sensitivity_level": client.sensitivity_level.value},
        )
        return _redirect_ui("/clients-ui", ok="Client updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/clients-ui", err=f"Update client failed: {exc}")


@router.post("/clients-ui/delete", include_in_schema=False)
def clients_ui_delete(
    client_id: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        if not client:
            return _redirect_ui("/clients-ui", err="Client not found")

        project_ref = session.exec(
            select(Project).where(
                Project.client_id == parsed_client_id,
                Project.organization_id == current_actor.organization.id,
            )
        ).first()
        asset_ref = session.exec(
            select(Asset).where(
                Asset.client_id == parsed_client_id,
                Asset.organization_id == current_actor.organization.id,
            )
        ).first()
        connection_ref = session.exec(
            select(CelonisConnection).where(
                CelonisConnection.client_id == parsed_client_id,
                CelonisConnection.organization_id == current_actor.organization.id,
            )
        ).first()
        todo_ref = session.exec(
            select(Todo).where(
                Todo.client_id == parsed_client_id,
                Todo.organization_id == current_actor.organization.id,
            )
        ).first()

        if project_ref or asset_ref or connection_ref or todo_ref:
            return _redirect_ui("/clients-ui", err="Cannot delete client with existing references")

        session.delete(client)
        session.commit()
        return _redirect_ui("/clients-ui", ok="Client deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/clients-ui", err=f"Delete client failed: {exc}")


def _todo_scope_details(
    todo: Todo,
    *,
    person_name_by_id: dict,
    client_name_by_id: dict,
    project_name_by_id: dict,
) -> dict:
    if todo.project_id:
        return {
            "scope_kind": "project",
            "scope_label": project_name_by_id.get(todo.project_id, "Unknown project"),
            "scope_href": f"/projects-ui/{todo.project_id}/overview",
        }
    if todo.client_id:
        return {
            "scope_kind": "client",
            "scope_label": client_name_by_id.get(todo.client_id, "Unknown client"),
            "scope_href": f"/clients-ui/{todo.client_id}/overview",
        }
    if todo.person_id:
        return {
            "scope_kind": "person",
            "scope_label": person_name_by_id.get(todo.person_id, "Unknown person"),
            "scope_href": f"/people-ui/{todo.person_id}/overview",
        }
    return {
        "scope_kind": "unknown",
        "scope_label": "Unknown scope",
        "scope_href": "/todos-ui",
    }


@router.get("/todos-ui")
def todos_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    view_mode = request.query_params.get("view", "board")
    if view_mode not in {"board", "list"}:
        view_mode = "board"

    all_todos = list(_org_todos(session, current_actor.organization.id))
    all_people = sorted(
        _org_people(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    all_clients = list(_org_clients(session, current_actor.organization.id))
    all_projects = list(_org_projects(session, current_actor.organization.id))
    todo_ids = {row.id for row in all_todos}
    all_tags = list(session.exec(select(TodoTag)).all())
    all_comments = list(session.exec(select(TodoComment)).all())
    all_links = list(session.exec(select(TodoLink)).all())
    all_documents = list(session.exec(select(TodoDocument)).all())

    person_name_by_id = {row.id: row.name for row in all_people}
    client_name_by_id = {row.id: row.name for row in all_clients}
    project_name_by_id = {row.id: row.name for row in all_projects}

    tag_names_by_todo: dict[UUID, list[str]] = {}
    for row in all_tags:
        if row.todo_id not in todo_ids:
            continue
        tag_names_by_todo.setdefault(row.todo_id, []).append(row.name)

    comment_count_by_todo: dict[UUID, int] = {}
    for row in all_comments:
        if row.todo_id not in todo_ids:
            continue
        comment_count_by_todo[row.todo_id] = comment_count_by_todo.get(row.todo_id, 0) + 1

    link_count_by_todo: dict[UUID, int] = {}
    for row in all_links:
        if row.todo_id not in todo_ids:
            continue
        link_count_by_todo[row.todo_id] = link_count_by_todo.get(row.todo_id, 0) + 1

    document_count_by_todo: dict[UUID, int] = {}
    for row in all_documents:
        if row.todo_id not in todo_ids:
            continue
        document_count_by_todo[row.todo_id] = document_count_by_todo.get(row.todo_id, 0) + 1

    priority_order = {TodoPriority.high.value: 0, TodoPriority.medium.value: 1, TodoPriority.low.value: 2}
    all_todos.sort(
        key=lambda row: (
            priority_order[row.priority.value],
            row.due_at or datetime.max,
            row.updated_at,
        )
    )

    todo_rows = []
    for row in all_todos:
        scope_details = _todo_scope_details(
            row,
            person_name_by_id=person_name_by_id,
            client_name_by_id=client_name_by_id,
            project_name_by_id=project_name_by_id,
        )
        todo_rows.append(
            {
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "long_description_markdown": row.long_description_markdown,
                "status": row.status.value,
                "priority": row.priority.value,
                "due_at": row.due_at,
                "completed_at": row.completed_at,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "assignee_id": row.assignee_id,
                "assignee_name": person_name_by_id.get(row.assignee_id, "-") if row.assignee_id else "-",
                "created_by_name": person_name_by_id.get(row.created_by, "Unknown"),
                "tag_names": sorted(tag_names_by_todo.get(row.id, [])),
                "comment_count": comment_count_by_todo.get(row.id, 0),
                "link_count": link_count_by_todo.get(row.id, 0),
                "document_count": document_count_by_todo.get(row.id, 0),
                "selected_url": _with_query_params("/todos-ui", view=view_mode, selected=str(row.id)),
                **scope_details,
            }
        )

    selected_todo = None
    selected_row = None
    selected_todo_id = request.query_params.get("selected")
    if selected_todo_id:
        try:
            parsed_selected_id = _parse_uuid(selected_todo_id, "selected")
            selected_todo = next((row for row in all_todos if row.id == parsed_selected_id), None)
        except ValueError:
            selected_todo = None
    if selected_todo is None and all_todos:
        selected_todo = all_todos[0]
    if selected_todo is not None:
        selected_row = next((row for row in todo_rows if row["id"] == selected_todo.id), None)

    board_columns = []
    for status in TodoStatus:
        column_rows = [row for row in todo_rows if row["status"] == status.value]
        board_columns.append(
            {
                "key": status.value,
                "label": status.value.replace("_", " ").title(),
                "rows": column_rows,
            }
        )

    selected_comments = []
    selected_tags = []
    selected_links = []
    selected_documents = []
    selected_activity = []
    detail_redirect = _with_query_params(
        "/todos-ui",
        view=view_mode,
        selected=str(selected_todo.id) if selected_todo else None,
    )

    if selected_todo is not None:
        selected_comments = [
            {
                "id": row.id,
                "content": row.content,
                "author_name": person_name_by_id.get(row.author_id, "Unknown"),
                "created_at": row.created_at,
            }
            for row in sorted(
                [row for row in all_comments if row.todo_id == selected_todo.id],
                key=lambda row: row.created_at,
                reverse=True,
            )
        ]
        selected_tags = sorted(
            [row for row in all_tags if row.todo_id == selected_todo.id],
            key=lambda row: row.name.lower(),
        )
        selected_links = [
            {
                "id": row.id,
                "label": row.label,
                "url": row.url,
                "normalized_url": _normalize_http_url(row.url),
                "created_at": row.created_at,
            }
            for row in sorted(
                [row for row in all_links if row.todo_id == selected_todo.id],
                key=lambda row: row.created_at,
                reverse=True,
            )
        ]
        selected_documents = [
            {
                "id": row.id,
                "title": row.title,
                "source_type": row.source_type.value,
                "url": row.url,
                "normalized_url": _normalize_http_url(row.url),
                "download_url": make_document_url(row.storage_path),
                "original_filename": row.original_filename,
                "uploader_name": person_name_by_id.get(row.uploaded_by, "Unknown"),
                "created_at": row.created_at,
            }
            for row in sorted(
                [row for row in all_documents if row.todo_id == selected_todo.id],
                key=lambda row: row.created_at,
                reverse=True,
            )
        ]
        selected_activity = [
            {
                "timestamp": row.timestamp,
                "action": row.action,
                "actor_name": person_name_by_id.get(row.actor_id, "Unknown"),
                "metadata_json": row.metadata_json,
            }
            for row in sorted(
                session.exec(
                    select(ActivityLog).where(
                        (ActivityLog.entity_type == EntityType.todo)
                        & (ActivityLog.entity_id == selected_todo.id)
                        & (ActivityLog.organization_id == current_actor.organization.id)
                    )
                ).all(),
                key=lambda row: row.timestamp,
                reverse=True,
            )
        ]

    scope_groups = [
        {
            "label": "People",
            "options": [{"value": f"person:{row.id}", "label": row.name} for row in all_people],
        },
        {
            "label": "Clients",
            "options": [{"value": f"client:{row.id}", "label": row.name} for row in all_clients],
        },
        {
            "label": "Projects",
            "options": [{"value": f"project:{row.id}", "label": row.name} for row in all_projects],
        },
    ]

    return templates.TemplateResponse(
        "todos.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "view_mode": view_mode,
            "board_columns": board_columns,
            "todo_rows": todo_rows,
            "selected_todo": selected_todo,
            "selected_row": selected_row,
            "selected_comments": selected_comments,
            "selected_tags": selected_tags,
            "selected_links": selected_links,
            "selected_documents": selected_documents,
            "selected_activity": selected_activity,
            "detail_redirect": detail_redirect,
            "scope_groups": scope_groups,
            "people": all_people,
            "todo_status_options": [row.value for row in TodoStatus],
            "todo_priority_options": [row.value for row in TodoPriority],
            "board_view_url": _with_query_params("/todos-ui", view="board", selected=str(selected_todo.id) if selected_todo else None),
            "list_view_url": _with_query_params("/todos-ui", view="list", selected=str(selected_todo.id) if selected_todo else None),
        },
    )


@router.post("/todos-ui/create", include_in_schema=False)
def todos_ui_create(
    title: str = Form(...),
    description: str = Form(""),
    long_description_markdown: str = Form(""),
    priority: str = Form("medium"),
    due_at: str = Form(""),
    assignee_id: str = Form(""),
    scope_ref: str = Form(""),
    person_id: str = Form(""),
    client_id: str = Form(""),
    project_id: str = Form(""),
    redirect_to: str = Form("/dashboard"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/dashboard")
    try:
        if not title.strip():
            return _redirect_ui(target_path, err="Todo title is required")

        parsed_person_id, parsed_client_id, parsed_project_id = _resolve_todo_scope(
            scope_ref=scope_ref,
            person_id=person_id,
            client_id=client_id,
            project_id=project_id,
        )
        org_people = {row.id for row in _org_people(session, current_actor.organization.id)}
        if parsed_person_id and parsed_person_id not in org_people:
            return _redirect_ui(target_path, err="Selected person is not in the active organization")
        if parsed_client_id and _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            return _redirect_ui(target_path, err="Selected client not found")
        if parsed_project_id and _get_org_project(session, parsed_project_id, current_actor.organization.id) is None:
            return _redirect_ui(target_path, err="Selected project not found")
        parsed_assignee_id = _parse_optional_uuid(assignee_id, "assignee_id")
        if parsed_assignee_id and parsed_assignee_id not in org_people:
            return _redirect_ui(target_path, err="Assignee must belong to the active organization")

        todo = Todo(
            organization_id=current_actor.organization.id,
            title=title.strip(),
            description=description.strip() or None,
            long_description_markdown=long_description_markdown.strip() or None,
            priority=TodoPriority(priority),
            due_at=_parse_optional_datetime(due_at, "due_at"),
            assignee_id=parsed_assignee_id,
            created_by=current_actor.person.id,
            person_id=parsed_person_id,
            client_id=parsed_client_id,
            project_id=parsed_project_id,
        )
        session.add(todo)
        session.commit()
        session.refresh(todo)

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=todo.id,
            actor_id=current_actor.person.id,
            action="todo.created",
            organization_id=current_actor.organization.id,
            metadata=_todo_activity_metadata(todo),
        )
        target_path = _with_query_params(target_path, selected=str(todo.id))
        return _redirect_ui(target_path, ok="Todo created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Create todo failed: {exc}")


@router.post("/todos-ui/update", include_in_schema=False)
def todos_ui_update(
    todo_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    long_description_markdown: str = Form(""),
    status: str = Form("open"),
    priority: str = Form("medium"),
    due_at: str = Form(""),
    assignee_id: str = Form(""),
    redirect_to: str = Form("/dashboard"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/dashboard")
    try:
        parsed_todo_id = _parse_uuid(todo_id, "todo_id")
        todo = _get_org_todo(session, parsed_todo_id, current_actor.organization.id)
        if not todo:
            return _redirect_ui(target_path, err="Todo not found")
        if not title.strip():
            return _redirect_ui(target_path, err="Todo title is required")

        org_people = {row.id for row in _org_people(session, current_actor.organization.id)}

        changed_fields = []
        if todo.title != title.strip():
            changed_fields.append("title")
        todo.title = title.strip()
        if (todo.description or None) != (description.strip() or None):
            changed_fields.append("description")
        todo.description = description.strip() or None
        if (todo.long_description_markdown or None) != (long_description_markdown.strip() or None):
            changed_fields.append("long_description_markdown")
        todo.long_description_markdown = long_description_markdown.strip() or None
        if todo.status.value != status:
            changed_fields.append("status")
        todo.status = TodoStatus(status)
        if todo.priority.value != priority:
            changed_fields.append("priority")
        todo.priority = TodoPriority(priority)
        parsed_due_at = _parse_optional_datetime(due_at, "due_at")
        if todo.due_at != parsed_due_at:
            changed_fields.append("due_at")
        todo.due_at = parsed_due_at
        parsed_assignee_id = _parse_optional_uuid(assignee_id, "assignee_id")
        if parsed_assignee_id and parsed_assignee_id not in org_people:
            return _redirect_ui(target_path, err="Assignee must belong to the active organization")
        if todo.assignee_id != parsed_assignee_id:
            changed_fields.append("assignee_id")
        todo.assignee_id = parsed_assignee_id
        todo.updated_at = datetime.utcnow()
        if todo.status == TodoStatus.done:
            todo.completed_at = datetime.utcnow()
        else:
            todo.completed_at = None

        session.add(todo)
        session.commit()

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=todo.id,
            actor_id=current_actor.person.id,
            action="todo.updated",
            organization_id=current_actor.organization.id,
            metadata={
                **_todo_activity_metadata(todo),
                "changed_fields": sorted(set(changed_fields)),
            },
        )
        target_path = _with_query_params(target_path, selected=str(todo.id))
        return _redirect_ui(target_path, ok="Todo updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Update todo failed: {exc}")


@router.post("/todos-ui/delete", include_in_schema=False)
def todos_ui_delete(
    todo_id: str = Form(...),
    redirect_to: str = Form("/dashboard"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/dashboard")
    try:
        parsed_todo_id = _parse_uuid(todo_id, "todo_id")
        todo = _get_org_todo(session, parsed_todo_id, current_actor.organization.id)
        if not todo:
            return _redirect_ui(target_path, err="Todo not found")

        deleted_files = delete_todo_with_children(session, todo)

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=parsed_todo_id,
            actor_id=current_actor.person.id,
            action="todo.deleted",
            organization_id=current_actor.organization.id,
            metadata={"deleted_file_count": len(deleted_files)},
        )
        return _redirect_ui(target_path, ok="Todo deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Delete todo failed: {exc}")


@router.post("/todos-ui/comments/create", include_in_schema=False)
def todos_ui_create_comment(
    todo_id: str = Form(...),
    content: str = Form(...),
    redirect_to: str = Form("/todos-ui"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/todos-ui")
    try:
        parsed_todo_id = _parse_uuid(todo_id, "todo_id")
        todo = _get_org_todo(session, parsed_todo_id, current_actor.organization.id)
        if not todo:
            return _redirect_ui(target_path, err="Todo not found")
        if not content.strip():
            return _redirect_ui(target_path, err="Comment content is required")

        comment = TodoComment(
            todo_id=parsed_todo_id,
            author_id=current_actor.person.id,
            content=content.strip(),
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=parsed_todo_id,
            actor_id=current_actor.person.id,
            action="todo.comment.added",
            organization_id=current_actor.organization.id,
            metadata={"comment_id": str(comment.id)},
        )
        return _redirect_ui(target_path, ok="Comment added")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Add comment failed: {exc}")


@router.post("/todos-ui/tags/create", include_in_schema=False)
def todos_ui_create_tag(
    todo_id: str = Form(...),
    name: str = Form(...),
    redirect_to: str = Form("/todos-ui"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/todos-ui")
    try:
        parsed_todo_id = _parse_uuid(todo_id, "todo_id")
        todo = _get_org_todo(session, parsed_todo_id, current_actor.organization.id)
        if not todo:
            return _redirect_ui(target_path, err="Todo not found")

        normalized_name = normalize_tag_name(name)
        if not normalized_name:
            return _redirect_ui(target_path, err="Tag name is required")

        existing_tag = next(
            (
                row
                for row in session.exec(select(TodoTag).where(TodoTag.todo_id == parsed_todo_id)).all()
                if row.name.casefold() == normalized_name.casefold()
            ),
            None,
        )
        if existing_tag:
            return _redirect_ui(target_path, err="Tag already exists")

        tag = TodoTag(todo_id=parsed_todo_id, name=normalized_name)
        session.add(tag)
        session.commit()
        session.refresh(tag)

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=parsed_todo_id,
            actor_id=current_actor.person.id,
            action="todo.tag.added",
            organization_id=current_actor.organization.id,
            metadata={"tag_id": str(tag.id), "tag": tag.name},
        )
        return _redirect_ui(target_path, ok="Tag added")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Add tag failed: {exc}")


@router.post("/todos-ui/tags/delete", include_in_schema=False)
def todos_ui_delete_tag(
    tag_id: str = Form(...),
    redirect_to: str = Form("/todos-ui"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/todos-ui")
    try:
        tag = session.get(TodoTag, _parse_uuid(tag_id, "tag_id"))
        if not tag:
            return _redirect_ui(target_path, err="Tag not found")

        if _get_org_todo(session, tag.todo_id, current_actor.organization.id) is None:
            return _redirect_ui(target_path, err="Tag not found")

        todo_id = tag.todo_id
        tag_name = tag.name
        session.delete(tag)
        session.commit()

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=todo_id,
            actor_id=current_actor.person.id,
            action="todo.tag.removed",
            organization_id=current_actor.organization.id,
            metadata={"tag": tag_name},
        )
        return _redirect_ui(target_path, ok="Tag removed")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Remove tag failed: {exc}")


@router.post("/todos-ui/links/create", include_in_schema=False)
def todos_ui_create_link(
    todo_id: str = Form(...),
    label: str = Form(""),
    url: str = Form(...),
    redirect_to: str = Form("/todos-ui"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/todos-ui")
    try:
        parsed_todo_id = _parse_uuid(todo_id, "todo_id")
        todo = _get_org_todo(session, parsed_todo_id, current_actor.organization.id)
        if not todo:
            return _redirect_ui(target_path, err="Todo not found")

        normalized_url = _normalize_http_url(url)
        if not normalized_url:
            return _redirect_ui(target_path, err="Link URL must start with http or https")

        link = TodoLink(todo_id=parsed_todo_id, label=label.strip() or None, url=normalized_url)
        session.add(link)
        session.commit()
        session.refresh(link)

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=parsed_todo_id,
            actor_id=current_actor.person.id,
            action="todo.link.added",
            organization_id=current_actor.organization.id,
            metadata={"link_id": str(link.id), "url": link.url},
        )
        return _redirect_ui(target_path, ok="Link added")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Add link failed: {exc}")


@router.post("/todos-ui/links/delete", include_in_schema=False)
def todos_ui_delete_link(
    link_id: str = Form(...),
    redirect_to: str = Form("/todos-ui"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/todos-ui")
    try:
        link = session.get(TodoLink, _parse_uuid(link_id, "link_id"))
        if not link:
            return _redirect_ui(target_path, err="Link not found")

        if _get_org_todo(session, link.todo_id, current_actor.organization.id) is None:
            return _redirect_ui(target_path, err="Link not found")

        todo_id = link.todo_id
        deleted_url = link.url
        session.delete(link)
        session.commit()

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=todo_id,
            actor_id=current_actor.person.id,
            action="todo.link.removed",
            organization_id=current_actor.organization.id,
            metadata={"url": deleted_url},
        )
        return _redirect_ui(target_path, ok="Link removed")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Remove link failed: {exc}")


@router.post("/todos-ui/documents/create", include_in_schema=False)
def todos_ui_create_document(
    todo_id: str = Form(...),
    title: str = Form(""),
    document_url: str = Form(""),
    upload: UploadFile | None = File(None),
    redirect_to: str = Form("/todos-ui"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/todos-ui")
    stored_upload_path: str | None = None
    try:
        parsed_todo_id = _parse_uuid(todo_id, "todo_id")
        todo = _get_org_todo(session, parsed_todo_id, current_actor.organization.id)
        if not todo:
            return _redirect_ui(target_path, err="Todo not found")

        if upload is not None and upload.filename:
            stored = store_uploaded_document(upload)
            stored_upload_path = stored["storage_path"]
            document = TodoDocument(
                todo_id=parsed_todo_id,
                source_type=TodoDocumentSource.file,
                title=title.strip() or stored["title"],
                storage_path=stored["storage_path"],
                original_filename=stored["original_filename"],
                uploaded_by=current_actor.person.id,
            )
        else:
            normalized_url = _normalize_http_url(document_url)
            if not normalized_url:
                return _redirect_ui(target_path, err="Provide either a valid document URL or an uploaded file")
            document = TodoDocument(
                todo_id=parsed_todo_id,
                source_type=TodoDocumentSource.url,
                title=title.strip() or normalized_url,
                url=normalized_url,
                uploaded_by=current_actor.person.id,
            )

        session.add(document)
        session.commit()
        session.refresh(document)

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=parsed_todo_id,
            actor_id=current_actor.person.id,
            action="todo.document.added",
            organization_id=current_actor.organization.id,
            metadata={
                "document_id": str(document.id),
                "source_type": document.source_type.value,
                "title": document.title,
            },
        )
        return _redirect_ui(target_path, ok="Document added")
    except Exception as exc:
        if stored_upload_path:
            remove_document_file(stored_upload_path)
        session.rollback()
        return _redirect_ui(target_path, err=f"Add document failed: {exc}")


@router.post("/todos-ui/documents/delete", include_in_schema=False)
def todos_ui_delete_document(
    document_id: str = Form(...),
    redirect_to: str = Form("/todos-ui"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/todos-ui")
    try:
        document = session.get(TodoDocument, _parse_uuid(document_id, "document_id"))
        if not document:
            return _redirect_ui(target_path, err="Document not found")

        if _get_org_todo(session, document.todo_id, current_actor.organization.id) is None:
            return _redirect_ui(target_path, err="Document not found")

        todo_id = document.todo_id
        storage_path = document.storage_path
        title = document.title
        session.delete(document)
        session.commit()

        if storage_path:
            remove_document_file(storage_path)

        log_activity(
            session,
            entity_type=EntityType.todo,
            entity_id=todo_id,
            actor_id=current_actor.person.id,
            action="todo.document.removed",
            organization_id=current_actor.organization.id,
            metadata={"title": title},
        )
        return _redirect_ui(target_path, ok="Document removed")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Remove document failed: {exc}")


@router.get("/people-ui/{person_id}/overview")
def person_overview_ui(
    person_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_person_id = _parse_uuid(person_id, "person_id")
    except ValueError as exc:
        return _redirect_ui("/people-ui", err=str(exc))

    org_people = _org_people(session, current_actor.organization.id)
    person = next((row for row in org_people if row.id == parsed_person_id), None)
    if person is None:
        return _redirect_ui("/people-ui", err="Person not found")

    memberships = list(
        session.exec(select(ProjectMembership).where(ProjectMembership.person_id == parsed_person_id)).all()
    )
    all_projects = _org_projects(session, current_actor.organization.id)
    org_project_ids = {project.id for project in all_projects}
    memberships = [row for row in memberships if row.project_id in org_project_ids]
    project_ids = {membership.project_id for membership in memberships}
    projects = [project for project in all_projects if project.id in project_ids] if project_ids else []
    client_ids = {project.client_id for project in projects}

    asset_memberships = list(
        session.exec(select(AssetMembership).where(AssetMembership.person_id == parsed_person_id)).all()
    )
    direct_asset_ids = {membership.asset_id for membership in asset_memberships}
    all_assets = _org_assets(session, current_actor.organization.id)
    project_assets = [asset for asset in all_assets if asset.project_id in project_ids] if project_ids else []
    direct_assets = [asset for asset in all_assets if asset.id in direct_asset_ids] if direct_asset_ids else []
    asset_by_id = {asset.id: asset for asset in [*project_assets, *direct_assets]}
    assets = sorted(asset_by_id.values(), key=lambda row: row.created_at, reverse=True)

    reviews = [
        row
        for row in _org_reviews(session, current_actor.organization.id)
        if row.author_id == parsed_person_id or row.reviewer_id == parsed_person_id
    ]
    review_ids = {review.id for review in reviews}

    all_todos = _org_todos(session, current_actor.organization.id)
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
    timeline_rows = _timeline_by_entity_keys(
        session,
        entity_keys,
        organization_id=current_actor.organization.id,
    )

    project_name_by_id = {project.id: project.name for project in projects}
    project_status_by_id = {project.id: project.status.value for project in projects}
    project_client_id_by_project_id = {project.id: project.client_id for project in projects}
    all_clients = _org_clients(session, current_actor.organization.id)
    client_name_by_id = {client.id: client.name for client in all_clients if client.id in client_ids}
    people = org_people
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
def client_overview_ui(
    client_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
    except ValueError as exc:
        return _redirect_ui("/clients-ui", err=str(exc))

    client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
    if not client:
        return _redirect_ui("/clients-ui", err="Client not found")

    projects = [
        row
        for row in _org_projects(session, current_actor.organization.id)
        if row.client_id == parsed_client_id
    ]
    project_ids = {project.id for project in projects}
    assets = [
        row
        for row in _org_assets(session, current_actor.organization.id)
        if row.client_id == parsed_client_id
    ]
    asset_ids = {asset.id for asset in assets}
    all_memberships = list(session.exec(select(ProjectMembership)).all())
    memberships = [row for row in all_memberships if row.project_id in project_ids] if project_ids else []
    person_ids = {membership.person_id for membership in memberships}

    all_reviews = _org_reviews(session, current_actor.organization.id)
    reviews = [
        row
        for row in all_reviews
        if row.project_id in project_ids or row.asset_id in asset_ids
    ]
    person_ids.update(review.author_id for review in reviews)
    person_ids.update(review.reviewer_id for review in reviews)

    all_people = _org_people(session, current_actor.organization.id)
    people = [row for row in all_people if row.id in person_ids] if person_ids else []
    person_name_by_id = {person.id: person.name for person in people}

    all_todos = _org_todos(session, current_actor.organization.id)
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
    timeline_rows = _timeline_by_entity_keys(
        session,
        entity_keys,
        organization_id=current_actor.organization.id,
    )

    project_name_by_id = {project.id: project.name for project in projects}
    asset_name_by_id = {asset.id: asset.name for asset in assets}
    all_people_name_by_id = {person.id: person.name for person in all_people}

    gitlab_repos = (
        list(session.exec(select(GitLabRepo)).all())
        if project_ids
        else []
    )
    gitlab_repos = [row for row in gitlab_repos if row.project_id in project_ids]
    repo_ids = {row.id for row in gitlab_repos}
    gitlab_runs = (
        [row for row in session.exec(select(GitLabPipelineRun)).all() if row.repo_id in repo_ids]
        if repo_ids
        else []
    )
    last_run_by_repo_id: dict[UUID, GitLabPipelineRun] = {}
    for row in sorted(gitlab_runs, key=lambda item: item.triggered_at, reverse=True):
        if row.repo_id not in last_run_by_repo_id:
            last_run_by_repo_id[row.repo_id] = row
    gitlab_repo_rows = [
        {
            "id": row.id,
            "name": row.name,
            "project_id": row.project_id,
            "project_name": project_name_by_id.get(row.project_id, "-"),
            "repo_path": row.repo_path,
            "default_branch": row.default_branch,
            "is_active": row.is_active,
            "last_status": last_run_by_repo_id[row.id].status if row.id in last_run_by_repo_id else "-",
            "last_triggered_at": (
                last_run_by_repo_id[row.id].triggered_at if row.id in last_run_by_repo_id else None
            ),
        }
        for row in sorted(gitlab_repos, key=lambda item: item.created_at, reverse=True)
    ]

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
            "latest_snapshot": session.exec(
                select(CelonisSnapshot)
                .where(CelonisSnapshot.client_id == parsed_client_id)
                .order_by(CelonisSnapshot.created_at.desc())
            ).first(),
            "client": client,
            "projects": projects,
            "assets": assets,
            "reviews": reviews,
            "people": people,
            "memberships": memberships,
            "todo_rows": todo_rows,
            "gitlab_repo_rows": gitlab_repo_rows,
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
def project_overview_ui(
    project_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
    except ValueError as exc:
        return _redirect_ui("/projects-ui", err=str(exc))

    project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
    if not project:
        return _redirect_ui("/projects-ui", err="Project not found")

    client = _get_org_client(session, project.client_id, current_actor.organization.id)
    memberships = list(
        session.exec(select(ProjectMembership).where(ProjectMembership.project_id == parsed_project_id)).all()
    )
    person_ids = {membership.person_id for membership in memberships}
    all_people = _org_people(session, current_actor.organization.id)
    people = [row for row in all_people if row.id in person_ids] if person_ids else []
    person_name_by_id = {person.id: person.name for person in people}

    assets = [
        row
        for row in _org_assets(session, current_actor.organization.id)
        if row.project_id == parsed_project_id
    ]
    asset_ids = {asset.id for asset in assets}
    reviews = [
        row
        for row in _org_reviews(session, current_actor.organization.id)
        if row.project_id == parsed_project_id
    ]
    for review in reviews:
        person_ids.add(review.author_id)
        person_ids.add(review.reviewer_id)

    todos = [
        row
        for row in _org_todos(session, current_actor.organization.id)
        if row.project_id == parsed_project_id
    ]
    todos.sort(key=lambda row: row.created_at, reverse=True)
    todo_ids = {todo.id for todo in todos}

    entity_keys: list[tuple[EntityType, UUID]] = [(EntityType.project, parsed_project_id)]
    entity_keys.append((EntityType.client, project.client_id))
    entity_keys.extend((EntityType.membership, row.id) for row in memberships)
    entity_keys.extend((EntityType.asset, asset_id) for asset_id in asset_ids)
    entity_keys.extend((EntityType.review, review.id) for review in reviews)
    entity_keys.extend((EntityType.person, person_id_value) for person_id_value in person_ids)
    entity_keys.extend((EntityType.todo, todo_id) for todo_id in todo_ids)
    timeline_rows = _timeline_by_entity_keys(
        session,
        entity_keys,
        organization_id=current_actor.organization.id,
    )

    asset_name_by_id = {asset.id: asset.name for asset in assets}
    all_people_name_by_id = {person.id: person.name for person in all_people}
    gitlab_repos = list(
        session.exec(select(GitLabRepo).where(GitLabRepo.project_id == parsed_project_id)).all()
    )
    repo_ids = {row.id for row in gitlab_repos}
    gitlab_runs = (
        [row for row in session.exec(select(GitLabPipelineRun)).all() if row.repo_id in repo_ids]
        if repo_ids
        else []
    )
    last_run_by_repo_id: dict[UUID, GitLabPipelineRun] = {}
    for row in sorted(gitlab_runs, key=lambda item: item.triggered_at, reverse=True):
        if row.repo_id not in last_run_by_repo_id:
            last_run_by_repo_id[row.repo_id] = row
    gitlab_repo_rows = [
        {
            "id": row.id,
            "name": row.name,
            "repo_path": row.repo_path,
            "default_branch": row.default_branch,
            "is_active": row.is_active,
            "last_status": last_run_by_repo_id[row.id].status if row.id in last_run_by_repo_id else "-",
            "last_triggered_at": (
                last_run_by_repo_id[row.id].triggered_at if row.id in last_run_by_repo_id else None
            ),
        }
        for row in sorted(gitlab_repos, key=lambda item: item.created_at, reverse=True)
    ]
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
            "gitlab_repo_rows": gitlab_repo_rows,
            "timeline_rows": timeline_rows,
            "person_name_by_id": person_name_by_id,
            "asset_name_by_id": asset_name_by_id,
            "all_people": all_people,
            "todo_status_options": [row.value for row in TodoStatus],
            "todo_priority_options": [row.value for row in TodoPriority],
        },
    )


@router.post("/gitlab-ui/repos/create", include_in_schema=False)
def gitlab_ui_create_repo(
    project_id: str = Form(...),
    name: str = Form(...),
    repo_path: str = Form(...),
    default_branch: str = Form("main"),
    token_override: str = Form(""),
    webhook_secret: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        if not project:
            return _redirect_ui("/projects-ui", err="Project not found")

        row = GitLabRepo(
            project_id=parsed_project_id,
            name=name.strip(),
            repo_path=repo_path.strip(),
            token_override=token_override.strip() or None,
            default_branch=default_branch.strip() or "main",
            webhook_secret=webhook_secret.strip() or None,
            created_by=current_actor.person.id,
        )
        session.add(row)
        session.commit()
        session.refresh(row)

        log_created(
            session,
            entity_type=EntityType.gitlab_repo,
            entity_id=row.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"project_id": str(row.project_id), "repo_path": row.repo_path},
        )
        return _redirect_ui(f"/projects-ui/{row.project_id}/overview", ok="GitLab repo created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/projects-ui", err=f"Create GitLab repo failed: {exc}")


@router.post("/gitlab-ui/repos/{repo_id}/trigger", include_in_schema=False)
def gitlab_ui_trigger_pipeline(
    repo_id: str,
    redirect_to: str = Form(""),
    ref: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    fallback_redirect = "/projects-ui"
    try:
        parsed_repo_id = _parse_uuid(repo_id, "repo_id")
        repo = session.get(GitLabRepo, parsed_repo_id)
        if not repo:
            return _redirect_ui(fallback_redirect, err="Active GitLab repo not found")
        project = _get_org_project(session, repo.project_id, current_actor.organization.id)
        if project is None or not repo.is_active:
            return _redirect_ui(fallback_redirect, err="Active GitLab repo not found")

        settings = get_settings()
        gateway = GitLabGateway(settings)
        result = gateway.trigger_pipeline(
            repo_path=repo.repo_path,
            ref=ref.strip() or repo.default_branch,
            variables={},
            token_override=repo.token_override,
        )

        run = GitLabPipelineRun(
            repo_id=repo.id,
            pipeline_id=result.pipeline_id,
            ref=result.ref,
            status=result.status,
            triggered_by=current_actor.person.id,
            web_url=result.web_url,
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        log_created(
            session,
            entity_type=EntityType.gitlab_pipeline_run,
            entity_id=run.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"repo_id": str(repo.id), "pipeline_id": run.pipeline_id, "status": run.status},
        )
        target = _normalize_redirect_path(redirect_to, fallback=f"/projects-ui/{repo.project_id}/overview")
        return _redirect_ui(target, ok=f"Pipeline #{run.pipeline_id} triggered")
    except Exception as exc:
        session.rollback()
        target = _normalize_redirect_path(redirect_to, fallback=fallback_redirect)
        return _redirect_ui(target, err=f"Trigger pipeline failed: {exc}")


@router.post("/gitlab-ui/repos/{repo_id}/deactivate", include_in_schema=False)
def gitlab_ui_deactivate_repo(
    repo_id: str,
    redirect_to: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    fallback_redirect = "/projects-ui"
    try:
        parsed_repo_id = _parse_uuid(repo_id, "repo_id")
        repo = session.get(GitLabRepo, parsed_repo_id)
        if not repo:
            return _redirect_ui(fallback_redirect, err="GitLab repo not found")
        project = _get_org_project(session, repo.project_id, current_actor.organization.id)
        if project is None:
            return _redirect_ui(fallback_redirect, err="GitLab repo not found")

        repo.is_active = False
        session.add(repo)
        session.commit()

        log_updated(
            session,
            entity_type=EntityType.gitlab_repo,
            entity_id=repo.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"is_active": repo.is_active},
        )
        target = _normalize_redirect_path(redirect_to, fallback=f"/projects-ui/{repo.project_id}/overview")
        return _redirect_ui(target, ok="GitLab repo deactivated")
    except Exception as exc:
        session.rollback()
        target = _normalize_redirect_path(redirect_to, fallback=fallback_redirect)
        return _redirect_ui(target, err=f"Deactivate GitLab repo failed: {exc}")


@router.get("/gitlab-ui/{repo_id}/overview")
def gitlab_repo_overview_ui(
    repo_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_repo_id = _parse_uuid(repo_id, "repo_id")
    except ValueError as exc:
        return _redirect_ui("/projects-ui", err=str(exc))

    repo = session.get(GitLabRepo, parsed_repo_id)
    if not repo:
        return _redirect_ui("/projects-ui", err="GitLab repo not found")

    project = _get_org_project(session, repo.project_id, current_actor.organization.id)
    if not project:
        return _redirect_ui("/projects-ui", err="Project not found")
    client = _get_org_client(session, project.client_id, current_actor.organization.id)

    runs = list(
        session.exec(select(GitLabPipelineRun).where(GitLabPipelineRun.repo_id == repo.id)).all()
    )
    runs = sorted(runs, key=lambda row: row.triggered_at, reverse=True)

    people = _org_people(session, current_actor.organization.id)
    person_name_by_id = {row.id: row.name for row in people}
    run_rows = [
        {
            "id": row.id,
            "pipeline_id": row.pipeline_id,
            "ref": row.ref,
            "status": row.status,
            "triggered_by": row.triggered_by,
            "triggered_by_name": person_name_by_id.get(row.triggered_by, "system") if row.triggered_by else "system",
            "triggered_at": row.triggered_at,
            "web_url": row.web_url,
            "updated_at": row.updated_at,
        }
        for row in runs
    ]

    return templates.TemplateResponse(
        "gitlab_repo_overview.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "repo": repo,
            "project": project,
            "client": client,
            "run_rows": run_rows,
        },
    )


@router.get("/templates-ui")
def templates_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    libraries = sorted(
        [
            row
            for row in _org_template_libraries(session, current_actor.organization.id)
            if row.library_type == LibraryType.template
        ],
        key=lambda row: row.created_at,
        reverse=True,
    )
    templates_rows = sorted(
        _org_templates(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    instantiations = sorted(
        _org_template_instantiations(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    projects = sorted(
        _org_projects(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    people = sorted(
        _org_people(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )

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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_scope = TemplateScope(scope)
        parsed_client_id = _parse_uuid(client_id, "client_id") if client_id.strip() else None
        if parsed_client_id and _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            return _redirect_ui("/templates-ui", err="Client not found")
        library = TemplateLibrary(
            organization_id=current_actor.organization.id,
            name=name.strip(),
            scope=parsed_scope,
            library_type=LibraryType.template,
            client_id=parsed_client_id,
        )
        session.add(library)
        session.commit()
        session.refresh(library)
        log_created(
            session,
            entity_type=EntityType.template,
            entity_id=library.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_library_id = _parse_uuid(library_id, "library_id")
        library = _get_org_template_library(session, parsed_library_id, current_actor.organization.id)
        if library is None:
            return _redirect_ui("/templates-ui", err="Library not found")
        parsed_created_by = _parse_uuid(created_by, "created_by")
        org_people = {row.id for row in _org_people(session, current_actor.organization.id)}
        if parsed_created_by not in org_people:
            return _redirect_ui(
                "/templates-ui",
                err="Template owner must belong to the active organization",
            )

        template = Template(
            organization_id=current_actor.organization.id,
            library_id=parsed_library_id,
            title=title.strip(),
            category=category.strip(),
            description=description.strip() or None,
            storage_type=TemplateStorageType(storage_type),
            storage_url=storage_url.strip(),
            created_by=parsed_created_by,
            requires_review=requires_review is not None,
        )
        session.add(template)
        session.commit()
        session.refresh(template)
        log_created(
            session,
            entity_type=EntityType.template,
            entity_id=template.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_template_id = _parse_uuid(template_id, "template_id")
        template = _get_org_template(session, parsed_template_id, current_actor.organization.id)
        if not template or not template.is_active:
            return _redirect_ui("/templates-ui", err="Template not found or inactive")

        parsed_project_id = _parse_uuid(project_id, "project_id")
        parsed_client_id = _parse_uuid(client_id, "client_id")
        parsed_author_id = _parse_uuid(author_id, "author_id")
        parsed_reviewer_id = _parse_uuid(reviewer_id, "reviewer_id")

        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        if project is None:
            return _redirect_ui("/templates-ui", err="Project not found")
        if client is None:
            return _redirect_ui("/templates-ui", err="Client not found")
        org_people = {row.id for row in _org_people(session, current_actor.organization.id)}
        if parsed_author_id not in org_people or parsed_reviewer_id not in org_people:
            return _redirect_ui(
                "/templates-ui",
                err="Author and reviewer must belong to the active organization",
            )

        instantiation = TemplateService.instantiate_template(
            session,
            template=template,
            payload=TemplateInstantiateCreate(
                project_id=parsed_project_id,
                client_id=parsed_client_id,
                author_id=parsed_author_id,
                reviewer_id=parsed_reviewer_id,
            ),
            organization_id=current_actor.organization.id,
        )
        log_created(
            session,
            entity_type=EntityType.template_instantiation,
            entity_id=instantiation.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"template_id": str(template.id), "project_id": str(instantiation.project_id)},
        )
        return _redirect_ui("/templates-ui", ok="Template instantiated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/templates-ui", err=f"Template instantiation failed: {exc}")


@router.get("/files-ui")
def files_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    libraries = sorted(
        [
            row
            for row in _org_template_libraries(session, current_actor.organization.id)
            if row.library_type == LibraryType.document
        ],
        key=lambda row: row.created_at,
        reverse=True,
    )
    files = sorted(
        _org_delivery_files(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )
    projects = sorted(
        _org_projects(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )

    library_name_by_id = {library.id: library.name for library in libraries}
    client_name_by_id = {client.id: client.name for client in clients}
    project_name_by_id = {project.id: project.name for project in projects}

    rows = [
        {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "file_source": row.file_source.value,
            "external_url": row.external_url,
            "library_id": row.library_id,
            "library_name": library_name_by_id.get(row.library_id, "-")
            if row.library_id
            else "-",
            "stored_filename": row.stored_filename,
            "mime_type": row.mime_type,
            "file_size_bytes": row.file_size_bytes,
            "client_name": client_name_by_id.get(row.client_id, "-") if row.client_id else "-",
            "project_name": project_name_by_id.get(row.project_id, "-") if row.project_id else "-",
            "created_at": row.created_at,
        }
        for row in files
    ]

    return templates.TemplateResponse(
        "files.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "rows": rows,
            "libraries": libraries,
            "clients": clients,
            "projects": projects,
            "template_scope_options": [row.value for row in TemplateScope],
            "file_source_options": [
                row.value for row in FileSource if row != FileSource.uploaded
            ],
            "allowed_upload_extensions": [".pdf", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"],
            "max_upload_bytes": get_settings().delivery_file_max_upload_bytes,
        },
    )


@router.post("/files-ui/link-library", include_in_schema=False)
def files_ui_link_library(
    name: str = Form(...),
    base_url: str = Form(""),
    scope: str = Form("global_scope"),
    client_id: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id") if client_id.strip() else None
        if parsed_client_id and _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            return _redirect_ui("/files-ui", err="Client not found")
        row = TemplateLibrary(
            organization_id=current_actor.organization.id,
            name=name.strip(),
            scope=TemplateScope(scope),
            library_type=LibraryType.document,
            client_id=parsed_client_id,
            base_url=_normalize_http_url(base_url) or None,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        log_created(
            session,
            entity_type=EntityType.template,
            entity_id=row.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={
                "library_type": row.library_type.value,
                "scope": row.scope.value,
                "client_id": str(row.client_id) if row.client_id else None,
                "base_url": row.base_url,
            },
        )
        return _redirect_ui("/files-ui", ok=f"Document library '{row.name}' linked")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/files-ui", err=f"Link library failed: {exc}")


@router.post("/files-ui/link", include_in_schema=False)
def files_ui_link_file(
    name: str = Form(...),
    file_source: str = Form(...),
    external_url: str = Form(...),
    description: str = Form(""),
    library_id: str = Form(""),
    client_id: str = Form(""),
    project_id: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_source = FileSource(file_source)
        if parsed_source == FileSource.uploaded:
            return _redirect_ui("/files-ui", err="Use Upload File for uploaded documents")

        normalized_url = _normalize_http_url(external_url)
        if not normalized_url:
            return _redirect_ui("/files-ui", err="A valid document URL is required")

        parsed_library_id = _parse_optional_uuid(library_id, "library_id")
        parsed_client_id = _parse_optional_uuid(client_id, "client_id")
        parsed_project_id = _parse_optional_uuid(project_id, "project_id")
        if parsed_library_id:
            library = _get_org_template_library(session, parsed_library_id, current_actor.organization.id)
            if library is None or library.library_type != LibraryType.document:
                return _redirect_ui("/files-ui", err="Library not found")
        if parsed_client_id and _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            return _redirect_ui("/files-ui", err="Client not found")
        if parsed_project_id and _get_org_project(session, parsed_project_id, current_actor.organization.id) is None:
            return _redirect_ui("/files-ui", err="Project not found")

        row = DeliveryFile(
            name=name.strip(),
            description=description.strip() or None,
            file_source=parsed_source,
            external_url=normalized_url,
            library_id=parsed_library_id,
            client_id=parsed_client_id,
            project_id=parsed_project_id,
            uploaded_by=current_actor.person.id,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        log_created(
            session,
            entity_type=EntityType.delivery_file,
            entity_id=row.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={
                "source": row.file_source.value,
                "library_id": str(row.library_id) if row.library_id else None,
                "client_id": str(row.client_id) if row.client_id else None,
                "project_id": str(row.project_id) if row.project_id else None,
            },
        )
        return _redirect_ui("/files-ui", ok=f"File link '{row.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/files-ui", err=f"Link document failed: {exc}")


@router.post("/files-ui/upload", include_in_schema=False)
def files_ui_upload_file(
    name: str = Form(...),
    upload: UploadFile = File(...),
    description: str = Form(""),
    library_id: str = Form(""),
    client_id: str = Form(""),
    project_id: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_library_id = _parse_optional_uuid(library_id, "library_id")
        parsed_client_id = _parse_optional_uuid(client_id, "client_id")
        parsed_project_id = _parse_optional_uuid(project_id, "project_id")
        if parsed_library_id:
            library = _get_org_template_library(session, parsed_library_id, current_actor.organization.id)
            if library is None or library.library_type != LibraryType.document:
                return _redirect_ui("/files-ui", err="Library not found")
        if parsed_client_id and _get_org_client(session, parsed_client_id, current_actor.organization.id) is None:
            return _redirect_ui("/files-ui", err="Client not found")
        if parsed_project_id and _get_org_project(session, parsed_project_id, current_actor.organization.id) is None:
            return _redirect_ui("/files-ui", err="Project not found")

        stored_filename, file_size_bytes = _store_uploaded_delivery_file(upload)
        row = DeliveryFile(
            name=name.strip(),
            description=description.strip() or None,
            file_source=FileSource.uploaded,
            library_id=parsed_library_id,
            client_id=parsed_client_id,
            project_id=parsed_project_id,
            stored_filename=stored_filename,
            mime_type=upload.content_type,
            file_size_bytes=file_size_bytes,
            uploaded_by=current_actor.person.id,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        log_created(
            session,
            entity_type=EntityType.delivery_file,
            entity_id=row.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={
                "source": row.file_source.value,
                "stored_filename": row.stored_filename,
                "size_bytes": row.file_size_bytes,
                "library_id": str(row.library_id) if row.library_id else None,
                "client_id": str(row.client_id) if row.client_id else None,
                "project_id": str(row.project_id) if row.project_id else None,
            },
        )
        return _redirect_ui("/files-ui", ok=f"Uploaded '{row.name}'")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/files-ui", err=f"Upload failed: {exc}")


@router.post("/files-ui/delete", include_in_schema=False)
def files_ui_delete_file(
    file_id: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        row = session.get(DeliveryFile, _parse_uuid(file_id, "file_id"))
        if not row:
            return _redirect_ui("/files-ui", err="File not found")

        org_library_ids = {lib.id for lib in _org_template_libraries(session, current_actor.organization.id)}
        org_client_ids = {client.id for client in _org_clients(session, current_actor.organization.id)}
        org_project_ids = {project.id for project in _org_projects(session, current_actor.organization.id)}
        org_person_ids = {person.id for person in _org_people(session, current_actor.organization.id)}
        if not _delivery_file_in_org(
            row,
            org_library_ids=org_library_ids,
            org_client_ids=org_client_ids,
            org_project_ids=org_project_ids,
            org_person_ids=org_person_ids,
        ):
            return _redirect_ui("/files-ui", err="File not found")

        stored_path: Path | None = None
        if row.file_source == FileSource.uploaded and row.stored_filename:
            stored_path = Path(get_settings().uploads_dir) / row.stored_filename

        session.delete(row)
        session.commit()

        if stored_path and stored_path.is_file():
            stored_path.unlink(missing_ok=True)

        log_activity(
            session,
            entity_type=EntityType.delivery_file,
            entity_id=row.id,
            actor_id=current_actor.person.id,
            action="delivery_file.deleted",
            organization_id=current_actor.organization.id,
            metadata={"name": row.name},
        )

        return _redirect_ui("/files-ui", ok="File deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/files-ui", err=f"Delete failed: {exc}")


@router.get("/timeline-ui")
def timeline_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    rows = sorted(
        _org_activity_logs(session, current_actor.organization.id),
        key=lambda row: row.timestamp,
        reverse=True,
    )
    people = sorted(
        _org_people(session, current_actor.organization.id),
        key=lambda row: row.created_at,
        reverse=True,
    )

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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_actor_id = _parse_uuid(actor_id, "actor_id")
        org_people = {row.id for row in _org_people(session, current_actor.organization.id)}
        if parsed_actor_id not in org_people:
            return _redirect_ui("/timeline-ui", err="Actor must belong to the active organization")

        row = ActivityLog(
            organization_id=current_actor.organization.id,
            action=action.strip(),
            entity_type=EntityType(entity_type),
            entity_id=_parse_uuid(entity_id, "entity_id"),
            actor_id=parsed_actor_id,
            metadata_json=_parse_json_object(metadata_json, field_name="metadata_json"),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        log_activity(
            session,
            entity_type=row.entity_type,
            entity_id=row.id,
            actor_id=current_actor.person.id,
            action="timeline_entry.created",
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_log_id = _parse_uuid(log_id, "log_id")
        row = _get_org_activity_log(session, parsed_log_id, current_actor.organization.id)
        if not row:
            return _redirect_ui("/timeline-ui", err="Timeline entry not found")

        parsed_actor_id = _parse_uuid(actor_id, "actor_id")
        org_people = {row.id for row in _org_people(session, current_actor.organization.id)}
        if parsed_actor_id not in org_people:
            return _redirect_ui("/timeline-ui", err="Actor must belong to the active organization")

        row.action = action.strip()
        row.entity_type = EntityType(entity_type)
        row.entity_id = _parse_uuid(entity_id, "entity_id")
        row.actor_id = parsed_actor_id
        row.metadata_json = _parse_json_object(metadata_json, field_name="metadata_json")
        session.add(row)
        session.commit()
        session.refresh(row)
        log_activity(
            session,
            entity_type=row.entity_type,
            entity_id=row.id,
            actor_id=current_actor.person.id,
            action="timeline_entry.updated",
            organization_id=current_actor.organization.id,
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
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_log_id = _parse_uuid(log_id, "log_id")
        row = _get_org_activity_log(session, parsed_log_id, current_actor.organization.id)
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
            actor_id=current_actor.person.id,
            action="timeline_entry.deleted",
            organization_id=current_actor.organization.id,
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


def _kpis_list_context(
    request: Request,
    session: Session,
    current_actor: CurrentActor,
    *,
    ok: str | None = None,
    err: str | None = None,
) -> dict:
    kpis = sorted(_org_kpis(session, current_actor.organization.id), key=lambda row: row.created_at, reverse=True)
    projects = sorted(_org_projects(session, current_actor.organization.id), key=lambda row: row.name.lower())
    clients = sorted(_org_clients(session, current_actor.organization.id), key=lambda row: row.name.lower())
    people = sorted(_org_people(session, current_actor.organization.id), key=lambda row: row.name.lower())
    return {
        "request": request,
        "ok_message": ok or request.query_params.get("ok"),
        "error_message": err or request.query_params.get("err"),
        "kpis": kpis,
        "projects": projects,
        "clients": clients,
        "people": people,
        "kpi_status_options": [row.value for row in KpiStatus],
        "selected_kpi": None,
        "versions": [],
        "author_names": {},
    }


@router.get("/kpis-ui")
def kpis_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    return templates.TemplateResponse(
        "kpis.html",
        _kpis_list_context(request, session, current_actor),
    )


@router.get("/kpis-ui/{kpi_id}")
def kpis_editor(
    request: Request,
    kpi_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
    if not kpi:
        return _redirect_ui("/kpis-ui", err="KPI not found")
    versions = sorted(
        session.exec(select(KpiVersion).where(KpiVersion.kpi_id == kpi_id)).all(),
        key=lambda row: row.version,
        reverse=True,
    )
    people = _org_people(session, current_actor.organization.id)
    author_names = {str(person.id): person.name for person in people}
    context = _kpis_list_context(request, session, current_actor)
    context.update(
        {
            "selected_kpi": kpi,
            "versions": versions,
            "author_names": author_names,
        }
    )
    return templates.TemplateResponse("kpis.html", context)


@router.post("/kpis-ui/create", include_in_schema=False)
def kpis_create(
    name: str = Form(...),
    description: str = Form(""),
    project_id: str = Form(...),
    client_id: str = Form(...),
    pql_formula: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        parsed_client_id = _parse_uuid(client_id, "client_id")
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        if project is None:
            return _redirect_ui("/kpis-ui", err="Project not found")
        if client is None:
            return _redirect_ui("/kpis-ui", err="Client not found")
        if project.client_id != client.id:
            return _redirect_ui("/kpis-ui", err="Project does not belong to selected client")

        kpi = KpiDefinition(
            name=name.strip(),
            description=description.strip() or None,
            project_id=parsed_project_id,
            client_id=parsed_client_id,
            pql_formula=pql_formula.strip() or None,
            owner_id=current_actor.person.id,
        )
        session.add(kpi)
        session.commit()
        session.refresh(kpi)
        log_created(
            session,
            entity_type=EntityType.kpi_definition,
            entity_id=kpi.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"project_id": str(kpi.project_id), "client_id": str(kpi.client_id)},
        )
        return _redirect_ui(f"/kpis-ui/{kpi.id}", ok=f"KPI '{kpi.name}' created")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/kpis-ui", err=f"Create failed: {exc}")


@router.post("/kpis-ui/{kpi_id}/save", include_in_schema=False)
def kpis_save_metadata(
    kpi_id: UUID,
    name: str = Form(...),
    description: str = Form(""),
    data_model: str = Form(""),
    celonis_url: str = Form(""),
    asset_identifier: str = Form(""),
    owner_id: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
        if not kpi:
            return _redirect_ui("/kpis-ui", err="KPI not found")

        parsed_owner_id = _parse_optional_uuid(owner_id, "owner_id")
        if parsed_owner_id:
            org_people_ids = {row.id for row in _org_people(session, current_actor.organization.id)}
            if parsed_owner_id not in org_people_ids:
                return _redirect_ui(f"/kpis-ui/{kpi_id}", err="Owner must belong to the active organization")

        kpi.name = name.strip()
        kpi.description = description.strip() or None
        kpi.data_model = data_model.strip() or None
        kpi.celonis_url = _normalize_http_url(celonis_url) or None
        kpi.asset_identifier = asset_identifier.strip() or None
        kpi.owner_id = parsed_owner_id
        kpi.updated_at = datetime.utcnow()
        session.add(kpi)
        session.commit()
        session.refresh(kpi)
        log_updated(
            session,
            entity_type=EntityType.kpi_definition,
            entity_id=kpi.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"updated_fields": ["name", "description", "data_model", "celonis_url", "asset_identifier", "owner_id"]},
        )
        return _redirect_ui(f"/kpis-ui/{kpi_id}", ok="Metadata saved")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(f"/kpis-ui/{kpi_id}", err=f"Save failed: {exc}")


@router.post("/kpis-ui/{kpi_id}/save-formula", include_in_schema=False)
def kpis_save_formula(
    kpi_id: UUID,
    pql_formula: str = Form(...),
    change_note: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
        if not kpi:
            return _redirect_ui("/kpis-ui", err="KPI not found")
        existing = session.exec(select(KpiVersion).where(KpiVersion.kpi_id == kpi_id)).all()
        next_version = max((row.version for row in existing), default=0) + 1
        version = KpiVersion(
            kpi_id=kpi_id,
            version=next_version,
            pql_formula=pql_formula.strip(),
            change_note=change_note.strip() or None,
            author_id=current_actor.person.id,
        )
        session.add(version)
        kpi.pql_formula = pql_formula.strip()
        kpi.updated_at = datetime.utcnow()
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
        return _redirect_ui(f"/kpis-ui/{kpi_id}", ok=f"Formula saved as version {next_version}")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(f"/kpis-ui/{kpi_id}", err=f"Save formula failed: {exc}")


@router.post("/kpis-ui/{kpi_id}/status", include_in_schema=False)
def kpis_update_status(
    kpi_id: UUID,
    status: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
        if not kpi:
            return _redirect_ui("/kpis-ui", err="KPI not found")
        kpi.status = KpiStatus(status)
        kpi.updated_at = datetime.utcnow()
        session.add(kpi)
        session.commit()
        log_updated(
            session,
            entity_type=EntityType.kpi_definition,
            entity_id=kpi.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={"status": kpi.status.value},
        )
        return _redirect_ui(f"/kpis-ui/{kpi_id}", ok=f"Status updated to {status}")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(f"/kpis-ui/{kpi_id}", err=f"Status update failed: {exc}")


@router.post("/kpis-ui/{kpi_id}/delete", include_in_schema=False)
def kpis_delete(
    kpi_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        kpi = _get_org_kpi(session, kpi_id, current_actor.organization.id)
        if not kpi:
            return _redirect_ui("/kpis-ui", err="KPI not found")
        kpi_name = kpi.name
        for row in session.exec(select(KpiVersion).where(KpiVersion.kpi_id == kpi_id)).all():
            session.delete(row)
        session.delete(kpi)
        session.commit()
        log_activity(
            session,
            entity_type=EntityType.kpi_definition,
            entity_id=kpi_id,
            actor_id=current_actor.person.id,
            action="kpi_definition.deleted",
            organization_id=current_actor.organization.id,
            metadata={"name": kpi_name},
        )
        return _redirect_ui("/kpis-ui", ok=f"KPI '{kpi_name}' deleted")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/kpis-ui", err=f"Delete failed: {exc}")


# ---------------------------------------------------------------------------
# Celonis Snapshot UI
# ---------------------------------------------------------------------------

@router.get("/snapshots-ui/{client_id}")
def snapshots_client_ui(
    client_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    client = _get_org_client(session, client_id, current_actor.organization.id)
    if client is None:
        return _redirect_ui("/clients-ui", err="Client not found")
    snapshots = session.exec(
        select(CelonisSnapshot)
        .where(CelonisSnapshot.client_id == client_id)
        .order_by(CelonisSnapshot.created_at.desc())
    ).all()
    ok_message = request.query_params.get("ok")
    error_message = request.query_params.get("err")
    return templates.TemplateResponse(
        "snapshots.html",
        {
            "request": request,
            "client": client,
            "snapshots": snapshots,
            "ok_message": ok_message,
            "error_message": error_message,
        },
    )


@router.post("/snapshots-ui/{client_id}/trigger")
def trigger_snapshot_ui(
    client_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    from foundry.services.snapshot_service import run_snapshot
    try:
        client = _get_org_client(session, client_id, current_actor.organization.id)
        if client is None:
            return _redirect_ui("/clients-ui", err="Client not found")
        snap = run_snapshot(session, client_id=client_id, triggered_by=current_actor.person.id)
        return _redirect_ui(f"/snapshots-ui/{client_id}", ok=f"Snapshot {snap.id} completed")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(f"/snapshots-ui/{client_id}", err=str(exc))


@router.get("/snapshots-ui/{client_id}/{snapshot_id}/detail")
def snapshot_detail_ui(
    client_id: UUID,
    snapshot_id: UUID,
    tab: str = "tasks",
    request: Request = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    client = _get_org_client(session, client_id, current_actor.organization.id)
    if client is None:
        return _redirect_ui("/clients-ui", err="Client not found")
    snap = session.get(CelonisSnapshot, snapshot_id)
    if snap is None or snap.client_id != client_id:
        return _redirect_ui(f"/snapshots-ui/{client_id}", err="Snapshot not found")
    tasks = session.exec(
        select(SnapshotTask).where(SnapshotTask.snapshot_id == snapshot_id)
    ).all()
    packages = session.exec(
        select(SnapshotPackage).where(SnapshotPackage.snapshot_id == snapshot_id)
    ).all()
    data_models = session.exec(
        select(SnapshotDataModel).where(SnapshotDataModel.snapshot_id == snapshot_id)
    ).all()
    jobs = session.exec(
        select(SnapshotJob).where(SnapshotJob.snapshot_id == snapshot_id)
    ).all()
    knowledge_models = session.exec(
        select(SnapshotKnowledgeModel).where(SnapshotKnowledgeModel.snapshot_id == snapshot_id)
    ).all()
    ok_message = request.query_params.get("ok") if request else None
    error_message = request.query_params.get("err") if request else None
    return templates.TemplateResponse(
        "snapshot_detail.html",
        {
            "request": request,
            "client": client,
            "snap": snap,
            "tasks": tasks,
            "packages": packages,
            "data_models": data_models,
            "jobs": jobs,
            "knowledge_models": knowledge_models,
            "active_tab": tab,
            "ok_message": ok_message,
            "error_message": error_message,
        },
    )


@router.post("/snapshots-ui/{client_id}/{snapshot_id}/export")
def snapshot_export_ui(
    client_id: UUID,
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        client = _get_org_client(session, client_id, current_actor.organization.id)
        snap = session.get(CelonisSnapshot, snapshot_id)
        if client is None or snap is None or snap.client_id != client_id:
            return _redirect_ui(f"/snapshots-ui/{client_id}", err="Snapshot not found")
        result = build_snapshot_export(
            session,
            snapshot_id=snapshot_id,
            base_output_dir=Path(get_settings().uploads_dir) / "snapshot_exports",
        )
        return _redirect_ui(
            f"/snapshots-ui/{client_id}/{snapshot_id}/detail",
            ok=f"Export bundle created: {result['bundle_path']}",
        )
    except Exception as exc:
        return _redirect_ui(
            f"/snapshots-ui/{client_id}/{snapshot_id}/detail",
            err=f"Export failed: {exc}",
        )


@router.get("/snapshots-ui/{client_id}/{snapshot_id}/download")
def snapshot_download_ui(
    client_id: UUID,
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    client = _get_org_client(session, client_id, current_actor.organization.id)
    if client is None:
        return _redirect_ui("/clients-ui", err="Client not found")
    snap = session.get(CelonisSnapshot, snapshot_id)
    if snap is None or snap.client_id != client_id:
        return _redirect_ui(f"/snapshots-ui/{client_id}", err="Snapshot not found")

    try:
        result = build_snapshot_export(
            session,
            snapshot_id=snapshot_id,
            base_output_dir=Path(get_settings().uploads_dir) / "snapshot_exports",
        )
        return FileResponse(
            path=result["bundle_path"],
            filename=f"snapshot_{snapshot_id}.zip",
            media_type="application/zip",
        )
    except Exception as exc:
        return _redirect_ui(
            f"/snapshots-ui/{client_id}/{snapshot_id}/detail",
            err=f"Download failed: {exc}",
        )


@router.get("/snapshots-ui/{client_id}/{snapshot_id}/delta")
def snapshot_delta_ui(
    client_id: UUID,
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    client = _get_org_client(session, client_id, current_actor.organization.id)
    if client is None:
        return _redirect_ui("/clients-ui", err="Client not found")
    snap = session.get(CelonisSnapshot, snapshot_id)
    if snap is None or snap.client_id != client_id:
        return _redirect_ui(f"/snapshots-ui/{client_id}", err="Snapshot not found")
    return build_snapshot_delta_report(session, snapshot_id=snapshot_id)


@router.get("/snapshots-ui/{client_id}/{snapshot_id}/replay-plan")
def snapshot_replay_plan_ui(
    client_id: UUID,
    snapshot_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    client = _get_org_client(session, client_id, current_actor.organization.id)
    if client is None:
        return _redirect_ui("/clients-ui", err="Client not found")
    snap = session.get(CelonisSnapshot, snapshot_id)
    if snap is None or snap.client_id != client_id:
        return _redirect_ui(f"/snapshots-ui/{client_id}", err="Snapshot not found")
    return build_snapshot_replay_plan(session, snapshot_id=snapshot_id)


# ---------------------------------------------------------------------------
# KPI Book UI
# ---------------------------------------------------------------------------

@router.get("/kpi-book-ui/{client_id}")
def kpi_book_ui(
    client_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    current_person=Depends(get_current_person_optional),
):
    client = session.get(Client, client_id)
    if client is None:
        return _redirect_ui("/clients-ui", err="Client not found")
    entries = session.exec(
        select(KpiBookEntry)
        .where(KpiBookEntry.client_id == client_id)
        .order_by(KpiBookEntry.created_at.desc())
    ).all()
    ok_message = request.query_params.get("ok")
    error_message = request.query_params.get("err")
    return templates.TemplateResponse(
        "kpi_book.html",
        {
            "request": request,
            "client": client,
            "entries": entries,
            "ok_message": ok_message,
            "error_message": error_message,
        },
    )


@router.post("/kpi-book-ui/{client_id}/create")
def kpi_book_create_ui(
    client_id: UUID,
    name: str = Form(...),
    description: str = Form(""),
    pql_formula: str = Form(""),
    package_name: str = Form(""),
    task_type: str = Form(""),
    is_shared: str = Form("off"),
    session: Session = Depends(get_session),
    current_person=Depends(get_current_person),
):
    try:
        entry = KpiBookEntry(
            client_id=client_id,
            saved_by=current_person.id,
            name=name,
            description=description or None,
            pql_formula=pql_formula or None,
            package_name=package_name or None,
            task_type=task_type or None,
            is_shared=(is_shared == "on"),
            tags_json=[],
        )
        session.add(entry)
        session.commit()
        return _redirect_ui(f"/kpi-book-ui/{client_id}", ok="Entry added to KPI Book")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(f"/kpi-book-ui/{client_id}", err=str(exc))


@router.post("/kpi-book-ui/{client_id}/save-from-snapshot/{task_id}")
def kpi_book_save_from_snapshot(
    client_id: UUID,
    task_id: UUID,
    session: Session = Depends(get_session),
    current_person=Depends(get_current_person),
):
    task = session.get(SnapshotTask, task_id)
    if task is None or task.client_id != client_id:
        return _redirect_ui(f"/kpi-book-ui/{client_id}", err="Task not found")
    try:
        entry = KpiBookEntry(
            client_id=client_id,
            snapshot_id=task.snapshot_id,
            snapshot_task_id=task.id,
            saved_by=current_person.id,
            name=task.name,
            description=task.description,
            pql_formula=task.pql_formula,
            package_name=None,
            task_type=task.task_type,
            is_shared=False,
            tags_json=[],
        )
        session.add(entry)
        session.commit()
        return _redirect_ui(
            f"/snapshots-ui/{client_id}/{task.snapshot_id}/detail?tab=tasks",
            ok=f"'{task.name}' saved to KPI Book",
        )
    except Exception as exc:
        session.rollback()
        return _redirect_ui(f"/kpi-book-ui/{client_id}", err=str(exc))


@router.post("/kpi-book-ui/{client_id}/{entry_id}/delete")
def kpi_book_delete_ui(
    client_id: UUID,
    entry_id: UUID,
    session: Session = Depends(get_session),
    current_person=Depends(get_current_person),
):
    entry = session.get(KpiBookEntry, entry_id)
    if entry is None or entry.client_id != client_id:
        return _redirect_ui(f"/kpi-book-ui/{client_id}", err="Entry not found")
    try:
        name = entry.name
        session.delete(entry)
        session.commit()
        return _redirect_ui(f"/kpi-book-ui/{client_id}", ok=f"'{name}' removed from KPI Book")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(f"/kpi-book-ui/{client_id}", err=str(exc))