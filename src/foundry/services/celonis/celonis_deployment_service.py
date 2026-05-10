from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from foundry.models import (
    ActivityLog,
    CelonisDeploymentRequest,
    CelonisDeploymentStatus,
    Client,
    EntityType,
    OrganizationMembership,
    Person,
    Project,
)
from foundry.services.activity_log import log_activity


class CelonisDeploymentServiceError(ValueError):
    pass


def _get_org_client(session: Session, client_id: UUID, organization_id: UUID) -> Client | None:
    client = session.get(Client, client_id)
    if client is None or client.organization_id != organization_id:
        return None
    return client


def _get_org_project(session: Session, project_id: UUID, organization_id: UUID) -> Project | None:
    project = session.get(Project, project_id)
    if project is None or project.organization_id != organization_id:
        return None
    return project


def _get_org_person(session: Session, person_id: UUID, organization_id: UUID) -> Person | None:
    person = session.get(Person, person_id)
    if person is None:
        return None
    membership = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.person_id == person_id,
        )
    ).first()
    return person if membership else None


def get_deployment_request(
    session: Session,
    *,
    deployment_request_id: UUID,
    organization_id: UUID,
) -> CelonisDeploymentRequest | None:
    req = session.get(CelonisDeploymentRequest, deployment_request_id)
    if req is None or req.organization_id != organization_id:
        return None
    return req


def list_deployment_requests(session: Session, *, organization_id: UUID) -> list[CelonisDeploymentRequest]:
    return list(
        session.exec(
            select(CelonisDeploymentRequest)
            .where(CelonisDeploymentRequest.organization_id == organization_id)
            .order_by(CelonisDeploymentRequest.created_at.desc())
        ).all()
    )


def list_deployment_approval_queue(
    session: Session,
    *,
    organization_id: UUID,
    reviewer_id: UUID | None = None,
    include_unassigned: bool = True,
) -> list[CelonisDeploymentRequest]:
    queue_items = list(
        session.exec(
            select(CelonisDeploymentRequest)
            .where(
                CelonisDeploymentRequest.organization_id == organization_id,
                CelonisDeploymentRequest.status == CelonisDeploymentStatus.awaiting_approval,
            )
            .order_by(CelonisDeploymentRequest.created_at.asc())
        ).all()
    )
    if reviewer_id is None:
        return queue_items
    return [
        req
        for req in queue_items
        if req.reviewer_id == reviewer_id or (include_unassigned and req.reviewer_id is None)
    ]


def list_deployment_history(
    session: Session,
    *,
    organization_id: UUID,
    deployment_request_id: UUID,
) -> list[ActivityLog]:
    req = get_deployment_request(
        session,
        deployment_request_id=deployment_request_id,
        organization_id=organization_id,
    )
    if req is None:
        raise CelonisDeploymentServiceError("Deployment request not found")

    return list(
        session.exec(
            select(ActivityLog)
            .where(
                ActivityLog.organization_id == organization_id,
                ActivityLog.entity_type == EntityType.celonis_deployment_request,
                ActivityLog.entity_id == deployment_request_id,
            )
            .order_by(ActivityLog.timestamp.asc())
        ).all()
    )


def _preflight_passed_for_run(
    session: Session,
    *,
    organization_id: UUID,
    client_id: UUID,
    preflight_run_id: str,
) -> bool:
    if not preflight_run_id.strip():
        return False

    logs = session.exec(
        select(ActivityLog).where(
            ActivityLog.organization_id == organization_id,
            ActivityLog.action == "celonis_connection.preflight",
            ActivityLog.entity_type == EntityType.celonis_connection,
        )
    ).all()
    matching_logs = [
        row
        for row in logs
        if str((row.metadata_json or {}).get("client_id", "")).strip() == str(client_id)
        and str((row.metadata_json or {}).get("run_id", "")).strip() == preflight_run_id.strip()
    ]
    return bool(matching_logs) and all(
        str((row.metadata_json or {}).get("permission_status", "")) == "authorized"
        for row in matching_logs
    )


