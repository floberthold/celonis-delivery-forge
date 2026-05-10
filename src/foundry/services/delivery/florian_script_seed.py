import ast
import hashlib
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlmodel import Session, select

from foundry.models import (
    Asset,
    AssetSnapshot,
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


_SHARED_ORG_SLUG = "florian-shared"
_SHARED_ORG_NAME = "Florian Shared"
_SHARED_CLIENT_NAME = "Florian Reusable Scripts"
_SHARED_CLIENT_URL = "https://example.invalid/florian"


@dataclass(frozen=True)
class FlorianRepoConfig:
    folder: str
    project_name: str
    notes: str
    include_globs: tuple[str, ...]
    default_branch: str = "main"


@dataclass(frozen=True)
class FlorianRegistrationProjectResult:
    folder: str
    project_id: UUID
    source_id: UUID
    assets_registered: int
    scripts_discovered: int


@dataclass(frozen=True)
class FlorianRegistrationResult:
    organization_id: UUID
    client_id: UUID
    project_results: tuple[FlorianRegistrationProjectResult, ...]

    @property
    def asset_count(self) -> int:
        return sum(row.assets_registered for row in self.project_results)


@dataclass(frozen=True)
class FlorianProjectImportResult:
    sources_created: int
    assets_registered: int
    snapshots_created: int
    scripts_discovered: int


_REPO_CONFIGS: tuple[FlorianRepoConfig, ...] = (
    FlorianRepoConfig(
        folder="pyCelonis-tools",
        project_name="pyCelonis Tools",
        notes="Curated reusable Celonis helper scripts mirrored from Florian reference code.",
        include_globs=(
            "local_scripts.py",
            "scripts/extractors/**/*.py",
            "scripts/migration/**/*.py",
            "scripts/consulting/**/*.py",
            "scripts/exports/**/*.py",
        ),
    ),
    FlorianRepoConfig(
        folder="pyCelonis%20-%20for%20Fuchs",
        project_name="pyCelonis For Fuchs",
        notes="Curated automation and extraction scripts imported from Florian's Fuchs repository.",
        include_globs=(
            "Automations/Automations/scripts.py",
            "Unassigned Apps/Forecast and Delta-Real-Time Load/Extraction/*.py",
            "Unassigned Apps/Test - Roboyo Workspace/roboyo_fb_mini_tools/local_scripts.py",
            "Unassigned Apps/Test - Roboyo Workspace/roboyo_fb_table_dependency_extractor/local_scripts.py",
            "Unassigned Apps/Test - Roboyo Workspace/roboyo_fb_script_automations/local_scripts.py",
        ),
    ),
    FlorianRepoConfig(
        folder="pyCelonis%20-%20OCPM%20migration%20tool",
        project_name="pyCelonis OCPM Migration Tool",
        notes="Curated migration, client, and extractor scripts imported from Florian's OCPM migration repo.",
        include_globs=(
            "local_scripts.py",
            "scripts/extractors/**/*.py",
            "app/services/*_client.py",
            "app/src/celonis/service/**/*.py",
            "app/src/tools/*.py",
        ),
    ),
)


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


def _looks_reusable_script(path: Path) -> bool:
    if path.suffix.lower() != ".py":
        return False
    if path.name == "__init__.py":
        return False
    lower_parts = {part.lower() for part in path.parts}
    if "tests" in lower_parts or "__pycache__" in lower_parts:
        return False
    lower_name = path.name.lower()
    if lower_name.startswith("test_") or lower_name.endswith("_test.py") or lower_name == "conftest.py":
        return False
    return True


def _discover_scripts(repo_dir: Path, config: FlorianRepoConfig) -> list[Path]:
    discovered: dict[str, Path] = {}
    for pattern in config.include_globs:
        for path in repo_dir.glob(pattern):
            if not path.is_file() or not _looks_reusable_script(path):
                continue
            rel = path.relative_to(repo_dir).as_posix()
            discovered[rel] = path
    return [discovered[key] for key in sorted(discovered)]


def _titleize(token: str) -> str:
    return token.replace("_", " ").replace("-", " ").strip().title()


def _asset_name(relative_path: Path) -> str:
    parts = list(relative_path.with_suffix("").parts)
    if not parts:
        return "Unnamed Script"
    leaf = parts[-1]
    if leaf in {"local_scripts", "service", "views", "km", "scripts"} and len(parts) >= 2:
        return f"{_titleize(parts[-2])} {_titleize(leaf)}"
    return _titleize(leaf)


def _asset_type(relative_path: Path) -> AssetType:
    token = relative_path.as_posix().lower()
    if "machine_learning" in token or "/ml" in token or "feature_vector" in token:
        return AssetType.ml_job
    if "extract" in token or "resolver" in token or "autodocument" in token:
        return AssetType.extractor
    if "migration" in token or "semantic_layer" in token or "package_manager" in token:
        return AssetType.data_model
    if "automation" in token:
        return AssetType.action_flow
    return AssetType.other


def _module_metadata(path: Path, relative_path: Path) -> dict:
    content = path.read_text(encoding="utf-8", errors="ignore")
    imports: list[str] = []
    functions: list[str] = []
    classes: list[str] = []
    docstring = ""
    parse_error = ""

    try:
        module = ast.parse(content)
    except SyntaxError as exc:
        parse_error = str(exc)
    else:
        functions = sorted(
            {
                node.name
                for node in module.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
        )
        classes = sorted(
            {
                node.name
                for node in module.body
                if isinstance(node, ast.ClassDef)
            }
        )
        for node in module.body:
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        docstring = ast.get_docstring(module) or ""

    sha256 = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
    return {
        "relative_path": relative_path.as_posix(),
        "asset_identifier": f"Florian/{relative_path.as_posix()}",
        "name": _asset_name(relative_path),
        "asset_type": _asset_type(relative_path).value,
        "line_count": len(content.splitlines()),
        "sha256": sha256,
        "functions": functions,
        "classes": classes,
        "imports": sorted({row for row in imports if row})[:25],
        "docstring": docstring,
        "parse_error": parse_error,
    }


def _manifest_sha(scripts: list[dict]) -> str:
    payload = "\n".join(f"{row['relative_path']}:{row['sha256']}" for row in scripts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _latest_snapshot(session: Session, source_id: UUID) -> AssetSnapshot | None:
    rows = session.exec(
        select(AssetSnapshot).where(AssetSnapshot.asset_source_id == source_id)
    ).all()
    if not rows:
        return None
    return sorted(rows, key=lambda row: row.received_at, reverse=True)[0]


def _ensure_source(
    session: Session,
    *,
    organization_id: UUID,
    name: str,
    repo_dir: Path,
    default_branch: str,
    notes: str,
) -> tuple[AssetSource, bool]:
    source = session.exec(
        select(AssetSource).where(
            AssetSource.organization_id == organization_id,
            AssetSource.name == name,
        )
    ).first()
    created = False
    if source is None:
        source = AssetSource(
            organization_id=organization_id,
            name=name,
            kind=AssetSourceKind.mirrored_repo,
            provider="florian",
            repo_url=str(repo_dir.resolve()),
            default_branch=default_branch,
            notes=notes,
        )
        session.add(source)
        session.flush()
        created = True
    return source, created


def _upsert_manifest_snapshot(
    session: Session,
    *,
    source: AssetSource,
    config: FlorianRepoConfig,
    repo_dir: Path,
    script_entries: list[dict],
) -> bool:
    manifest_sha = _manifest_sha(script_entries)
    latest = _latest_snapshot(session, source.id)
    latest_sha = (latest.summary_json or {}).get("manifest_sha256") if latest else None
    if latest_sha == manifest_sha:
        return False

    session.add(
        AssetSnapshot(
            asset_source_id=source.id,
            version_label=f"catalog-{manifest_sha[:12]}",
            source_ref=manifest_sha,
            summary_json={
                "source": "florian_reusable_script_seed",
                "repo_folder": config.folder,
                "repo_path": str(repo_dir.resolve()),
                "script_count": len(script_entries),
                "manifest_sha256": manifest_sha,
                "scripts": script_entries,
            },
        )
    )
    return True


def register_florian_script_assets(
    session: Session,
    *,
    actor_id: UUID,
    root_dir: Path,
) -> FlorianRegistrationResult:
    if not root_dir.exists() or not root_dir.is_dir():
        raise ValueError(f"Florian shared directory not found: {root_dir}")

    org = _get_or_create_shared_org(session, actor_id)
    client = _get_or_create_shared_client(session, org.id)

    project_results: list[FlorianRegistrationProjectResult] = []

    for config in _REPO_CONFIGS:
        repo_dir = root_dir / config.folder
        if not repo_dir.exists() or not repo_dir.is_dir():
            continue

        project = session.exec(
            select(Project).where(
                Project.organization_id == org.id,
                Project.client_id == client.id,
                Project.name == config.project_name,
            )
        ).first()
        if project is None:
            project = Project(
                organization_id=org.id,
                client_id=client.id,
                name=config.project_name,
                status=ProjectStatus.active,
            )
            session.add(project)
            session.flush()

        source, _ = _ensure_source(
            session,
            organization_id=org.id,
            name=config.project_name,
            repo_dir=repo_dir,
            default_branch=config.default_branch,
            notes=config.notes,
        )

        scripts = _discover_scripts(repo_dir, config)
        script_entries = [
            _module_metadata(path, Path(config.folder) / path.relative_to(repo_dir))
            for path in scripts
        ]

        assets_registered = 0
        for entry in script_entries:
            existing = session.exec(
                select(Asset).where(
                    Asset.organization_id == org.id,
                    Asset.project_id == project.id,
                    Asset.asset_identifier == entry["asset_identifier"],
                )
            ).first()
            if existing is None:
                session.add(
                    Asset(
                        organization_id=org.id,
                        project_id=project.id,
                        client_id=client.id,
                        type=AssetType(entry["asset_type"]),
                        status=AssetStatus.draft,
                        name=entry["name"],
                        asset_identifier=entry["asset_identifier"],
                    )
                )
                assets_registered += 1
            else:
                existing.name = entry["name"]
                existing.type = AssetType(entry["asset_type"])
                session.add(existing)

        _upsert_manifest_snapshot(
            session,
            source=source,
            config=config,
            repo_dir=repo_dir,
            script_entries=script_entries,
        )

        project_results.append(
            FlorianRegistrationProjectResult(
                folder=config.folder,
                project_id=project.id,
                source_id=source.id,
                assets_registered=assets_registered,
                scripts_discovered=len(script_entries),
            )
        )

    session.commit()

    return FlorianRegistrationResult(
        organization_id=org.id,
        client_id=client.id,
        project_results=tuple(project_results),
    )


def import_florian_scripts_to_project(
    session: Session,
    *,
    organization_id: UUID,
    project_id: UUID,
    client_id: UUID,
    root_dir: Path,
) -> FlorianProjectImportResult:
    if not root_dir.exists() or not root_dir.is_dir():
        raise ValueError(f"Florian shared directory not found: {root_dir}")

    sources_created = 0
    assets_registered = 0
    snapshots_created = 0
    scripts_discovered = 0

    for config in _REPO_CONFIGS:
        repo_dir = root_dir / config.folder
        if not repo_dir.exists() or not repo_dir.is_dir():
            continue

        source_name = f"Florian: {config.project_name}"
        source, created = _ensure_source(
            session,
            organization_id=organization_id,
            name=source_name,
            repo_dir=repo_dir,
            default_branch=config.default_branch,
            notes=config.notes,
        )
        if created:
            sources_created += 1

        scripts = _discover_scripts(repo_dir, config)
        script_entries = [
            _module_metadata(path, Path(config.folder) / path.relative_to(repo_dir))
            for path in scripts
        ]
        scripts_discovered += len(script_entries)

        for entry in script_entries:
            existing = session.exec(
                select(Asset).where(
                    Asset.organization_id == organization_id,
                    Asset.project_id == project_id,
                    Asset.asset_identifier == entry["asset_identifier"],
                )
            ).first()
            if existing is not None:
                continue

            session.add(
                Asset(
                    organization_id=organization_id,
                    project_id=project_id,
                    client_id=client_id,
                    type=AssetType(entry["asset_type"]),
                    status=AssetStatus.draft,
                    name=entry["name"],
                    asset_identifier=entry["asset_identifier"],
                )
            )
            assets_registered += 1

        if _upsert_manifest_snapshot(
            session,
            source=source,
            config=config,
            repo_dir=repo_dir,
            script_entries=script_entries,
        ):
            snapshots_created += 1

    session.commit()
    return FlorianProjectImportResult(
        sources_created=sources_created,
        assets_registered=assets_registered,
        snapshots_created=snapshots_created,
        scripts_discovered=scripts_discovered,
    )