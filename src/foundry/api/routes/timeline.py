from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import ActivityLog, EntityType

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/")
def list_timeline(
    entity_type: EntityType | None = None,
    entity_id: UUID | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    stmt = select(ActivityLog).where(ActivityLog.organization_id == current_actor.organization.id)
    if entity_type:
        stmt = stmt.where(ActivityLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(ActivityLog.entity_id == entity_id)
    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.timestamp, reverse=True)
    return rows
