"""add forum insight tracking

Revision ID: 20260321_0006
Revises: 20260321_0005
Create Date: 2026-03-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0006"
down_revision = "20260321_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "foruminsight",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("thread_title", sa.String(), nullable=False),
        sa.Column("problem_summary", sa.Text(), nullable=False),
        sa.Column("proposed_action", sa.Text(), nullable=True),
        sa.Column("impact_score", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("target_week", sa.String(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["person.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_foruminsight_topic"), "foruminsight", ["topic"], unique=False)
    op.create_index(op.f("ix_foruminsight_source_url"), "foruminsight", ["source_url"], unique=False)
    op.create_index(op.f("ix_foruminsight_status"), "foruminsight", ["status"], unique=False)
    op.create_index(op.f("ix_foruminsight_owner_id"), "foruminsight", ["owner_id"], unique=False)
    op.create_index(op.f("ix_foruminsight_reviewer_id"), "foruminsight", ["reviewer_id"], unique=False)
    op.create_index(op.f("ix_foruminsight_target_week"), "foruminsight", ["target_week"], unique=False)
    op.create_index(op.f("ix_foruminsight_created_by"), "foruminsight", ["created_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_foruminsight_created_by"), table_name="foruminsight")
    op.drop_index(op.f("ix_foruminsight_target_week"), table_name="foruminsight")
    op.drop_index(op.f("ix_foruminsight_reviewer_id"), table_name="foruminsight")
    op.drop_index(op.f("ix_foruminsight_owner_id"), table_name="foruminsight")
    op.drop_index(op.f("ix_foruminsight_status"), table_name="foruminsight")
    op.drop_index(op.f("ix_foruminsight_source_url"), table_name="foruminsight")
    op.drop_index(op.f("ix_foruminsight_topic"), table_name="foruminsight")
    op.drop_table("foruminsight")