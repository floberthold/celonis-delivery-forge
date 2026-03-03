from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import EntityType, Todo, TodoStatus
from foundry.schemas import TodoCreate, TodoOut, TodoUpdate
from foundry.services.activity_log import log_activity

router = APIRouter(prefix="/todos", tags=["todos"])


def _validate_scope(*, person_id: UUID | None, client_id: UUID | None, project_id: UUID | None) -> None:
    scopes = [person_id, client_id, project_id]
    selected = sum(1 for value in scopes if value is not None)
    if selected != 1:
        raise HTTPException(status_code=400, detail="Exactly one of person_id, client_id, project_id is required")


@router.post("/", response_model=TodoOut)
def create_todo(payload: TodoCreate, session: Session = Depends(get_session)):
    _validate_scope(person_id=payload.person_id, client_id=payload.client_id, project_id=payload.project_id)
    todo = Todo(**payload.model_dump())
    session.add(todo)
    session.commit()
    session.refresh(todo)

    log_activity(
        session,
        entity_type=EntityType.todo,
        entity_id=todo.id,
        actor_id=todo.created_by,
        action="todo.created",
        metadata={
            "person_id": str(todo.person_id) if todo.person_id else None,
            "client_id": str(todo.client_id) if todo.client_id else None,
            "project_id": str(todo.project_id) if todo.project_id else None,
            "status": todo.status.value,
            "priority": todo.priority.value,
        },
    )
    return todo


@router.get("/", response_model=list[TodoOut])
def list_todos(
    person_id: UUID | None = None,
    client_id: UUID | None = None,
    project_id: UUID | None = None,
    assignee_id: UUID | None = None,
    status: TodoStatus | None = None,
    session: Session = Depends(get_session),
):
    stmt = select(Todo)
    if person_id:
        stmt = stmt.where(Todo.person_id == person_id)
    if client_id:
        stmt = stmt.where(Todo.client_id == client_id)
    if project_id:
        stmt = stmt.where(Todo.project_id == project_id)
    if assignee_id:
        stmt = stmt.where(Todo.assignee_id == assignee_id)
    if status:
        stmt = stmt.where(Todo.status == status)
    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda row: row.created_at, reverse=True)
    return rows


@router.patch("/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: UUID, payload: TodoUpdate, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    updates = payload.model_dump(exclude_unset=True)
    for field_name, field_value in updates.items():
        setattr(todo, field_name, field_value)

    if payload.status is not None:
        if payload.status == TodoStatus.done:
            todo.completed_at = datetime.utcnow()
        else:
            todo.completed_at = None

    todo.updated_at = datetime.utcnow()
    session.add(todo)
    session.commit()
    session.refresh(todo)

    log_activity(
        session,
        entity_type=EntityType.todo,
        entity_id=todo.id,
        actor_id=todo.created_by,
        action="todo.updated",
        metadata={"status": todo.status.value, "priority": todo.priority.value},
    )
    return todo


@router.delete("/{todo_id}")
def delete_todo(todo_id: UUID, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    actor_id = todo.created_by
    session.delete(todo)
    session.commit()

    log_activity(
        session,
        entity_type=EntityType.todo,
        entity_id=todo_id,
        actor_id=actor_id,
        action="todo.deleted",
    )
    return {"deleted": True, "id": str(todo_id)}
