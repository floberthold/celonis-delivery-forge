from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import EntityType, ForumInsight, ForumInsightStatus
from foundry.schemas import ForumInsightCreate, ForumInsightOut, ForumInsightUpdate
from foundry.services.activity_log import log_activity

router = APIRouter(prefix="/forum-insights", tags=["forum-insights"])


def _forum_insight_metadata(insight: ForumInsight) -> dict:
    return {
        "topic": insight.topic,
        "source_url": insight.source_url,
        "thread_title": insight.thread_title,
        "status": insight.status.value,
        "impact_score": insight.impact_score,
        "confidence_score": insight.confidence_score,
        "owner_id": str(insight.owner_id) if insight.owner_id else None,
        "reviewer_id": str(insight.reviewer_id) if insight.reviewer_id else None,
        "target_week": insight.target_week,
    }


@router.post("/", response_model=ForumInsightOut)
def create_forum_insight(payload: ForumInsightCreate, session: Session = Depends(get_session)):
    insight = ForumInsight(**payload.model_dump())
    session.add(insight)
    session.commit()
    session.refresh(insight)

    log_activity(
        session,
        entity_type=EntityType.forum_insight,
        entity_id=insight.id,
        actor_id=payload.created_by,
        action="forum_insight.created",
        metadata=_forum_insight_metadata(insight),
    )
    return insight


@router.get("/", response_model=list[ForumInsightOut])
def list_forum_insights(
    topic: str | None = None,
    status: ForumInsightStatus | None = None,
    owner_id: UUID | None = None,
    reviewer_id: UUID | None = None,
    target_week: str | None = None,
    session: Session = Depends(get_session),
):
    stmt = select(ForumInsight)
    if topic:
        stmt = stmt.where(ForumInsight.topic == topic)
    if status:
        stmt = stmt.where(ForumInsight.status == status)
    if owner_id:
        stmt = stmt.where(ForumInsight.owner_id == owner_id)
    if reviewer_id:
        stmt = stmt.where(ForumInsight.reviewer_id == reviewer_id)
    if target_week:
        stmt = stmt.where(ForumInsight.target_week == target_week)

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.created_at, reverse=True)
    return rows


@router.patch("/{insight_id}", response_model=ForumInsightOut)
def update_forum_insight(insight_id: UUID, payload: ForumInsightUpdate, session: Session = Depends(get_session)):
    insight = session.get(ForumInsight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Forum insight not found")

    updates = payload.model_dump(exclude_unset=True)
    actor_id = updates.pop("actor_id")
    changed_fields = sorted(updates.keys())
    for field_name, field_value in updates.items():
        setattr(insight, field_name, field_value)

    insight.updated_at = datetime.utcnow()
    session.add(insight)
    session.commit()
    session.refresh(insight)

    log_activity(
        session,
        entity_type=EntityType.forum_insight,
        entity_id=insight.id,
        actor_id=actor_id,
        action="forum_insight.updated",
        metadata={
            **_forum_insight_metadata(insight),
            "changed_fields": changed_fields,
        },
    )
    return insight
