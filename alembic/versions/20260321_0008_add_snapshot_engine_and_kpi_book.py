"""add celonis snapshot engine and kpi book

Revision ID: 20260321_0012
Revises: 20260321_0011
Create Date: 2026-03-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260321_0012"
down_revision = "20260321_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # celonissnapshot
    op.create_table(
        "celonissnapshot",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False, index=True),
        sa.Column("triggered_by", sa.Uuid(), sa.ForeignKey("person.id"), nullable=False, index=True),
        sa.Column("status", sa.String(), nullable=False, index=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    # snapshotpackage
    op.create_table(
        "snapshotpackage",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False, index=True),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=True),
        sa.Column("space_id", sa.String(), nullable=True),
        sa.Column("space_name", sa.String(), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # snapshottask
    op.create_table(
        "snapshottask",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False, index=True),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(), nullable=True, index=True),
        sa.Column("task_id", sa.String(), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("task_type", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pql_formula", sa.Text(), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # snapshotdatamodel
    op.create_table(
        "snapshotdatamodel",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False, index=True),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False, index=True),
        sa.Column("data_model_id", sa.String(), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("space_id", sa.String(), nullable=True),
        sa.Column("space_name", sa.String(), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # snapshotjob
    op.create_table(
        "snapshotjob",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False, index=True),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False, index=True),
        sa.Column("job_id", sa.String(), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("pool_id", sa.String(), nullable=True),
        sa.Column("pool_name", sa.String(), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # snapshotknowledgemodel
    op.create_table(
        "snapshotknowledgemodel",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False, index=True),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False, index=True),
        sa.Column("km_id", sa.String(), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("space_id", sa.String(), nullable=True),
        sa.Column("space_name", sa.String(), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # kpibookentry
    op.create_table(
        "kpibookentry",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False, index=True),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=True, index=True),
        sa.Column("snapshot_task_id", sa.Uuid(), sa.ForeignKey("snapshottask.id"), nullable=True, index=True),
        sa.Column("saved_by", sa.Uuid(), sa.ForeignKey("person.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pql_formula", sa.Text(), nullable=True),
        sa.Column("package_name", sa.String(), nullable=True),
        sa.Column("task_type", sa.String(), nullable=True),
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default="0", index=True),
        sa.Column("tags_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("kpibookentry")
    op.drop_table("snapshotknowledgemodel")
    op.drop_table("snapshotjob")
    op.drop_table("snapshotdatamodel")
    op.drop_table("snapshottask")
    op.drop_table("snapshotpackage")
    op.drop_table("celonissnapshot")
