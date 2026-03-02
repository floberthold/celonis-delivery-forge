from uuid import UUID

from sqlmodel import Session

from foundry.models import ActivityLog, EntityType


def log_activity(
    session: Session,
    *,
    entity_type: EntityType,
    entity_id: UUID,
    actor_id: UUID,
    action: str,
    metadata: dict | None = None,
) -> ActivityLog:
    event = ActivityLog(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        action=action,
        metadata_json=metadata or {},
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
