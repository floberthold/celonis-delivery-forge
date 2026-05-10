"""add snapshot package definition table

Revision ID: 20260510_0021
Revises: 20260322_0020
Create Date: 2026-05-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260510_0021"
down_revision = "20260322_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "snapshotpackagedefinition",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), sa.ForeignKey("celonissnapshot.id"), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("package_key", sa.String(), nullable=True),
        sa.Column("definition_id", sa.String(), nullable=False, server_default="studio.config.yaml"),
        sa.Column("source_endpoint", sa.String(), nullable=True),
        sa.Column("raw_yaml", sa.Text(), nullable=False, server_default=""),
        sa.Column("parsed_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_snapshotpackagedefinition_snapshot_id",
        "snapshotpackagedefinition",
        ["snapshot_id"],
    )
    op.create_index(
        "ix_snapshotpackagedefinition_client_id",
        "snapshotpackagedefinition",
        ["client_id"],
    )
    op.create_index(
        "ix_snapshotpackagedefinition_package_id",
        "snapshotpackagedefinition",
        ["package_id"],
    )
    op.create_index(
        "ix_snapshotpackagedefinition_definition_id",
        "snapshotpackagedefinition",
        ["definition_id"],
    )


def downgrade() -> None:
    op.drop_table("snapshotpackagedefinition")
