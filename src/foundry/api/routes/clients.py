from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import Client
from foundry.schemas import ClientCreate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/", response_model=Client)
def create_client(payload: ClientCreate, session: Session = Depends(get_session)):
    client = Client(**payload.model_dump())
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.get("/", response_model=list[Client])
def list_clients(session: Session = Depends(get_session)):
    return list(session.exec(select(Client)).all())
