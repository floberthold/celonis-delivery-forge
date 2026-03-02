from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import EntityType, Project, ProjectMembership
from foundry.schemas import ProjectAssign, ProjectCreate, ProjectStatusUpdate
from foundry.services.activity_log import log_activity
from foundry.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=Project)
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)):
    project = Project(**payload.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/", response_model=list[Project])
def list_projects(session: Session = Depends(get_session)):
    return list(session.exec(select(Project)).all())


@router.post("/{project_id}/memberships", response_model=ProjectMembership)
def assign_user(project_id: UUID, payload: ProjectAssign, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    assignment = ProjectMembership(
        project_id=project_id,
        person_id=payload.person_id,
        role=payload.role,
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)

    log_activity(
        session,
        entity_type=EntityType.membership,
        entity_id=assignment.id,
        actor_id=payload.person_id,
        action="membership.assigned",
        metadata={"project_id": str(project_id), "role": payload.role.value},
    )

    return assignment


@router.patch("/{project_id}/status", response_model=Project)
def update_project_status(
    project_id: UUID,
    actor_id: UUID,
    payload: ProjectStatusUpdate,
    session: Session = Depends(get_session),
):
    return ProjectService.update_project_status(
        session,
        project_id=project_id,
        actor_id=actor_id,
        payload=payload,
    )
