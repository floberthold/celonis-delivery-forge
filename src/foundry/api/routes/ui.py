import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlsplit, urlunsplit
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
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
from foundry import db as db_module
from foundry.db import get_session
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
    CelonisUserToken,
    CelonisSnapshot,
    CelonisDeploymentRequest,
    CelonisDeploymentStatus,
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
    Organization,
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
    SnapshotPackageDefinition,
    SnapshotSpace,
    SnapshotTask,
    SnapshotTaskDetail,
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
    TryCelonisDemo,
)
from foundry.schemas import (
    ReviewDecisionCreate,
    ReviewRequestCreate,
    TemplateInstantiateCreate,
)
from foundry.settings import get_settings
from foundry.security import (
    create_access_token,
    create_action_token,
    decode_action_token,
    hash_password,
    verify_password,
)
from foundry.services.project_service import ProjectService
from foundry.services.review_service import ReviewService
from foundry.services.activity_log import log_activity, log_created, log_updated
from foundry.services.celonis_data_agent_service import list_data_agent_tools
from foundry.services.celonis_deployment_service import (
    CelonisDeploymentServiceError,
    acknowledge_deployment_diff,
    cancel_deployment_request,
    create_deployment_request,
    decide_deployment_request,
    list_deployment_requests,
    submit_deployment_for_approval,
)
from foundry.services.email_service import send_email
from foundry.services.template_seed import seed_default_templates
from foundry.services.template_service import TemplateService
from foundry.services.trycelonis_demo_rebuild import sync_trycelonis_demos
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
from foundry.services.snapshot_coverage_service import (
    build_snapshot_coverage_filename,
    build_snapshot_coverage_report,
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
    # Use the active runtime engine so auth context stays aligned after DB fallback.
    with Session(db_module.engine) as session:
        person = get_current_person_optional(request=request, token=None, session=session)
    return {"current_person": person}


def _enum_or_value(value: object, default: str = "") -> str:
    if value is None:
        return default
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        return enum_value
    return str(value)


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


def _wants_json_response(request: Request | None) -> bool:
    if request is None:
        return False
    response_mode = request.query_params.get("response_mode") or request.query_params.get("format")
    if isinstance(response_mode, str) and response_mode.strip().lower() == "json":
        return True
    if request.headers.get("x-forge-response-mode", "").strip().lower() == "json":
        return True
    accept = request.headers.get("accept", "").lower()
    return "application/json" in accept


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


def _sort_datetime_key(value: datetime | None) -> float:
    if value is None:
        return float("-inf")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.timestamp()


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


def _snapshot_component_rows(payload: object, *, limit: int = 80) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    stack: list[tuple[str, object]] = [("$", payload)]
    while stack and len(rows) < limit:
        path, node = stack.pop()
        if isinstance(node, dict):
            rows.append({"path": path, "kind": "object", "preview": f"{len(node)} fields"})
            for key, value in reversed(list(node.items())[:12]):
                stack.append((f"{path}.{key}", value))
            continue
        if isinstance(node, list):
            rows.append({"path": path, "kind": "array", "preview": f"{len(node)} items"})
            for index in range(min(len(node), 8) - 1, -1, -1):
                stack.append((f"{path}[{index}]", node[index]))
            continue
        preview = "null" if node is None else str(node)
        if len(preview) > 120:
            preview = f"{preview[:117]}..."
        rows.append({"path": path, "kind": "value", "preview": preview})
    return rows


def _snapshot_reference_ids(payload: object, *, max_refs: int = 120) -> list[str]:
    refs: set[str] = set()
    stack: list[object] = [payload]

    def _add_ref(value: object) -> None:
        if isinstance(value, (str, int, float)):
            candidate = str(value).strip()
            if 0 < len(candidate) <= 120:
                refs.add(candidate)

    while stack and len(refs) < max_refs:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    stack.append(value)
                key_lower = key.lower()
                if key_lower == "id" or key_lower.endswith("id") or key_lower.endswith("_id") or key_lower.endswith("key"):
                    if isinstance(value, list):
                        for item in value:
                            _add_ref(item)
                    else:
                        _add_ref(value)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, (dict, list)):
                    stack.append(item)
    return sorted(refs)


def _snapshot_entity_maps(
    *,
    packages: Sequence[SnapshotPackage],
    tasks: Sequence[SnapshotTask],
    data_models: Sequence[SnapshotDataModel],
    jobs: Sequence[SnapshotJob],
    knowledge_models: Sequence[SnapshotKnowledgeModel],
) -> dict[str, dict[str, dict[str, object]]]:
    return {
        "packages": {
            row.package_id: {
                "id": row.package_id,
                "name": row.name,
                "raw_json": row.raw_json or {},
                "change_type": _enum_or_value(row.change_type, "unchanged"),
                "family": "package",
            }
            for row in packages
        },
        "tasks": {
            row.task_id: {
                "id": row.task_id,
                "name": row.name,
                "raw_json": row.raw_json or {},
                "change_type": _enum_or_value(row.change_type, "unchanged"),
                "family": "task",
                "task_type": row.task_type or "unknown",
            }
            for row in tasks
        },
        "data_models": {
            row.data_model_id: {
                "id": row.data_model_id,
                "name": row.name,
                "raw_json": row.raw_json or {},
                "change_type": _enum_or_value(row.change_type, "unchanged"),
                "family": "data_model",
            }
            for row in data_models
        },
        "jobs": {
            row.job_id: {
                "id": row.job_id,
                "name": row.name,
                "raw_json": row.raw_json or {},
                "change_type": _enum_or_value(row.change_type, "unchanged"),
                "family": "job",
            }
            for row in jobs
        },
        "knowledge_models": {
            row.km_id: {
                "id": row.km_id,
                "name": row.name,
                "raw_json": row.raw_json or {},
                "change_type": _enum_or_value(row.change_type, "unchanged"),
                "family": "knowledge_model",
            }
            for row in knowledge_models
        },
    }


def _snapshot_family_diff(
    current_rows: dict[str, dict[str, object]],
    baseline_rows: dict[str, dict[str, object]],
) -> dict[str, object]:
    entries: list[dict[str, str]] = []
    counts = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}
    all_ids = sorted(set(current_rows.keys()) | set(baseline_rows.keys()))

    for asset_id in all_ids:
        current = current_rows.get(asset_id)
        baseline = baseline_rows.get(asset_id)
        if current is None:
            status = "removed"
            name = str((baseline or {}).get("name") or asset_id)
        elif baseline is None:
            status = "added"
            name = str(current.get("name") or asset_id)
        else:
            current_raw = json.dumps(current.get("raw_json", {}), sort_keys=True, default=str)
            baseline_raw = json.dumps(baseline.get("raw_json", {}), sort_keys=True, default=str)
            status = "modified" if current_raw != baseline_raw else "unchanged"
            name = str(current.get("name") or baseline.get("name") or asset_id)
        counts[status] += 1
        entries.append({"id": asset_id, "name": name, "status": status})

    return {"counts": counts, "entries": entries}


def _snapshot_dependency_index(
    *,
    packages: Sequence[SnapshotPackage],
    tasks: Sequence[SnapshotTask],
    data_models: Sequence[SnapshotDataModel],
    jobs: Sequence[SnapshotJob],
    knowledge_models: Sequence[SnapshotKnowledgeModel],
) -> dict[str, dict[str, object]]:
    index: dict[str, dict[str, object]] = {}

    def _upsert(entity_id: str, family: str, name: str, raw_json: dict) -> None:
        if not entity_id:
            return
        if entity_id in index:
            return
        index[entity_id] = {
            "id": entity_id,
            "family": family,
            "name": name,
            "raw_json": raw_json or {},
        }

    for row in packages:
        _upsert(row.package_id, "package", row.name, row.raw_json or {})
    for row in tasks:
        _upsert(row.task_id, "task", row.name, row.raw_json or {})
    for row in data_models:
        _upsert(row.data_model_id, "data_model", row.name, row.raw_json or {})
    for row in jobs:
        _upsert(row.job_id, "job", row.name, row.raw_json or {})
    for row in knowledge_models:
        _upsert(row.km_id, "knowledge_model", row.name, row.raw_json or {})
    return index


def _snapshot_hierarchy_spaces(
    *,
    spaces: Sequence[SnapshotSpace],
    packages: Sequence[SnapshotPackage],
    package_tasks: dict[str, list[SnapshotTask]],
    dependency_index: dict[str, dict[str, object]],
) -> tuple[list[dict[str, object]], list[str]]:
    hierarchy_spaces: dict[str, dict[str, Any]] = {}

    for row in spaces:
        hierarchy_spaces[row.space_id] = {
            "space_id": row.space_id,
            "space_name": row.name,
            "packages": [],
            "package_count": 0,
            "asset_count": 0,
        }

    asset_types: set[str] = set()

    def _ensure_space(space_id: str | None, space_name: str | None) -> dict[str, Any]:
        normalized_id = (space_id or "").strip() or "__unassigned__"
        if normalized_id not in hierarchy_spaces:
            hierarchy_spaces[normalized_id] = {
                "space_id": normalized_id,
                "space_name": (space_name or "").strip() or "Unassigned Space",
                "packages": [],
                "package_count": 0,
                "asset_count": 0,
            }
        return hierarchy_spaces[normalized_id]

    for pkg in sorted(packages, key=lambda row: (row.name or "").lower()):
        container = _ensure_space(pkg.space_id, pkg.space_name)
        container_packages: list[dict[str, Any]] = container["packages"]
        asset_rows: list[dict[str, object]] = []
        pkg_tasks = sorted(package_tasks.get(pkg.package_id, []), key=lambda row: (row.name or "").lower())
        for task in pkg_tasks:
            asset_type = (task.task_type or "unknown").strip() or "unknown"
            asset_types.add(asset_type)
            refs = _snapshot_reference_ids(task.raw_json or {}, max_refs=24)
            linked_dependencies = [
                dependency_index[ref]
                for ref in refs
                if ref in dependency_index and ref not in {pkg.package_id, task.task_id}
            ][:10]
            asset_rows.append(
                {
                    "task": task,
                    "asset_type": asset_type,
                    "refs": refs,
                    "linked_dependencies": linked_dependencies,
                    "component_rows": _snapshot_component_rows(task.raw_json or {}, limit=16),
                }
            )

        container_packages.append(
            {
                "package": pkg,
                "assets": asset_rows,
                "asset_count": len(asset_rows),
                "component_rows": _snapshot_component_rows(pkg.raw_json or {}, limit=12),
            }
        )
        container["package_count"] = container["package_count"] + 1
        container["asset_count"] = container["asset_count"] + len(asset_rows)

    hierarchy_rows = sorted(
        hierarchy_spaces.values(),
        key=lambda row: str(row.get("space_name") or "").lower(),
    )
    return hierarchy_rows, sorted(asset_types, key=lambda row: row.lower())


def _crawl_snapshot_dependencies(
    *,
    seed_refs: list[str],
    index: dict[str, dict[str, object]],
    skip_ids: set[str] | None = None,
    max_nodes: int = 60,
) -> list[dict[str, object]]:
    queue = [row for row in seed_refs if row]
    visited: set[str] = set(skip_ids or set())
    dependencies: list[dict[str, object]] = []

    while queue and len(dependencies) < max_nodes:
        ref = queue.pop(0)
        if ref in visited:
            continue
        visited.add(ref)
        entity = index.get(ref)
        if entity is None:
            continue
        dependencies.append(entity)
        nested_refs = _snapshot_reference_ids(entity.get("raw_json", {}), max_refs=40)
        for nested in nested_refs:
            if nested not in visited:
                queue.append(nested)
    return dependencies


def _asset_type_for_task(task_type: str | None) -> AssetType:
    token = (task_type or "").strip().lower()
    if "kpi" in token:
        return AssetType.kpi
    if "action" in token:
        return AssetType.action_flow
    if "job" in token or "extract" in token:
        return AssetType.extractor
    if "ml" in token:
        return AssetType.ml_job
    if "view" in token or "analysis" in token:
        return AssetType.view
    return AssetType.other


def _asset_type_for_family(family: str, *, task_type: str | None = None) -> AssetType:
    if family == "task":
        return _asset_type_for_task(task_type)
    if family == "data_model":
        return AssetType.data_model
    if family == "job":
        return AssetType.extractor
    if family == "package":
        return AssetType.view
    return AssetType.other


def _snapshot_path_lookup(payload: object, path: str) -> object | None:
    if not path.startswith("$"):
        return None
    cursor = payload
    token_pattern = re.compile(r"\.?([A-Za-z0-9_]+)|\[(\d+)\]")
    for match in token_pattern.finditer(path[1:]):
        key, index = match.groups()
        if key is not None:
            if not isinstance(cursor, dict):
                return None
            cursor = cursor.get(key)
            continue
        if index is not None:
            if not isinstance(cursor, list):
                return None
            idx = int(index)
            if idx < 0 or idx >= len(cursor):
                return None
            cursor = cursor[idx]
    return cursor


