from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import Client, EntityType, Template, TemplateLibrary
from foundry.schemas import (
    TemplateCreate,
    TemplateInstantiateCreate,
    TemplateInstantiationOut,
    TemplateLibraryCreate,
    TemplateOut,
)
from foundry.services.activity_log import log_created
from foundry.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("/libraries", response_model=TemplateLibrary)
def create_library(
    payload: TemplateLibraryCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if payload.client_id is not None:
        client = session.get(Client, payload.client_id)
        if not client or client.organization_id != current_actor.organization.id:
            raise HTTPException(status_code=404, detail="Client not found")

    library = TemplateLibrary(
        organization_id=current_actor.organization.id,
        **payload.model_dump(),
    )
    session.add(library)
    session.commit()
    session.refresh(library)

    log_created(
        session,
        entity_type=EntityType.template,
        entity_id=library.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={
            "scope": library.scope.value,
            "client_id": str(library.client_id) if library.client_id else None,
            "library_id": str(library.id),
        },
    )
    return library


@router.post("/", response_model=Template)
def create_template(
    payload: TemplateCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if payload.created_by != current_actor.person.id:
        raise HTTPException(status_code=403, detail="created_by must match authenticated user")

    library = session.get(TemplateLibrary, payload.library_id)
    if not library or library.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=404, detail="Template library not found")

    template = Template(
        organization_id=current_actor.organization.id,
        **payload.model_dump(),
    )
    session.add(template)
    session.commit()
    session.refresh(template)

    log_created(
        session,
        entity_type=EntityType.template,
        entity_id=template.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"library_id": str(template.library_id), "category": template.category},
    )
    return template


@router.get("/", response_model=list[TemplateOut])
def list_templates(
    client_id: UUID | None = None,
    category: str | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    return TemplateService.list_templates(
        session,
        organization_id=current_actor.organization.id,
        client_id=client_id,
        category=category,
    )


@router.post("/{template_id}/instantiate", response_model=TemplateInstantiationOut)
def instantiate_template(
    template_id: UUID,
    payload: TemplateInstantiateCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if payload.author_id != current_actor.person.id:
        raise HTTPException(status_code=403, detail="author_id must match authenticated user")

    template = session.exec(
        select(Template).where(
            Template.id == template_id,
            Template.is_active,
            Template.organization_id == current_actor.organization.id,
        )
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateService.instantiate_template(
        session,
        template=template,
        payload=payload,
        organization_id=current_actor.organization.id,
    )
