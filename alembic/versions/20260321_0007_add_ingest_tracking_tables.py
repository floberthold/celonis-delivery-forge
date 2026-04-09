"""add ingest tracking tables

Revision ID: 20260321_0007
Revises: 20260321_0006
Create Date: 2026-03-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0007"
down_revision = "20260321_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assetsource",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("repo_url", sa.String(), nullable=True),
        sa.Column("default_branch", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assetsource_organization_id"), "assetsource", ["organization_id"], unique=False)
    op.create_index(op.f("ix_assetsource_name"), "assetsource", ["name"], unique=False)
    op.create_index(op.f("ix_assetsource_kind"), "assetsource", ["kind"], unique=False)
    op.create_index(op.f("ix_assetsource_provider"), "assetsource", ["provider"], unique=False)

    op.create_table(
        "assetsnapshot",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_source_id", sa.Uuid(), nullable=False),
        sa.Column("version_label", sa.String(), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=True),
        sa.Column("manifest_path", sa.String(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asset_source_id"], ["assetsource.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assetsnapshot_asset_source_id"), "assetsnapshot", ["asset_source_id"], unique=False)
    op.create_index(op.f("ix_assetsnapshot_received_at"), "assetsnapshot", ["received_at"], unique=False)

    op.create_table(
        "ingestrun",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_source_id", sa.Uuid(), nullable=False),
        sa.Column("asset_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("triggered_by", sa.Uuid(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asset_source_id"], ["assetsource.id"]),
        sa.ForeignKeyConstraint(["asset_snapshot_id"], ["assetsnapshot.id"]),
        sa.ForeignKeyConstraint(["triggered_by"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestrun_asset_source_id"), "ingestrun", ["asset_source_id"], unique=False)
    op.create_index(op.f("ix_ingestrun_asset_snapshot_id"), "ingestrun", ["asset_snapshot_id"], unique=False)
    op.create_index(op.f("ix_ingestrun_status"), "ingestrun", ["status"], unique=False)
    op.create_index(op.f("ix_ingestrun_triggered_by"), "ingestrun", ["triggered_by"], unique=False)
    op.create_index(op.f("ix_ingestrun_created_at"), "ingestrun", ["created_at"], unique=False)

    op.create_table(
        "ingestfinding",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ingest_run_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("finding_type", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("is_blocking", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ingest_run_id"], ["ingestrun.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestfinding_ingest_run_id"), "ingestfinding", ["ingest_run_id"], unique=False)
    op.create_index(op.f("ix_ingestfinding_severity"), "ingestfinding", ["severity"], unique=False)
    op.create_index(op.f("ix_ingestfinding_finding_type"), "ingestfinding", ["finding_type"], unique=False)
    op.create_index(op.f("ix_ingestfinding_is_blocking"), "ingestfinding", ["is_blocking"], unique=False)
    op.create_index(op.f("ix_ingestfinding_created_at"), "ingestfinding", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ingestfinding_created_at"), table_name="ingestfinding")
    op.drop_index(op.f("ix_ingestfinding_is_blocking"), table_name="ingestfinding")
    op.drop_index(op.f("ix_ingestfinding_finding_type"), table_name="ingestfinding")
    op.drop_index(op.f("ix_ingestfinding_severity"), table_name="ingestfinding")
    op.drop_index(op.f("ix_ingestfinding_ingest_run_id"), table_name="ingestfinding")
    op.drop_table("ingestfinding")

    op.drop_index(op.f("ix_ingestrun_created_at"), table_name="ingestrun")
    op.drop_index(op.f("ix_ingestrun_triggered_by"), table_name="ingestrun")
    op.drop_index(op.f("ix_ingestrun_status"), table_name="ingestrun")
    op.drop_index(op.f("ix_ingestrun_asset_snapshot_id"), table_name="ingestrun")
    op.drop_index(op.f("ix_ingestrun_asset_source_id"), table_name="ingestrun")
    op.drop_table("ingestrun")

    op.drop_index(op.f("ix_assetsnapshot_received_at"), table_name="assetsnapshot")
    op.drop_index(op.f("ix_assetsnapshot_asset_source_id"), table_name="assetsnapshot")
    op.drop_table("assetsnapshot")

    op.drop_index(op.f("ix_assetsource_provider"), table_name="assetsource")
    op.drop_index(op.f("ix_assetsource_kind"), table_name="assetsource")
    op.drop_index(op.f("ix_assetsource_name"), table_name="assetsource")
    op.drop_index(op.f("ix_assetsource_organization_id"), table_name="assetsource")
    op.drop_table("assetsource")
