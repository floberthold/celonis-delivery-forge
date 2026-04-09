"""add use case library and roadmap tables

Revision ID: 20260321_0005
Revises: 20260320_0004
Create Date: 2026-03-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0005"
down_revision = "20260320_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usecase",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("process_domain", sa.String(), nullable=True),
        sa.Column("owner_person_id", sa.Uuid(), nullable=True),
        sa.Column("client_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("maturity", sa.String(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("api_dependencies_json", sa.JSON(), nullable=False),
        sa.Column("is_anonymized_ready", sa.Boolean(), nullable=False),
        sa.Column("is_client_view_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_industry_benchmark_eligible", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["client.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usecase_title"), "usecase", ["title"], unique=False)
    op.create_index(op.f("ix_usecase_industry"), "usecase", ["industry"], unique=False)
    op.create_index(op.f("ix_usecase_process_domain"), "usecase", ["process_domain"], unique=False)
    op.create_index(op.f("ix_usecase_owner_person_id"), "usecase", ["owner_person_id"], unique=False)
    op.create_index(op.f("ix_usecase_client_id"), "usecase", ["client_id"], unique=False)
    op.create_index(op.f("ix_usecase_project_id"), "usecase", ["project_id"], unique=False)
    op.create_index(op.f("ix_usecase_maturity"), "usecase", ["maturity"], unique=False)

    op.create_table(
        "usecaseroadmapitem",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("initiative", sa.String(), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("owner_person_id", sa.Uuid(), nullable=True),
        sa.Column("target_month", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("percent_complete", sa.Integer(), nullable=False),
        sa.Column("blockers", sa.Text(), nullable=True),
        sa.Column("last_update_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_person_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usecaseroadmapitem_phase"), "usecaseroadmapitem", ["phase"], unique=False)
    op.create_index(op.f("ix_usecaseroadmapitem_owner_person_id"), "usecaseroadmapitem", ["owner_person_id"], unique=False)
    op.create_index(op.f("ix_usecaseroadmapitem_target_month"), "usecaseroadmapitem", ["target_month"], unique=False)
    op.create_index(op.f("ix_usecaseroadmapitem_status"), "usecaseroadmapitem", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_usecaseroadmapitem_status"), table_name="usecaseroadmapitem")
    op.drop_index(op.f("ix_usecaseroadmapitem_target_month"), table_name="usecaseroadmapitem")
    op.drop_index(op.f("ix_usecaseroadmapitem_owner_person_id"), table_name="usecaseroadmapitem")
    op.drop_index(op.f("ix_usecaseroadmapitem_phase"), table_name="usecaseroadmapitem")
    op.drop_table("usecaseroadmapitem")

    op.drop_index(op.f("ix_usecase_maturity"), table_name="usecase")
    op.drop_index(op.f("ix_usecase_project_id"), table_name="usecase")
    op.drop_index(op.f("ix_usecase_client_id"), table_name="usecase")
    op.drop_index(op.f("ix_usecase_owner_person_id"), table_name="usecase")
    op.drop_index(op.f("ix_usecase_process_domain"), table_name="usecase")
    op.drop_index(op.f("ix_usecase_industry"), table_name="usecase")
    op.drop_index(op.f("ix_usecase_title"), table_name="usecase")
    op.drop_table("usecase")
