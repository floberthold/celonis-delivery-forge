from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import get_current_person
from foundry.db import get_session
from foundry.models import EntityType, Person, ReviewComment, ReviewRequest
from foundry.schemas import ReviewCommentCreate, ReviewDecisionCreate, ReviewRequestCreate, ReviewRequestOut
from foundry.services.activity_log import log_updated
from foundry.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/submit", response_model=ReviewRequestOut)
def submit_review(
    payload: ReviewRequestCreate,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    if payload.author_id != current_person.id:
        raise HTTPException(status_code=403, detail="author_id must match authenticated user")
    return ReviewService.submit_for_review(session, payload)


@router.post("/decision", response_model=ReviewRequestOut)
def decide_review(
    payload: ReviewDecisionCreate,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    if payload.reviewer_id != current_person.id:
        raise HTTPException(status_code=403, detail="reviewer_id must match authenticated user")
    return ReviewService.decide_review(session, payload)


@router.post("/comment", response_model=ReviewComment)
def add_comment(
    payload: ReviewCommentCreate,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    if payload.author_id != current_person.id:
        raise HTTPException(status_code=403, detail="author_id must match authenticated user")

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
        actor_id=current_person.id,
        metadata={"comment_id": str(comment.id)},
    )

    return comment


@router.get("/", response_model=list[ReviewRequestOut])
def list_reviews(session: Session = Depends(get_session)):
    return list(session.exec(select(ReviewRequest)).all())
