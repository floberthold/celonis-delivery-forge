from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import Person
from foundry.schemas import UserCreate
from foundry.security import hash_password

router = APIRouter(prefix="/people", tags=["people"])


@router.post("/", response_model=Person)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    person = Person(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


@router.get("/", response_model=list[Person])
def list_users(session: Session = Depends(get_session)):
    return list(session.exec(select(Person)).all())
