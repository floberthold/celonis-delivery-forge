"""add agent and quest orchestration tables

Revision ID: 20260321_0013
Revises: 20260321_0012
Create Date: 2026-03-21 01:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0013"
down_revision = "20260321_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role_label", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("capability_summary_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("is_system_agent", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_organization_id"), "agent", ["organization_id"], unique=False)
    op.create_index(op.f("ix_agent_name"), "agent", ["name"], unique=False)
    op.create_index(op.f("ix_agent_status"), "agent", ["status"], unique=False)
    op.create_index(op.f("ix_agent_created_by"), "agent", ["created_by"], unique=False)
    op.create_index(op.f("ix_agent_is_system_agent"), "agent", ["is_system_agent"], unique=False)

    op.create_table(
        "agentcapability",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("skill", sa.String(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agentcapability_agent_id"), "agentcapability", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agentcapability_skill"), "agentcapability", ["skill"], unique=False)

    op.create_table(
        "quest",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("owner_person_id", sa.Uuid(), nullable=True),
        sa.Column("suggested_by_agent_id", sa.Uuid(), nullable=True),
        sa.Column("client_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("linked_todo_id", sa.Uuid(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["owner_person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["suggested_by_agent_id"], ["agent.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["client.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["linked_todo_id"], ["todo.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quest_organization_id"), "quest", ["organization_id"], unique=False)
    op.create_index(op.f("ix_quest_title"), "quest", ["title"], unique=False)
    op.create_index(op.f("ix_quest_status"), "quest", ["status"], unique=False)
    op.create_index(op.f("ix_quest_source"), "quest", ["source"], unique=False)
    op.create_index(op.f("ix_quest_priority"), "quest", ["priority"], unique=False)
    op.create_index(op.f("ix_quest_owner_person_id"), "quest", ["owner_person_id"], unique=False)
    op.create_index(op.f("ix_quest_suggested_by_agent_id"), "quest", ["suggested_by_agent_id"], unique=False)
    op.create_index(op.f("ix_quest_client_id"), "quest", ["client_id"], unique=False)
    op.create_index(op.f("ix_quest_project_id"), "quest", ["project_id"], unique=False)
    op.create_index(op.f("ix_quest_linked_todo_id"), "quest", ["linked_todo_id"], unique=False)
    op.create_index(op.f("ix_quest_due_at"), "quest", ["due_at"], unique=False)
    op.create_index(op.f("ix_quest_created_by"), "quest", ["created_by"], unique=False)
    op.create_index(op.f("ix_quest_created_at"), "quest", ["created_at"], unique=False)

    op.create_table(
        "questobjective",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quest_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["quest_id"], ["quest.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questobjective_quest_id"), "questobjective", ["quest_id"], unique=False)
    op.create_index(op.f("ix_questobjective_is_done"), "questobjective", ["is_done"], unique=False)

    op.create_table(
        "questassignment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quest_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=True),
        sa.Column("assignee_person_id", sa.Uuid(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=False, server_default="assigned"),
        sa.Column("assigned_by", sa.Uuid(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["quest_id"], ["quest.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"]),
        sa.ForeignKeyConstraint(["assignee_person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["assigned_by"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questassignment_quest_id"), "questassignment", ["quest_id"], unique=False)
    op.create_index(op.f("ix_questassignment_agent_id"), "questassignment", ["agent_id"], unique=False)
    op.create_index(
        op.f("ix_questassignment_assignee_person_id"),
        "questassignment",
        ["assignee_person_id"],
        unique=False,
    )
    op.create_index(op.f("ix_questassignment_state"), "questassignment", ["state"], unique=False)
    op.create_index(op.f("ix_questassignment_assigned_by"), "questassignment", ["assigned_by"], unique=False)

    op.create_table(
        "questfeedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quest_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("feedback_type", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["quest_id"], ["quest.id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questfeedback_quest_id"), "questfeedback", ["quest_id"], unique=False)
    op.create_index(op.f("ix_questfeedback_actor_id"), "questfeedback", ["actor_id"], unique=False)
    op.create_index(op.f("ix_questfeedback_feedback_type"), "questfeedback", ["feedback_type"], unique=False)
    op.create_index(op.f("ix_questfeedback_created_at"), "questfeedback", ["created_at"], unique=False)

    op.create_table(
        "taskdependency",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("blocker_todo_id", sa.Uuid(), nullable=False),
        sa.Column("dependent_todo_id", sa.Uuid(), nullable=False),
        sa.Column("dependency_type", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["blocker_todo_id"], ["todo.id"]),
        sa.ForeignKeyConstraint(["dependent_todo_id"], ["todo.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_taskdependency_organization_id"), "taskdependency", ["organization_id"], unique=False)
    op.create_index(op.f("ix_taskdependency_blocker_todo_id"), "taskdependency", ["blocker_todo_id"], unique=False)
    op.create_index(op.f("ix_taskdependency_dependent_todo_id"), "taskdependency", ["dependent_todo_id"], unique=False)
    op.create_index(op.f("ix_taskdependency_dependency_type"), "taskdependency", ["dependency_type"], unique=False)
    op.create_index(op.f("ix_taskdependency_created_by"), "taskdependency", ["created_by"], unique=False)
    op.create_index(op.f("ix_taskdependency_created_at"), "taskdependency", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_taskdependency_created_at"), table_name="taskdependency")
    op.drop_index(op.f("ix_taskdependency_created_by"), table_name="taskdependency")
    op.drop_index(op.f("ix_taskdependency_dependency_type"), table_name="taskdependency")
    op.drop_index(op.f("ix_taskdependency_dependent_todo_id"), table_name="taskdependency")
    op.drop_index(op.f("ix_taskdependency_blocker_todo_id"), table_name="taskdependency")
    op.drop_index(op.f("ix_taskdependency_organization_id"), table_name="taskdependency")
    op.drop_table("taskdependency")

    op.drop_index(op.f("ix_questfeedback_created_at"), table_name="questfeedback")
    op.drop_index(op.f("ix_questfeedback_feedback_type"), table_name="questfeedback")
    op.drop_index(op.f("ix_questfeedback_actor_id"), table_name="questfeedback")
    op.drop_index(op.f("ix_questfeedback_quest_id"), table_name="questfeedback")
    op.drop_table("questfeedback")

    op.drop_index(op.f("ix_questassignment_assigned_by"), table_name="questassignment")
    op.drop_index(op.f("ix_questassignment_state"), table_name="questassignment")
    op.drop_index(op.f("ix_questassignment_assignee_person_id"), table_name="questassignment")
    op.drop_index(op.f("ix_questassignment_agent_id"), table_name="questassignment")
    op.drop_index(op.f("ix_questassignment_quest_id"), table_name="questassignment")
    op.drop_table("questassignment")

    op.drop_index(op.f("ix_questobjective_is_done"), table_name="questobjective")
    op.drop_index(op.f("ix_questobjective_quest_id"), table_name="questobjective")
    op.drop_table("questobjective")

    op.drop_index(op.f("ix_quest_created_at"), table_name="quest")
    op.drop_index(op.f("ix_quest_created_by"), table_name="quest")
    op.drop_index(op.f("ix_quest_due_at"), table_name="quest")
    op.drop_index(op.f("ix_quest_linked_todo_id"), table_name="quest")
    op.drop_index(op.f("ix_quest_project_id"), table_name="quest")
    op.drop_index(op.f("ix_quest_client_id"), table_name="quest")
    op.drop_index(op.f("ix_quest_suggested_by_agent_id"), table_name="quest")
    op.drop_index(op.f("ix_quest_owner_person_id"), table_name="quest")
    op.drop_index(op.f("ix_quest_priority"), table_name="quest")
    op.drop_index(op.f("ix_quest_source"), table_name="quest")
    op.drop_index(op.f("ix_quest_status"), table_name="quest")
    op.drop_index(op.f("ix_quest_title"), table_name="quest")
    op.drop_index(op.f("ix_quest_organization_id"), table_name="quest")
    op.drop_table("quest")

    op.drop_index(op.f("ix_agentcapability_skill"), table_name="agentcapability")
    op.drop_index(op.f("ix_agentcapability_agent_id"), table_name="agentcapability")
    op.drop_table("agentcapability")

    op.drop_index(op.f("ix_agent_is_system_agent"), table_name="agent")
    op.drop_index(op.f("ix_agent_created_by"), table_name="agent")
    op.drop_index(op.f("ix_agent_status"), table_name="agent")
    op.drop_index(op.f("ix_agent_name"), table_name="agent")
    op.drop_index(op.f("ix_agent_organization_id"), table_name="agent")
    op.drop_table("agent")
