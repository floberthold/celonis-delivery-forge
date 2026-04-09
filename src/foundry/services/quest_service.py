from datetime import datetime
from uuid import UUID

from sqlalchemy import desc
from sqlmodel import Session, col, select

from foundry.models import (
    ActivityLog,
    EntityType,
    Quest,
    QuestAssignment,
    QuestFeedback,
    QuestFeedbackType,
    QuestObjective,
    QuestPriority,
    QuestSource,
    QuestStatus,
)


_ALLOWED_STATUS_TRANSITIONS: dict[QuestStatus, set[QuestStatus]] = {
    QuestStatus.draft: {QuestStatus.suggested, QuestStatus.accepted, QuestStatus.active, QuestStatus.blocked, QuestStatus.archived},
    QuestStatus.suggested: {QuestStatus.accepted, QuestStatus.active, QuestStatus.blocked, QuestStatus.archived},
    QuestStatus.accepted: {QuestStatus.active, QuestStatus.blocked, QuestStatus.done, QuestStatus.archived},
    QuestStatus.active: {QuestStatus.blocked, QuestStatus.done, QuestStatus.archived},
    QuestStatus.blocked: {QuestStatus.accepted, QuestStatus.active, QuestStatus.done, QuestStatus.archived},
    QuestStatus.done: {QuestStatus.archived},
    QuestStatus.archived: set(),
}


class QuestServiceError(ValueError):
    pass


def _quest_metadata(quest: Quest) -> dict:
    return {
        "title": quest.title,
        "status": quest.status.value,
        "priority": quest.priority.value,
        "source": quest.source.value,
        "project_id": str(quest.project_id) if quest.project_id else None,
        "client_id": str(quest.client_id) if quest.client_id else None,
    }


def _append_activity(
    session: Session,
    *,
    entity_id: UUID,
    actor_id: UUID,
    organization_id: UUID,
    action: str,
    metadata: dict,
) -> None:
    session.add(
        ActivityLog(
            organization_id=organization_id,
            entity_type=EntityType.quest,
            entity_id=entity_id,
            actor_id=actor_id,
            action=action,
            metadata_json=metadata,
        )
    )


def _validate_status_transition(current_status: QuestStatus, new_status: QuestStatus) -> None:
    if new_status == current_status:
        return

    allowed = _ALLOWED_STATUS_TRANSITIONS[current_status]
    if new_status not in allowed:
        raise QuestServiceError(
            f"Invalid quest status transition: {current_status.value} -> {new_status.value}"
        )


def get_org_quest(session: Session, quest_id: UUID, organization_id: UUID) -> Quest | None:
    quest = session.get(Quest, quest_id)
    if not quest or quest.organization_id != organization_id:
        return None
    return quest


def create_quest(
    session: Session,
    *,
    organization_id: UUID,
    actor_id: UUID,
    data: dict,
    default_owner_person_id: UUID | None = None,
) -> Quest:
    payload = dict(data)
    if payload.get("owner_person_id") is None and default_owner_person_id is not None:
        payload["owner_person_id"] = default_owner_person_id

    quest = Quest(
        organization_id=organization_id,
        created_by=actor_id,
        **payload,
    )
    session.add(quest)
    session.flush()

    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.created",
        metadata=_quest_metadata(quest),
    )

    session.commit()
    session.refresh(quest)
    return quest


def update_quest(
    session: Session,
    *,
    quest: Quest,
    actor_id: UUID,
    organization_id: UUID,
    updates: dict,
) -> Quest:
    changed_fields = sorted(updates.keys())
    new_status = updates.get("status")
    if new_status is not None:
        _validate_status_transition(quest.status, new_status)

    for field_name, field_value in updates.items():
        setattr(quest, field_name, field_value)
    quest.updated_at = datetime.utcnow()
    session.add(quest)

    session.add(
        QuestFeedback(
            quest_id=quest.id,
            actor_id=actor_id,
            feedback_type=QuestFeedbackType.edited,
            note="Quest updated",
            metadata_json={"changed_fields": changed_fields},
        )
    )
    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.updated",
        metadata=_quest_metadata(quest),
    )

    session.commit()
    session.refresh(quest)
    return quest


def pause_quest(
    session: Session,
    *,
    quest: Quest,
    actor_id: UUID,
    organization_id: UUID,
) -> Quest:
    _validate_status_transition(quest.status, QuestStatus.blocked)
    quest.status = QuestStatus.blocked
    quest.updated_at = datetime.utcnow()
    session.add(quest)
    session.add(
        QuestFeedback(
            quest_id=quest.id,
            actor_id=actor_id,
            feedback_type=QuestFeedbackType.paused,
            note="Quest paused by user",
        )
    )
    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.paused",
        metadata=_quest_metadata(quest),
    )

    session.commit()
    session.refresh(quest)
    return quest