def create_deployment_request(
    session: Session,
    *,
    organization_id: UUID,
    actor_id: UUID,
    client_id: UUID,
    project_id: UUID,
    target_space_name: str = "",
    target_package_key: str = "",
    target_package_name: str = "",
    preflight_run_id: str = "",
    notes: str = "",
) -> CelonisDeploymentRequest:
    if _get_org_client(session, client_id, organization_id) is None:
        raise CelonisDeploymentServiceError("Client not found")
    if _get_org_project(session, project_id, organization_id) is None:
        raise CelonisDeploymentServiceError("Project not found")

    cleaned_run_id = preflight_run_id.strip()
    req = CelonisDeploymentRequest(
        organization_id=organization_id,
        project_id=project_id,
        client_id=client_id,
        created_by=actor_id,
        target_space_name=target_space_name.strip() or None,
        target_package_key=target_package_key.strip() or None,
        target_package_name=target_package_name.strip() or None,
        preflight_run_id=cleaned_run_id or None,
        preflight_passed=_preflight_passed_for_run(
            session,
            organization_id=organization_id,
            client_id=client_id,
            preflight_run_id=cleaned_run_id,
        ) if cleaned_run_id else False,
        notes=notes.strip() or None,
    )
    session.add(req)
    session.commit()
    session.refresh(req)
    log_activity(
        session,
        entity_type=EntityType.celonis_deployment_request,
        entity_id=req.id,
        actor_id=actor_id,
        action="celonis_deployment_request.created",
        organization_id=organization_id,
        metadata={"client_id": str(client_id), "project_id": str(project_id)},
    )
    return req


def acknowledge_deployment_diff(
    session: Session,
    *,
    organization_id: UUID,
    actor_id: UUID,
    deployment_request_id: UUID,
) -> CelonisDeploymentRequest:
    req = get_deployment_request(session, deployment_request_id=deployment_request_id, organization_id=organization_id)
    if req is None:
        raise CelonisDeploymentServiceError("Deployment request not found")
    if req.status != CelonisDeploymentStatus.draft:
        raise CelonisDeploymentServiceError("Can only acknowledge diff on draft requests")

    req.permission_diff_acknowledged = True
    req.permission_diff_acknowledged_by = actor_id
    req.updated_at = datetime.utcnow()
    session.add(req)
    session.commit()
    session.refresh(req)
    log_activity(
        session,
        entity_type=EntityType.celonis_deployment_request,
        entity_id=req.id,
        actor_id=actor_id,
        action="celonis_deployment_request.diff_acknowledged",
        organization_id=organization_id,
        metadata={},
    )
    return req


def submit_deployment_for_approval(
    session: Session,
    *,
    organization_id: UUID,
    actor_id: UUID,
    deployment_request_id: UUID,
) -> CelonisDeploymentRequest:
    req = get_deployment_request(session, deployment_request_id=deployment_request_id, organization_id=organization_id)
    if req is None:
        raise CelonisDeploymentServiceError("Deployment request not found")
    if req.status != CelonisDeploymentStatus.draft:
        raise CelonisDeploymentServiceError("Only draft requests can be submitted")
    if not req.preflight_passed:
        raise CelonisDeploymentServiceError(
            "Preflight must pass before submitting for approval"
        )
    if not req.permission_diff_acknowledged:
        raise CelonisDeploymentServiceError(
            "Permission diff must be acknowledged before submitting for approval"
        )
    if req.reviewer_id is None:
        raise CelonisDeploymentServiceError(
            "Reviewer must be assigned before submitting for approval"
        )

    req.status = CelonisDeploymentStatus.awaiting_approval
    req.updated_at = datetime.utcnow()
    session.add(req)
    session.commit()
    session.refresh(req)
    log_activity(
        session,
        entity_type=EntityType.celonis_deployment_request,
        entity_id=req.id,
        actor_id=actor_id,
        action="celonis_deployment_request.submitted_for_approval",
        organization_id=organization_id,
        metadata={},
    )
    return req


