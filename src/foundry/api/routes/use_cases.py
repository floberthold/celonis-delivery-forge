from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import false, or_
from sqlmodel import Session, col, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import (
    Client,
    EntityType,
    OrganizationMembership,
    Project,
    RoadmapItemStatus,
    UseCase,
    UseCaseMaturity,
    UseCaseRoadmapItem,
)
from foundry.schemas import (
    UseCaseCreate,
    UseCaseIndustryBenchmarkSummaryOut,
    UseCaseOut,
    UseCaseViewOut,
    UseCaseRoadmapItemCreate,
    UseCaseRoadmapItemOut,
    UseCaseRoadmapItemUpdate,
    UseCaseUpdate,
)
from foundry.services.activity_log import log_activity, log_created, log_updated
from foundry.services.use_case_views import to_industry_benchmark_summary, to_view_payload

router = APIRouter(prefix="/use-cases", tags=["use-cases"])


def _org_person_ids(session: Session, organization_id: UUID) -> set[UUID]:
    return {
        row.person_id
        for row in session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id
            )
        ).all()
    }


def _org_client_ids(session: Session, organization_id: UUID) -> set[UUID]:
    return {
        row.id
        for row in session.exec(select(Client).where(Client.organization_id == organization_id)).all()
    }


def _org_project_ids(session: Session, organization_id: UUID) -> set[UUID]:
    return {
        row.id
        for row in session.exec(select(Project).where(Project.organization_id == organization_id)).all()
    }


def _get_org_client(session: Session, client_id: UUID, organization_id: UUID) -> Client | None:
    return session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == organization_id,
        )
    ).first()


def _get_org_project(session: Session, project_id: UUID, organization_id: UUID) -> Project | None:
    return session.exec(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == organization_id,
        )
    ).first()


def _use_case_in_org(
    use_case: UseCase,
    org_client_ids: set[UUID],
    org_project_ids: set[UUID],
    org_person_ids: set[UUID],
) -> bool:
    return (
        (use_case.client_id is not None and use_case.client_id in org_client_ids)
        or (use_case.project_id is not None and use_case.project_id in org_project_ids)
        or (use_case.owner_person_id is not None and use_case.owner_person_id in org_person_ids)
    )


def _get_org_use_case(session: Session, use_case_id: UUID, organization_id: UUID) -> UseCase | None:
    use_case = session.get(UseCase, use_case_id)
    if use_case is None:
        return None
    if _use_case_in_org(
        use_case,
        _org_client_ids(session, organization_id),
        _org_project_ids(session, organization_id),
        _org_person_ids(session, organization_id),
    ):
        return use_case
    return None


def _get_org_roadmap_item(session: Session, item_id: UUID, organization_id: UUID) -> UseCaseRoadmapItem | None:
    item = session.get(UseCaseRoadmapItem, item_id)
    if item is None or item.owner_person_id is None:
        return None
    if item.owner_person_id in _org_person_ids(session, organization_id):
        return item
    return None


def _apply_org_use_case_scope(stmt, *, session: Session, organization_id: UUID):
    org_client_ids = _org_client_ids(session, organization_id)
    org_project_ids = _org_project_ids(session, organization_id)
    org_person_ids = _org_person_ids(session, organization_id)

    ownership_clauses = []
    if org_client_ids:
        ownership_clauses.append(UseCase.client_id.in_(org_client_ids))
    if org_project_ids:
        ownership_clauses.append(UseCase.project_id.in_(org_project_ids))
    if org_person_ids:
        ownership_clauses.append(UseCase.owner_person_id.in_(org_person_ids))

    if not ownership_clauses:
        return stmt.where(false())
    return stmt.where(or_(*ownership_clauses))


def _apply_org_roadmap_scope(stmt, *, session: Session, organization_id: UUID):
    org_person_ids = _org_person_ids(session, organization_id)
    if not org_person_ids:
        return stmt.where(false())
    return stmt.where(UseCaseRoadmapItem.owner_person_id.in_(org_person_ids))


def _validate_percent_complete(value: int) -> None:
    if value < 0 or value > 100:
        raise HTTPException(status_code=400, detail="percent_complete must be between 0 and 100")


def _build_use_case_query(
    *,
    q: str | None,
    industry: str | None,
    process_domain: str | None,
    client_id: UUID | None,
    project_id: UUID | None,
    maturity: UseCaseMaturity | None,
):
    stmt = select(UseCase)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                col(UseCase.title).ilike(pattern),
                col(UseCase.summary).ilike(pattern),
                col(UseCase.industry).ilike(pattern),
                col(UseCase.process_domain).ilike(pattern),
            )
        )
    if industry:
        stmt = stmt.where(UseCase.industry == industry)
    if process_domain:
        stmt = stmt.where(UseCase.process_domain == process_domain)
    if client_id:
        stmt = stmt.where(UseCase.client_id == client_id)
    if project_id:
        stmt = stmt.where(UseCase.project_id == project_id)
    if maturity:
        stmt = stmt.where(UseCase.maturity == maturity)
    return stmt