def _store_uploaded_delivery_file(upload_file: UploadFile) -> tuple[str, int]:
    settings = get_settings()
    input_dir = Path(settings.input_dir).resolve() / "delivery_files"
    input_dir.mkdir(parents=True, exist_ok=True)

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
    destination = input_dir / stored_filename

    upload_file.file.seek(0)
    with destination.open("wb") as handle:
        shutil.copyfileobj(upload_file.file, handle)

    return stored_filename, destination.stat().st_size


def _redirect_login(
    *,
    err: str | None = None,
    ok: str | None = None,
    next_path: str | None = None,
) -> RedirectResponse:
    next_query = ""
    normalized_next_path = _normalize_redirect_path(next_path, "/dashboard") if next_path else None
    if normalized_next_path:
        next_query = f"next_path={quote_plus(normalized_next_path)}"

    if err:
        separator = "&" if next_query else ""
        return RedirectResponse(
            url=f"/login?{next_query}{separator}err={quote_plus(err)}" if next_query else f"/login?err={quote_plus(err)}",
            status_code=303,
        )
    if ok:
        separator = "&" if next_query else ""
        return RedirectResponse(
            url=f"/login?{next_query}{separator}ok={quote_plus(ok)}" if next_query else f"/login?ok={quote_plus(ok)}",
            status_code=303,
        )
    return RedirectResponse(url=f"/login?{next_query}" if next_query else "/login", status_code=303)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "workspace"


def _build_unique_org_slug(session: Session, base_name: str) -> str:
    base_slug = _slugify(base_name)
    candidate = base_slug
    counter = 2
    while session.exec(select(Organization).where(Organization.slug == candidate)).first():
        candidate = f"{base_slug}-{counter}"
        counter += 1
    return candidate


def _validate_registration_password(password: str, confirm_password: str) -> None:
    if password != confirm_password:
        raise ValueError("Passwords do not match")
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters")


def _app_public_base_url(request: Request) -> str:
    configured = get_settings().public_base_url.strip()
    if configured:
        return configured.rstrip("/")
    return str(request.base_url).rstrip("/")


def _send_registration_email(*, request: Request, email: str, token: str) -> None:
    verify_url = f"{_app_public_base_url(request)}/register/verify?token={quote_plus(token)}"
    send_email(
        to_email=email,
        subject="Confirm your Celonis Delivery Forge account",
        body_text=(
            "Welcome to Celonis Delivery Forge.\n\n"
            "Use this link to activate your account:\n"
            f"{verify_url}\n\n"
            "The link expires automatically. If you did not request this, ignore this email."
        ),
    )


def _send_password_reset_email(*, request: Request, email: str, token: str) -> None:
    reset_url = f"{_app_public_base_url(request)}/reset-password?token={quote_plus(token)}"
    send_email(
        to_email=email,
        subject="Reset your Celonis Delivery Forge password",
        body_text=(
            "A password reset was requested for your account.\n\n"
            "Use this link to set a new password:\n"
            f"{reset_url}\n\n"
            "The link expires automatically. If you did not request this, ignore this email."
        ),
    )


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


def _org_trycelonis_demos(session: Session, organization_id: UUID) -> list[TryCelonisDemo]:
    return list(
        session.exec(select(TryCelonisDemo).where(TryCelonisDemo.organization_id == organization_id)).all()
    )


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


def _get_org_active_celonis_connection(
    session: Session,
    client_id: UUID,
    organization_id: UUID,
) -> CelonisConnection | None:
    return session.exec(
        select(CelonisConnection).where(
            CelonisConnection.client_id == client_id,
            CelonisConnection.organization_id == organization_id,
            CelonisConnection.is_active == True,  # noqa: E712
        )
    ).first()


def _get_org_person_celonis_token(
    session: Session,
    organization_id: UUID,
    person_id: UUID,
) -> CelonisUserToken | None:
    return session.exec(
        select(CelonisUserToken).where(
            CelonisUserToken.organization_id == organization_id,
            CelonisUserToken.person_id == person_id,
        )
    ).first()


def _upsert_org_person_celonis_token(
    session: Session,
    organization_id: UUID,
    person_id: UUID,
    token_value: str,
) -> CelonisUserToken:
    row = _get_org_person_celonis_token(session, organization_id, person_id)
    now = datetime.utcnow()
    if row is None:
        row = CelonisUserToken(
            organization_id=organization_id,
            person_id=person_id,
            token_value=token_value,
            created_at=now,
            updated_at=now,
        )
    else:
        row.token_value = token_value
        row.updated_at = now
    session.add(row)
    return row


def _mask_token_value(token_value: str) -> str:
    cleaned = (token_value or "").strip()
    if not cleaned:
        return "not set"
    if len(cleaned) <= 8:
        return "*" * len(cleaned)
    return f"{cleaned[:4]}...{cleaned[-4:]}"


def _latest_celonis_system_access_by_person(
    session: Session,
    organization_id: UUID,
) -> dict[UUID, dict]:
    logs = sorted(
        [
            row
            for row in _org_activity_logs(session, organization_id)
            if row.action == "celonis_connection.preflight"
        ],
        key=lambda r: _sort_datetime_key(r.timestamp),
        reverse=True,
    )
    access_by_person: dict[UUID, dict] = {}
    for row in logs:
        person_id = row.actor_id
        if person_id is None:
            continue
        metadata = row.metadata_json or {}
        service = str(metadata.get("service") or "").strip()
        if not service:
            continue
        permission_status = str(metadata.get("permission_status") or "unknown").strip().lower()
        if not permission_status:
            permission_status = "unknown"

        person_access = access_by_person.setdefault(
            person_id,
            {
                "service_status": {},
                "last_preflight_at": None,
            },
        )
        service_status = person_access["service_status"]
        if service in service_status:
            continue
        service_status[service] = permission_status
        if person_access["last_preflight_at"] is None:
            person_access["last_preflight_at"] = row.timestamp

    return access_by_person


def _active_project_token_scopes_by_person(
    session: Session,
    organization_id: UUID,
) -> dict[UUID, list[dict[str, object]]]:
    project_name_by_id = {
        row.id: row.name for row in _org_projects(session, organization_id)
    }
    logs = sorted(
        [
            row
            for row in _org_activity_logs(session, organization_id)
            if row.action == "project.celonis_token.updated" and row.entity_type == EntityType.project
        ],
        key=lambda r: _sort_datetime_key(r.timestamp),
        reverse=True,
    )
    active_by_person: dict[UUID, list[dict[str, object]]] = {}
    seen_keys: set[tuple[UUID, UUID]] = set()
    for row in logs:
        if row.actor_id is None:
            continue
        project_id = row.entity_id
        person_id = row.actor_id
        lookup_key = (person_id, project_id)
        if lookup_key in seen_keys:
            continue
        seen_keys.add(lookup_key)

        metadata = row.metadata_json or {}
        if not metadata.get("token_present"):
            continue

        active_by_person.setdefault(person_id, []).append(
            {
                "project_id": project_id,
                "project_name": project_name_by_id.get(project_id, "Unknown project"),
                "updated_at": row.timestamp,
            }
        )

    return active_by_person


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
    rows.sort(key=lambda row: _sort_datetime_key(row.timestamp), reverse=True)

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
    """Simplified dashboard context with only essential metrics and organization data."""
    # Count entities (only fetch counts, not full lists)
    clients_count = len(_org_clients(session, current_actor.organization.id))
    projects_count = len(_org_projects(session, current_actor.organization.id))
    assets_count = len(_org_assets(session, current_actor.organization.id))
    trycelonis_demo_count = len(_org_trycelonis_demos(session, current_actor.organization.id))
    reviews_count = len(_org_reviews(session, current_actor.organization.id))
    timeline_count = len(_org_activity_logs(session, current_actor.organization.id))
    
    # Count team members in organization
    memberships = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == current_actor.organization.id
        )
    ).all()
    team_member_count = len(memberships)

    logs = sorted(
        _org_activity_logs(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.timestamp),
        reverse=True,
    )
    target_run_id: str | None = None
    celonis_preflight_rows: list[dict[str, str | int | None]] = []
    for row in logs:
        if row.action != "celonis_connection.preflight":
            continue
        metadata = row.metadata_json or {}
        run_id = str(metadata.get("run_id", "")).strip() or None
        if target_run_id is None:
            target_run_id = run_id
        if target_run_id and run_id != target_run_id:
            continue
        permission_status = str(metadata.get("permission_status", "unknown")).strip().lower() or "unknown"
        celonis_preflight_rows.append(
            {
                "service": str(metadata.get("service", "core")),
                "permission_status": permission_status,
                "status_code": metadata.get("status_code") if isinstance(metadata.get("status_code"), int) else None,
                "run_id": run_id,
            }
        )
    celonis_preflight_rows.sort(key=lambda item: str(item["service"]).lower())

    return {
        "request": request,
        "active_organization": current_actor.organization,
        "ok_message": request.query_params.get("ok"),
        "error_message": request.query_params.get("err"),
        "clients_count": clients_count,
        "projects_count": projects_count,
        "assets_count": assets_count,
        "trycelonis_demo_count": trycelonis_demo_count,
        "reviews_count": reviews_count,
        "timeline_count": timeline_count,
        "team_member_count": team_member_count,
        "celonis_preflight_rows": celonis_preflight_rows,
        "latest_preflight_run_id": target_run_id,
    }


