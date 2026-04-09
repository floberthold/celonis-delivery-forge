"""add extraction diagnostics for packages

Revision ID: 20260322_0018
Revises: 20260322_0017
Create Date: 2026-03-22 03:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260322_0018"
down_revision = "20260322_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("snapshotpackage", sa.Column("extraction_diagnostics", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("snapshotpackage", "extraction_diagnostics")
