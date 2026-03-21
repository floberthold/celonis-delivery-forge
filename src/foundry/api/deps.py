from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import Organization, OrganizationMembership, Person
from foundry.settings import get_settings

AUTH_COOKIE_NAME = "foundry_access_token"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


@dataclass
class CurrentActor:
    person: Person
    organization: Organization | None
    membership: OrganizationMembership | None


def _resolve_actor_from_token(*, token: str, session: Session) -> CurrentActor:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        token_org_id = payload.get("org_id")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    try:
        person_id = UUID(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found",
        )

    if token_org_id is None:
        return CurrentActor(person=person, organization=None, membership=None)

    try:
        organization_id = UUID(token_org_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    organization = session.get(Organization, organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated organization not found",
        )

    membership = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.person_id == person.id,
        )
    ).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated membership not found",
        )

    return CurrentActor(person=person, organization=organization, membership=membership)


def get_current_actor(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> CurrentActor:
    effective_token = token or request.cookies.get(AUTH_COOKIE_NAME)
    if not effective_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return _resolve_actor_from_token(token=effective_token, session=session)


def get_current_actor_with_org(
    current_actor: CurrentActor = Depends(get_current_actor),
) -> CurrentActor:
    if current_actor.organization is None or current_actor.membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active organization required for this operation",
        )
    return current_actor


def get_current_person(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Person:
    return get_current_actor(request=request, token=token, session=session).person


def get_current_person_optional(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Person | None:
    effective_token = token or request.cookies.get(AUTH_COOKIE_NAME)
    if not effective_token:
        return None
    try:
        return _resolve_actor_from_token(token=effective_token, session=session).person
    except HTTPException:
        return None
