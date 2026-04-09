from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import EntityType, OrganizationMembership, OrganizationRole, Person
from foundry.schemas import UserCreate
from foundry.security import hash_password, validate_password_length
from foundry.services.activity_log import log_created

router = APIRouter(prefix="/people", tags=["people"])


def _org_people(session: Session, organization_id):
    memberships = list(
        session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id
            )
        ).all()
    )
    if not memberships:
        return []
    person_ids = [row.person_id for row in memberships]
    return list(session.exec(select(Person).where(Person.id.in_(person_ids))).all())


def _get_org_membership(session: Session, organization_id, person_id):
    return session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.person_id == person_id,
        )
    ).first()


@router.post("/", response_model=Person)
def create_user(
    payload: UserCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        validate_password_length(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    person = session.exec(select(Person).where(Person.email == payload.email.lower())).first()
    created = False
    if person is None:
        person = Person(
            email=payload.email.lower(),
            name=payload.name,
            hashed_password=hash_password(payload.password),
        )
        session.add(person)
        session.commit()
        session.refresh(person)
        created = True

    membership = _get_org_membership(session, current_actor.organization.id, person.id)
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
    if not created:
        session.refresh(person)
    return person


@router.get("/", response_model=list[Person])
def list_users(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    people = _org_people(session, current_actor.organization.id)
    people.sort(key=lambda row: row.created_at, reverse=True)
    return people
