"""add todo table

Revision ID: 20260303_0002
Revises: 20260302_0001
Create Date: 2026-03-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260303_0002"
down_revision = "20260302_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "todo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=True),
        sa.Column("client_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "(CASE WHEN person_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN client_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN project_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_todo_exactly_one_scope",
        ),
        sa.ForeignKeyConstraint(["assignee_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["person.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["client.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_todo_assignee_id"), "todo", ["assignee_id"], unique=False)
    op.create_index(op.f("ix_todo_created_by"), "todo", ["created_by"], unique=False)
    op.create_index(op.f("ix_todo_status"), "todo", ["status"], unique=False)
    op.create_index(op.f("ix_todo_due_at"), "todo", ["due_at"], unique=False)
    op.create_index(op.f("ix_todo_person_id"), "todo", ["person_id"], unique=False)
    op.create_index(op.f("ix_todo_client_id"), "todo", ["client_id"], unique=False)
    op.create_index(op.f("ix_todo_project_id"), "todo", ["project_id"], unique=False)
    op.create_index("ix_todo_project_status_due", "todo", ["project_id", "status", "due_at"], unique=False)
    op.create_index("ix_todo_client_status_due", "todo", ["client_id", "status", "due_at"], unique=False)
    op.create_index("ix_todo_person_status_due", "todo", ["person_id", "status", "due_at"], unique=False)

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "activitylog" in inspector.get_table_names():
        existing_indexes = {index["name"] for index in inspector.get_indexes("activitylog")}
        if "ix_activitylog_entity_type_entity_id_timestamp" not in existing_indexes:
            op.create_index(
                "ix_activitylog_entity_type_entity_id_timestamp",
                "activitylog",
                ["entity_type", "entity_id", "timestamp"],
                unique=False,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "activitylog" in inspector.get_table_names():
        existing_indexes = {index["name"] for index in inspector.get_indexes("activitylog")}
        if "ix_activitylog_entity_type_entity_id_timestamp" in existing_indexes:
            op.drop_index("ix_activitylog_entity_type_entity_id_timestamp", table_name="activitylog")

    op.drop_index("ix_todo_person_status_due", table_name="todo")
    op.drop_index("ix_todo_client_status_due", table_name="todo")
    op.drop_index("ix_todo_project_status_due", table_name="todo")
    op.drop_index(op.f("ix_todo_project_id"), table_name="todo")
    op.drop_index(op.f("ix_todo_client_id"), table_name="todo")
    op.drop_index(op.f("ix_todo_person_id"), table_name="todo")
    op.drop_index(op.f("ix_todo_due_at"), table_name="todo")
    op.drop_index(op.f("ix_todo_status"), table_name="todo")
    op.drop_index(op.f("ix_todo_created_by"), table_name="todo")
    op.drop_index(op.f("ix_todo_assignee_id"), table_name="todo")
    op.drop_table("todo")