def _orchestration_context(request: Request, session: Session, current_actor: CurrentActor) -> dict:
    clients = _org_clients(session, current_actor.organization.id)
    projects = _org_projects(session, current_actor.organization.id)
    quests = _org_quests(session, current_actor.organization.id)
    people = _org_people(session, current_actor.organization.id)
    agents = _org_agents(session, current_actor.organization.id)
    todos = _org_todos(session, current_actor.organization.id)

    projects_by_id = {row.id: row for row in projects}
    people_by_id = {row.id: row for row in people}
    map_mode = (request.query_params.get("map_mode") or "").strip().lower() in {"1", "true", "yes"}

    open_statuses = {QuestStatus.draft, QuestStatus.suggested, QuestStatus.accepted, QuestStatus.active, QuestStatus.blocked}
    open_quests = [row for row in quests if row.status in open_statuses]
    active_quests = [row for row in quests if row.status == QuestStatus.active]
    blocked_quests = [row for row in quests if row.status == QuestStatus.blocked]

    project_todos: dict[UUID, list[Todo]] = {}
    for row in todos:
        if row.project_id is None:
            continue
        project_todos.setdefault(row.project_id, []).append(row)

    in_progress_todo_by_person: dict[UUID, Todo] = {}
    next_todo_by_person: dict[UUID, Todo] = {}
    for row in sorted(todos, key=lambda item: _sort_datetime_key(item.updated_at), reverse=True):
        if row.assignee_id is None:
            continue
        if row.status == TodoStatus.in_progress and row.assignee_id not in in_progress_todo_by_person:
            in_progress_todo_by_person[row.assignee_id] = row
            continue
        if row.status != TodoStatus.done and row.assignee_id not in next_todo_by_person:
            next_todo_by_person[row.assignee_id] = row

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
                "project_id": str(row.project_id),
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
    assignment_states_by_person: dict[UUID, set[str]] = {}
    for row in open_quests:
        objectives_by_quest_id[row.id] = list_objectives_service(session, quest_id=row.id)
        assignment_rows = list_assignments_service(session, quest_id=row.id)
        assignments_by_quest_id[row.id] = assignment_rows
        for assignment in assignment_rows:
            if assignment.assignee_person_id is None:
                continue
            assignment_states_by_person.setdefault(assignment.assignee_person_id, set()).add((assignment.state or "assigned").strip().lower())

    quest_rows: list[dict[str, object]] = []
    for row in sorted(open_quests, key=lambda item: _sort_datetime_key(item.created_at), reverse=True)[:10]:
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
    agent_status_by_name = {row.name.casefold(): row.status.value for row in agents}
    preferred_project_by_person: dict[UUID, UUID] = {}
    for row in sorted(open_quests, key=lambda item: _sort_datetime_key(item.created_at), reverse=True):
        if row.owner_person_id is None or row.project_id is None:
            continue
        preferred_project_by_person.setdefault(row.owner_person_id, row.project_id)

    for row in sorted(people, key=lambda item: item.name.lower())[:8]:
        if row.role_global == GlobalRole.admin:
            unit_type = "guardian"
        else:
            unit_type = ["builder", "scout", "courier"][len(units) % 3]

        preferred_project_id = preferred_project_by_person.get(row.id)
        linked_agent_status = agent_status_by_name.get(row.name.casefold(), "active")
        active_todo = in_progress_todo_by_person.get(row.id)
        next_todo = next_todo_by_person.get(row.id)
        assignment_states = assignment_states_by_person.get(row.id, set())

        if linked_agent_status == "offline":
            activity_state = "killed"
            bubble_text = "offline"
        elif active_todo:
            activity_state = "working"
            bubble_text = f"{active_todo.title} ({active_todo.status.value})"
            preferred_project_id = active_todo.project_id or preferred_project_id
        elif "blocked" in assignment_states:
            activity_state = "thinking"
            bubble_text = "blocked, re-planning"
        elif next_todo:
            activity_state = "chatting"
            bubble_text = f"next: {next_todo.title}"
            preferred_project_id = next_todo.project_id or preferred_project_id
        elif linked_agent_status in {"idle", "paused"}:
            activity_state = "sleeping"
            bubble_text = "resting"
        else:
            activity_state = "idle"
            bubble_text = "patrolling"

        units.append(
            {
                "id": str(row.id),
                "name": row.name,
                "unit_type": unit_type,
                "role": _enum_or_value(row.role_global, "member"),
                "preferred_project_id": str(preferred_project_id) if preferred_project_id else None,
                "activity_state": activity_state,
                "activity_text": bubble_text,
            }
        )

    project_open_counts: dict[UUID, int] = {}
    project_high_counts: dict[UUID, int] = {}
    for row in open_quests:
        if row.project_id is None:
            continue
        project_open_counts[row.project_id] = project_open_counts.get(row.project_id, 0) + 1
        if row.priority in {QuestPriority.high, QuestPriority.critical}:
            project_high_counts[row.project_id] = project_high_counts.get(row.project_id, 0) + 1

    map_width = 960
    map_height = 560
    area_width = 190
    area_height = 150
    area_gap_x = 28
    area_gap_y = 24
    grid_cols = 4
    offset_x = 42
    offset_y = 52

    map_areas: list[dict[str, object]] = []
    area_by_project_id: dict[str, dict[str, object]] = {}
    for idx, project in enumerate(sorted(projects, key=lambda row: row.name.lower())[:8]):
        grid_x = idx % grid_cols
        grid_y = idx // grid_cols
        project_todo_rows = project_todos.get(project.id, [])
        open_todo_count = sum(1 for row in project_todo_rows if row.status != TodoStatus.done)
        in_progress_todo_count = sum(1 for row in project_todo_rows if row.status == TodoStatus.in_progress)
        done_todo_count = sum(1 for row in project_todo_rows if row.status == TodoStatus.done)
        board_url = _with_query_params(
            "/orchestration-ui",
            board_project_id=str(project.id),
            map_mode="1" if map_mode else None,
        )
        area = {
            "id": f"area-{project.id}",
            "kind": "project",
            "project_id": str(project.id),
            "project_name": project.name,
            "x": offset_x + (grid_x * (area_width + area_gap_x)),
            "y": offset_y + (grid_y * (area_height + area_gap_y)),
            "width": area_width,
            "height": area_height,
            "open_count": project_open_counts.get(project.id, 0),
            "high_count": project_high_counts.get(project.id, 0),
            "todo_open_count": open_todo_count,
            "todo_in_progress_count": in_progress_todo_count,
            "todo_done_count": done_todo_count,
            "board_url": board_url,
            "board_deep_link_url": f"/orchestration-ui/board/{project.id}",
            "desk_zone": {
                "x": offset_x + (grid_x * (area_width + area_gap_x)) + 18,
                "y": offset_y + (grid_y * (area_height + area_gap_y)) + 84,
                "width": area_width - 36,
                "height": 54,
            },
        }
        map_areas.append(area)
        area_by_project_id[str(project.id)] = area

    sleep_zone = {
        "id": "zone-sleep",
        "kind": "sleep_zone",
        "project_id": "",
        "project_name": "Rest House",
        "x": 20,
        "y": map_height - 140,
        "width": 190,
        "height": 96,
        "open_count": 0,
        "high_count": 0,
        "todo_open_count": 0,
        "todo_in_progress_count": 0,
        "todo_done_count": 0,
        "board_url": None,
        "board_deep_link_url": None,
    }
    graveyard_zone = {
        "id": "zone-graveyard",
        "kind": "graveyard",
        "project_id": "",
        "project_name": "Agent Graveyard",
        "x": map_width - 220,
        "y": map_height - 126,
        "width": 190,
        "height": 90,
        "open_count": 0,
        "high_count": 0,
        "todo_open_count": 0,
        "todo_in_progress_count": 0,
        "todo_done_count": 0,
        "board_url": None,
        "board_deep_link_url": None,
    }
    map_areas.append(sleep_zone)
    map_areas.append(graveyard_zone)
    area_by_id = {str(row["id"]): row for row in map_areas}

    map_units: list[dict[str, object]] = []
    for idx, row in enumerate(units):
        target_project_id = row.get("preferred_project_id")
        activity_state = str(row.get("activity_state") or "idle")

        if activity_state == "killed":
            target_area = area_by_id.get("zone-graveyard")
            target_area_id = "zone-graveyard"
        elif activity_state == "sleeping":
            target_area = area_by_id.get("zone-sleep")
            target_area_id = "zone-sleep"
        else:
            target_area = area_by_project_id.get(str(target_project_id)) if target_project_id else None
            target_area_id = str(target_area["id"]) if target_area else None

        if target_area:
            base_x = int(target_area["x"]) + 28 + ((idx % 4) * 26)
            base_y = int(target_area["y"]) + 34 + ((idx % 3) * 24)
        else:
            base_x = 80 + ((idx % 9) * 92)
            base_y = 430 + ((idx % 2) * 58)

        map_units.append(
            {
                "id": str(row["id"]),
                "name": str(row["name"]),
                "unit_type": str(row["unit_type"]),
                "role": str(row["role"]),
                "sprite_key": str(row["unit_type"]),
                "x": base_x,
                "y": base_y,
                "speed": 30 + (idx % 3) * 7,
                "target_area_id": target_area_id,
                "target_project_id": str(target_project_id) if target_project_id else None,
                "activity_state": activity_state,
                "activity_text": str(row.get("activity_text") or ""),
            }
        )

    selected_board_project_id: UUID | None = None
    selected_board_project_raw = (request.query_params.get("board_project_id") or "").strip()
    if selected_board_project_raw:
        try:
            parsed_board_project = UUID(selected_board_project_raw)
            if parsed_board_project in projects_by_id:
                selected_board_project_id = parsed_board_project
        except ValueError:
            selected_board_project_id = None
    if selected_board_project_id is None and area_by_project_id:
        first_project_id = next(iter(area_by_project_id.keys()), "")
        if first_project_id:
            selected_board_project_id = UUID(first_project_id)

    selected_board_project = projects_by_id.get(selected_board_project_id) if selected_board_project_id else None
    selected_board_todos = sorted(
        project_todos.get(selected_board_project_id, []),
        key=lambda row: (
            0 if row.status == TodoStatus.in_progress else (1 if row.status == TodoStatus.open else 2),
            0 if row.priority == TodoPriority.high else (1 if row.priority == TodoPriority.medium else 2),
            _sort_datetime_key(row.updated_at),
        ),
    ) if selected_board_project_id else []

    selected_board_todo_id_raw = (request.query_params.get("board_todo_id") or "").strip()
    selected_board_todo_id: UUID | None = None
    if selected_board_todo_id_raw:
        try:
            selected_board_todo_id = UUID(selected_board_todo_id_raw)
        except ValueError:
            selected_board_todo_id = None

    selected_board_todo = next((row for row in selected_board_todos if row.id == selected_board_todo_id), None)
    if selected_board_todo is None and selected_board_todos:
        selected_board_todo = selected_board_todos[0]

    board_rows = [
        {
            "id": str(row.id),
            "title": row.title,
            "description": row.description,
            "status": row.status.value,
            "priority": row.priority.value,
            "assignee_id": row.assignee_id,
            "assignee_name": people_by_id.get(row.assignee_id).name if row.assignee_id and row.assignee_id in people_by_id else "-",
            "selected": selected_board_todo is not None and selected_board_todo.id == row.id,
        }
        for row in selected_board_todos
    ]

    board_columns = []
    for status in TodoStatus:
        board_columns.append(
            {
                "key": status.value,
                "label": status.value.replace("_", " ").title(),
                "rows": [row for row in board_rows if row["status"] == status.value],
            }
        )

    board_redirect_url = _with_query_params(
        "/orchestration-ui",
        board_project_id=str(selected_board_project_id) if selected_board_project_id else None,
        board_todo_id=str(selected_board_todo.id) if selected_board_todo else None,
        map_mode="1" if map_mode else None,
    )

    popout_url = _with_query_params(
        "/orchestration-ui",
        board_project_id=str(selected_board_project_id) if selected_board_project_id else None,
        board_todo_id=str(selected_board_todo.id) if selected_board_todo else None,
        map_mode="1",
    )

    orchestration_map_payload = {
        "width": map_width,
        "height": map_height,
        "areas": map_areas,
        "agents": map_units,
        "sprite_base_path": "/static/sprites/agents",
        "map_mode": map_mode,
        "initial_zoom": 1.35 if map_mode else 1.0,
        "selected_board_project_id": str(selected_board_project_id) if selected_board_project_id else None,
        "control_urls": {
            "board_base_url": "/orchestration-ui",
            "popout_url": popout_url,
        },
    }

    selected_quest_action = (request.query_params.get("quest_action") or "").strip()
    selected_quest_actor_id = (request.query_params.get("quest_actor_id") or "").strip()

    quest_activity = sorted(
        [
            row
            for row in _org_activity_logs(session, current_actor.organization.id)
            if row.entity_type == EntityType.quest
        ],
        key=lambda row: _sort_datetime_key(row.timestamp),
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
        "orchestration_map_payload": orchestration_map_payload,
        "map_mode": map_mode,
        "map_popout_url": popout_url,
        "map_close_url": board_redirect_url if map_mode else None,
        "project_board_project": selected_board_project,
        "project_board_columns": board_columns,
        "project_board_rows": board_rows,
        "project_board_selected_todo": selected_board_todo,
        "project_board_redirect_url": board_redirect_url,
        "project_board_people": sorted(people, key=lambda row: row.name.lower()),
        "form_projects": sorted(projects, key=lambda row: row.name.lower()),
        "form_people": sorted(people, key=lambda row: row.name.lower()),
        "form_agents": sorted(agents, key=lambda row: row.name.lower()),
        "quest_priority_options": [row.value for row in QuestPriority],
        "todo_status_options": [row.value for row in TodoStatus],
        "todo_priority_options": [row.value for row in TodoPriority],
        "assignment_state_options": ["assigned", "in_progress", "blocked", "done"],
        "quest_status_options": [row.value for row in QuestStatus],
        "override_policy": "Full user control enabled",
    }


