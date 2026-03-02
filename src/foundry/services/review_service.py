from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from foundry.models import (
    Asset,
    AssetStatus,
    DecisionType,
    EntityType,
    ProjectMembership,
    ReviewDecision,
    ReviewRequest,
    ReviewStatus,
)
from foundry.schemas import ReviewDecisionCreate, ReviewRequestCreate
from foundry.services.activity_log import log_activity


class ReviewService:
    @staticmethod
    def _ensure_dual_control(session: Session, review: ReviewRequest) -> None:
        if review.author_id == review.reviewer_id:
            raise HTTPException(status_code=400, detail="Author and reviewer must be different users")

        assignments = session.exec(
            select(ProjectMembership).where(ProjectMembership.project_id == review.project_id)
        ).all()
        active_assignments = [
            assignment
            for assignment in assignments
            if assignment.end_date is None or assignment.end_date >= datetime.utcnow()
        ]
        if len(active_assignments) < 2:
            raise HTTPException(
                status_code=400,
                detail="Project must have at least 2 assigned colleagues for dual control",
            )

    @staticmethod
    def _ensure_membership(session: Session, *, project_id, person_id, error_text: str) -> None:
        assignments = session.exec(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.person_id == person_id,
            )
        ).all()
        active_assignments = [
            assignment
            for assignment in assignments
            if assignment.end_date is None or assignment.end_date >= datetime.utcnow()
        ]
        if not active_assignments:
            raise HTTPException(status_code=400, detail=error_text)

    @staticmethod
    def submit_for_review(session: Session, payload: ReviewRequestCreate) -> ReviewRequest:
        asset = session.get(Asset, payload.asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        review = ReviewRequest(
            asset_id=payload.asset_id,
            project_id=payload.project_id,
            author_id=payload.author_id,
            reviewer_id=payload.reviewer_id,
            change_summary=payload.change_summary,
            status=ReviewStatus.in_review,
            submitted_at=datetime.utcnow(),
        )
        ReviewService._ensure_dual_control(session, review)
        ReviewService._ensure_membership(
            session,
            project_id=payload.project_id,
            person_id=payload.author_id,
            error_text="Only assigned project members may submit review",
        )
        ReviewService._ensure_membership(
            session,
            project_id=payload.project_id,
            person_id=payload.reviewer_id,
            error_text="Reviewer must belong to the same project",
        )

        asset.status = AssetStatus.in_review
        session.add(review)
        session.add(asset)
        session.commit()
        session.refresh(review)

        log_activity(
            session,
            entity_type=EntityType.review,
            entity_id=review.id,
            actor_id=payload.author_id,
            action="review.submitted",
            metadata={"asset_id": str(payload.asset_id), "project_id": str(payload.project_id)},
        )
        return review

    @staticmethod
    def decide_review(session: Session, payload: ReviewDecisionCreate) -> ReviewRequest:
        review = session.get(ReviewRequest, payload.review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review request not found")
        if review.reviewer_id != payload.reviewer_id:
            raise HTTPException(status_code=403, detail="Only assigned reviewer can decide this review")

        asset = session.get(Asset, review.asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        decision = ReviewDecision(
            review_request_id=payload.review_id,
            reviewer_id=payload.reviewer_id,
            decision=payload.decision,
            note=payload.note,
        )
        session.add(decision)

        if payload.decision == DecisionType.approve:
            review.status = ReviewStatus.approved
            review.snippet_worthy = payload.snippet_worthy
            asset.status = AssetStatus.approved
            activity = "review.approved"
        else:
            review.status = ReviewStatus.changes_requested
            review.snippet_worthy = False
            asset.status = AssetStatus.draft
            activity = "review.changes_requested"

        if payload.snippet_worthy and payload.decision != DecisionType.approve:
            raise HTTPException(status_code=400, detail="Snippet-worthy flag only possible if approved")

        review.decision_at = datetime.utcnow()
        session.add(review)
        session.add(asset)
        session.commit()
        session.refresh(review)

        log_activity(
            session,
            entity_type=EntityType.review,
            entity_id=review.id,
            actor_id=payload.reviewer_id,
            action=activity,
            metadata={"decision": payload.decision.value, "asset_id": str(review.asset_id)},
        )

        return review
