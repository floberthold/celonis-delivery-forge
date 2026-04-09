"""add celonis deployment requests table

Revision ID: 20260322_0016
Revises: 20260322_0015
Create Date: 2026-03-22 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260322_0016"
down_revision = "20260322_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "celonisdeploymentrequest",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("person.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("target_space_name", sa.String(), nullable=True),
        sa.Column("target_package_key", sa.String(), nullable=True),
        sa.Column("target_package_name", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("preflight_run_id", sa.String(), nullable=True),
        sa.Column("preflight_passed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("permission_diff_acknowledged", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("permission_diff_acknowledged_by", sa.Uuid(), nullable=True),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("reviewer_decision", sa.String(), nullable=True),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_celonisdeploymentrequest_organization_id", "celonisdeploymentrequest", ["organization_id"])
    op.create_index("ix_celonisdeploymentrequest_project_id", "celonisdeploymentrequest", ["project_id"])
    op.create_index("ix_celonisdeploymentrequest_client_id", "celonisdeploymentrequest", ["client_id"])
    op.create_index("ix_celonisdeploymentrequest_created_by", "celonisdeploymentrequest", ["created_by"])
    op.create_index("ix_celonisdeploymentrequest_status", "celonisdeploymentrequest", ["status"])
    op.create_index("ix_celonisdeploymentrequest_reviewer_id", "celonisdeploymentrequest", ["reviewer_id"])
    op.create_index("ix_celonisdeploymentrequest_permission_diff_acknowledged_by", "celonisdeploymentrequest", ["permission_diff_acknowledged_by"])


def downgrade() -> None:
    op.drop_index("ix_celonisdeploymentrequest_permission_diff_acknowledged_by", table_name="celonisdeploymentrequest")
    op.drop_index("ix_celonisdeploymentrequest_reviewer_id", table_name="celonisdeploymentrequest")
    op.drop_index("ix_celonisdeploymentrequest_status", table_name="celonisdeploymentrequest")
    op.drop_index("ix_celonisdeploymentrequest_created_by", table_name="celonisdeploymentrequest")
    op.drop_index("ix_celonisdeploymentrequest_client_id", table_name="celonisdeploymentrequest")
    op.drop_index("ix_celonisdeploymentrequest_project_id", table_name="celonisdeploymentrequest")
    op.drop_index("ix_celonisdeploymentrequest_organization_id", table_name="celonisdeploymentrequest")
    op.drop_table("celonisdeploymentrequest")