def reprioritize_quest(
    session: Session,
    *,
    quest: Quest,
    actor_id: UUID,
    organization_id: UUID,
    priority: QuestPriority,
) -> Quest:
    quest.priority = priority
    quest.updated_at = datetime.utcnow()
    session.add(quest)
    session.add(
        QuestFeedback(
            quest_id=quest.id,
            actor_id=actor_id,
            feedback_type=QuestFeedbackType.edited,
            note="Quest reprioritized",
            metadata_json={"priority": quest.priority.value},
        )
    )
    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.reprioritized",
        metadata=_quest_metadata(quest),
    )

    session.commit()
    session.refresh(quest)
    return quest


def replace_quest(
    session: Session,
    *,
    quest: Quest,
    actor_id: UUID,
    organization_id: UUID,
    title: str,
    description: str | None,
    priority: QuestPriority,
) -> Quest:
    _validate_status_transition(quest.status, QuestStatus.archived)
    quest.status = QuestStatus.archived
    quest.updated_at = datetime.utcnow()
    session.add(quest)

    replacement = Quest(
        organization_id=organization_id,
        title=title,
        description=description,
        status=QuestStatus.suggested,
        source=QuestSource.user_authored,
        priority=priority,
        owner_person_id=actor_id,
        client_id=quest.client_id,
        project_id=quest.project_id,
        linked_todo_id=quest.linked_todo_id,
        due_at=quest.due_at,
        created_by=actor_id,
    )
    session.add(replacement)
    session.flush()

    session.add(
        QuestFeedback(
            quest_id=quest.id,
            actor_id=actor_id,
            feedback_type=QuestFeedbackType.replaced,
            note="Quest replaced",
            metadata_json={"replacement_quest_id": str(replacement.id)},
        )
    )

    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.replaced",
        metadata={
            **_quest_metadata(quest),
            "replacement_quest_id": str(replacement.id),
        },
    )
    _append_activity(
        session,
        entity_id=replacement.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.created",
        metadata=_quest_metadata(replacement),
    )

    session.commit()
    session.refresh(replacement)
    return replacement


def delete_quest(
    session: Session,
    *,
    quest: Quest,
    actor_id: UUID,
    organization_id: UUID,
) -> UUID:
    quest_id = quest.id
    metadata = _quest_metadata(quest)
    session.delete(quest)

    _append_activity(
        session,
        entity_id=quest_id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.deleted",
        metadata=metadata,
    )

    session.commit()
    return quest_id


def add_feedback(
    session: Session,
    *,
    quest: Quest,
    actor_id: UUID,
    organization_id: UUID,
    feedback_type: QuestFeedbackType,
    note: str | None,
    metadata_json: dict,
) -> QuestFeedback:
    feedback = QuestFeedback(
        quest_id=quest.id,
        actor_id=actor_id,
        feedback_type=feedback_type,
        note=note,
        metadata_json=metadata_json,
    )
    session.add(feedback)
    session.flush()

    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.feedback_added",
        metadata={
            **_quest_metadata(quest),
            "feedback_type": feedback_type.value,
        },
    )

    session.commit()
    session.refresh(feedback)
    return feedback


def list_objectives(session: Session, *, quest_id: UUID) -> list[QuestObjective]:
    return list(
        session.exec(
            select(QuestObjective)
            .where(QuestObjective.quest_id == quest_id)
            .order_by(col(QuestObjective.sort_order), col(QuestObjective.created_at))
        ).all()
    )


def create_objective(
    session: Session,
    *,
    quest: Quest,
    actor_id: UUID,
    organization_id: UUID,
    title: str,
    details: str | None,
    sort_order: int | None,
) -> QuestObjective:
    objective_sort_order = sort_order
    if objective_sort_order is None:
        existing = list_objectives(session, quest_id=quest.id)
        objective_sort_order = (max((row.sort_order for row in existing), default=-1) + 1)

    objective = QuestObjective(
        quest_id=quest.id,
        title=title,
        details=details,
        sort_order=objective_sort_order,
    )
    session.add(objective)
    session.flush()

    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.objective_added",
        metadata={
            **_quest_metadata(quest),
            "objective_id": str(objective.id),
            "objective_title": objective.title,
            "sort_order": objective.sort_order,
        },
    )

    session.commit()
    session.refresh(objective)
    return objective


