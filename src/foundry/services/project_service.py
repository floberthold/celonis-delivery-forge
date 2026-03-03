from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from foundry.models import Asset, AssetStatus, EntityType, Project, ProjectMembership, ProjectStatus
from foundry.schemas import ProjectStatusUpdate
from foundry.services.activity_log import log_activity


class ProjectService:
    @staticmethod
    def _active_memberships(session: Session, project_id: UUID) -> list[ProjectMembership]:
        memberships = session.exec(
            select(ProjectMembership).where(ProjectMembership.project_id == project_id)
        ).all()
        now = datetime.utcnow()
        return [
            membership
            for membership in memberships
            if membership.start_date <= now and (membership.end_date is None or membership.end_date >= now)
        ]

    @staticmethod
    def ensure_can_be_active(session: Session, project_id: UUID) -> None:
        if len(ProjectService._active_memberships(session, project_id)) < 2:
            raise HTTPException(
                status_code=400,
                detail="Project cannot be active with fewer than 2 active memberships",
            )

    @staticmethod
    def ensure_can_be_closed(session: Session, project_id: UUID) -> None:
        in_review_assets = session.exec(
            select(Asset).where(Asset.project_id == project_id, Asset.status == AssetStatus.in_review)
        ).all()
        if in_review_assets:
            raise HTTPException(
                status_code=400,
                detail="Project cannot be closed while assets are still in review",
            )

    @staticmethod
    def update_project_status(
        session: Session,
        *,
        project_id: UUID,
        actor_id: UUID,
        payload: ProjectStatusUpdate,
    ) -> Project:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if payload.status == ProjectStatus.active:
            ProjectService.ensure_can_be_active(session, project_id)
        if payload.status == ProjectStatus.closed:
            ProjectService.ensure_can_be_closed(session, project_id)

        previous_status = project.status
        project.status = payload.status
        session.add(project)
        session.commit()
        session.refresh(project)

        log_activity(
            session,
            entity_type=EntityType.project,
            entity_id=project.id,
            actor_id=actor_id,
            action="project.updated",
            metadata={"old_status": previous_status.value, "new_status": payload.status.value},
        )

        return project
