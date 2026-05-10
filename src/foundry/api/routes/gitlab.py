import hmac
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.integrations.gitlab_gateway import GitLabGateway
from foundry.models import EntityType, GitLabPipelineRun, GitLabRepo, Project
from foundry.schemas import (
    GitLabPipelineRunOut,
    GitLabRepoCreate,
    GitLabRepoOut,
    GitLabRepoUpdate,
    GitLabTriggerRequest,
)
from foundry.services.activity_log import log_created, log_updated
from foundry.settings import get_settings

router = APIRouter(prefix="/gitlab", tags=["gitlab"])


def _get_org_project(session: Session, project_id: UUID, organization_id: UUID) -> Project | None:
    project = session.get(Project, project_id)
    if not project or project.organization_id != organization_id:
        return None
    return project


def _get_org_repo(session: Session, repo_id: UUID, organization_id: UUID) -> GitLabRepo | None:
    repo = session.get(GitLabRepo, repo_id)
    if not repo:
        return None
    if _get_org_project(session, repo.project_id, organization_id) is None:
        return None
    return repo


def _to_repo_out(repo: GitLabRepo) -> GitLabRepoOut:
    return GitLabRepoOut(
        id=repo.id,
        project_id=repo.project_id,
        name=repo.name,
        repo_path=repo.repo_path,
        token_override="***" if repo.token_override else None,
        default_branch=repo.default_branch,
        webhook_secret=repo.webhook_secret,
        is_active=repo.is_active,
        created_by=repo.created_by,
        created_at=repo.created_at,
    )