@router.get("/orchestration-ui/board/{project_id}")
def orchestration_project_board(
    project_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if _get_org_project(session, project_id, current_actor.organization.id) is None:
        return _redirect_ui("/orchestration-ui", err="Project not found")

    map_mode = (request.query_params.get("map_mode") or "").strip().lower() in {"1", "true", "yes"}
    return RedirectResponse(
        url=_with_query_params(
            "/orchestration-ui",
            board_project_id=str(project_id),
            map_mode="1" if map_mode else None,
        ),
        status_code=303,
    )


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
        if _sort_datetime_key(row.start_date) > _sort_datetime_key(now):
            continue
        if row.end_date is not None and _sort_datetime_key(row.end_date) < _sort_datetime_key(now):
            continue
        active_membership_count_by_project[row.project_id] = (
            active_membership_count_by_project.get(row.project_id, 0) + 1
        )

    last_activity_by_project: dict[UUID, datetime] = {}
    for row in activity_rows:
        if row.entity_type != EntityType.project:
            continue
        current = last_activity_by_project.get(row.entity_id)
        if current is None or _sort_datetime_key(row.timestamp) > _sort_datetime_key(current):
            last_activity_by_project[row.entity_id] = row.timestamp

    connection_by_client = {row.client_id: row for row in celonis_connections}
    client_name_by_id = {row.id: row.name for row in clients}
    user_celonis_token = _get_org_person_celonis_token(
        session,
        current_actor.organization.id,
        current_actor.person.id,
    )

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
            and _sort_datetime_key(row.submitted_at or row.created_at)
            < _sort_datetime_key(stale_review_cutoff)
        )

        open_todos = sum(1 for row in project_todos if row.status != TodoStatus.done)
        overdue_high_prio_todos = sum(
            1
            for row in project_todos
            if row.status != TodoStatus.done
            and row.priority == TodoPriority.high
            and row.due_at is not None
            and _sort_datetime_key(row.due_at) < _sort_datetime_key(now)
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
            if _sort_datetime_key(row.timestamp) < _sort_datetime_key(workflow_window_cutoff):
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
            pm_health_reason = "Overdue high-priority todos require immediate action"
        elif open_todos > 0 or pending_reviews > 0 or not connection_active:
            pm_health = "warning"
            pm_reasons: list[str] = []
            if open_todos > 0:
                pm_reasons.append(f"{open_todos} open todos")
            if pending_reviews > 0:
                pm_reasons.append(f"{pending_reviews} pending reviews")
            if not connection_active:
                pm_reasons.append("No active Celonis connection")
            pm_health_reason = "; ".join(pm_reasons)
        else:
            pm_health = "healthy"
            pm_health_reason = "No PM risks detected"

        if deprecated_assets > 0 or stale_reviews > 0:
            dev_health = "critical"
            dev_reasons: list[str] = []
            if deprecated_assets > 0:
                dev_reasons.append(f"{deprecated_assets} deprecated assets")
            if stale_reviews > 0:
                dev_reasons.append(f"{stale_reviews} stale in-review items")
            dev_health_reason = "; ".join(dev_reasons)
        elif not connection_active or (technical_total > 0 and technical_healthy < technical_total):
            dev_health = "warning"
            dev_reasons = []
            if not connection_active:
                dev_reasons.append("No active Celonis connection")
            if technical_total > 0 and technical_healthy < technical_total:
                dev_reasons.append(
                    f"Technical asset approvals incomplete ({technical_healthy}/{technical_total})"
                )
            dev_health_reason = "; ".join(dev_reasons)
        else:
            dev_health = "healthy"
            dev_health_reason = "No Dev risks detected"

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
                "project_overview_label": f"Project Overview: {project.name}",
                "project_status": project.status.value,
                "celonis_package_url": project.celonis_package_url,
                "celonis_app_url": project.celonis_app_url,
                "member_count": active_membership_count_by_project.get(project.id, 0),
                "open_todos": open_todos,
                "overdue_high_prio_todos": overdue_high_prio_todos,
                "pending_reviews": pending_reviews,
                "asset_total": asset_total,
                "assets_approved": assets_approved,
                "asset_approval_rate": asset_approval_rate,
                "last_activity": last_activity_by_project.get(project.id),
                "pm_health": pm_health,
                "pm_health_reason": pm_health_reason,
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
                "dev_health_reason": dev_health_reason,
                "has_user_celonis_token": bool(user_celonis_token and user_celonis_token.token_value),
            }
        )

    health_rank = {"healthy": 0, "warning": 1, "critical": 2}

    def _worst_health(rows: list[dict], key: str) -> str:
        if not rows:
            return "healthy"
        return max((row[key] for row in rows), key=lambda value: health_rank.get(value, 0))

    def _worst_row(rows: list[dict], key: str) -> dict | None:
        if not rows:
            return None
        return max(rows, key=lambda row: health_rank.get(row[key], 0))

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
        worst_pm_row = _worst_row(client_project_rows, "pm_health")
        worst_dev_row = _worst_row(client_project_rows, "dev_health")

        rows_with_rollups.append(
            {
                "row_kind": "client_summary",
                "client_id": client.id,
                "client_name": client.name,
                "project_count": len(client_project_rows),
                "project_id": None,
                "project_name": "Portfolio summary",
                "project_overview_label": "Portfolio summary",
                "project_status": f"{len(client_project_rows)} projects",
                "celonis_package_url": None,
                "celonis_app_url": None,
                "member_count": sum(row["member_count"] for row in client_project_rows),
                "open_todos": sum(row["open_todos"] for row in client_project_rows),
                "overdue_high_prio_todos": sum(row["overdue_high_prio_todos"] for row in client_project_rows),
                "pending_reviews": sum(row["pending_reviews"] for row in client_project_rows),
                "asset_total": asset_total,
                "assets_approved": assets_approved,
                "asset_approval_rate": (assets_approved / asset_total) if asset_total else 0.0,
                "last_activity": last_activity,
                "pm_health": _worst_health(client_project_rows, "pm_health"),
                "pm_health_reason": (
                    worst_pm_row["pm_health_reason"] if worst_pm_row is not None else "No projects available"
                ),
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
                "dev_health_reason": (
                    worst_dev_row["dev_health_reason"] if worst_dev_row is not None else "No projects available"
                ),
                "has_user_celonis_token": bool(user_celonis_token and user_celonis_token.token_value),
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
        "sensitivity_options": [row.value for row in SensitivityLevel],
        "has_user_celonis_token": bool(user_celonis_token and user_celonis_token.token_value),
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
            "ok_message": request.query_params.get("ok"),
            "next_path": _normalize_redirect_path(request.query_params.get("next_path"), "/dashboard"),
        },
    )


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "error_message": request.query_params.get("err"),
            "ok_message": request.query_params.get("ok"),
        },
    )


@router.post("/register", include_in_schema=False)
def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        normalized_email = email.strip().lower()
        normalized_name = name.strip()
        if not normalized_name:
            return _redirect_ui("/register", err="Name is required")

        _validate_registration_password(password, confirm_password)

        existing = session.exec(select(Person).where(Person.email == normalized_email)).first()
        if existing:
            return _redirect_ui("/register", err="An account with that email already exists")

        token = create_action_token(
            subject=normalized_email,
            purpose="register",
            expires_minutes=get_settings().registration_token_expire_minutes,
            extra_claims={
                "name": normalized_name,
                "pwd_hash": hash_password(password),
            },
        )
        _send_registration_email(request=request, email=normalized_email, token=token)
    except ValueError as exc:
        return _redirect_ui("/register", err=str(exc))
    except Exception as exc:
        return _redirect_ui("/register", err=f"Failed to send verification email: {exc}")

    return _redirect_ui(
        "/register",
        ok="Verification email sent. Open your inbox and click the activation link.",
    )


@router.get("/register/verify")
def register_verify(
    token: str,
    session: Session = Depends(get_session),
):
    try:
        claims = decode_action_token(token=token, expected_purpose="register")
        email = claims.get("sub", "").strip().lower()
        name = claims.get("name", "").strip()
        password_hash = claims.get("pwd_hash", "").strip()

        if not email or not name or not password_hash:
            return _redirect_ui("/register", err="Registration token is invalid")

        existing = session.exec(select(Person).where(Person.email == email)).first()
        if existing:
            return _redirect_login(ok="Your account is already active. You can sign in now.")

        person = Person(email=email, name=name, hashed_password=password_hash)
        session.add(person)
        session.commit()
        session.refresh(person)

        settings = get_settings()
        existing_organizations = session.exec(select(Organization)).all()
        organization: Organization
        membership_role = OrganizationRole.owner
        if settings.registration_join_single_existing_org and len(existing_organizations) == 1:
            organization = existing_organizations[0]
            membership_role = OrganizationRole.member
        else:
            organization = Organization(
                name=f"{name} Workspace",
                slug=_build_unique_org_slug(session, f"{name}-workspace"),
            )
            session.add(organization)
            session.commit()
            session.refresh(organization)

        membership = OrganizationMembership(
            organization_id=organization.id,
            person_id=person.id,
            role=membership_role,
        )
        session.add(membership)
        session.commit()

        seed_default_templates(session, organization_id=organization.id)
    except ValueError as exc:
        return _redirect_ui("/register", err=str(exc))
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/register", err=f"Registration failed: {exc}")

    return _redirect_login(ok="Account verified. You can sign in now.")


@router.get("/forgot-password")
def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        "forgot_password.html",
        {
            "request": request,
            "error_message": request.query_params.get("err"),
            "ok_message": request.query_params.get("ok"),
        },
    )


@router.post("/forgot-password", include_in_schema=False)
def forgot_password_submit(
    request: Request,
    email: str = Form(...),
    session: Session = Depends(get_session),
):
    normalized_email = email.strip().lower()
    person = session.exec(select(Person).where(Person.email == normalized_email)).first()

    if person:
        try:
            token = create_action_token(
                subject=str(person.id),
                purpose="password-reset",
                expires_minutes=get_settings().password_reset_token_expire_minutes,
            )
            _send_password_reset_email(request=request, email=normalized_email, token=token)
        except Exception as exc:
            return _redirect_ui("/forgot-password", err=f"Failed to send reset email: {exc}")

    return _redirect_ui(
        "/forgot-password",
        ok="If the account exists, a reset email has been sent.",
    )


@router.get("/reset-password")
def reset_password_page(request: Request, token: str = ""):
    if not token:
        return _redirect_ui("/forgot-password", err="Reset token is required")

    error_message = ""
    try:
        decode_action_token(token=token, expected_purpose="password-reset")
    except ValueError as exc:
        error_message = str(exc)

    return templates.TemplateResponse(
        "reset_password.html",
        {
            "request": request,
            "token": token,
            "error_message": error_message,
        },
    )


@router.post("/reset-password", include_in_schema=False)
def reset_password_submit(
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        claims = decode_action_token(token=token, expected_purpose="password-reset")
        person_id = _parse_uuid(claims.get("sub", ""), "person_id")
        person = session.get(Person, person_id)
        if person is None:
            return _redirect_ui("/forgot-password", err="Account no longer exists")

        _validate_registration_password(password, confirm_password)
        person.hashed_password = hash_password(password)
        session.add(person)
        session.commit()
    except ValueError as exc:
        return _redirect_ui("/forgot-password", err=str(exc))
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/forgot-password", err=f"Password reset failed: {exc}")

    return _redirect_login(ok="Password updated. Sign in with your new password.")


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
        return _redirect_login(err="Invalid credentials", next_path=next_path)

    memberships = list(
        session.exec(
            select(OrganizationMembership).where(OrganizationMembership.person_id == person.id)
        ).all()
    )
    if not memberships:
        return _redirect_login(
            err="No organization membership found. Ask your admin for access.",
            next_path=next_path,
        )

    # UI login does not ask users to choose an organization, so prefer owner/admin memberships first.
    memberships.sort(
        key=lambda row: (
            0 if row.role in {OrganizationRole.owner, OrganizationRole.admin} else 1,
            row.joined_at,
        )
    )
    selected_org_id = memberships[0].organization_id

    token = create_access_token(str(person.id), organization_id=str(selected_org_id))
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


@router.get("/account-ui")
def account_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    person = session.get(Person, current_actor.person.id)
    if person is None:
        return _redirect_login(err="Account not found")

    memberships = list(
        session.exec(
            select(OrganizationMembership).where(OrganizationMembership.person_id == person.id)
        ).all()
    )
    organizations = {
        row.id: row
        for row in session.exec(
            select(Organization).where(
                Organization.id.in_([membership.organization_id for membership in memberships])
            )
        ).all()
    }
    membership_rows = [
        {
            "organization_name": organizations[membership.organization_id].name
            if membership.organization_id in organizations
            else "Unknown",
            "organization_slug": organizations[membership.organization_id].slug
            if membership.organization_id in organizations
            else "-",
            "role": _enum_or_value(membership.role, "member"),
            "joined_at": membership.joined_at,
        }
        for membership in sorted(memberships, key=lambda row: _sort_datetime_key(row.joined_at))
    ]

    return templates.TemplateResponse(
        "account.html",
        {
            "request": request,
            "person": person,
            "membership_rows": membership_rows,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
        },
    )


@router.post("/account-ui/update", include_in_schema=False)
def account_ui_update(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    confirm_password: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        person = session.get(Person, current_actor.person.id)
        if person is None:
            return _redirect_login(err="Account not found")

        normalized_name = name.strip()
        normalized_email = email.strip().lower()
        if not normalized_name:
            return _redirect_ui("/account-ui", err="Name is required")
        if not normalized_email:
            return _redirect_ui("/account-ui", err="Email is required")

        existing = session.exec(select(Person).where(Person.email == normalized_email)).first()
        if existing and existing.id != person.id:
            return _redirect_ui("/account-ui", err="Email is already in use")

        person.name = normalized_name
        person.email = normalized_email

        has_password_input = bool(password.strip() or confirm_password.strip())
        if has_password_input:
            _validate_registration_password(password, confirm_password)
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
            metadata={
                "email": person.email,
                "self_service": True,
                "password_updated": has_password_input,
            },
        )
        return _redirect_ui("/account-ui", ok="Account updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/account-ui", err=f"Update account failed: {exc}")


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


@router.get("/sales-ui", include_in_schema=False)
def sales_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    rows = sorted(
        _org_trycelonis_demos(session, current_actor.organization.id),
        key=lambda row: (_sort_datetime_key(row.last_synced_at), row.title.lower()),
        reverse=True,
    )
    settings = get_settings()
    return templates.TemplateResponse(
        "sales.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "rows": rows,
            "trycelonis_catalog_url": settings.trycelonis_catalog_url,
            "trycelonis_manifest_path": settings.trycelonis_manifest_path,
            "demo_count": len(rows),
            "last_synced_at": rows[0].last_synced_at if rows else None,
        },
    )