@router.post("/", response_model=UseCaseOut)
def create_use_case(
    payload: UseCaseCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if payload.client_id and _get_org_client(session, payload.client_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if payload.project_id and _get_org_project(session, payload.project_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.owner_person_id and payload.owner_person_id not in _org_person_ids(session, current_actor.organization.id):
        raise HTTPException(status_code=404, detail="Owner not found")

    use_case = UseCase(**payload.model_dump())
    session.add(use_case)
    session.commit()
    session.refresh(use_case)

    log_created(
        session,
        entity_type=EntityType.use_case,
        entity_id=use_case.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={
            "title": use_case.title,
            "maturity": use_case.maturity.value,
            "industry": use_case.industry,
        },
    )
    return use_case


@router.get("/", response_model=list[UseCaseOut])
def list_use_cases(
    q: str | None = None,
    industry: str | None = None,
    process_domain: str | None = None,
    client_id: UUID | None = None,
    project_id: UUID | None = None,
    maturity: UseCaseMaturity | None = None,
    anonymized_ready: bool | None = None,
    client_view_enabled: bool | None = None,
    industry_benchmark_eligible: bool | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if client_id and _get_org_client(session, client_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if project_id and _get_org_project(session, project_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = _build_use_case_query(
        q=q,
        industry=industry,
        process_domain=process_domain,
        client_id=client_id,
        project_id=project_id,
        maturity=maturity,
    )
    if anonymized_ready is not None:
        stmt = stmt.where(UseCase.is_anonymized_ready == anonymized_ready)
    if client_view_enabled is not None:
        stmt = stmt.where(UseCase.is_client_view_enabled == client_view_enabled)
    if industry_benchmark_eligible is not None:
        stmt = stmt.where(UseCase.is_industry_benchmark_eligible == industry_benchmark_eligible)

    stmt = _apply_org_use_case_scope(
        stmt,
        session=session,
        organization_id=current_actor.organization.id,
    )

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return rows


@router.get("/views/internal", response_model=list[UseCaseViewOut])
def list_internal_view(
    q: str | None = None,
    industry: str | None = None,
    process_domain: str | None = None,
    client_id: UUID | None = None,
    project_id: UUID | None = None,
    maturity: UseCaseMaturity | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if client_id and _get_org_client(session, client_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if project_id and _get_org_project(session, project_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = _build_use_case_query(
        q=q,
        industry=industry,
        process_domain=process_domain,
        client_id=client_id,
        project_id=project_id,
        maturity=maturity,
    )
    stmt = _apply_org_use_case_scope(
        stmt,
        session=session,
        organization_id=current_actor.organization.id,
    )
    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return [to_view_payload(row, view_mode="internal") for row in rows]


@router.get("/views/anonymized", response_model=list[UseCaseViewOut])
def list_anonymized_view(
    q: str | None = None,
    industry: str | None = None,
    process_domain: str | None = None,
    maturity: UseCaseMaturity | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    stmt = _build_use_case_query(
        q=q,
        industry=industry,
        process_domain=process_domain,
        client_id=None,
        project_id=None,
        maturity=maturity,
    ).where(UseCase.is_anonymized_ready == True)  # noqa: E712

    stmt = _apply_org_use_case_scope(
        stmt,
        session=session,
        organization_id=current_actor.organization.id,
    )

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return [to_view_payload(row, view_mode="anonymized") for row in rows]


@router.get("/views/client/{client_id}", response_model=list[UseCaseViewOut])
def list_client_view(
    client_id: UUID,
    q: str | None = None,
    industry: str | None = None,
    process_domain: str | None = None,
    maturity: UseCaseMaturity | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if _get_org_client(session, client_id, current_actor.organization.id) is None:
        raise HTTPException(status_code=404, detail="Client not found")

    stmt = _build_use_case_query(
        q=q,
        industry=industry,
        process_domain=process_domain,
        client_id=client_id,
        project_id=None,
        maturity=maturity,
    ).where(UseCase.is_client_view_enabled == True)  # noqa: E712

    stmt = _apply_org_use_case_scope(
        stmt,
        session=session,
        organization_id=current_actor.organization.id,
    )

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return [to_view_payload(row, view_mode="client") for row in rows]


@router.get("/views/industry-benchmark", response_model=list[UseCaseViewOut])
def list_industry_benchmark_view(
    q: str | None = None,
    industry: str | None = None,
    process_domain: str | None = None,
    maturity: UseCaseMaturity | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    stmt = _build_use_case_query(
        q=q,
        industry=industry,
        process_domain=process_domain,
        client_id=None,
        project_id=None,
        maturity=maturity,
    ).where(UseCase.is_industry_benchmark_eligible == True)  # noqa: E712

    stmt = _apply_org_use_case_scope(
        stmt,
        session=session,
        organization_id=current_actor.organization.id,
    )

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return [to_view_payload(row, view_mode="industry_benchmark") for row in rows]


@router.get("/views/industry-benchmark/summary", response_model=UseCaseIndustryBenchmarkSummaryOut)
def get_industry_benchmark_summary(
    industry: str | None = None,
    process_domain: str | None = None,
    maturity: UseCaseMaturity | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    stmt = _build_use_case_query(
        q=None,
        industry=industry,
        process_domain=process_domain,
        client_id=None,
        project_id=None,
        maturity=maturity,
    ).where(UseCase.is_industry_benchmark_eligible == True)  # noqa: E712

    stmt = _apply_org_use_case_scope(
        stmt,
        session=session,
        organization_id=current_actor.organization.id,
    )

    rows = list(session.exec(stmt).all())
    return to_industry_benchmark_summary(rows)


@router.get("/{use_case_id}", response_model=UseCaseOut)
def get_use_case(
    use_case_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    use_case = _get_org_use_case(session, use_case_id, current_actor.organization.id)
    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")
    return use_case


@router.patch("/{use_case_id}", response_model=UseCaseOut)
def update_use_case(
    use_case_id: UUID,
    payload: UseCaseUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    use_case = _get_org_use_case(session, use_case_id, current_actor.organization.id)
    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    updates = payload.model_dump(exclude_unset=True)
    if "client_id" in updates and updates["client_id"] is not None:
        if _get_org_client(session, updates["client_id"], current_actor.organization.id) is None:
            raise HTTPException(status_code=404, detail="Client not found")
    if "project_id" in updates and updates["project_id"] is not None:
        if _get_org_project(session, updates["project_id"], current_actor.organization.id) is None:
            raise HTTPException(status_code=404, detail="Project not found")
    if "owner_person_id" in updates and updates["owner_person_id"] is not None:
        if updates["owner_person_id"] not in _org_person_ids(session, current_actor.organization.id):
            raise HTTPException(status_code=404, detail="Owner not found")

    for field_name, field_value in updates.items():
        setattr(use_case, field_name, field_value)

    use_case.updated_at = datetime.utcnow()
    session.add(use_case)
    session.commit()
    session.refresh(use_case)

    log_updated(
        session,
        entity_type=EntityType.use_case,
        entity_id=use_case.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"updated_fields": sorted(updates.keys())},
    )

    return use_case


@router.delete("/{use_case_id}")
def delete_use_case(
    use_case_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    use_case = _get_org_use_case(session, use_case_id, current_actor.organization.id)
    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    deleted_title = use_case.title
    session.delete(use_case)
    session.commit()

    log_activity(
        session,
        entity_type=EntityType.use_case,
        entity_id=use_case_id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        action="use_case.deleted",
        metadata={"title": deleted_title},
    )
    return {"ok": True}


@router.post("/roadmap", response_model=UseCaseRoadmapItemOut)
def create_roadmap_item(
    payload: UseCaseRoadmapItemCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    _validate_percent_complete(payload.percent_complete)
    if payload.owner_person_id and payload.owner_person_id not in _org_person_ids(session, current_actor.organization.id):
        raise HTTPException(status_code=404, detail="Owner not found")

    item = UseCaseRoadmapItem(**payload.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)

    log_created(
        session,
        entity_type=EntityType.use_case_roadmap_item,
        entity_id=item.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={
            "initiative": item.initiative,
            "phase": item.phase,
            "status": item.status.value,
        },
    )
    return item


@router.get("/roadmap", response_model=list[UseCaseRoadmapItemOut])
def list_roadmap_items(
    phase: str | None = None,
    status: RoadmapItemStatus | None = None,
    owner_person_id: UUID | None = None,
    target_month: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if owner_person_id and owner_person_id not in _org_person_ids(session, current_actor.organization.id):
        raise HTTPException(status_code=404, detail="Owner not found")

    stmt = select(UseCaseRoadmapItem)

    if phase:
        stmt = stmt.where(UseCaseRoadmapItem.phase == phase)
    if status:
        stmt = stmt.where(UseCaseRoadmapItem.status == status)
    if owner_person_id:
        stmt = stmt.where(UseCaseRoadmapItem.owner_person_id == owner_person_id)
    if target_month:
        stmt = stmt.where(UseCaseRoadmapItem.target_month == target_month)

    stmt = _apply_org_roadmap_scope(
        stmt,
        session=session,
        organization_id=current_actor.organization.id,
    )

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return rows[:limit]


@router.patch("/roadmap/{item_id}", response_model=UseCaseRoadmapItemOut)
def update_roadmap_item(
    item_id: UUID,
    payload: UseCaseRoadmapItemUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    item = _get_org_roadmap_item(session, item_id, current_actor.organization.id)
    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    updates = payload.model_dump(exclude_unset=True)
    if "percent_complete" in updates:
        _validate_percent_complete(updates["percent_complete"])
    if "owner_person_id" in updates and updates["owner_person_id"] is not None:
        if updates["owner_person_id"] not in _org_person_ids(session, current_actor.organization.id):
            raise HTTPException(status_code=404, detail="Owner not found")

    for field_name, field_value in updates.items():
        setattr(item, field_name, field_value)

    item.updated_at = datetime.utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)

    log_updated(
        session,
        entity_type=EntityType.use_case_roadmap_item,
        entity_id=item.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"updated_fields": sorted(updates.keys())},
    )

    return item
