"""add organization tables

Revision ID: 20260320_0004
Revises: 20260319_0003
Create Date: 2026-03-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260320_0004"
down_revision = "20260319_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organization_slug"), "organization", ["slug"], unique=True)

    op.create_table(
        "organizationmembership",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_organizationmembership_organization_id"),
        "organizationmembership",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organizationmembership_person_id"),
        "organizationmembership",
        ["person_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_organizationmembership_person_id"), table_name="organizationmembership")
    op.drop_index(op.f("ix_organizationmembership_organization_id"), table_name="organizationmembership")
    op.drop_table("organizationmembership")

    op.drop_index(op.f("ix_organization_slug"), table_name="organization")
    op.drop_table("organization")
