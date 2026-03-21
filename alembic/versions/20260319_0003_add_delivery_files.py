"""add delivery files table and library_type to templates

Revision ID: 20260321_0010
Revises: 20260321_0009
Create Date: 2026-03-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0010"
down_revision = "20260321_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add library_type column to templatelibrary
    op.add_column(
        "templatelibrary",
        sa.Column("library_type", sa.String(), nullable=False, server_default="template"),
    )
    # Add base_url column to templatelibrary
    op.add_column("templatelibrary", sa.Column("base_url", sa.String(), nullable=True))

    # Create deliveryfile table
    op.create_table(
        "deliveryfile",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("file_source", sa.String(), nullable=False),
        sa.Column("external_url", sa.String(), nullable=True),
        sa.Column("library_id", sa.Uuid(), nullable=True),
        sa.Column("stored_filename", sa.String(), nullable=True),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["client.id"]),
        sa.ForeignKeyConstraint(["library_id"], ["templatelibrary.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deliveryfile_client_id"), "deliveryfile", ["client_id"], unique=False)
    op.create_index(op.f("ix_deliveryfile_library_id"), "deliveryfile", ["library_id"], unique=False)
    op.create_index(op.f("ix_deliveryfile_project_id"), "deliveryfile", ["project_id"], unique=False)
    op.create_index(op.f("ix_deliveryfile_uploaded_by"), "deliveryfile", ["uploaded_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_deliveryfile_uploaded_by"), table_name="deliveryfile")
    op.drop_index(op.f("ix_deliveryfile_project_id"), table_name="deliveryfile")
    op.drop_index(op.f("ix_deliveryfile_library_id"), table_name="deliveryfile")
    op.drop_index(op.f("ix_deliveryfile_client_id"), table_name="deliveryfile")
    op.drop_table("deliveryfile")

    op.drop_column("templatelibrary", "base_url")
    op.drop_column("templatelibrary", "library_type")