@router.post("/sales-ui/trycelonis-sync", include_in_schema=False)
def sales_ui_trycelonis_sync(
    catalog_url: str = Form(""),
    manifest_path: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    settings = get_settings()
    try:
        result = sync_trycelonis_demos(
            session,
            organization_id=current_actor.organization.id,
            catalog_url=catalog_url.strip() or settings.trycelonis_catalog_url,
            manifest_path=manifest_path.strip() or settings.trycelonis_manifest_path,
        )
        return _redirect_ui(
            "/sales-ui",
            ok=f"TryCelonis sync complete: imported {result.imported}, updated {result.updated}, total {result.total}.",
        )
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/sales-ui", err=f"TryCelonis sync failed: {exc}")


def _latest_preflight_rows_for_client(
    session: Session,
    *,
    organization_id: UUID,
    client_id: UUID,
) -> list[dict]:
    def _normalize_preflight_status(raw_status: str, status_code: int | None) -> str:
        status = (raw_status or "unknown").strip().lower()
        if status == "unknown" and status_code in {301, 302, 303, 307, 308}:
            return "redirect-to-login"
        return status

    def _preflight_remediation(service: str, status: str) -> str:
        service_key = (service or "").strip().lower()
        rights_hint = {
            "core": "Grant Core platform/API access for app keys.",
            "process-mining": "Grant Process Mining API read rights (teams and data models).",
            "data-integration": "Grant Data Integration API read rights (pools, jobs, transformations).",
            "studio": (
                "Grant Studio API list/read rights for spaces. "
                "Package-level Use/Edit/Delete/Manage permissions alone may not allow "
                "tenant-wide /studio/api/spaces listing."
            ),
            "apps": "Grant Apps API read rights (apps/packages listing).",
        }.get(service_key, "Grant the API read rights required by this service.")

        if status == "authorized":
            return "OK"
        if status == "missing-token":
            return "Save a per-user token in Step 3 or configure FORGE_CELONIS_API_TOKEN."
        if status in {"unauthorized", "forbidden", "redirect-to-login"}:
            return f"App key is valid but missing service scope. {rights_hint}"
        if status == "not-found":
            return "Endpoint unavailable for this tenant. Confirm service availability and endpoint version."
        if status == "unreachable":
            return "Tenant URL or network connectivity issue. Verify base URL, DNS, proxy, and firewall."
        if status == "server-error":
            return "Celonis service returned 5xx. Retry later and inspect tenant service health."
        return f"Check endpoint availability and rights. {rights_hint}"

    logs = sorted(
        _org_activity_logs(session, organization_id),
        key=lambda row: _sort_datetime_key(row.timestamp),
        reverse=True,
    )
    preflight_rows: list[dict] = []
    target_run_id: str | None = None
    for row in logs:
        if row.action != "celonis_connection.preflight":
            continue
        metadata = row.metadata_json or {}
        raw_client_id = str(metadata.get("client_id", "")).strip()
        if raw_client_id != str(client_id):
            continue
        run_id = str(metadata.get("run_id", "")).strip() or None
        if target_run_id is None:
            target_run_id = run_id
        if target_run_id and run_id != target_run_id:
            continue
        raw_status = str(metadata.get("permission_status", "unknown"))
        status_code = metadata.get("status_code")
        normalized_status = _normalize_preflight_status(raw_status, status_code)
        preflight_rows.append(
            {
                "service": metadata.get("service", "core"),
                "permission_status": normalized_status,
                "status_code": status_code,
                "probe_url": metadata.get("probe_url") or "-",
                "remediation": _preflight_remediation(
                    str(metadata.get("service", "core")),
                    normalized_status,
                ),
                "run_id": run_id,
                "timestamp": row.timestamp,
            }
        )
    return sorted(preflight_rows, key=lambda item: str(item["service"]))


def _celonis_setup_context(
    request: Request,
    session: Session,
    current_actor: CurrentActor,
    *,
    selected_client: Client | None,
) -> dict:
    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda row: row.name.lower(),
    )
    connection = (
        _get_org_active_celonis_connection(
            session,
            selected_client.id,
            current_actor.organization.id,
        )
        if selected_client
        else None
    )
    user_token = _get_org_person_celonis_token(
        session,
        current_actor.organization.id,
        current_actor.person.id,
    )
    env_token_configured = bool((get_settings().celonis_api_token or "").strip())
    preflight_rows = (
        _latest_preflight_rows_for_client(
            session,
            organization_id=current_actor.organization.id,
            client_id=selected_client.id,
        )
        if selected_client
        else []
    )
    authorized_count = sum(1 for row in preflight_rows if row["permission_status"] == "authorized")
    all_authorized = bool(preflight_rows) and all(
        row["permission_status"] == "authorized" for row in preflight_rows
    )
    has_any_authorized = authorized_count > 0
    limited_scope = bool(preflight_rows) and has_any_authorized and not all_authorized

    step_client_ready = selected_client is not None
    step_connection_ready = connection is not None
    step_token_ready = bool(user_token and user_token.token_value) or env_token_configured
    # Partial preflight success is considered usable; unresolved services stay visible in summary.
    step_validation_ready = bool(preflight_rows) and has_any_authorized
    if not step_client_ready:
        next_step = 1
    elif not step_connection_ready:
        next_step = 2
    elif not step_token_ready:
        next_step = 3
    elif not step_validation_ready:
        next_step = 4
    else:
        next_step = 5

    return {
        "request": request,
        "active_organization": current_actor.organization,
        "ok_message": request.query_params.get("ok"),
        "error_message": request.query_params.get("err"),
        "clients": clients,
        "selected_client": selected_client,
        "active_connection": connection,
        "user_token_present": bool(user_token and user_token.token_value),
        "env_token_configured": env_token_configured,
        "preflight_rows": preflight_rows,
        "preflight_all_authorized": all_authorized,
        "preflight_limited_scope": limited_scope,
        "preflight_authorized_count": authorized_count,
        "preflight_total": len(preflight_rows),
        "latest_run_id": preflight_rows[0]["run_id"] if preflight_rows else None,
        "step_client_ready": step_client_ready,
        "step_connection_ready": step_connection_ready,
        "step_token_ready": step_token_ready,
        "step_validation_ready": step_validation_ready,
        "next_step": next_step,
    }


@router.get("/onboarding/celonis-setup")
def celonis_setup_wizard(
    request: Request,
    client_id: str = "",
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
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

    return templates.TemplateResponse(
        "celonis_setup_wizard.html",
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
            existing.updated_at = datetime.utcnow()

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
            metadata={"email": person.email, "role_global": _enum_or_value(person.role_global, "member")},
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
                "role": _enum_or_value(membership.role, "member"),
            },
        )
        return _redirect_dashboard(ok="Project membership created")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Create membership failed: {exc}")


