"""add salesforce_url to client and project

Revision ID: 20260321_0009
Revises: 20260321_0008
Create Date: 2026-03-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0009"
down_revision = "20260321_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    table_names = set(inspector.get_table_names())
    if "client" in table_names:
        client_columns = {column["name"] for column in inspector.get_columns("client")}
        if "salesforce_url" not in client_columns:
            op.add_column("client", sa.Column("salesforce_url", sa.String(), nullable=True))

    if "project" in table_names:
        project_columns = {column["name"] for column in inspector.get_columns("project")}
        if "salesforce_url" not in project_columns:
            op.add_column("project", sa.Column("salesforce_url", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    table_names = set(inspector.get_table_names())
    if "project" in table_names:
        project_columns = {column["name"] for column in inspector.get_columns("project")}
        if "salesforce_url" in project_columns:
            op.drop_column("project", "salesforce_url")

    if "client" in table_names:
        client_columns = {column["name"] for column in inspector.get_columns("client")}
        if "salesforce_url" in client_columns:
            op.drop_column("client", "salesforce_url")
