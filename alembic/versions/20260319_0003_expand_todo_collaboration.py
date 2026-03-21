"""expand todo collaboration support

Revision ID: 20260319_0003
Revises: 20260303_0002
Create Date: 2026-03-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260319_0003"
down_revision = "20260303_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("todo", sa.Column("long_description_markdown", sa.Text(), nullable=True))

    op.create_table(
        "todocomment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("todo_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["todo_id"], ["todo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_todocomment_author_id"), "todocomment", ["author_id"], unique=False)
    op.create_index(op.f("ix_todocomment_todo_id"), "todocomment", ["todo_id"], unique=False)

    op.create_table(
        "todotag",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("todo_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["todo_id"], ["todo.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("todo_id", "name", name="uq_todotag_todo_name"),
    )
    op.create_index(op.f("ix_todotag_name"), "todotag", ["name"], unique=False)
    op.create_index(op.f("ix_todotag_todo_id"), "todotag", ["todo_id"], unique=False)

    op.create_table(
        "todolink",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("todo_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["todo_id"], ["todo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_todolink_todo_id"), "todolink", ["todo_id"], unique=False)

    op.create_table(
        "tododocument",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("todo_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("storage_path", sa.String(), nullable=True),
        sa.Column("original_filename", sa.String(), nullable=True),
        sa.Column("uploaded_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["todo_id"], ["todo.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["person.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tododocument_todo_id"), "tododocument", ["todo_id"], unique=False)
    op.create_index(op.f("ix_tododocument_uploaded_by"), "tododocument", ["uploaded_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tododocument_uploaded_by"), table_name="tododocument")
    op.drop_index(op.f("ix_tododocument_todo_id"), table_name="tododocument")
    op.drop_table("tododocument")

    op.drop_index(op.f("ix_todolink_todo_id"), table_name="todolink")
    op.drop_table("todolink")

    op.drop_index(op.f("ix_todotag_todo_id"), table_name="todotag")
    op.drop_index(op.f("ix_todotag_name"), table_name="todotag")
    op.drop_table("todotag")

    op.drop_index(op.f("ix_todocomment_todo_id"), table_name="todocomment")
    op.drop_index(op.f("ix_todocomment_author_id"), table_name="todocomment")
    op.drop_table("todocomment")

    op.drop_column("todo", "long_description_markdown")