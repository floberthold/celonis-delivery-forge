from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import (
    Client,
    LibraryType,
    OrganizationMembership,
    Person,
    Project,
    Template,
    TemplateInstantiation,
    TemplateLibrary,
    TemplateScope,
    TemplateStorageType,
)

router = APIRouter(tags=["ui"])

_UI_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "ui" / "templates"
_templates = Jinja2Templates(directory=str(_UI_TEMPLATE_DIR))


def _sort_datetime_key(value):
    if value is None:
        return float("-inf")
    return value.timestamp()


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


def _org_clients(session: Session, organization_id: UUID) -> list[Client]:
    return list(session.exec(select(Client).where(Client.organization_id == organization_id)).all())


def _org_projects(session: Session, organization_id: UUID) -> list[Project]:
    return list(session.exec(select(Project).where(Project.organization_id == organization_id)).all())


def _org_people(session: Session, organization_id: UUID) -> list[Person]:
    membership_rows = list(
        session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id
            )
        ).all()
    )
    if not membership_rows:
        return []
    person_ids = {membership.person_id for membership in membership_rows}
    return [
        row
        for row in session.exec(select(Person)).all()
        if row.id in person_ids
    ]


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

    return _templates.TemplateResponse(request, "templates.html",
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

