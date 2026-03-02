from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import Person
from foundry.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/token")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    person = session.exec(select(Person).where(Person.email == payload.email)).first()
    if not person or not verify_password(payload.password, person.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(person.id))
    return {"access_token": token, "token_type": "bearer"}
