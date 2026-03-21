from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor, get_current_person
from foundry.db import get_session
from foundry.models import (
    EntityType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
)
from foundry.schemas import OrganizationCreate, OrganizationOut
from foundry.services.activity_log import log_created
from foundry.services.template_seed import seed_default_templates

router = APIRouter(prefix="/orgs", tags=["orgs"])


def _normalize_slug(value: str) -> str:
    return value.strip().lower()


@router.post("/", response_model=OrganizationOut)
def create_organization(
    payload: OrganizationCreate,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    normalized_slug = _normalize_slug(payload.slug)
    if not normalized_slug:
        raise HTTPException(status_code=400, detail="slug cannot be empty")

    existing = session.exec(
        select(Organization).where(func.lower(Organization.slug) == normalized_slug)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Organization slug already exists")

    organization = Organization(name=payload.name.strip(), slug=normalized_slug)
    membership = OrganizationMembership(
        organization_id=organization.id,
        person_id=current_person.id,
        role=OrganizationRole.owner,
    )

    session.add(organization)
    session.add(membership)
    session.commit()
    session.refresh(organization)

    seed_default_templates(session, organization_id=organization.id)

    log_created(
        session,
        entity_type=EntityType.organization,
        entity_id=organization.id,
        actor_id=current_person.id,
        organization_id=organization.id,
        metadata={"name": organization.name, "slug": organization.slug},
    )
    return organization


@router.get("/mine", response_model=list[OrganizationOut])
def list_my_organizations(
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    memberships = list(
        session.exec(
            select(OrganizationMembership).where(OrganizationMembership.person_id == current_person.id)
        ).all()
    )
    organizations: list[Organization] = []
    for membership in memberships:
        organization = session.get(Organization, membership.organization_id)
        if organization:
            organizations.append(organization)
    organizations.sort(key=lambda row: row.created_at, reverse=True)
    return organizations


@router.get("/active", response_model=OrganizationOut)
def get_active_organization(current_actor: CurrentActor = Depends(get_current_actor)):
    if not current_actor.organization:
        raise HTTPException(status_code=404, detail="No active organization selected")
    return current_actor.organization