@router.post("/memberships-ui/create", include_in_schema=False)
def memberships_ui_create(
    project_id: str = Form(...),
    person_id: str = Form(...),
    role: str = Form("contributor"),
    redirect_to: str = Form("/dashboard"),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    target_path = _normalize_redirect_path(redirect_to, "/dashboard")
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
                "role": _enum_or_value(membership.role, "member"),
            },
        )
        return _redirect_ui(target_path, ok="Project membership added")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(target_path, err=f"Add membership failed: {exc}")


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
        key=lambda row: _sort_datetime_key(row.created_at),
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
        key=lambda row: _sort_datetime_key(row.created_at),
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
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    assets = _org_assets(session, current_actor.organization.id)
    projects = _org_projects(session, current_actor.organization.id)
    people = sorted(
        _org_people(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
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
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    rows = [
        {
            "id": person.id,
            "name": person.name,
            "email": person.email,
            "role_global": _enum_or_value(person.role_global, "member"),
            "role_org": _enum_or_value(membership_by_person_id[person.id].role, "member")
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
            metadata={"email": person.email, "role_global": _enum_or_value(person.role_global, "member")},
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
            metadata={"email": person.email, "role_global": _enum_or_value(person.role_global, "member")},
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
        key=lambda row: _sort_datetime_key(row.created_at),
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
        key=lambda row: _sort_datetime_key(row.created_at),
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
            (row.due_at is None, _sort_datetime_key(row.due_at)),
            _sort_datetime_key(row.updated_at),
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
                key=lambda row: _sort_datetime_key(row.created_at),
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
                key=lambda row: _sort_datetime_key(row.created_at),
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
                key=lambda row: _sort_datetime_key(row.created_at),
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
                key=lambda row: _sort_datetime_key(row.timestamp),
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
    assets = sorted(asset_by_id.values(), key=lambda row: _sort_datetime_key(row.created_at), reverse=True)

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
    todos.sort(key=lambda row: _sort_datetime_key(row.created_at), reverse=True)
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
            "role": _enum_or_value(membership.role, "member"),
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
    todos.sort(key=lambda row: _sort_datetime_key(row.created_at), reverse=True)
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
        for row in sorted(gitlab_repos, key=lambda item: _sort_datetime_key(item.created_at), reverse=True)
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
            "membership_role_options": [row.value for row in MembershipRole],
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
    todos.sort(key=lambda row: _sort_datetime_key(row.created_at), reverse=True)
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
        for row in sorted(gitlab_repos, key=lambda item: _sort_datetime_key(item.created_at), reverse=True)
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
            "membership_role_options": [row.value for row in MembershipRole],
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
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    templates_rows = sorted(
        _org_templates(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    instantiations = sorted(
        _org_template_instantiations(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    projects = sorted(
        _org_projects(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    people = sorted(
        _org_people(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
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
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    files = sorted(
        _org_delivery_files(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    projects = sorted(
        _org_projects(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
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
            stored_path = Path(get_settings().input_dir).resolve() / "delivery_files" / row.stored_filename

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
        key=lambda row: _sort_datetime_key(row.timestamp),
        reverse=True,
    )
    people = sorted(
        _org_people(session, current_actor.organization.id),
        key=lambda row: _sort_datetime_key(row.created_at),
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
    return RedirectResponse(url="/docs-site/user/", status_code=307)


@router.get("/docu/developer.html")
def docu_developer(request: Request):
    return RedirectResponse(url="/docs-site/developer/", status_code=307)


@router.get("/docu/guide-admin-setup.html")
def docu_guide_admin_setup(request: Request):
    return RedirectResponse(url="/docs-site/admin/full-setup/", status_code=307)


@router.get("/docu/guide-account-flows.html")
def docu_guide_account_flows(request: Request):
    return RedirectResponse(url="/docs-site/guides/account-flows/", status_code=307)


@router.get("/docu/guide-delivery-walkthrough.html")
def docu_guide_delivery_walkthrough(request: Request):
    return RedirectResponse(url="/docs-site/guides/delivery-walkthrough/", status_code=307)


@router.get("/docu/guide-action-flow-templates.html")
def docu_guide_action_flow_templates(request: Request):
    return RedirectResponse(url="/docs-site/guides/action-flow-template-catalog/", status_code=307)


# ---------------------------------------------------------------------------
# Celonis Token Admin page
# ---------------------------------------------------------------------------

@router.get("/celonis-token-admin-ui", include_in_schema=False)
def celonis_token_admin_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    people = _org_people(session, current_actor.organization.id)
    person_by_id = {person.id: person for person in people}
    token_rows = sorted(
        list(
            session.exec(
                select(CelonisUserToken).where(
                    CelonisUserToken.organization_id == current_actor.organization.id
                )
            ).all()
        ),
        key=lambda row: _sort_datetime_key(getattr(row, "updated_at", None)),
        reverse=True,
    )
    access_by_person = _latest_celonis_system_access_by_person(
        session,
        current_actor.organization.id,
    )
    project_scopes_by_person = _active_project_token_scopes_by_person(
        session,
        current_actor.organization.id,
    )

    rows = []
    for token_row in token_rows:
        person = person_by_id.get(token_row.person_id)
        access = access_by_person.get(token_row.person_id, {})
        service_status = access.get("service_status", {})
        authorized_services = sorted(
            service for service, status in service_status.items() if status == "authorized"
        )
        restricted_services = sorted(
            f"{service} ({status})"
            for service, status in service_status.items()
            if status != "authorized"
        )
        rows.append(
            {
                "row_kind": "person",
                "id": token_row.id,
                "person_id": token_row.person_id,
                "person_name": person.name if person else "Unknown",
                "person_email": person.email if person else "Unknown",
                "target_name": person.name if person else "Unknown",
                "scope": "person+organization",
                "token_preview": _mask_token_value(token_row.token_value),
                "updated_at": token_row.updated_at,
                "authorized_services": authorized_services,
                "restricted_services": restricted_services,
                "last_preflight_at": access.get("last_preflight_at"),
            }
        )
        for project_scope in sorted(
            project_scopes_by_person.get(token_row.person_id, []),
            key=lambda item: _sort_datetime_key(item.get("updated_at")),
            reverse=True,
        ):
            rows.append(
                {
                    "row_kind": "project",
                    "id": token_row.id,
                    "person_id": token_row.person_id,
                    "person_name": person.name if person else "Unknown",
                    "person_email": person.email if person else "Unknown",
                    "target_name": str(project_scope.get("project_name") or "Unknown project"),
                    "scope": "project",
                    "token_preview": _mask_token_value(token_row.token_value),
                    "updated_at": project_scope.get("updated_at") or token_row.updated_at,
                    "authorized_services": authorized_services,
                    "restricted_services": restricted_services,
                    "last_preflight_at": access.get("last_preflight_at"),
                }
            )

    return templates.TemplateResponse(
        "celonis_token_admin.html",
        {
            "request": request,
            "active_organization": current_actor.organization,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "edit_id": request.query_params.get("edit"),
            "rows": rows,
            "people_options": sorted(
                [
                    {"id": person.id, "name": person.name, "email": person.email}
                    for person in people
                ],
                key=lambda row: (row["name"] or "").lower(),
            ),
        },
    )


@router.post("/celonis-token-admin-ui/create", include_in_schema=False)
def celonis_token_admin_create(
    person_id: str = Form(...),
    token_value: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_person_id = _parse_uuid(person_id, "person_id")
        membership = _get_org_membership(session, parsed_person_id, current_actor.organization.id)
        if membership is None:
            return _redirect_ui("/celonis-token-admin-ui", err="Selected user is not in the organization")

        cleaned = token_value.strip()
        if not cleaned:
            return _redirect_ui("/celonis-token-admin-ui", err="Token value cannot be blank")

        _upsert_org_person_celonis_token(
            session,
            current_actor.organization.id,
            parsed_person_id,
            cleaned,
        )
        session.commit()
        log_activity(
            session,
            entity_type=EntityType.person,
            entity_id=parsed_person_id,
            actor_id=current_actor.person.id,
            action="celonis_user_token.admin_saved",
            organization_id=current_actor.organization.id,
            metadata={
                "person_id": str(parsed_person_id),
                "scope": "person+organization",
                "token_present": True,
            },
        )
        return _redirect_ui("/celonis-token-admin-ui", ok="Token saved")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-token-admin-ui", err=f"Save token failed: {exc}")


@router.post("/celonis-token-admin-ui/update", include_in_schema=False)
def celonis_token_admin_update(
    token_id: str = Form(...),
    token_value: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_token_id = _parse_uuid(token_id, "token_id")
        row = session.get(CelonisUserToken, parsed_token_id)
        if row is None or row.organization_id != current_actor.organization.id:
            return _redirect_ui("/celonis-token-admin-ui", err="Token entry not found")

        cleaned = token_value.strip()
        if not cleaned:
            return _redirect_ui(
                f"/celonis-token-admin-ui?edit={token_id}",
                err="Token value cannot be blank",
            )

        row.token_value = cleaned
        row.updated_at = datetime.utcnow()
        session.add(row)
        session.commit()
        log_activity(
            session,
            entity_type=EntityType.person,
            entity_id=row.person_id,
            actor_id=current_actor.person.id,
            action="celonis_user_token.admin_saved",
            organization_id=current_actor.organization.id,
            metadata={
                "person_id": str(row.person_id),
                "scope": "person+organization",
                "token_present": True,
            },
        )
        return _redirect_ui("/celonis-token-admin-ui", ok="Token updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-token-admin-ui", err=f"Update token failed: {exc}")


@router.post("/celonis-token-admin-ui/delete", include_in_schema=False)
def celonis_token_admin_delete(
    token_id: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_token_id = _parse_uuid(token_id, "token_id")
        row = session.get(CelonisUserToken, parsed_token_id)
        if row is None or row.organization_id != current_actor.organization.id:
            return _redirect_ui("/celonis-token-admin-ui", err="Token entry not found")

        person_id = row.person_id
        session.delete(row)
        session.commit()
        log_activity(
            session,
            entity_type=EntityType.person,
            entity_id=person_id,
            actor_id=current_actor.person.id,
            action="celonis_user_token.admin_cleared",
            organization_id=current_actor.organization.id,
            metadata={
                "person_id": str(person_id),
                "scope": "person+organization",
                "token_present": False,
            },
        )
        return _redirect_ui("/celonis-token-admin-ui", ok="Token removed")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-token-admin-ui", err=f"Delete token failed: {exc}")


# ---------------------------------------------------------------------------
# Celonis Credentials page
# ---------------------------------------------------------------------------

@router.get("/celonis-credentials-ui", include_in_schema=False)
def celonis_credentials_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    user_token = _get_org_person_celonis_token(
        session, current_actor.organization.id, current_actor.person.id
    )
    env_token_configured = bool((get_settings().celonis_api_token or "").strip())
    recent_logs = sorted(
        [
            row
            for row in _org_activity_logs(session, current_actor.organization.id)
            if row.action in ("celonis_user_token.saved", "celonis_user_token.cleared")
            and (row.metadata_json or {}).get("person_id") == str(current_actor.person.id)
        ],
        key=lambda r: _sort_datetime_key(r.timestamp),
        reverse=True,
    )[:10]
    return templates.TemplateResponse(
        "celonis_credentials.html",
        {
            "request": request,
            "active_organization": current_actor.organization,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "token_present": bool(user_token and user_token.token_value),
            "token_updated_at": getattr(user_token, "updated_at", None) if user_token else None,
            "env_token_configured": env_token_configured,
            "activity_rows": [
                {
                    "timestamp": row.timestamp,
                    "action": row.action.replace("celonis_user_token.", ""),
                    "metadata_json": row.metadata_json or {},
                }
                for row in recent_logs
            ],
        },
    )


@router.post("/celonis-credentials-ui/save-token", include_in_schema=False)
def celonis_credentials_save_token(
    token_value: str = Form(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        cleaned = token_value.strip()
        if not cleaned:
            return _redirect_ui("/celonis-credentials-ui", err="Token value cannot be blank")
        _upsert_org_person_celonis_token(
            session, current_actor.organization.id, current_actor.person.id, cleaned
        )
        session.commit()
        log_activity(
            session,
            entity_type=EntityType.person,
            entity_id=current_actor.person.id,
            actor_id=current_actor.person.id,
            action="celonis_user_token.saved",
            organization_id=current_actor.organization.id,
            metadata={
                "person_id": str(current_actor.person.id),
                "token_present": True,
            },
        )
        return _redirect_ui("/celonis-credentials-ui", ok="Token saved successfully")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-credentials-ui", err=f"Save token failed: {exc}")


@router.post("/celonis-credentials-ui/clear-token", include_in_schema=False)
def celonis_credentials_clear_token(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        existing = _get_org_person_celonis_token(
            session, current_actor.organization.id, current_actor.person.id
        )
        if existing:
            session.delete(existing)
            session.commit()
        log_activity(
            session,
            entity_type=EntityType.person,
            entity_id=current_actor.person.id,
            actor_id=current_actor.person.id,
            action="celonis_user_token.cleared",
            organization_id=current_actor.organization.id,
            metadata={
                "person_id": str(current_actor.person.id),
                "token_present": False,
            },
        )
        return _redirect_ui("/celonis-credentials-ui", ok="Token cleared")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-credentials-ui", err=f"Clear token failed: {exc}")


# ---------------------------------------------------------------------------
# Celonis Discovery page
# ---------------------------------------------------------------------------

def _recent_preflights_for_org(session: Session, organization_id: UUID) -> list[dict]:
    """Return one summary row per preflight run (latest 20 runs, most recent first)."""
    logs = sorted(
        [
            row
            for row in _org_activity_logs(session, organization_id)
            if row.action == "celonis_connection.preflight"
        ],
        key=lambda r: _sort_datetime_key(r.timestamp),
        reverse=True,
    )
    seen_runs: dict[str, dict] = {}
    for row in logs:
        meta = row.metadata_json or {}
        run_id = str(meta.get("run_id", "")).strip() or str(row.id)
        if run_id in seen_runs:
            continue
        seen_runs[run_id] = {
            "id": run_id,
            "client_id": str(meta.get("client_id", "")),
            "client_name": "",
            "space_name": meta.get("space_name") or "",
            "passed": meta.get("permission_status") == "authorized",
            "created_at": row.timestamp,
        }
        if len(seen_runs) >= 20:
            break
    return list(seen_runs.values())


@router.get("/celonis-discovery-ui", include_in_schema=False)
def celonis_discovery_ui(
    request: Request,
    client_id: str = "",
    space_name: str = "",
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda c: c.name.lower(),
    )
    client_map = {str(c.id): c.name for c in clients}
    selected_client_id = client_id.strip() or (str(clients[0].id) if clients else "")

    preflight_rows: list[dict] = []
    all_authorized = False
    preflight_run_id: str | None = None
    if selected_client_id:
        try:
            parsed_cid = _parse_uuid(selected_client_id, "client_id")
            preflight_rows = _latest_preflight_rows_for_client(
                session,
                organization_id=current_actor.organization.id,
                client_id=parsed_cid,
            )
            if preflight_rows:
                all_authorized = all(r["permission_status"] == "authorized" for r in preflight_rows)
                preflight_run_id = preflight_rows[0].get("run_id")
        except Exception:
            pass

    recent_preflights = _recent_preflights_for_org(session, current_actor.organization.id)
    for row in recent_preflights:
        row["client_name"] = client_map.get(row["client_id"], row["client_id"])

    user_token = _get_org_person_celonis_token(
        session, current_actor.organization.id, current_actor.person.id
    )
    # Reshape preflight_rows for template (use permission_status as "status")
    display_rows = [
        {
            "service": r.get("service", ""),
            "check": "permission",
            "status": r.get("permission_status", "unknown"),
            "detail": r.get("probe_url") or "",
        }
        for r in preflight_rows
    ]
    return templates.TemplateResponse(
        "celonis_discovery.html",
        {
            "request": request,
            "active_organization": current_actor.organization,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "clients": clients,
            "selected_client_id": selected_client_id,
            "space_name": space_name,
            "preflight_rows": display_rows,
            "all_authorized": all_authorized,
            "preflight_run_id": preflight_run_id,
            "recent_preflights": recent_preflights,
            "token_present": bool(user_token and user_token.token_value),
        },
    )


@router.post("/celonis-discovery-ui/run-preflight", include_in_schema=False)
def celonis_discovery_run_preflight(
    client_id: str = Form(...),
    space_name: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        client = _get_org_client(session, parsed_client_id, current_actor.organization.id)
        if client is None:
            return _redirect_ui("/celonis-discovery-ui", err="Client not found")
        connection = _get_org_active_celonis_connection(
            session, parsed_client_id, current_actor.organization.id
        )
        if connection is None:
            return _redirect_ui(
                f"/celonis-discovery-ui?client_id={parsed_client_id}",
                err="No active Celonis connection for this client — configure one in Celonis Setup",
            )
        user_token = _get_org_person_celonis_token(
            session, current_actor.organization.id, current_actor.person.id
        )
        token_override = user_token.token_value if user_token else None
        gateway = CelonisGateway(get_settings())
        run_id = str(uuid4())
        services = list(CelonisGateway.SERVICE_DEFAULT_PROBES.keys())
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
                    "source": "discovery_ui",
                    "space_name": space_name.strip(),
                    "run_id": run_id,
                },
            )
        total = len(services)
        ok_msg = (
            f"Preflight complete — all {total} services authorized (run {run_id})"
            if authorized_count == total
            else f"Preflight complete — {authorized_count}/{total} services authorized (run {run_id})"
        )
        return _redirect_ui(
            f"/celonis-discovery-ui?client_id={parsed_client_id}&space_name={quote_plus(space_name.strip())}",
            ok=ok_msg,
        )
    except Exception as exc:
        session.rollback()
        return _redirect_ui(
            f"/celonis-discovery-ui?client_id={client_id}",
            err=f"Preflight failed: {exc}",
        )


# ---------------------------------------------------------------------------
# Celonis Deployments page
# ---------------------------------------------------------------------------

def _get_deploy_request(
    session: Session, deploy_id: UUID, organization_id: UUID
) -> CelonisDeploymentRequest | None:
    req = session.get(CelonisDeploymentRequest, deploy_id)
    if not req or req.organization_id != organization_id:
        return None
    return req


@router.get("/celonis-tool-hub-ui", include_in_schema=False)
def celonis_tool_hub_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
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
    return templates.TemplateResponse(
        "celonis_tool_hub.html",
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


@router.get("/celonis-deployments-ui", include_in_schema=False)
def celonis_deployments_ui(
    request: Request,
    client_id: str = "",
    space_name: str = "",
    preflight_run_id: str = "",
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    clients = sorted(
        _org_clients(session, current_actor.organization.id),
        key=lambda c: c.name.lower(),
    )
    projects = sorted(
        _org_projects(session, current_actor.organization.id),
        key=lambda p: p.name.lower(),
    )
    client_map = {str(c.id): c.name for c in clients}
    project_map = {str(p.id): p.name for p in projects}

    deploy_requests = list_deployment_requests(session, organization_id=current_actor.organization.id)

    from collections import Counter
    status_counts = Counter(r.status.value for r in deploy_requests)
    counts = {
        "draft": status_counts.get("draft", 0),
        "awaiting_approval": status_counts.get("awaiting_approval", 0),
        "approved": status_counts.get("approved", 0),
        "cancelled": status_counts.get("cancelled", 0),
    }

    enriched = []
    for req in deploy_requests:
        enriched.append({
            "id": req.id,
            "client_id": req.client_id,
            "client_name": client_map.get(str(req.client_id), str(req.client_id)),
            "project_name": project_map.get(str(req.project_id), str(req.project_id)),
            "target_space_name": req.target_space_name,
            "target_package_key": req.target_package_key,
            "status": req.status.value,
            "preflight_passed": req.preflight_passed,
            "permission_diff_acknowledged": req.permission_diff_acknowledged,
            "created_at": req.created_at,
            "reviewer_note": req.reviewer_note,
            "can_review": (
                req.status == CelonisDeploymentStatus.awaiting_approval
                and str(req.created_by) != str(current_actor.person.id)
            ),
        })

    return templates.TemplateResponse(
        "celonis_deployments.html",
        {
            "request": request,
            "active_organization": current_actor.organization,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "clients": clients,
            "projects": projects,
            "counts": counts,
            "deploy_requests": enriched,
            "prefill_client_id": client_id.strip(),
            "prefill_space_name": space_name.strip(),
            "prefill_preflight_run_id": preflight_run_id.strip(),
        },
    )


@router.post("/celonis-deployments-ui/create", include_in_schema=False)
def celonis_deployments_create(
    client_id: str = Form(...),
    project_id: str = Form(...),
    target_space_name: str = Form(""),
    target_package_key: str = Form(""),
    target_package_name: str = Form(""),
    preflight_run_id: str = Form(""),
    notes: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_client_id = _parse_uuid(client_id, "client_id")
        parsed_project_id = _parse_uuid(project_id, "project_id")
        create_deployment_request(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            client_id=parsed_client_id,
            project_id=parsed_project_id,
            target_space_name=target_space_name,
            target_package_key=target_package_key,
            target_package_name=target_package_name,
            preflight_run_id=preflight_run_id,
            notes=notes,
        )
        return _redirect_ui("/celonis-deployments-ui", ok="Deployment request created")
    except CelonisDeploymentServiceError as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=str(exc))
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=f"Create request failed: {exc}")


@router.post("/celonis-deployments-ui/{deploy_id}/acknowledge-diff", include_in_schema=False)
def celonis_deployments_acknowledge_diff(
    deploy_id: str,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_id = _parse_uuid(deploy_id, "deploy_id")
        acknowledge_deployment_diff(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            deployment_request_id=parsed_id,
        )
        return _redirect_ui("/celonis-deployments-ui", ok="Permission diff acknowledged")
    except CelonisDeploymentServiceError as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=str(exc))
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=f"Acknowledge diff failed: {exc}")


@router.post("/celonis-deployments-ui/{deploy_id}/submit-for-approval", include_in_schema=False)
def celonis_deployments_submit_for_approval(
    deploy_id: str,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_id = _parse_uuid(deploy_id, "deploy_id")
        submit_deployment_for_approval(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            deployment_request_id=parsed_id,
        )
        return _redirect_ui("/celonis-deployments-ui", ok="Request submitted for approval")
    except CelonisDeploymentServiceError as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=str(exc))
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=f"Submit for approval failed: {exc}")


@router.post("/celonis-deployments-ui/{deploy_id}/approve", include_in_schema=False)
def celonis_deployments_approve(
    deploy_id: str,
    decision: str = Form(...),
    reviewer_note: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_id = _parse_uuid(deploy_id, "deploy_id")
        decide_deployment_request(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            deployment_request_id=parsed_id,
            decision=decision,
            reviewer_note=reviewer_note,
        )
        return _redirect_ui(
            "/celonis-deployments-ui",
            ok=f"Request {decision}",
        )
    except CelonisDeploymentServiceError as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=str(exc))
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=f"Review action failed: {exc}")


@router.post("/celonis-deployments-ui/{deploy_id}/cancel", include_in_schema=False)
def celonis_deployments_cancel(
    deploy_id: str,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        parsed_id = _parse_uuid(deploy_id, "deploy_id")
        cancel_deployment_request(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            deployment_request_id=parsed_id,
        )
        return _redirect_ui("/celonis-deployments-ui", ok="Request cancelled")
    except CelonisDeploymentServiceError as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=str(exc))
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/celonis-deployments-ui", err=f"Cancel request failed: {exc}")


@router.get("/tenant-ui")
def tenant_ui(request: Request):
    return templates.TemplateResponse(
        "tenant.html",
        {
            "request": request,
        },
    )


@router.get("/workspace-ui")
def workspace_ui(request: Request):
    tenant_url = request.query_params.get("url") or "https://id.celonis.cloud/user/ui/login"
    return templates.TemplateResponse(
        "workspace.html",
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
    kpis = sorted(_org_kpis(session, current_actor.organization.id), key=lambda row: _sort_datetime_key(row.created_at), reverse=True)
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
    active_connection = _get_org_active_celonis_connection(
        session,
        client_id,
        current_actor.organization.id,
    )
    ok_message = request.query_params.get("ok")
    error_message = request.query_params.get("err")
    return templates.TemplateResponse(
        "snapshots.html",
        {
            "request": request,
            "client": client,
            "snapshots": snapshots,
            "has_active_connection": active_connection is not None,
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
        if _get_org_active_celonis_connection(session, client_id, current_actor.organization.id) is None:
            return _redirect_ui(
                f"/snapshots-ui/{client_id}",
                err="No active Celonis connection configured. Open Dashboard and save a Celonis connection for this client.",
            )
        token_row = _get_org_person_celonis_token(
            session,
            current_actor.organization.id,
            current_actor.person.id,
        )
        token_override = token_row.token_value.strip() if token_row and token_row.token_value else None
        run_kwargs: dict = {}
        if token_override:
            run_kwargs["token_override"] = token_override
        snap = run_snapshot(
            session,
            client_id=client_id,
            triggered_by=current_actor.person.id,
            organization_id=current_actor.organization.id,
            **run_kwargs,
        )
        return _redirect_ui(f"/snapshots-ui/{client_id}", ok=f"Snapshot {snap.id} completed")
    except Exception as exc:
        session.rollback()
        return _redirect_ui(f"/snapshots-ui/{client_id}", err=str(exc))


@router.get("/snapshots-ui/{client_id}/{snapshot_id}/detail")
def snapshot_detail_ui(
    client_id: UUID,
    snapshot_id: UUID,
    request: Request,
    tab: str = "tasks",
    compare_to: str | None = None,
    project_id: str | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    client = _get_org_client(session, client_id, current_actor.organization.id)
    if client is None:
        return _redirect_ui("/clients-ui", err="Client not found")
    snap = session.get(CelonisSnapshot, snapshot_id)
    if snap is None or snap.client_id != client_id:
        return _redirect_ui(f"/snapshots-ui/{client_id}", err="Snapshot not found")
    active_tab = "hierarchy" if tab in {"deep_packages", "hierarchy"} else tab
    tasks = session.exec(
        select(SnapshotTask).where(SnapshotTask.snapshot_id == snapshot_id)
    ).all()
    spaces = session.exec(
        select(SnapshotSpace).where(SnapshotSpace.snapshot_id == snapshot_id)
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
    task_details = session.exec(
        select(SnapshotTaskDetail).where(SnapshotTaskDetail.snapshot_id == snapshot_id)
    ).all()
    package_definitions = session.exec(
        select(SnapshotPackageDefinition).where(SnapshotPackageDefinition.snapshot_id == snapshot_id)
    ).all()

    baseline_snapshot: CelonisSnapshot | None = None
    baseline_packages: Sequence[SnapshotPackage] = []
    baseline_tasks: Sequence[SnapshotTask] = []
    baseline_data_models: Sequence[SnapshotDataModel] = []
    baseline_jobs: Sequence[SnapshotJob] = []
    baseline_knowledge_models: Sequence[SnapshotKnowledgeModel] = []

    if compare_to:
        try:
            baseline_snapshot_id = UUID(compare_to)
            candidate = session.get(CelonisSnapshot, baseline_snapshot_id)
            if candidate and candidate.client_id == client_id:
                baseline_snapshot = candidate
        except ValueError:
            baseline_snapshot = None

    if baseline_snapshot is None:
        baseline_candidates = session.exec(
            select(CelonisSnapshot).where(
                CelonisSnapshot.client_id == client_id,
                CelonisSnapshot.id != snapshot_id,
            )
        ).all()
        baseline_snapshot = (
            sorted(
                baseline_candidates,
                key=lambda row: _sort_datetime_key(row.created_at),
                reverse=True,
            )[0]
            if baseline_candidates
            else None
        )

    if baseline_snapshot is not None:
        baseline_packages = session.exec(
            select(SnapshotPackage).where(SnapshotPackage.snapshot_id == baseline_snapshot.id)
        ).all()
        baseline_tasks = session.exec(
            select(SnapshotTask).where(SnapshotTask.snapshot_id == baseline_snapshot.id)
        ).all()
        baseline_data_models = session.exec(
            select(SnapshotDataModel).where(SnapshotDataModel.snapshot_id == baseline_snapshot.id)
        ).all()
        baseline_jobs = session.exec(
            select(SnapshotJob).where(SnapshotJob.snapshot_id == baseline_snapshot.id)
        ).all()
        baseline_knowledge_models = session.exec(
            select(SnapshotKnowledgeModel).where(SnapshotKnowledgeModel.snapshot_id == baseline_snapshot.id)
        ).all()

    current_maps = _snapshot_entity_maps(
        packages=packages,
        tasks=tasks,
        data_models=data_models,
        jobs=jobs,
        knowledge_models=knowledge_models,
    )
    baseline_maps = _snapshot_entity_maps(
        packages=baseline_packages,
        tasks=baseline_tasks,
        data_models=baseline_data_models,
        jobs=baseline_jobs,
        knowledge_models=baseline_knowledge_models,
    )
    snapshot_diff = {
        "packages": _snapshot_family_diff(current_maps["packages"], baseline_maps["packages"]),
        "tasks": _snapshot_family_diff(current_maps["tasks"], baseline_maps["tasks"]),
        "data_models": _snapshot_family_diff(current_maps["data_models"], baseline_maps["data_models"]),
        "jobs": _snapshot_family_diff(current_maps["jobs"], baseline_maps["jobs"]),
        "knowledge_models": _snapshot_family_diff(
            current_maps["knowledge_models"], baseline_maps["knowledge_models"]
        ),
    }

    dependency_index = _snapshot_dependency_index(
        packages=packages,
        tasks=tasks,
        data_models=data_models,
        jobs=jobs,
        knowledge_models=knowledge_models,
    )

    package_tasks: dict[str, list[SnapshotTask]] = {}
    for task in tasks:
        package_tasks.setdefault(task.package_id or "", []).append(task)

    package_definition_map: dict[str, list[SnapshotPackageDefinition]] = {}
    for definition in package_definitions:
        package_definition_map.setdefault(definition.package_id, []).append(definition)

    package_rows: list[dict[str, object]] = []
    for package in sorted(packages, key=lambda row: ((row.name or "").lower(), row.package_id)):
        definition_rows = sorted(
            package_definition_map.get(package.package_id, []),
            key=lambda row: (row.source_endpoint or "", row.definition_id or ""),
        )
        package_rows.append(
            {
                "package": package,
                "asset_count": len(package_tasks.get(package.package_id, [])),
                "definition_count": len(definition_rows),
                "component_rows": _snapshot_component_rows(package.raw_json or {}, limit=30),
                "definition_rows": definition_rows,
            }
        )

    task_detail_by_task_id = {row.task_id: row for row in task_details}
    task_detail_rows: list[dict[str, object]] = []
    for task in sorted(tasks, key=lambda row: ((row.name or "").lower(), row.task_id)):
        detail = task_detail_by_task_id.get(task.task_id)
        references_json = detail.references_json if detail else {}
        reference_assets = references_json.get("assets") if isinstance(references_json, dict) else []
        reference_tables = references_json.get("tables") if isinstance(references_json, dict) else []
        reference_columns = references_json.get("columns") if isinstance(references_json, dict) else []
        task_detail_rows.append(
            {
                "task": task,
                "detail": detail,
                "reference_assets": reference_assets if isinstance(reference_assets, list) else [],
                "reference_tables": reference_tables if isinstance(reference_tables, list) else [],
                "reference_columns": reference_columns if isinstance(reference_columns, list) else [],
                "dependency_count": len(detail.dependencies_json) if detail else 0,
            }
        )

    hierarchy_spaces, hierarchy_asset_types = _snapshot_hierarchy_spaces(
        spaces=spaces,
        packages=packages,
        package_tasks=package_tasks,
        dependency_index=dependency_index,
    )

    deep_packages: list[dict[str, object]] = []
    for pkg in sorted(packages, key=lambda row: (row.name or "").lower()):
        pkg_task_rows = package_tasks.get(pkg.package_id, [])
        task_rows: list[dict[str, object]] = []
        for task in sorted(pkg_task_rows, key=lambda row: (row.name or "").lower()):
            refs = _snapshot_reference_ids(task.raw_json or {}, max_refs=40)
            linked_dependencies = [
                dependency_index[ref]
                for ref in refs
                if ref in dependency_index and ref not in {task.task_id, pkg.package_id}
            ]
            task_rows.append(
                {
                    "task": task,
                    "component_rows": _snapshot_component_rows(task.raw_json or {}, limit=30),
                    "refs": refs,
                    "linked_dependencies": linked_dependencies[:20],
                }
            )

        pkg_refs = _snapshot_reference_ids(pkg.raw_json or {}, max_refs=30)
        deep_packages.append(
            {
                "package": pkg,
                "component_rows": _snapshot_component_rows(pkg.raw_json or {}, limit=25),
                "refs": pkg_refs,
                "linked_dependencies": [
                    dependency_index[ref]
                    for ref in pkg_refs
                    if ref in dependency_index and ref != pkg.package_id
                ][:20],
                "tasks": task_rows,
            }
        )

    all_snapshots = session.exec(
        select(CelonisSnapshot).where(CelonisSnapshot.client_id == client_id)
    ).all()
    all_snapshots = sorted(
        all_snapshots,
        key=lambda row: _sort_datetime_key(row.created_at),
        reverse=True,
    )
    compare_candidates = [row for row in all_snapshots if row.id != snapshot_id]

    org_projects = _org_projects(session, current_actor.organization.id)
    client_projects = [row for row in org_projects if row.client_id == client.id]
    selected_project_id: UUID | None = None
    if project_id:
        try:
            parsed_project_id = UUID(project_id)
            selected_project = next((row for row in client_projects if row.id == parsed_project_id), None)
            if selected_project is not None:
                selected_project_id = selected_project.id
        except ValueError:
            selected_project_id = None
    if selected_project_id is None and client_projects:
        selected_project_id = client_projects[0].id

    ok_message = request.query_params.get("ok") if request else None
    error_message = request.query_params.get("err") if request else None
    return templates.TemplateResponse(
        "snapshot_detail.html",
        {
            "request": request,
            "client": client,
            "snap": snap,
            "spaces": spaces,
            "tasks": tasks,
            "task_details": task_details,
            "task_detail_rows": task_detail_rows,
            "packages": packages,
            "package_rows": package_rows,
            "data_models": data_models,
            "jobs": jobs,
            "knowledge_models": knowledge_models,
            "hierarchy_spaces": hierarchy_spaces,
            "hierarchy_asset_types": hierarchy_asset_types,
            "deep_packages": deep_packages,
            "snapshot_diff": snapshot_diff,
            "baseline_snapshot": baseline_snapshot,
            "compare_candidates": compare_candidates,
            "compare_to": str(baseline_snapshot.id) if baseline_snapshot else "",
            "client_projects": client_projects,
            "selected_project_id": str(selected_project_id) if selected_project_id else "",
            "active_tab": active_tab,
            "ok_message": ok_message,
            "error_message": error_message,
        },
    )


@router.post("/snapshots-ui/{client_id}/{snapshot_id}/create-app-asset", include_in_schema=False)
def snapshot_create_app_asset_ui(
    client_id: UUID,
    snapshot_id: UUID,
    source_kind: str = Form(...),
    source_id: str = Form(...),
    source_name: str = Form(...),
    project_id: str = Form(...),
    task_type: str = Form(""),
    component_path: str = Form(""),
    tab: str = Form("packages"),
    compare_to: str = Form(""),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    detail_path = _with_query_params(
        f"/snapshots-ui/{client_id}/{snapshot_id}/detail",
        tab=tab or "packages",
        compare_to=compare_to or None,
        project_id=project_id,
    )

    client = _get_org_client(session, client_id, current_actor.organization.id)
    if client is None:
        return _redirect_ui("/clients-ui", err="Client not found")

    try:
        parsed_project_id = _parse_uuid(project_id, "project_id")
        project = _get_org_project(session, parsed_project_id, current_actor.organization.id)
        if project is None:
            return _redirect_ui(detail_path, err="Project not found")
        if project.client_id != client.id:
            return _redirect_ui(detail_path, err="Project does not belong to this client")

        packages = session.exec(
            select(SnapshotPackage).where(SnapshotPackage.snapshot_id == snapshot_id)
        ).all()
        tasks = session.exec(
            select(SnapshotTask).where(SnapshotTask.snapshot_id == snapshot_id)
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
        dependency_index = _snapshot_dependency_index(
            packages=packages,
            tasks=tasks,
            data_models=data_models,
            jobs=jobs,
            knowledge_models=knowledge_models,
        )

        source_payload: dict[str, object] | None = None
        normalized_kind = source_kind.strip().lower()
        normalized_id = source_id.strip()
        name_value = source_name.strip() or normalized_id

        if normalized_kind == "package":
            row = next((item for item in packages if item.package_id == normalized_id), None)
            if row is None:
                return _redirect_ui(detail_path, err="Package not found in snapshot")
            source_payload = {
                "id": row.package_id,
                "family": "package",
                "name": row.name,
                "raw_json": row.raw_json or {},
                "task_type": None,
            }
        elif normalized_kind == "task":
            row = next((item for item in tasks if item.task_id == normalized_id), None)
            if row is None:
                return _redirect_ui(detail_path, err="Task not found in snapshot")
            source_payload = {
                "id": row.task_id,
                "family": "task",
                "name": row.name,
                "raw_json": row.raw_json or {},
                "task_type": row.task_type,
            }
        elif normalized_kind == "component":
            row = next((item for item in tasks if item.task_id == normalized_id), None)
            if row is None:
                return _redirect_ui(detail_path, err="Task not found for component source")
            if not component_path:
                return _redirect_ui(detail_path, err="Component path is missing")
            component_value = _snapshot_path_lookup(row.raw_json or {}, component_path)
            source_payload = {
                "id": f"{row.task_id}:{component_path}",
                "family": "component",
                "name": f"{row.name} :: {component_path}",
                "raw_json": component_value,
                "task_type": row.task_type,
            }
            if component_value is None:
                return _redirect_ui(detail_path, err="Component path no longer exists")
        else:
            return _redirect_ui(detail_path, err="Unsupported source type")

        primary_asset_type = _asset_type_for_family(
            str(source_payload["family"]),
            task_type=(task_type or str(source_payload.get("task_type") or "")),
        )
        source_entity_id = str(source_payload["id"])
        identifier = f"snapshot:{snapshot_id}:{normalized_kind}:{source_entity_id}"

        existing_assets = [
            row
            for row in _org_assets(session, current_actor.organization.id)
            if row.project_id == parsed_project_id
        ]
        existing_identifiers = {row.asset_identifier: row for row in existing_assets if row.asset_identifier}

        created_asset: Asset
        if identifier in existing_identifiers:
            created_asset = existing_identifiers[identifier]
        else:
            created_asset = Asset(
                organization_id=current_actor.organization.id,
                project_id=parsed_project_id,
                client_id=client.id,
                type=primary_asset_type,
                name=name_value,
                status=AssetStatus.draft,
                asset_identifier=identifier,
            )
            session.add(created_asset)
            session.flush()

        source_refs = _snapshot_reference_ids(source_payload.get("raw_json", {}), max_refs=80)
        dependencies = _crawl_snapshot_dependencies(
            seed_refs=source_refs,
            index=dependency_index,
            skip_ids={source_entity_id},
            max_nodes=40,
        )

        dependency_created = 0
        for dependency in dependencies:
            dep_id = str(dependency["id"])
            dep_identifier = f"snapshot:{snapshot_id}:{dependency['family']}:{dep_id}"
            if dep_identifier in existing_identifiers:
                continue
            dep_type = _asset_type_for_family(
                str(dependency.get("family") or "other"),
                task_type=str(dependency.get("task_type") or ""),
            )
            dep_asset = Asset(
                organization_id=current_actor.organization.id,
                project_id=parsed_project_id,
                client_id=client.id,
                type=dep_type,
                name=f"Dependency: {dependency.get('name') or dep_id}",
                status=AssetStatus.draft,
                asset_identifier=dep_identifier,
            )
            session.add(dep_asset)
            existing_identifiers[dep_identifier] = dep_asset
            dependency_created += 1

        session.commit()

        log_created(
            session,
            entity_type=EntityType.asset,
            entity_id=created_asset.id,
            actor_id=current_actor.person.id,
            organization_id=current_actor.organization.id,
            metadata={
                "type": created_asset.type.value,
                "project_id": str(created_asset.project_id),
                "client_id": str(created_asset.client_id),
                "snapshot_id": str(snapshot_id),
                "source_kind": normalized_kind,
                "source_id": source_entity_id,
                "dependency_count": len(dependencies),
                "dependency_assets_created": dependency_created,
            },
        )

        created_msg = (
            f"App asset '{created_asset.name}' created with {dependency_created} dependency assets"
            if identifier not in {row.asset_identifier for row in existing_assets if row.asset_identifier}
            else f"App asset '{created_asset.name}' already exists; linked {dependency_created} new dependency assets"
        )
        return _redirect_ui(detail_path, ok=created_msg)
    except Exception as exc:
        session.rollback()
        return _redirect_ui(detail_path, err=f"Create app asset failed: {exc}")


@router.post("/snapshots-ui/{client_id}/{snapshot_id}/export")
def snapshot_export_ui(
    client_id: UUID,
    snapshot_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    wants_json = _wants_json_response(request)
    try:
        client = _get_org_client(session, client_id, current_actor.organization.id)
        snap = session.get(CelonisSnapshot, snapshot_id)
        if client is None or snap is None or snap.client_id != client_id:
            if wants_json:
                return JSONResponse({"ok": False, "error": "Snapshot not found"}, status_code=404)
            return _redirect_ui(f"/snapshots-ui/{client_id}", err="Snapshot not found")
        settings = get_settings()
        output_dir = getattr(settings, "generated_dir", settings.uploads_dir)
        result = build_snapshot_export(
            session,
            snapshot_id=snapshot_id,
            base_output_dir=Path(output_dir) / "snapshot_exports",
        )
        if wants_json:
            return {
                "ok": True,
                "snapshot_id": str(snapshot_id),
                "message": f"Export bundle created: {result['bundle_path']}",
                "result": result,
            }
        return _redirect_ui(
            f"/snapshots-ui/{client_id}/{snapshot_id}/detail",
            ok=f"Export bundle created: {result['bundle_path']}",
        )
    except Exception as exc:
        if wants_json:
            return JSONResponse(
                {
                    "ok": False,
                    "snapshot_id": str(snapshot_id),
                    "error": f"Export failed: {exc}",
                },
                status_code=500,
            )
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
        settings = get_settings()
        output_dir = getattr(settings, "generated_dir", settings.uploads_dir)
        result = build_snapshot_export(
            session,
            snapshot_id=snapshot_id,
            base_output_dir=Path(output_dir) / "snapshot_exports",
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


@router.get("/snapshots-ui/{client_id}/{snapshot_id}/coverage")
def snapshot_coverage_ui(
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
    return build_snapshot_coverage_report(snap)


@router.get("/snapshots-ui/{client_id}/{snapshot_id}/coverage/download")
def snapshot_coverage_download_ui(
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
    payload = build_snapshot_coverage_report(snap)
    filename = build_snapshot_coverage_filename(snapshot_id)
    return Response(
        content=json.dumps(payload, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Tool Hub UI
# ---------------------------------------------------------------------------

@router.get("/celonis-tool-hub-ui")
def tool_hub_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    """Display tool hub catalog with status and controls."""
    import json
    
    try:
        catalog_path = Path(get_settings().uploads_dir).parent / ".orchestration/tool-hub/catalog.json"
        tools = []
        generated_at = None
        tool_count = 0
        
        if catalog_path.exists():
            catalog_data = json.loads(catalog_path.read_text())
            tools = catalog_data.get("tools", [])
            generated_at = catalog_data.get("generated_at_utc", "Unknown")
            tool_count = len(tools)
        
        ok_message = request.query_params.get("ok")
        error_message = request.query_params.get("err")
        
        return templates.TemplateResponse(
            "celonis-tool-hub-ui.html",
            {
                "request": request,
                "tools": tools,
                "tool_count": tool_count,
                "generated_at": generated_at,
                "ok_message": ok_message,
                "error_message": error_message,
            },
        )
    except Exception as exc:
        error_message = f"Error loading tool hub catalog: {str(exc)}"
        return templates.TemplateResponse(
            "celonis-tool-hub-ui.html",
            {
                "request": request,
                "tools": [],
                "tool_count": 0,
                "generated_at": None,
                "ok_message": None,
                "error_message": error_message,
            },
        )


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
