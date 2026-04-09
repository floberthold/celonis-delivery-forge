from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import (
    Asset,
    AssetSource,
    AssetSourceKind,
    AssetStatus,
    AssetType,
    Client,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Project,
    ProjectStatus,
)
from foundry.schemas import CelonisMarketplaceProjectOut, CelonisMarketplaceRegisterOut
from foundry.settings import get_settings

router = APIRouter(prefix="/celonis-marketplace", tags=["celonis-marketplace"])

_SHARED_ORG_SLUG = "celonis-shared"
_SHARED_ORG_NAME = "Celonis Shared"
_SHARED_CLIENT_NAME = "Celonis (Shared)"
_SHARED_CLIENT_URL = "https://celonis.com"

_PROJECT_NAME_OVERRIDES = {
    "dm-load-optimization": "DM Load Optimization",
    "image-processing": "Image Processing Pipeline",
    "Independent_Requirement_Script": "Independent Requirement Script",
    "KPI_Resolver": "KPI Resolver",
    "m-20-ocpm-bootstrapper-main": "OCPM Bootstrapper",
}

_PROJECT_TYPE_HINTS = {
    "dm-load-optimization": AssetType.data_model,
    "KPI_Resolver": AssetType.kpi,
}


def _get_or_create_shared_org(session: Session, actor_id: UUID) -> Organization:
    org = session.exec(select(Organization).where(Organization.slug == _SHARED_ORG_SLUG)).first()
    if org is None:
        org = Organization(name=_SHARED_ORG_NAME, slug=_SHARED_ORG_SLUG)
        session.add(org)
        session.flush()

    membership = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org.id,
            OrganizationMembership.person_id == actor_id,
        )
    ).first()
    if membership is None:
        session.add(
            OrganizationMembership(
                organization_id=org.id,
                person_id=actor_id,
                role=OrganizationRole.owner,
            )
        )
    return org


def _get_or_create_shared_client(session: Session, organization_id: UUID) -> Client:
    client = session.exec(
        select(Client).where(
            Client.organization_id == organization_id,
            Client.name == _SHARED_CLIENT_NAME,
        )
    ).first()
    if client is None:
        client = Client(
            organization_id=organization_id,
            name=_SHARED_CLIENT_NAME,
            tenant_url=_SHARED_CLIENT_URL,
        )
        session.add(client)
        session.flush()
    return client


def _project_name(folder_name: str) -> str:
    return _PROJECT_NAME_OVERRIDES.get(folder_name, folder_name.replace("-", " ").strip().title())


def _default_asset_type(folder_name: str, relative_path: Path) -> AssetType:
    hinted = _PROJECT_TYPE_HINTS.get(folder_name)
    if hinted is not None:
        return hinted

    token = relative_path.as_posix().lower()
    if "kpi" in token:
        return AssetType.kpi
    if "data_model" in token or token.startswith("dm"):
        return AssetType.data_model
    return AssetType.other


def _discover_assets(project_dir: Path) -> list[Path]:
    discovered: dict[str, Path] = {}

    for notebook in project_dir.rglob("*.ipynb"):
        rel = notebook.relative_to(project_dir)
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue
        discovered[rel.as_posix()] = notebook

    for py_file in project_dir.rglob("*.py"):
        rel = py_file.relative_to(project_dir)
        if len(rel.parts) > 3:
            continue
        filename = py_file.name.lower()
        if filename.startswith("test_") or filename.endswith("_test.py"):
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue
        discovered[rel.as_posix()] = py_file

    for marker in ("README.md", "pyproject.toml", "requirements.txt"):
        marker_path = project_dir / marker
        if marker_path.exists():
            discovered[marker] = marker_path

    return [discovered[key] for key in sorted(discovered)]


@router.post("/register", response_model=CelonisMarketplaceRegisterOut)
def register_celonis_marketplace(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    settings = get_settings()
    shared_root = Path(settings.celonis_shared_dir)
    if not shared_root.exists() or not shared_root.is_dir():
        raise HTTPException(status_code=400, detail=f"Celonis shared directory not found: {shared_root}")

    org = _get_or_create_shared_org(session, current_actor.person.id)
    client = _get_or_create_shared_client(session, org.id)

    project_results: list[CelonisMarketplaceProjectOut] = []
    total_assets = 0

    project_dirs = sorted(
        [
            child
            for child in shared_root.iterdir()
            if child.is_dir() and not child.name.startswith(".") and child.name != "__pycache__"
        ],
        key=lambda row: row.name.lower(),
    )

    for project_dir in project_dirs:
        pname = _project_name(project_dir.name)

        project = session.exec(
            select(Project).where(
                Project.organization_id == org.id,
                Project.client_id == client.id,
                Project.name == pname,
            )
        ).first()
        if project is None:
            project = Project(
                organization_id=org.id,
                client_id=client.id,
                name=pname,
                status=ProjectStatus.active,
            )
            session.add(project)
            session.flush()

        source = session.exec(
            select(AssetSource).where(
                AssetSource.organization_id == org.id,
                AssetSource.name == project_dir.name,
            )
        ).first()
        if source is None:
            source = AssetSource(
                organization_id=org.id,
                name=project_dir.name,
                kind=AssetSourceKind.celonis_marketplace,
                provider="celonis",
                repo_url=str(project_dir.resolve()),
                default_branch="main",
                notes="Auto-registered from Code from Celonis shared folder",
            )
            session.add(source)
            session.flush()

        registered_assets = 0
        for asset_path in _discover_assets(project_dir):
            relative = asset_path.relative_to(project_dir)
            identifier = f"Code from Celonis/{project_dir.name}/{relative.as_posix()}"
            existing = session.exec(
                select(Asset).where(
                    Asset.organization_id == org.id,
                    Asset.project_id == project.id,
                    Asset.asset_identifier == identifier,
                )
            ).first()
            if existing:
                continue

            atype = _default_asset_type(project_dir.name, relative)
            asset = Asset(
                organization_id=org.id,
                project_id=project.id,
                client_id=client.id,
                type=atype,
                status=AssetStatus.draft,
                name=relative.stem,
                asset_identifier=identifier,
            )
            session.add(asset)
            registered_assets += 1

        total_assets += registered_assets
        project_results.append(
            CelonisMarketplaceProjectOut(
                folder=project_dir.name,
                project_id=project.id,
                source_id=source.id,
                assets_registered=registered_assets,
            )
        )

    session.commit()

    return CelonisMarketplaceRegisterOut(
        organization_id=org.id,
        client_id=client.id,
        project_count=len(project_results),
        asset_count=total_assets,
        projects=project_results,
    )