@router.post("/repos", response_model=GitLabRepoOut)
def create_repo(
    payload: GitLabRepoCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    org_id = current_actor.organization.id
    project = _get_org_project(session, payload.project_id, org_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo = GitLabRepo(
        project_id=payload.project_id,
        name=payload.name.strip(),
        repo_path=payload.repo_path.strip(),
        token_override=payload.token_override.strip() if payload.token_override else None,
        default_branch=payload.default_branch.strip() or "main",
        webhook_secret=payload.webhook_secret.strip() if payload.webhook_secret else None,
        created_by=current_actor.person.id,
    )
    session.add(repo)
    session.commit()
    session.refresh(repo)

    log_created(
        session,
        entity_type=EntityType.gitlab_repo,
        entity_id=repo.id,
        actor_id=current_actor.person.id,
        organization_id=org_id,
        metadata={"project_id": str(repo.project_id), "repo_path": repo.repo_path},
    )
    return _to_repo_out(repo)


@router.get("/repos", response_model=list[GitLabRepoOut])
def list_repos(
    project_id: UUID | None = None,
    client_id: UUID | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    org_id = current_actor.organization.id
    repos = [
        row
        for row in session.exec(select(GitLabRepo)).all()
        if _get_org_project(session, row.project_id, org_id) is not None
    ]
    if project_id:
        if _get_org_project(session, project_id, org_id) is None:
            return []
        repos = [row for row in repos if row.project_id == project_id]
    if client_id:
        projects = [
            row
            for row in session.exec(select(Project).where(Project.client_id == client_id)).all()
            if row.organization_id == org_id
        ]
        project_ids = {project.id for project in projects}
        repos = [row for row in repos if row.project_id in project_ids]
    return [_to_repo_out(row) for row in repos]


@router.get("/repos/{repo_id}", response_model=GitLabRepoOut)
def get_repo(
    repo_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    repo = _get_org_repo(session, repo_id, current_actor.organization.id)
    if not repo:
        raise HTTPException(status_code=404, detail="GitLab repo not found")
    return _to_repo_out(repo)


@router.patch("/repos/{repo_id}", response_model=GitLabRepoOut)
def update_repo(
    repo_id: UUID,
    payload: GitLabRepoUpdate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    repo = _get_org_repo(session, repo_id, current_actor.organization.id)
    if not repo:
        raise HTTPException(status_code=404, detail="GitLab repo not found")

    update = payload.model_dump(exclude_unset=True)
    if "name" in update:
        repo.name = (update["name"] or "").strip()
    if "repo_path" in update:
        repo.repo_path = (update["repo_path"] or "").strip()
    if "token_override" in update:
        repo.token_override = (update["token_override"] or "").strip() or None
    if "default_branch" in update:
        repo.default_branch = (update["default_branch"] or "").strip() or "main"
    if "webhook_secret" in update:
        repo.webhook_secret = (update["webhook_secret"] or "").strip() or None
    if "is_active" in update:
        repo.is_active = bool(update["is_active"])

    session.add(repo)
    session.commit()
    session.refresh(repo)

    log_updated(
        session,
        entity_type=EntityType.gitlab_repo,
        entity_id=repo.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"is_active": repo.is_active, "repo_path": repo.repo_path},
    )

    return _to_repo_out(repo)


@router.delete("/repos/{repo_id}", response_model=GitLabRepoOut)
def deactivate_repo(
    repo_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    repo = _get_org_repo(session, repo_id, current_actor.organization.id)
    if not repo:
        raise HTTPException(status_code=404, detail="GitLab repo not found")

    repo.is_active = False
    session.add(repo)
    session.commit()
    session.refresh(repo)

    log_updated(
        session,
        entity_type=EntityType.gitlab_repo,
        entity_id=repo.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"is_active": repo.is_active},
    )
    return _to_repo_out(repo)


@router.post("/repos/{repo_id}/pipeline/trigger", response_model=GitLabPipelineRunOut)
def trigger_repo_pipeline(
    repo_id: UUID,
    payload: GitLabTriggerRequest,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    repo = _get_org_repo(session, repo_id, current_actor.organization.id)
    if not repo or not repo.is_active:
        raise HTTPException(status_code=404, detail="Active GitLab repo not found")

    ref = (payload.ref or repo.default_branch).strip() or repo.default_branch
    settings = get_settings()
    gateway = GitLabGateway(settings)
    try:
        result = gateway.trigger_pipeline(
            repo_path=repo.repo_path,
            ref=ref,
            variables=payload.variables,
            token_override=repo.token_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitLab trigger failed: {exc}") from exc

    run = GitLabPipelineRun(
        repo_id=repo.id,
        pipeline_id=result.pipeline_id,
        ref=result.ref,
        status=result.status,
        triggered_by=current_actor.person.id,
        web_url=result.web_url,
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    log_created(
        session,
        entity_type=EntityType.gitlab_pipeline_run,
        entity_id=run.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"repo_id": str(repo.id), "pipeline_id": run.pipeline_id, "status": run.status},
    )

    return run


@router.get("/repos/{repo_id}/pipelines", response_model=list[GitLabPipelineRunOut])
def list_repo_pipelines(
    repo_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    repo = _get_org_repo(session, repo_id, current_actor.organization.id)
    if not repo:
        raise HTTPException(status_code=404, detail="GitLab repo not found")

    rows = list(
        session.exec(
            select(GitLabPipelineRun).where(GitLabPipelineRun.repo_id == repo_id)
        ).all()
    )
    return sorted(rows, key=lambda row: row.triggered_at, reverse=True)


@router.get("/repos/{repo_id}/pipelines/{pipeline_id}/refresh", response_model=GitLabPipelineRunOut)
def refresh_pipeline_status(
    repo_id: UUID,
    pipeline_id: int,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    repo = _get_org_repo(session, repo_id, current_actor.organization.id)
    if not repo:
        raise HTTPException(status_code=404, detail="GitLab repo not found")

    run = session.exec(
        select(GitLabPipelineRun).where(
            GitLabPipelineRun.repo_id == repo_id,
            GitLabPipelineRun.pipeline_id == pipeline_id,
        )
    ).first()
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    settings = get_settings()
    gateway = GitLabGateway(settings)
    try:
        result = gateway.get_pipeline_status(
            repo_path=repo.repo_path,
            pipeline_id=run.pipeline_id,
            token_override=repo.token_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitLab refresh failed: {exc}") from exc

    run.status = result.status
    run.ref = result.ref or run.ref
    run.web_url = result.web_url or run.web_url
    run.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


@router.post("/webhooks/{repo_id}")
def gitlab_webhook(
    repo_id: UUID,
    payload: dict,
    x_gitlab_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    repo = session.get(GitLabRepo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="GitLab repo not found")

    expected = repo.webhook_secret or ""
    provided = x_gitlab_token or ""
    if expected and not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=403, detail="Invalid webhook token")

    object_kind = payload.get("object_kind")
    if object_kind != "pipeline":
        return {"ok": True, "ignored": True}

    object_attributes = payload.get("object_attributes") or {}
    gitlab_pipeline_id = object_attributes.get("id")
    gitlab_status = object_attributes.get("status")
    gitlab_ref = object_attributes.get("ref")
    gitlab_web_url = object_attributes.get("web_url")

    if gitlab_pipeline_id is None:
        raise HTTPException(status_code=400, detail="Missing pipeline id in webhook payload")

    run = session.exec(
        select(GitLabPipelineRun).where(
            GitLabPipelineRun.repo_id == repo_id,
            GitLabPipelineRun.pipeline_id == int(gitlab_pipeline_id),
        )
    ).first()

    if not run:
        run = GitLabPipelineRun(
            repo_id=repo_id,
            pipeline_id=int(gitlab_pipeline_id),
            ref=str(gitlab_ref or repo.default_branch),
            status=str(gitlab_status or "pending"),
            triggered_by=None,
            web_url=gitlab_web_url,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
    else:
        run.status = str(gitlab_status or run.status)
        if gitlab_ref:
            run.ref = str(gitlab_ref)
        if gitlab_web_url:
            run.web_url = str(gitlab_web_url)
        run.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    session.add(run)
    session.commit()
    return {"ok": True}

