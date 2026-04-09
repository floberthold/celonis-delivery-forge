"""add gitlab ci tables

Revision ID: 20260321_0008
Revises: 20260321_0007
Create Date: 2026-03-21 00:08:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0008"
down_revision = "20260321_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gitlabrepo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("repo_path", sa.String(), nullable=False),
        sa.Column("token_override", sa.String(), nullable=True),
        sa.Column("default_branch", sa.String(), nullable=False),
        sa.Column("webhook_secret", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gitlabrepo_project_id"), "gitlabrepo", ["project_id"], unique=False)
    op.create_index(op.f("ix_gitlabrepo_created_by"), "gitlabrepo", ["created_by"], unique=False)

    op.create_table(
        "gitlabpipelinerun",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repo_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_id", sa.Integer(), nullable=False),
        sa.Column("ref", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("triggered_by", sa.Uuid(), nullable=True),
        sa.Column("triggered_at", sa.DateTime(), nullable=False),
        sa.Column("web_url", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["gitlabrepo.id"]),
        sa.ForeignKeyConstraint(["triggered_by"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gitlabpipelinerun_repo_id"), "gitlabpipelinerun", ["repo_id"], unique=False)
    op.create_index(
        op.f("ix_gitlabpipelinerun_pipeline_id"),
        "gitlabpipelinerun",
        ["pipeline_id"],
        unique=False,
    )
    op.create_index(op.f("ix_gitlabpipelinerun_status"), "gitlabpipelinerun", ["status"], unique=False)
    op.create_index(
        op.f("ix_gitlabpipelinerun_triggered_by"),
        "gitlabpipelinerun",
        ["triggered_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_gitlabpipelinerun_triggered_by"), table_name="gitlabpipelinerun")
    op.drop_index(op.f("ix_gitlabpipelinerun_status"), table_name="gitlabpipelinerun")
    op.drop_index(op.f("ix_gitlabpipelinerun_pipeline_id"), table_name="gitlabpipelinerun")
    op.drop_index(op.f("ix_gitlabpipelinerun_repo_id"), table_name="gitlabpipelinerun")
    op.drop_table("gitlabpipelinerun")

    op.drop_index(op.f("ix_gitlabrepo_created_by"), table_name="gitlabrepo")
    op.drop_index(op.f("ix_gitlabrepo_project_id"), table_name="gitlabrepo")
    op.drop_table("gitlabrepo")
