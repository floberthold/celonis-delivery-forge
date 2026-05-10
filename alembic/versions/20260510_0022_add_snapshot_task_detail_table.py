"""add snapshot task detail table

Revision ID: 20260510_0022
Revises: 20260510_0021
Create Date: 2026-05-10 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260510_0022"
down_revision = "20260510_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "snapshottaskdetail",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("package_id", sa.String(), nullable=True),
        sa.Column("task_type", sa.String(), nullable=True),
        sa.Column("source_endpoint", sa.String(), nullable=True),
        sa.Column("detail_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("references_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("dependencies_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_snapshottaskdetail_snapshot_id", "snapshottaskdetail", ["snapshot_id"])
    op.create_index("ix_snapshottaskdetail_client_id", "snapshottaskdetail", ["client_id"])
    op.create_index("ix_snapshottaskdetail_task_id", "snapshottaskdetail", ["task_id"])
    op.create_index("ix_snapshottaskdetail_package_id", "snapshottaskdetail", ["package_id"])


def downgrade() -> None:
    op.drop_table("snapshottaskdetail")
