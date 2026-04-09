from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from uuid import UUID

from foundry.db import get_session
from foundry.models import EntityType, OrganizationMembership, Person
from foundry.security import create_access_token, verify_password
from foundry.services.activity_log import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    organization_id: UUID | None = None


@router.post("/token")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    person = session.exec(select(Person).where(Person.email == payload.email)).first()
    if not person:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, person.hashed_password):
        log_activity(
            session,
            entity_type=EntityType.person,
            entity_id=person.id,
            actor_id=person.id,
            action="auth.login.failed",
            metadata={"email": person.email},
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    log_activity(
        session,
        entity_type=EntityType.person,
        entity_id=person.id,
        actor_id=person.id,
        action="auth.login.success",
        metadata={"email": person.email},
    )

    memberships = list(
        session.exec(
            select(OrganizationMembership).where(OrganizationMembership.person_id == person.id)
        ).all()
    )
    membership_by_org = {membership.organization_id: membership for membership in memberships}

    selected_organization_id: UUID | None = None
    if payload.organization_id is not None:
        if payload.organization_id not in membership_by_org:
            raise HTTPException(
                status_code=403,
                detail="You are not a member of the requested organization",
            )
        selected_organization_id = payload.organization_id
    elif len(memberships) == 1:
        selected_organization_id = memberships[0].organization_id
    elif len(memberships) > 1:
        raise HTTPException(
            status_code=400,
            detail="organization_id is required because your account belongs to multiple organizations",
        )

    token = create_access_token(
        str(person.id),
        organization_id=str(selected_organization_id) if selected_organization_id else None,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "organization_id": selected_organization_id,
    }
