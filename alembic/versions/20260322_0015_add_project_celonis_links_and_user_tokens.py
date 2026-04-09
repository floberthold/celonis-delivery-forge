"""add project celonis links and per-user celonis tokens

Revision ID: 20260322_0015
Revises: 20260322_0014
Create Date: 2026-03-22 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260322_0015"
down_revision = "20260322_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("project", sa.Column("celonis_package_url", sa.String(), nullable=True))
    op.add_column("project", sa.Column("celonis_app_url", sa.String(), nullable=True))

    op.create_table(
        "celonisuusertoken",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("person_id", sa.Uuid(), sa.ForeignKey("person.id"), nullable=False),
        sa.Column("token_value", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "person_id", name="uq_celonis_user_token_org_person"),
    )
    op.create_index("ix_celonisuusertoken_organization_id", "celonisuusertoken", ["organization_id"])
    op.create_index("ix_celonisuusertoken_person_id", "celonisuusertoken", ["person_id"])


def downgrade() -> None:
    op.drop_index("ix_celonisuusertoken_person_id", table_name="celonisuusertoken")
    op.drop_index("ix_celonisuusertoken_organization_id", table_name="celonisuusertoken")
    op.drop_table("celonisuusertoken")
    op.drop_column("project", "celonis_app_url")
    op.drop_column("project", "celonis_package_url")
