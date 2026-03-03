from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import EntityType, Person
from foundry.security import create_access_token, verify_password
from foundry.services.activity_log import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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

    token = create_access_token(str(person.id))
    return {"access_token": token, "token_type": "bearer"}
