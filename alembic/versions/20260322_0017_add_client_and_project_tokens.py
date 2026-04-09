"""add client and project level celonis tokens

Revision ID: 20260322_0017
Revises: 20260322_0016
Create Date: 2026-03-22 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260322_0017"
down_revision = "20260322_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add token_name column to existing CelonisUserToken
    op.add_column("celonisuusertoken", sa.Column("token_name", sa.String(), nullable=True))

    # Create CelonisClientToken table
    op.create_table(
        "celonisclienttoken",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("client_id", sa.Uuid(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("token_name", sa.String(), nullable=True),
        sa.Column("token_value", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "client_id", name="uq_celonis_client_token_org_client"),
    )
    op.create_index("ix_celonisclienttoken_organization_id", "celonisclienttoken", ["organization_id"])
    op.create_index("ix_celonisclienttoken_client_id", "celonisclienttoken", ["client_id"])

    # Create CelonisProjectToken table
    op.create_table(
        "celonisprojecttoken",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("token_name", sa.String(), nullable=True),
        sa.Column("token_value", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "project_id", name="uq_celonis_project_token_org_project"),
    )
    op.create_index("ix_celonisprojecttoken_organization_id", "celonisprojecttoken", ["organization_id"])
    op.create_index("ix_celonisprojecttoken_project_id", "celonisprojecttoken", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_celonisprojecttoken_project_id", table_name="celonisprojecttoken")
    op.drop_index("ix_celonisprojecttoken_organization_id", table_name="celonisprojecttoken")
    op.drop_table("celonisprojecttoken")

    op.drop_index("ix_celonisclienttoken_client_id", table_name="celonisclienttoken")
    op.drop_index("ix_celonisclienttoken_organization_id", table_name="celonisclienttoken")
    op.drop_table("celonisclienttoken")

    op.drop_column("celonisuusertoken", "token_name")
