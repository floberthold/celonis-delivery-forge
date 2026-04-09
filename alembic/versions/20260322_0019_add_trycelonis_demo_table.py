"""add trycelonis demo catalog table

Revision ID: 20260322_0019
Revises: 20260322_0018
Create Date: 2026-03-22 17:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260322_0019"
down_revision = "20260322_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trycelonisdemo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("catalog_url", sa.String(), nullable=True),
        sa.Column("source_kind", sa.String(), nullable=False),
        sa.Column("industries_json", sa.JSON(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("image_urls_json", sa.JSON(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("is_visible", sa.Boolean(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trycelonisdemo_organization_id"), "trycelonisdemo", ["organization_id"], unique=False)
    op.create_index(op.f("ix_trycelonisdemo_title"), "trycelonisdemo", ["title"], unique=False)
    op.create_index(op.f("ix_trycelonisdemo_slug"), "trycelonisdemo", ["slug"], unique=False)
    op.create_index(op.f("ix_trycelonisdemo_source_url"), "trycelonisdemo", ["source_url"], unique=False)
    op.create_index(op.f("ix_trycelonisdemo_source_kind"), "trycelonisdemo", ["source_kind"], unique=False)
    op.create_index(op.f("ix_trycelonisdemo_last_synced_at"), "trycelonisdemo", ["last_synced_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trycelonisdemo_last_synced_at"), table_name="trycelonisdemo")
    op.drop_index(op.f("ix_trycelonisdemo_source_kind"), table_name="trycelonisdemo")
    op.drop_index(op.f("ix_trycelonisdemo_source_url"), table_name="trycelonisdemo")
    op.drop_index(op.f("ix_trycelonisdemo_slug"), table_name="trycelonisdemo")
    op.drop_index(op.f("ix_trycelonisdemo_title"), table_name="trycelonisdemo")
    op.drop_index(op.f("ix_trycelonisdemo_organization_id"), table_name="trycelonisdemo")
    op.drop_table("trycelonisdemo")