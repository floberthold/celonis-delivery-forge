"""add template tables

Revision ID: 20260302_0001
Revises:
Create Date: 2026-03-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260302_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "templatelibrary",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["client.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_templatelibrary_client_id"), "templatelibrary", ["client_id"], unique=False)

    op.create_table(
        "template",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("library_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("storage_type", sa.String(), nullable=False),
        sa.Column("storage_url", sa.String(), nullable=False),
        sa.Column("prefill_schema_json", sa.JSON(), nullable=False),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["person.id"]),
        sa.ForeignKeyConstraint(["library_id"], ["templatelibrary.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_template_created_by"), "template", ["created_by"], unique=False)
    op.create_index(op.f("ix_template_library_id"), "template", ["library_id"], unique=False)

    op.create_table(
        "templateinstantiation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("generated_url", sa.String(), nullable=False),
        sa.Column("prefill_data_json", sa.JSON(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("review_request_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"]),
        sa.ForeignKeyConstraint(["author_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["client.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["review_request_id"], ["reviewrequest.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["template.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_templateinstantiation_asset_id"), "templateinstantiation", ["asset_id"], unique=False)
    op.create_index(op.f("ix_templateinstantiation_author_id"), "templateinstantiation", ["author_id"], unique=False)
    op.create_index(op.f("ix_templateinstantiation_client_id"), "templateinstantiation", ["client_id"], unique=False)
    op.create_index(op.f("ix_templateinstantiation_project_id"), "templateinstantiation", ["project_id"], unique=False)
    op.create_index(
        op.f("ix_templateinstantiation_review_request_id"),
        "templateinstantiation",
        ["review_request_id"],
        unique=False,
    )
    op.create_index(op.f("ix_templateinstantiation_reviewer_id"), "templateinstantiation", ["reviewer_id"], unique=False)
    op.create_index(op.f("ix_templateinstantiation_template_id"), "templateinstantiation", ["template_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_templateinstantiation_template_id"), table_name="templateinstantiation")
    op.drop_index(op.f("ix_templateinstantiation_reviewer_id"), table_name="templateinstantiation")
    op.drop_index(op.f("ix_templateinstantiation_review_request_id"), table_name="templateinstantiation")
    op.drop_index(op.f("ix_templateinstantiation_project_id"), table_name="templateinstantiation")
    op.drop_index(op.f("ix_templateinstantiation_client_id"), table_name="templateinstantiation")
    op.drop_index(op.f("ix_templateinstantiation_author_id"), table_name="templateinstantiation")
    op.drop_index(op.f("ix_templateinstantiation_asset_id"), table_name="templateinstantiation")
    op.drop_table("templateinstantiation")

    op.drop_index(op.f("ix_template_library_id"), table_name="template")
    op.drop_index(op.f("ix_template_created_by"), table_name="template")
    op.drop_table("template")

    op.drop_index(op.f("ix_templatelibrary_client_id"), table_name="templatelibrary")
    op.drop_table("templatelibrary")
