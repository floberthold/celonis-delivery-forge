from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import Client, EntityType
from foundry.schemas import ClientCreate
from foundry.services.activity_log import log_created

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/", response_model=Client)
def create_client(
    payload: ClientCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    client = Client(
        organization_id=current_actor.organization.id,
        **payload.model_dump(),
    )
    session.add(client)
    session.commit()
    session.refresh(client)
    log_created(
        session,
        entity_type=EntityType.client,
        entity_id=client.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"name": client.name, "sensitivity_level": client.sensitivity_level.value},
    )
    return client


@router.get("/", response_model=list[Client])
def list_clients(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    stmt = select(Client).where(Client.organization_id == current_actor.organization.id)
    return list(session.exec(stmt).all())