def update_objective(
    session: Session,
    *,
    quest: Quest,
    objective_id: UUID,
    actor_id: UUID,
    organization_id: UUID,
    updates: dict,
) -> QuestObjective:
    objective = session.get(QuestObjective, objective_id)
    if objective is None or objective.quest_id != quest.id:
        raise QuestServiceError("Objective not found")

    if "is_done" in updates:
        is_done = bool(updates["is_done"])
        updates["completed_at"] = datetime.utcnow() if is_done else None

    for field_name, field_value in updates.items():
        setattr(objective, field_name, field_value)

    session.add(objective)
    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.objective_updated",
        metadata={
            **_quest_metadata(quest),
            "objective_id": str(objective.id),
            "objective_title": objective.title,
            "is_done": objective.is_done,
            "sort_order": objective.sort_order,
        },
    )

    session.commit()
    session.refresh(objective)
    return objective


def delete_objective(
    session: Session,
    *,
    quest: Quest,
    objective_id: UUID,
    actor_id: UUID,
    organization_id: UUID,
) -> UUID:
    objective = session.get(QuestObjective, objective_id)
    if objective is None or objective.quest_id != quest.id:
        raise QuestServiceError("Objective not found")

    deleted_id = objective.id
    deleted_title = objective.title
    session.delete(objective)
    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.objective_deleted",
        metadata={
            **_quest_metadata(quest),
            "objective_id": str(deleted_id),
            "objective_title": deleted_title,
        },
    )

    session.commit()
    return deleted_id


def list_assignments(session: Session, *, quest_id: UUID) -> list[QuestAssignment]:
    return list(
        session.exec(
            select(QuestAssignment)
            .where(QuestAssignment.quest_id == quest_id)
            .order_by(desc(col(QuestAssignment.assigned_at)))
        ).all()
    )


def create_assignment(
    session: Session,
    *,
    quest: Quest,
    actor_id: UUID,
    organization_id: UUID,
    agent_id: UUID | None,
    assignee_person_id: UUID | None,
    role: str | None,
    state: str,
) -> QuestAssignment:
    if agent_id is None and assignee_person_id is None:
        raise QuestServiceError("At least one assignee is required")

    assignment = QuestAssignment(
        quest_id=quest.id,
        agent_id=agent_id,
        assignee_person_id=assignee_person_id,
        role=role,
        state=state,
        assigned_by=actor_id,
    )
    session.add(assignment)
    session.flush()

    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.assignment_added",
        metadata={
            **_quest_metadata(quest),
            "assignment_id": str(assignment.id),
            "agent_id": str(assignment.agent_id) if assignment.agent_id else None,
            "assignee_person_id": (
                str(assignment.assignee_person_id) if assignment.assignee_person_id else None
            ),
            "role": assignment.role,
            "state": assignment.state,
        },
    )

    session.commit()
    session.refresh(assignment)
    return assignment


def update_assignment(
    session: Session,
    *,
    quest: Quest,
    assignment_id: UUID,
    actor_id: UUID,
    organization_id: UUID,
    updates: dict,
) -> QuestAssignment:
    assignment = session.get(QuestAssignment, assignment_id)
    if assignment is None or assignment.quest_id != quest.id:
        raise QuestServiceError("Assignment not found")

    for field_name, field_value in updates.items():
        setattr(assignment, field_name, field_value)

    session.add(assignment)
    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.assignment_updated",
        metadata={
            **_quest_metadata(quest),
            "assignment_id": str(assignment.id),
            "agent_id": str(assignment.agent_id) if assignment.agent_id else None,
            "assignee_person_id": (
                str(assignment.assignee_person_id) if assignment.assignee_person_id else None
            ),
            "role": assignment.role,
            "state": assignment.state,
        },
    )

    session.commit()
    session.refresh(assignment)
    return assignment


def delete_assignment(
    session: Session,
    *,
    quest: Quest,
    assignment_id: UUID,
    actor_id: UUID,
    organization_id: UUID,
) -> UUID:
    assignment = session.get(QuestAssignment, assignment_id)
    if assignment is None or assignment.quest_id != quest.id:
        raise QuestServiceError("Assignment not found")

    deleted_id = assignment.id
    session.delete(assignment)
    _append_activity(
        session,
        entity_id=quest.id,
        actor_id=actor_id,
        organization_id=organization_id,
        action="quest.assignment_deleted",
        metadata={
            **_quest_metadata(quest),
            "assignment_id": str(deleted_id),
        },
    )

    session.commit()
    return deleted_id
