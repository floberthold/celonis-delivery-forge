import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.integrations.celonis_import import CelonisGateway
from foundry.models import (
    ActivityLog,
    Asset,
    AssetType,
    CelonisConnection,
    Client,
    DecisionType,
    GlobalRole,
    MembershipRole,
    Person,
    Project,
    ProjectMembership,
    ProjectStatus,
    ReviewRequest,
    SensitivityLevel,
)
from foundry.schemas import ReviewDecisionCreate, ReviewRequestCreate
from foundry.settings import get_settings
from foundry.security import hash_password
from foundry.services.review_service import ReviewService

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "ui" / "templates"))


def _redirect_dashboard(*, ok: str | None = None, err: str | None = None) -> RedirectResponse:
    if ok:
        return RedirectResponse(url=f"/dashboard?ok={quote_plus(ok)}", status_code=303)
    if err:
        return RedirectResponse(url=f"/dashboard?err={quote_plus(err)}", status_code=303)
    return RedirectResponse(url="/dashboard", status_code=303)


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError(f"Invalid UUID for {field_name}") from exc


def _dashboard_context(request: Request, session: Session) -> dict:
    clients = list(session.exec(select(Client).order_by(Client.created_at.desc())).all())
    projects = list(session.exec(select(Project).order_by(Project.created_at.desc())).all())
    assets = list(session.exec(select(Asset).order_by(Asset.created_at.desc())).all())
    reviews = list(session.exec(select(ReviewRequest).order_by(ReviewRequest.created_at.desc())).all())
    timeline = list(session.exec(select(ActivityLog).order_by(ActivityLog.timestamp.desc())).all())
    people = list(session.exec(select(Person).order_by(Person.created_at.desc())).all())
    memberships = list(session.exec(select(ProjectMembership)).all())
    celonis_connections = list(
        session.exec(select(CelonisConnection).order_by(CelonisConnection.updated_at.desc())).all()
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


@router.get("/dashboard")
def dashboard(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse("dashboard.html", _dashboard_context(request, session))


@router.post("/dashboard/create-client", include_in_schema=False)
def dashboard_create_client(
    name: str = Form(...),
    tenant_url: str = Form(...),
    sensitivity_level: str = Form("medium"),
    session: Session = Depends(get_session),
):
    try:
        client = Client(
            name=name.strip(),
            tenant_url=tenant_url.strip(),
            sensitivity_level=SensitivityLevel(sensitivity_level),
        )
        session.add(client)
        session.commit()
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
):
    try:
        project = Project(
            name=name.strip(),
            client_id=_parse_uuid(client_id, "client_id"),
            status=ProjectStatus(status),
        )
        session.add(project)
        session.commit()
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
):
    try:
        membership = ProjectMembership(
            project_id=_parse_uuid(project_id, "project_id"),
            person_id=_parse_uuid(person_id, "person_id"),
            role=MembershipRole(role),
        )
        session.add(membership)
        session.commit()
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
):
    try:
        payload = ReviewRequestCreate(
            asset_id=_parse_uuid(asset_id, "asset_id"),
            project_id=_parse_uuid(project_id, "project_id"),
            author_id=_parse_uuid(author_id, "author_id"),
            reviewer_id=_parse_uuid(reviewer_id, "reviewer_id"),
            change_summary=change_summary.strip(),
        )
        ReviewService.submit_for_review(session, payload)
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
):
    try:
        payload = ReviewDecisionCreate(
            review_id=_parse_uuid(review_id, "review_id"),
            reviewer_id=_parse_uuid(reviewer_id, "reviewer_id"),
            decision=DecisionType(decision),
            note=note.strip() or None,
            snippet_worthy=snippet_worthy is not None,
        )
        ReviewService.decide_review(session, payload)
        return _redirect_dashboard(ok="Review decision applied")
    except Exception as exc:
        session.rollback()
        return _redirect_dashboard(err=f"Review decision failed: {exc}")


@router.post("/dashboard/celonis-connection", include_in_schema=False)
def dashboard_celonis_connection(
    client_id: str = Form(...),
    tenant_base_url: str = Form(...),
    session: Session = Depends(get_session),
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
            return _redirect_dashboard(ok="Celonis connection updated")

        row = CelonisConnection(client_id=parsed_client_id, tenant_base_url=tenant_base_url.strip())
        session.add(row)
        session.commit()
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
    projects = list(session.exec(select(Project).order_by(Project.created_at.desc())).all())
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
            "rows": rows,
        },
    )


@router.get("/assets-ui")
def assets_ui(request: Request, session: Session = Depends(get_session)):
    assets = list(session.exec(select(Asset).order_by(Asset.created_at.desc())).all())
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
            "rows": rows,
        },
    )


@router.get("/reviews-ui")
def reviews_ui(request: Request, session: Session = Depends(get_session)):
    reviews = list(session.exec(select(ReviewRequest).order_by(ReviewRequest.created_at.desc())).all())
    assets = list(session.exec(select(Asset)).all())
    people = list(session.exec(select(Person)).all())

    asset_name_by_id = {asset.id: asset.name for asset in assets}
    person_name_by_id = {person.id: person.name for person in people}

    rows = [
        {
            "id": review.id,
            "asset_name": asset_name_by_id.get(review.asset_id, "Unknown"),
            "author_name": person_name_by_id.get(review.author_id, "Unknown"),
            "reviewer_name": person_name_by_id.get(review.reviewer_id, "Unknown"),
            "status": review.status.value,
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
            "rows": rows,
        },
    )


@router.get("/timeline-ui")
def timeline_ui(request: Request, session: Session = Depends(get_session)):
    rows = list(session.exec(select(ActivityLog).order_by(ActivityLog.timestamp.desc())).all())

    return templates.TemplateResponse(
        "timeline.html",
        {
            "request": request,
            "rows": rows,
        },
    )


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