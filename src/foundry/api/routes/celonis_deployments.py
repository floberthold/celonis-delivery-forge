from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import Person
from foundry.schemas import (
    CelonisDeploymentDecisionCreate,
    CelonisDeploymentHistoryEventOut,
    CelonisDeploymentRequestCreate,
    CelonisDeploymentRequestOut,
    CelonisDeploymentReviewerAssignCreate,
)
from foundry.services.celonis.celonis_deployment_service import (
    CelonisDeploymentServiceError,
    acknowledge_deployment_diff,
    assign_deployment_reviewer,
    cancel_deployment_request,
    create_deployment_request,
    decide_deployment_request,
    list_deployment_approval_queue,
    list_deployment_history,
    list_deployment_requests,
    submit_deployment_for_approval,
)

router = APIRouter(prefix="/celonis/deployments", tags=["celonis-deployments"])


@router.get("/", response_model=list[CelonisDeploymentRequestOut])
def list_celonis_deployments(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    return list_deployment_requests(session, organization_id=current_actor.organization.id)


@router.get("/queue", response_model=list[CelonisDeploymentRequestOut])
def list_celonis_deployment_queue(
    reviewer_id: UUID | None = Query(default=None),
    include_unassigned: bool = Query(default=True),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    return list_deployment_approval_queue(
        session,
        organization_id=current_actor.organization.id,
        reviewer_id=reviewer_id,
        include_unassigned=include_unassigned,
    )


@router.post("/", response_model=CelonisDeploymentRequestOut)
def create_celonis_deployment(
    payload: CelonisDeploymentRequestCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        return create_deployment_request(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            client_id=payload.client_id,
            project_id=payload.project_id,
            target_space_name=payload.target_space_name or "",
            target_package_key=payload.target_package_key or "",
            target_package_name=payload.target_package_name or "",
            preflight_run_id=payload.preflight_run_id or "",
            notes=payload.notes or "",
        )
    except CelonisDeploymentServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{deployment_request_id}/acknowledge-diff", response_model=CelonisDeploymentRequestOut)
def acknowledge_celonis_deployment_diff(
    deployment_request_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        return acknowledge_deployment_diff(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            deployment_request_id=deployment_request_id,
        )
    except CelonisDeploymentServiceError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{deployment_request_id}/submit-for-approval", response_model=CelonisDeploymentRequestOut)
def submit_celonis_deployment_for_approval(
    deployment_request_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        return submit_deployment_for_approval(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            deployment_request_id=deployment_request_id,
        )
    except CelonisDeploymentServiceError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{deployment_request_id}/assign-reviewer", response_model=CelonisDeploymentRequestOut)
def assign_celonis_deployment_reviewer(
    deployment_request_id: UUID,
    payload: CelonisDeploymentReviewerAssignCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        return assign_deployment_reviewer(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            deployment_request_id=deployment_request_id,
            reviewer_id=payload.reviewer_id,
        )
    except CelonisDeploymentServiceError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{deployment_request_id}/decision", response_model=CelonisDeploymentRequestOut)
def decide_celonis_deployment(
    deployment_request_id: UUID,
    payload: CelonisDeploymentDecisionCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        return decide_deployment_request(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            deployment_request_id=deployment_request_id,
            decision=payload.decision,
            reviewer_note=payload.reviewer_note or "",
        )
    except CelonisDeploymentServiceError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{deployment_request_id}/cancel", response_model=CelonisDeploymentRequestOut)
def cancel_celonis_deployment(
    deployment_request_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        return cancel_deployment_request(
            session,
            organization_id=current_actor.organization.id,
            actor_id=current_actor.person.id,
            deployment_request_id=deployment_request_id,
        )
    except CelonisDeploymentServiceError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{deployment_request_id}/history", response_model=list[CelonisDeploymentHistoryEventOut])
def list_celonis_deployment_history(
    deployment_request_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    try:
        events = list_deployment_history(
            session,
            organization_id=current_actor.organization.id,
            deployment_request_id=deployment_request_id,
        )
    except CelonisDeploymentServiceError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    actor_ids = {event.actor_id for event in events}
    people = session.exec(select(Person).where(Person.id.in_(actor_ids))).all() if actor_ids else []
    by_actor_id = {person.id: person for person in people}

    return [
        CelonisDeploymentHistoryEventOut(
            id=event.id,
            deployment_request_id=deployment_request_id,
            action=event.action,
            actor_id=event.actor_id,
            actor_name=(by_actor_id[event.actor_id].name if event.actor_id in by_actor_id else None),
            actor_email=(by_actor_id[event.actor_id].email if event.actor_id in by_actor_id else None),
            timestamp=event.timestamp,
            metadata_json=event.metadata_json or {},
        )
        for event in events
    ]