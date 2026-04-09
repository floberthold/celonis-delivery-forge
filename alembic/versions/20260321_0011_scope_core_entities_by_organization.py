"""scope core entities by organization

Revision ID: 20260321_0011
Revises: 20260321_0010
Create Date: 2026-03-21 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_0011"
down_revision = "20260321_0010"
branch_labels = None
depends_on = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _has_fk(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    return constraint_name in {
        foreign_key.get("name") for foreign_key in inspector.get_foreign_keys(table_name)
    }


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    supports_alter_fk = bind.dialect.name != "sqlite"

    targets = [
        ("client", "fk_client_organization_id_organization", op.f("ix_client_organization_id")),
        ("project", "fk_project_organization_id_organization", op.f("ix_project_organization_id")),
        ("asset", "fk_asset_organization_id_organization", op.f("ix_asset_organization_id")),
        (
            "activitylog",
            "fk_activitylog_organization_id_organization",
            op.f("ix_activitylog_organization_id"),
        ),
        ("todo", "fk_todo_organization_id_organization", op.f("ix_todo_organization_id")),
        (
            "celonisconnection",
            "fk_celonisconnection_organization_id_organization",
            op.f("ix_celonisconnection_organization_id"),
        ),
        (
            "templatelibrary",
            "fk_templatelibrary_organization_id_organization",
            op.f("ix_templatelibrary_organization_id"),
        ),
        ("template", "fk_template_organization_id_organization", op.f("ix_template_organization_id")),
        (
            "templateinstantiation",
            "fk_templateinstantiation_organization_id_organization",
            op.f("ix_templateinstantiation_organization_id"),
        ),
    ]

    for table_name, fk_name, index_name in targets:
        if not _has_table(inspector, table_name):
            continue

        if not _has_column(inspector, table_name, "organization_id"):
            op.add_column(table_name, sa.Column("organization_id", sa.Uuid(), nullable=True))

        if (
            supports_alter_fk
            and _has_table(inspector, "organization")
            and not _has_fk(inspector, table_name, fk_name)
        ):
            op.create_foreign_key(
                fk_name,
                table_name,
                "organization",
                ["organization_id"],
                ["id"],
            )

        if not _has_index(inspector, table_name, index_name):
            op.create_index(index_name, table_name, ["organization_id"], unique=False)

        inspector = sa.inspect(bind)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    supports_alter_fk = bind.dialect.name != "sqlite"

    targets = [
        (
            "templateinstantiation",
            "fk_templateinstantiation_organization_id_organization",
            op.f("ix_templateinstantiation_organization_id"),
        ),
        ("template", "fk_template_organization_id_organization", op.f("ix_template_organization_id")),
        (
            "templatelibrary",
            "fk_templatelibrary_organization_id_organization",
            op.f("ix_templatelibrary_organization_id"),
        ),
        (
            "celonisconnection",
            "fk_celonisconnection_organization_id_organization",
            op.f("ix_celonisconnection_organization_id"),
        ),
        ("todo", "fk_todo_organization_id_organization", op.f("ix_todo_organization_id")),
        (
            "activitylog",
            "fk_activitylog_organization_id_organization",
            op.f("ix_activitylog_organization_id"),
        ),
        ("asset", "fk_asset_organization_id_organization", op.f("ix_asset_organization_id")),
        ("project", "fk_project_organization_id_organization", op.f("ix_project_organization_id")),
        ("client", "fk_client_organization_id_organization", op.f("ix_client_organization_id")),
    ]

    for table_name, fk_name, index_name in targets:
        if not _has_table(inspector, table_name):
            continue

        if _has_index(inspector, table_name, index_name):
            op.drop_index(index_name, table_name=table_name)

        if supports_alter_fk and _has_fk(inspector, table_name, fk_name):
            op.drop_constraint(fk_name, table_name, type_="foreignkey")

        if _has_column(inspector, table_name, "organization_id"):
            op.drop_column(table_name, "organization_id")

        inspector = sa.inspect(bind)