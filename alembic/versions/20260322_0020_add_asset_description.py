"""add description column to asset

Revision ID: 20260322_0020
Revises: 20260322_0019
Create Date: 2026-03-22 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260322_0020"
down_revision = "20260322_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("asset", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("asset", "description")
