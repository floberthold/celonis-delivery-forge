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


def log_created(
    session: Session,
    *,
    entity_type: EntityType,
    entity_id: UUID,
    actor_id: UUID,
    metadata: dict | None = None,
) -> ActivityLog:
    return log_activity(
        session,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        action=f"{entity_type.value}.created",
        metadata=metadata,
    )


def log_updated(
    session: Session,
    *,
    entity_type: EntityType,
    entity_id: UUID,
    actor_id: UUID,
    metadata: dict | None = None,
) -> ActivityLog:
    return log_activity(
        session,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        action=f"{entity_type.value}.updated",
        metadata=metadata,
    )
