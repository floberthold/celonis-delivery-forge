from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import Template, TemplateLibrary
from foundry.schemas import (
    TemplateCreate,
    TemplateInstantiateCreate,
    TemplateInstantiationOut,
    TemplateLibraryCreate,
    TemplateOut,
)
from foundry.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("/libraries", response_model=TemplateLibrary)
def create_library(payload: TemplateLibraryCreate, session: Session = Depends(get_session)):
    library = TemplateLibrary(**payload.model_dump())
    session.add(library)
    session.commit()
    session.refresh(library)
    return library


@router.post("/", response_model=Template)
def create_template(payload: TemplateCreate, session: Session = Depends(get_session)):
    template = Template(**payload.model_dump())
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


@router.get("/", response_model=list[TemplateOut])
def list_templates(
    client_id: UUID | None = None,
    category: str | None = None,
    session: Session = Depends(get_session),
):
    return TemplateService.list_templates(session, client_id=client_id, category=category)


@router.post("/{template_id}/instantiate", response_model=TemplateInstantiationOut)
def instantiate_template(
    template_id: UUID,
    payload: TemplateInstantiateCreate,
    session: Session = Depends(get_session),
):
    template = session.exec(
        select(Template).where(Template.id == template_id, Template.is_active == True)
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateService.instantiate_template(session, template=template, payload=payload)