def assign_deployment_reviewer(
    session: Session,
    *,
    organization_id: UUID,
    actor_id: UUID,
    deployment_request_id: UUID,
    reviewer_id: UUID,
) -> CelonisDeploymentRequest:
    req = get_deployment_request(session, deployment_request_id=deployment_request_id, organization_id=organization_id)
    if req is None:
        raise CelonisDeploymentServiceError("Deployment request not found")
    if req.status not in {CelonisDeploymentStatus.draft, CelonisDeploymentStatus.awaiting_approval}:
        raise CelonisDeploymentServiceError("Can only assign reviewer for draft or awaiting approval requests")
    if str(req.created_by) == str(reviewer_id):
        raise CelonisDeploymentServiceError("The request creator cannot be the reviewer")
    if _get_org_person(session, reviewer_id, organization_id) is None:
        raise CelonisDeploymentServiceError("Reviewer not found in organization")

    req.reviewer_id = reviewer_id
    req.updated_at = datetime.utcnow()
    session.add(req)
    session.commit()
    session.refresh(req)
    log_activity(
        session,
        entity_type=EntityType.celonis_deployment_request,
        entity_id=req.id,
        actor_id=actor_id,
        action="celonis_deployment_request.reviewer_assigned",
        organization_id=organization_id,
        metadata={"reviewer_id": str(reviewer_id)},
    )
    return req


def decide_deployment_request(
    session: Session,
    *,
    organization_id: UUID,
    actor_id: UUID,
    deployment_request_id: UUID,
    decision: str,
    reviewer_note: str = "",
) -> CelonisDeploymentRequest:
    req = get_deployment_request(session, deployment_request_id=deployment_request_id, organization_id=organization_id)
    if req is None:
        raise CelonisDeploymentServiceError("Deployment request not found")
    if req.status != CelonisDeploymentStatus.awaiting_approval:
        raise CelonisDeploymentServiceError("Request is not awaiting approval")
    if req.reviewer_id is not None and str(req.reviewer_id) != str(actor_id):
        raise CelonisDeploymentServiceError("Only the assigned reviewer can decide this request")
    if str(req.created_by) == str(actor_id):
        raise CelonisDeploymentServiceError(
            "The request creator cannot be the reviewer"
        )
    if decision not in {"approved", "rejected"}:
        raise CelonisDeploymentServiceError("Invalid decision value")

    if req.reviewer_id is None:
        req.reviewer_id = actor_id
    req.reviewer_decision = decision
    req.reviewer_note = reviewer_note.strip() or None
    req.status = (
        CelonisDeploymentStatus.approved if decision == "approved" else CelonisDeploymentStatus.draft
    )
    req.updated_at = datetime.utcnow()
    session.add(req)
    session.commit()
    session.refresh(req)
    log_activity(
        session,
        entity_type=EntityType.celonis_deployment_request,
        entity_id=req.id,
        actor_id=actor_id,
        action=f"celonis_deployment_request.{decision}",
        organization_id=organization_id,
        metadata={"decision": decision},
    )
    return req


def cancel_deployment_request(
    session: Session,
    *,
    organization_id: UUID,
    actor_id: UUID,
    deployment_request_id: UUID,
) -> CelonisDeploymentRequest:
    req = get_deployment_request(session, deployment_request_id=deployment_request_id, organization_id=organization_id)
    if req is None:
        raise CelonisDeploymentServiceError("Deployment request not found")
    if req.status == CelonisDeploymentStatus.cancelled:
        raise CelonisDeploymentServiceError("Request is already cancelled")

    req.status = CelonisDeploymentStatus.cancelled
    req.updated_at = datetime.utcnow()
    session.add(req)
    session.commit()
    session.refresh(req)
    log_activity(
        session,
        entity_type=EntityType.celonis_deployment_request,
        entity_id=req.id,
        actor_id=actor_id,
        action="celonis_deployment_request.cancelled",
        organization_id=organization_id,
        metadata={},
    )
    return req