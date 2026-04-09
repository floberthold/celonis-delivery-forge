from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from foundry.models import (
    Asset,
    AssetType,
    Client,
    EntityType,
    Person,
    Project,
    Template,
    TemplateInstantiation,
    TemplateLibrary,
    TemplateScope,
)
from foundry.schemas import ReviewRequestCreate, TemplateInstantiateCreate
from foundry.services.activity_log import log_activity
from foundry.services.review_service import ReviewService


class TemplateService:
    @staticmethod
    def list_templates(
        session: Session,
        *,
        organization_id: UUID | None = None,
        client_id: UUID | None = None,
        category: str | None = None,
    ) -> list[Template]:
        global_library_ids = list(
            session.exec(
                select(TemplateLibrary.id).where(
                    TemplateLibrary.scope == TemplateScope.global_scope,
                    TemplateLibrary.organization_id == organization_id,
                )
            ).all()
        )
        allowed_library_ids = set(global_library_ids)

        if client_id is not None:
            client_library_ids = list(
                session.exec(
                    select(TemplateLibrary.id).where(
                        TemplateLibrary.scope == TemplateScope.client_scope,
                        TemplateLibrary.client_id == client_id,
                        TemplateLibrary.organization_id == organization_id,
                    )
                ).all()
            )
            allowed_library_ids.update(client_library_ids)

        if not allowed_library_ids:
            return []

        templates = list(
            session.exec(
                select(Template).where(
                    Template.is_active,
                    Template.organization_id == organization_id,
                )
            ).all()
        )
        filtered = [template for template in templates if template.library_id in allowed_library_ids]

        if category:
            filtered = [template for template in filtered if template.category == category]

        return filtered

    @staticmethod
    def instantiate_template(
        session: Session,
        *,
        template: Template,
        payload: TemplateInstantiateCreate,
        organization_id: UUID | None = None,
    ) -> TemplateInstantiation:
        project = session.get(Project, payload.project_id)
        if not project or project.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.client_id != payload.client_id:
            raise HTTPException(status_code=400, detail="Project does not belong to the specified client")

        client = session.get(Client, payload.client_id)
        if not client or client.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Client not found")

        author = session.get(Person, payload.author_id)
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")

        reviewer = session.get(Person, payload.reviewer_id)
        if not reviewer:
            raise HTTPException(status_code=404, detail="Reviewer not found")

        instantiated_at = datetime.utcnow().isoformat()
        prefill_data_json = {
            "client_name": client.name,
            "tenant_url": client.tenant_url,
            "project_name": project.name,
            "template_title": template.title,
            "instantiated_at": instantiated_at,
        }

        parsed = urlparse(template.storage_url)
        query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query_params.update(prefill_data_json)
        generated_url = urlunparse(parsed._replace(query=urlencode(query_params)))

        asset_id = None
        review_request_id = None

        if template.requires_review:
            asset = Asset(
                organization_id=organization_id,
                type=AssetType.other,
                name=f"Template Output: {template.title}",
                project_id=payload.project_id,
                client_id=payload.client_id,
                celonis_url=generated_url,
            )
            session.add(asset)
            session.commit()
            session.refresh(asset)

            review = ReviewService.submit_for_review(
                session,
                ReviewRequestCreate(
                    asset_id=asset.id,
                    project_id=payload.project_id,
                    author_id=payload.author_id,
                    reviewer_id=payload.reviewer_id,
                    change_summary=f"Template instantiation for {template.title}",
                ),
                organization_id=organization_id,
            )
            asset_id = asset.id
            review_request_id = review.id

        instantiation = TemplateInstantiation(
            organization_id=organization_id,
            template_id=template.id,
            project_id=payload.project_id,
            client_id=payload.client_id,
            author_id=payload.author_id,
            reviewer_id=payload.reviewer_id,
            generated_url=generated_url,
            prefill_data_json=prefill_data_json,
            asset_id=asset_id,
            review_request_id=review_request_id,
        )
        session.add(instantiation)
        session.commit()
        session.refresh(instantiation)

        log_activity(
            session,
            entity_type=EntityType.template_instantiation,
            entity_id=instantiation.id,
            actor_id=payload.author_id,
            action="template.instantiated",
            organization_id=organization_id,
            metadata={
                "template_id": str(template.id),
                "project_id": str(payload.project_id),
                "generated_url": generated_url,
            },
        )

        return instantiation
