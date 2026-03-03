from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import get_current_person
from foundry.db import get_session
from foundry.models import EntityType, Person
from foundry.schemas import UserCreate
from foundry.security import hash_password, validate_password_length
from foundry.services.activity_log import log_created

router = APIRouter(prefix="/people", tags=["people"])


@router.post("/", response_model=Person)
def create_user(
    payload: UserCreate,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    try:
        validate_password_length(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    person = Person(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
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
    return person


@router.get("/", response_model=list[Person])
def list_users(session: Session = Depends(get_session)):
    return list(session.exec(select(Person)).all())
