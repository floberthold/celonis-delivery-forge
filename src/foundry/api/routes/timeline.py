from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import ActivityLog

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/")
def list_timeline(entity_id: UUID | None = None, session: Session = Depends(get_session)):
    stmt = select(ActivityLog)
    if entity_id:
        stmt = stmt.where(ActivityLog.entity_id == entity_id)
    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.timestamp, reverse=True)
    return rows
