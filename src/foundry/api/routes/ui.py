from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import ActivityLog, Asset, Client, Person, Project, ProjectMembership, ReviewRequest

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "ui" / "templates"))


@router.get("/")
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=307)


@router.get("/dashboard")
def dashboard(request: Request, session: Session = Depends(get_session)):
    clients = list(session.exec(select(Client).order_by(Client.created_at.desc())).all())
    projects = list(session.exec(select(Project).order_by(Project.created_at.desc())).all())
    assets = list(session.exec(select(Asset).order_by(Asset.created_at.desc())).all())
    reviews = list(session.exec(select(ReviewRequest).order_by(ReviewRequest.created_at.desc())).all())
    timeline = list(session.exec(select(ActivityLog).order_by(ActivityLog.timestamp.desc())).all())

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
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
        },
    )


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