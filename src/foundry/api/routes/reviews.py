from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import EntityType, Project, ReviewComment, ReviewRequest
from foundry.schemas import ReviewCommentCreate, ReviewDecisionCreate, ReviewRequestCreate, ReviewRequestOut
from foundry.services.activity_log import log_updated
from foundry.services.delivery.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/submit", response_model=ReviewRequestOut)
def submit_review(
    payload: ReviewRequestCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if payload.author_id != current_actor.person.id:
        raise HTTPException(status_code=403, detail="author_id must match authenticated user")
    return ReviewService.submit_for_review(
        session,
        payload,
        organization_id=current_actor.organization.id,
    )


@router.post("/decision", response_model=ReviewRequestOut)
def decide_review(
    payload: ReviewDecisionCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if payload.reviewer_id != current_actor.person.id:
        raise HTTPException(status_code=403, detail="reviewer_id must match authenticated user")
    return ReviewService.decide_review(
        session,
        payload,
        organization_id=current_actor.organization.id,
    )


@router.post("/comment", response_model=ReviewComment)
def add_comment(
    payload: ReviewCommentCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if payload.author_id != current_actor.person.id:
        raise HTTPException(status_code=403, detail="author_id must match authenticated user")

    review = session.get(ReviewRequest, payload.review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review request not found")

    project = session.get(Project, review.project_id)
    if not project or project.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=404, detail="Review request not found")

    comment = ReviewComment(
        review_request_id=payload.review_id,
        author_id=payload.author_id,
        content=payload.content,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)

    log_updated(
        session,
        entity_type=EntityType.review,
        entity_id=payload.review_id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"comment_id": str(comment.id)},
    )

    return comment


@router.get("/", response_model=list[ReviewRequestOut])
def list_reviews(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    projects = {
        project.id
        for project in session.exec(
            select(Project).where(Project.organization_id == current_actor.organization.id)
        ).all()
    }
    if not projects:
        return []

    rows = list(
        session.exec(select(ReviewRequest).where(ReviewRequest.project_id.in_(projects))).all()
    )
    return [row for row in rows if row.project_id in projects]
