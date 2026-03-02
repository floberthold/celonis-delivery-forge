from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import ReviewComment, ReviewRequest
from foundry.schemas import ReviewCommentCreate, ReviewDecisionCreate, ReviewRequestCreate, ReviewRequestOut
from foundry.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/submit", response_model=ReviewRequestOut)
def submit_review(payload: ReviewRequestCreate, session: Session = Depends(get_session)):
    return ReviewService.submit_for_review(session, payload)


@router.post("/decision", response_model=ReviewRequestOut)
def decide_review(payload: ReviewDecisionCreate, session: Session = Depends(get_session)):
    return ReviewService.decide_review(session, payload)


@router.post("/comment", response_model=ReviewComment)
def add_comment(payload: ReviewCommentCreate, session: Session = Depends(get_session)):
    comment = ReviewComment(
        review_request_id=payload.review_id,
        author_id=payload.author_id,
        content=payload.content,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


@router.get("/", response_model=list[ReviewRequestOut])
def list_reviews(session: Session = Depends(get_session)):
    return list(session.exec(select(ReviewRequest)).all())
