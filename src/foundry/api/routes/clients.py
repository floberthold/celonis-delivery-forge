from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from foundry.api.deps import get_current_person
from foundry.db import get_session
from foundry.models import Client, EntityType, Person
from foundry.schemas import ClientCreate
from foundry.services.activity_log import log_created

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/", response_model=Client)
def create_client(
    payload: ClientCreate,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    client = Client(**payload.model_dump())
    session.add(client)
    session.commit()
    session.refresh(client)
    log_created(
        session,
        entity_type=EntityType.client,
        entity_id=client.id,
        actor_id=current_person.id,
        metadata={"name": client.name, "sensitivity_level": client.sensitivity_level.value},
    )
    return client


@router.get("/", response_model=list[Client])
def list_clients(session: Session = Depends(get_session)):
    return list(session.exec(select(Client)).all())
