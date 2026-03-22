from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlmodel import Session, col, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import Quest, QuestStatus
from foundry.schemas import (
    QuestAssignmentCreate,
    QuestAssignmentOut,
    QuestAssignmentUpdate,
    QuestCreate,
    QuestFeedbackCreate,
    QuestObjectiveCreate,
    QuestObjectiveOut,
    QuestObjectiveUpdate,
    QuestOut,
    QuestReplace,
    QuestReprioritize,
    QuestUpdate,
)
from foundry.services.quest_service import (
    add_feedback as add_feedback_service,
    create_assignment as create_assignment_service,
    create_objective as create_objective_service,
    create_quest as create_quest_service,
    delete_assignment as delete_assignment_service,
    delete_objective as delete_objective_service,
    delete_quest as delete_quest_service,
    get_org_quest,
    list_assignments as list_assignments_service,
    list_objectives as list_objectives_service,
    pause_quest as pause_quest_service,
    replace_quest as replace_quest_service,
    reprioritize_quest as reprioritize_quest_service,
    QuestServiceError,
    update_assignment as update_assignment_service,
    update_objective as update_objective_service,
    update_quest as update_quest_service,
)

router = APIRouter(prefix="/quests", tags=["quests"])


def _require_org_id(current_actor: CurrentActor) -> UUID:
    if current_actor.organization is None:
        raise HTTPException(status_code=403, detail="Active organization required")
    return current_actor.organization.id


@router.post("/", response_model=QuestOut)
def create_quest(
    payload: QuestCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = create_quest_service(
        session,
        organization_id=organization_id,
        actor_id=current_actor.person.id,
        data=payload.model_dump(),
        default_owner_person_id=current_actor.person.id,
    )
    return quest


@router.get("/", response_model=list[QuestOut])
def list_quests(
    status: QuestStatus | None = None,
    project_id: UUID | None = None,
    owner_person_id: UUID | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    stmt = select(Quest).where(Quest.organization_id == organization_id)
    if status is not None:
        stmt = stmt.where(Quest.status == status)
    if project_id is not None:
        stmt = stmt.where(Quest.project_id == project_id)
    if owner_person_id is not None:
        stmt = stmt.where(Quest.owner_person_id == owner_person_id)
    stmt = stmt.order_by(desc(col(Quest.created_at)))
    return list(session.exec(stmt).all())


@router.patch("/{quest_id}", response_model=QuestOut)
def update_quest(
    quest_id: UUID,
    payload: QuestUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    updates = payload.model_dump(exclude_unset=True)
    try:
        return update_quest_service(
            session,
            actor_id=current_actor.person.id,
            organization_id=organization_id,
            quest=quest,
            updates=updates,
        )
    except QuestServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{quest_id}/pause", response_model=QuestOut)
def pause_quest(
    quest_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    try:
        return pause_quest_service(
            session,
            actor_id=current_actor.person.id,
            organization_id=organization_id,
            quest=quest,
        )
    except QuestServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{quest_id}/reprioritize", response_model=QuestOut)
def reprioritize_quest(
    quest_id: UUID,
    payload: QuestReprioritize,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    return reprioritize_quest_service(
        session,
        actor_id=current_actor.person.id,
        organization_id=organization_id,
        quest=quest,
        priority=payload.priority,
    )


@router.post("/{quest_id}/replace", response_model=QuestOut)
def replace_quest(
    quest_id: UUID,
    payload: QuestReplace,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    try:
        return replace_quest_service(
            session,
            actor_id=current_actor.person.id,
            organization_id=organization_id,
            quest=quest,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
        )
    except QuestServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{quest_id}")
def delete_quest(
    quest_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    deleted_id = delete_quest_service(
        session,
        quest=quest,
        actor_id=current_actor.person.id,
        organization_id=organization_id,
    )
    return {"deleted": True, "id": str(deleted_id)}


@router.post("/{quest_id}/feedback")
def add_quest_feedback(
    quest_id: UUID,
    payload: QuestFeedbackCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    feedback = add_feedback_service(
        session,
        quest=quest,
        actor_id=current_actor.person.id,
        organization_id=organization_id,
        feedback_type=payload.feedback_type,
        note=payload.note,
        metadata_json=payload.metadata_json,
    )
    return {"id": str(feedback.id)}


@router.get("/{quest_id}/objectives", response_model=list[QuestObjectiveOut])
def list_quest_objectives(
    quest_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    return list_objectives_service(session, quest_id=quest.id)


@router.post("/{quest_id}/objectives", response_model=QuestObjectiveOut)
def create_quest_objective(
    quest_id: UUID,
    payload: QuestObjectiveCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    return create_objective_service(
        session,
        quest=quest,
        actor_id=current_actor.person.id,
        organization_id=organization_id,
        title=payload.title,
        details=payload.details,
        sort_order=payload.sort_order,
    )


@router.patch("/{quest_id}/objectives/{objective_id}", response_model=QuestObjectiveOut)
def update_quest_objective(
    quest_id: UUID,
    objective_id: UUID,
    payload: QuestObjectiveUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    try:
        return update_objective_service(
            session,
            quest=quest,
            objective_id=objective_id,
            actor_id=current_actor.person.id,
            organization_id=organization_id,
            updates=payload.model_dump(exclude_unset=True),
        )
    except QuestServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{quest_id}/objectives/{objective_id}")
def delete_quest_objective(
    quest_id: UUID,
    objective_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    try:
        deleted_id = delete_objective_service(
            session,
            quest=quest,
            objective_id=objective_id,
            actor_id=current_actor.person.id,
            organization_id=organization_id,
        )
    except QuestServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": True, "id": str(deleted_id)}


@router.get("/{quest_id}/assignments", response_model=list[QuestAssignmentOut])
def list_quest_assignments(
    quest_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    return list_assignments_service(session, quest_id=quest.id)


@router.post("/{quest_id}/assignments", response_model=QuestAssignmentOut)
def create_quest_assignment(
    quest_id: UUID,
    payload: QuestAssignmentCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    try:
        return create_assignment_service(
            session,
            quest=quest,
            actor_id=current_actor.person.id,
            organization_id=organization_id,
            agent_id=payload.agent_id,
            assignee_person_id=payload.assignee_person_id,
            role=payload.role,
            state=payload.state,
        )
    except QuestServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{quest_id}/assignments/{assignment_id}", response_model=QuestAssignmentOut)
def update_quest_assignment(
    quest_id: UUID,
    assignment_id: UUID,
    payload: QuestAssignmentUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    try:
        return update_assignment_service(
            session,
            quest=quest,
            assignment_id=assignment_id,
            actor_id=current_actor.person.id,
            organization_id=organization_id,
            updates=payload.model_dump(exclude_unset=True),
        )
    except QuestServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{quest_id}/assignments/{assignment_id}")
def delete_quest_assignment(
    quest_id: UUID,
    assignment_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    organization_id = _require_org_id(current_actor)
    quest = get_org_quest(session, quest_id, organization_id)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    try:
        deleted_id = delete_assignment_service(
            session,
            quest=quest,
            assignment_id=assignment_id,
            actor_id=current_actor.person.id,
            organization_id=organization_id,
        )
    except QuestServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": True, "id": str(deleted_id)}
