from uuid import UUID

from sqlmodel import Session, select

from foundry.models import Template, TemplateLibrary, TemplateScope, TemplateStorageType

DEFAULT_LIBRARY_NAME = "Global Delivery Templates"
DEFAULT_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("Project Planning Deck", "project_planning"),
    ("Scoping Workshop Deck", "scoping"),
    ("Goal Setting Deck", "goal_setting"),
    ("Value Framing Deck", "value_framing"),
    ("KPI Definition Deck", "kpi_definition"),
    ("Measurement Framework Deck", "measurement"),
)


def seed_default_templates(session: Session, organization_id: UUID | None = None) -> None:
    library = session.exec(
        select(TemplateLibrary).where(
            TemplateLibrary.scope == TemplateScope.global_scope,
            TemplateLibrary.name == DEFAULT_LIBRARY_NAME,
            TemplateLibrary.organization_id == organization_id,
        )
    ).first()

    if library is None:
        library = TemplateLibrary(
            organization_id=organization_id,
            name=DEFAULT_LIBRARY_NAME,
            scope=TemplateScope.global_scope,
        )
        session.add(library)
        session.commit()
        session.refresh(library)

    existing_titles = {
        row.title
        for row in session.exec(
            select(Template).where(Template.library_id == library.id)
        ).all()
    }

    rows_to_add = []
    for title, category in DEFAULT_TEMPLATES:
        if title in existing_titles:
            continue
        rows_to_add.append(
            Template(
                organization_id=organization_id,
                library_id=library.id,
                title=title,
                category=category,
                storage_type=TemplateStorageType.sharepoint,
                storage_url="https://contoso.sharepoint.com/:p:/r/sites/delivery-forge/template",
                prefill_schema_json={
                    "required": ["client_name", "tenant_url", "project_name"],
                    "optional": ["instantiated_at", "template_title"],
                },
                requires_review=True,
                is_active=True,
                created_by=None,
            )
        )

    if not rows_to_add:
        return

    session.add_all(rows_to_add)
    session.commit()
