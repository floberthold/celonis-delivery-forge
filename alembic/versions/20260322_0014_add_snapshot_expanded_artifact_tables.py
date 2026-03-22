"""add expanded Celonis snapshot artifact tables (spaces, apps, data pools, transformations)

Revision ID: 20260322_0014
Revises: 20260321_0013
Create Date: 2026-03-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260322_0014"
down_revision = "20260321_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # snapshotspace
    op.create_table(
        "snapshotspace",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("space_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_snapshotspace_snapshot_id", "snapshotspace", ["snapshot_id"])
    op.create_index("ix_snapshotspace_client_id", "snapshotspace", ["client_id"])
    op.create_index("ix_snapshotspace_space_id", "snapshotspace", ["space_id"])

    # snapshotapp
    op.create_table(
        "snapshotapp",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("app_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("space_id", sa.String(), nullable=True),
        sa.Column("space_name", sa.String(), nullable=True),
        sa.Column("package_key", sa.String(), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_snapshotapp_snapshot_id", "snapshotapp", ["snapshot_id"])
    op.create_index("ix_snapshotapp_client_id", "snapshotapp", ["client_id"])
    op.create_index("ix_snapshotapp_app_id", "snapshotapp", ["app_id"])

    # snapshotdatapool
    op.create_table(
        "snapshotdatapool",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("pool_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_snapshotdatapool_snapshot_id", "snapshotdatapool", ["snapshot_id"])
    op.create_index("ix_snapshotdatapool_client_id", "snapshotdatapool", ["client_id"])
    op.create_index("ix_snapshotdatapool_pool_id", "snapshotdatapool", ["pool_id"])

    # snapshottransformation
    op.create_table(
        "snapshottransformation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("transformation_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("pool_id", sa.String(), nullable=True),
        sa.Column("pool_name", sa.String(), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_snapshottransformation_snapshot_id", "snapshottransformation", ["snapshot_id"])
    op.create_index("ix_snapshottransformation_client_id", "snapshottransformation", ["client_id"])
    op.create_index("ix_snapshottransformation_transformation_id", "snapshottransformation", ["transformation_id"])
    op.create_index("ix_snapshottransformation_pool_id", "snapshottransformation", ["pool_id"])


def downgrade() -> None:
    op.drop_table("snapshottransformation")
    op.drop_table("snapshotdatapool")
    op.drop_table("snapshotapp")
    op.drop_table("snapshotspace")
