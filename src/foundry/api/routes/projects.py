from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import Client, EntityType, Project, ProjectMembership
from foundry.schemas import ProjectAssign, ProjectCreate, ProjectStatusUpdate
from foundry.services.activity_log import log_created
from foundry.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=Project)
def create_project(
    payload: ProjectCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    client = session.get(Client, payload.client_id)
    if not client or client.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=404, detail="Client not found")

    project = Project(
        organization_id=current_actor.organization.id,
        **payload.model_dump(),
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    log_created(
        session,
        entity_type=EntityType.project,
        entity_id=project.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"client_id": str(project.client_id), "status": project.status.value},
    )
    return project


@router.get("/", response_model=list[Project])
def list_projects(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    stmt = select(Project).where(Project.organization_id == current_actor.organization.id)
    return list(session.exec(stmt).all())


@router.post("/{project_id}/memberships", response_model=ProjectMembership)
def assign_user(
    project_id: UUID,
    payload: ProjectAssign,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    project = session.get(Project, project_id)
    if not project or project.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=404, detail="Project not found")

    assignment = ProjectMembership(
        project_id=project_id,
        person_id=payload.person_id,
        role=payload.role,
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)

    log_created(
        session,
        entity_type=EntityType.membership,
        entity_id=assignment.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"project_id": str(project_id), "role": payload.role.value},
    )

    return assignment


@router.patch("/{project_id}/status", response_model=Project)
def update_project_status(
    project_id: UUID,
    payload: ProjectStatusUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    return ProjectService.update_project_status(
        session,
        project_id=project_id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        payload=payload,
    )
