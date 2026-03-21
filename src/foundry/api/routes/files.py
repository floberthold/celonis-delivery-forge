import re
import shutil
from pathlib import Path
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import (
    Client,
    DeliveryFile,
    EntityType,
    FileSource,
    OrganizationMembership,
    Project,
    TemplateLibrary,
)
from foundry.schemas import DeliveryFileLinkCreate, DeliveryFileOut, FileViewerUrlResponse
from foundry.services.activity_log import log_created
from foundry.settings import get_settings

router = APIRouter(prefix="/files", tags=["files"])
settings = get_settings()


_OFFICE_EXTENSIONS = {".ppt", ".pptx", ".xls", ".xlsx"}
_ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"}
_ALLOWED_UPLOAD_MIME_TYPES = {
    "application/pdf",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "application/csv",
    "application/octet-stream",
}


def _normalize_http_url(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.lower().startswith(("http://", "https://")):
        return candidate
    return f"https://{candidate}"


def _make_office_viewer_url(source_url: str) -> str:
    return f"https://view.officeapps.live.com/op/embed.aspx?src={quote(source_url, safe='')}"


def _guess_extension(row: DeliveryFile) -> str:
    if row.stored_filename:
        return Path(row.stored_filename).suffix.lower()
    if row.external_url:
        return Path(row.external_url.split("?", 1)[0]).suffix.lower()
    return ""


def _public_download_url(file_id: UUID) -> str | None:
    base = settings.public_base_url.strip().rstrip("/")
    if not base:
        return None
    return f"{base}/files/{file_id}/download"


def _get_upload_size(upload: UploadFile) -> int:
    upload.file.seek(0, 2)
    size = upload.file.tell()
    upload.file.seek(0)
    return size


def _validate_upload(upload: UploadFile) -> tuple[str, int]:
    original_name = (upload.filename or "").strip()
    suffix = Path(original_name).suffix.lower()
    if suffix not in _ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file extension. Allowed: "
                + ", ".join(sorted(_ALLOWED_UPLOAD_EXTENSIONS))
            ),
        )

    mime_type = (upload.content_type or "").lower()
    if mime_type and mime_type not in _ALLOWED_UPLOAD_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type: {mime_type}",
        )

    size = _get_upload_size(upload)
    if size > settings.delivery_file_max_upload_bytes:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File exceeds max allowed size of {settings.delivery_file_max_upload_bytes} bytes"
            ),
        )
    return suffix, size


def _build_viewer_payload(row: DeliveryFile) -> FileViewerUrlResponse:
    download_url = f"/files/{row.id}/download"
    extension = _guess_extension(row)
    normalized_external_url = _normalize_http_url(row.external_url)

    if row.file_source == FileSource.uploaded:
        if extension == ".pdf" or (row.mime_type or "").lower() == "application/pdf":
            return FileViewerUrlResponse(
                viewer_url=download_url,
                viewer_type="pdf",
                download_url=download_url,
            )

        if extension in _OFFICE_EXTENSIONS:
            public_download_url = _public_download_url(row.id)
            if public_download_url:
                return FileViewerUrlResponse(
                    viewer_url=_make_office_viewer_url(public_download_url),
                    viewer_type="office",
                    download_url=download_url,
                )

        return FileViewerUrlResponse(viewer_url=None, viewer_type=None, download_url=download_url)

    if normalized_external_url:
        if extension == ".pdf":
            return FileViewerUrlResponse(
                viewer_url=normalized_external_url,
                viewer_type="pdf",
                download_url=download_url,
            )

        if extension in _OFFICE_EXTENSIONS or row.file_source in {
            FileSource.sharepoint_doc,
            FileSource.onedrive_doc,
        }:
            return FileViewerUrlResponse(
                viewer_url=_make_office_viewer_url(normalized_external_url),
                viewer_type="office",
                download_url=download_url,
            )

        return FileViewerUrlResponse(
            viewer_url=normalized_external_url,
            viewer_type="external",
            download_url=download_url,
        )

    return FileViewerUrlResponse(viewer_url=None, viewer_type=None, download_url=download_url)


def _org_person_ids(session: Session, organization_id: UUID) -> set[UUID]:
    memberships = list(
        session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id
            )
        ).all()
    )
    return {row.person_id for row in memberships}


def _get_org_client(session: Session, client_id: UUID, organization_id: UUID) -> Client | None:
    client = session.get(Client, client_id)
    if not client or client.organization_id != organization_id:
        return None
    return client


def _get_org_project(session: Session, project_id: UUID, organization_id: UUID) -> Project | None:
    project = session.get(Project, project_id)
    if not project or project.organization_id != organization_id:
        return None
    return project


def _get_org_library(session: Session, library_id: UUID, organization_id: UUID) -> TemplateLibrary | None:
    library = session.get(TemplateLibrary, library_id)
    if not library or library.organization_id != organization_id:
        return None
    return library


def _delivery_file_in_org(session: Session, row: DeliveryFile, organization_id: UUID) -> bool:
    person_ids = _org_person_ids(session, organization_id)
    return bool(
        (row.library_id and _get_org_library(session, row.library_id, organization_id) is not None)
        or (row.client_id and _get_org_client(session, row.client_id, organization_id) is not None)
        or (row.project_id and _get_org_project(session, row.project_id, organization_id) is not None)
        or (row.uploaded_by and row.uploaded_by in person_ids)
    )


@router.post("/link", response_model=DeliveryFileOut)
def create_file_link(
    payload: DeliveryFileLinkCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if payload.file_source == FileSource.uploaded:
        raise HTTPException(status_code=400, detail="Use /files/upload for uploaded files")

    normalized_url = _normalize_http_url(payload.external_url)
    if not normalized_url:
        raise HTTPException(status_code=400, detail="external_url is required for link sources")

    org_id = current_actor.organization.id

    if payload.library_id:
        library = _get_org_library(session, payload.library_id, org_id)
        if not library:
            raise HTTPException(status_code=404, detail="Library not found")
    if payload.client_id and _get_org_client(session, payload.client_id, org_id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if payload.project_id and _get_org_project(session, payload.project_id, org_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    row = DeliveryFile(
        **payload.model_dump(exclude={"external_url"}),
        external_url=normalized_url,
        uploaded_by=current_actor.person.id,
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    log_created(
        session,
        entity_type=EntityType.delivery_file,
        entity_id=row.id,
        actor_id=current_actor.person.id,
        organization_id=org_id,
        metadata={
            "source": row.file_source.value,
            "library_id": str(row.library_id) if row.library_id else None,
            "client_id": str(row.client_id) if row.client_id else None,
            "project_id": str(row.project_id) if row.project_id else None,
        },
    )

    return row


@router.post("/upload", response_model=DeliveryFileOut)
def upload_file(
    name: str = Form(...),
    description: str = Form(""),
    library_id: UUID | None = Form(None),
    client_id: UUID | None = Form(None),
    project_id: UUID | None = Form(None),
    upload: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    _validate_upload(upload)

    org_id = current_actor.organization.id
    if library_id and _get_org_library(session, library_id, org_id) is None:
        raise HTTPException(status_code=404, detail="Library not found")
    if client_id and _get_org_client(session, client_id, org_id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if project_id and _get_org_project(session, project_id, org_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    original_name = (upload.filename or "file").strip() or "file"
    source_path = Path(original_name)
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", source_path.stem).strip("-._") or "file"
    safe_suffix = re.sub(r"[^A-Za-z0-9.]+", "", source_path.suffix)[:16]
    stored_filename = f"{uuid4().hex}_{safe_stem[:48]}{safe_suffix}"
    destination = uploads_dir / stored_filename

    upload.file.seek(0)
    with destination.open("wb") as handle:
        shutil.copyfileobj(upload.file, handle)

    file_size_bytes = destination.stat().st_size

    row = DeliveryFile(
        name=name.strip(),
        description=description.strip() or None,
        file_source=FileSource.uploaded,
        library_id=library_id,
        client_id=client_id,
        project_id=project_id,
        stored_filename=stored_filename,
        mime_type=upload.content_type,
        file_size_bytes=file_size_bytes,
        uploaded_by=current_actor.person.id,
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    log_created(
        session,
        entity_type=EntityType.delivery_file,
        entity_id=row.id,
        actor_id=current_actor.person.id,
        organization_id=org_id,
        metadata={
            "source": row.file_source.value,
            "stored_filename": row.stored_filename,
            "size_bytes": row.file_size_bytes,
            "library_id": str(row.library_id) if row.library_id else None,
            "client_id": str(row.client_id) if row.client_id else None,
            "project_id": str(row.project_id) if row.project_id else None,
        },
    )

    return row


@router.get("/", response_model=list[DeliveryFileOut])
def list_files(
    project_id: UUID | None = None,
    client_id: UUID | None = None,
    file_source: FileSource | None = None,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    org_id = current_actor.organization.id
    if project_id is not None and _get_org_project(session, project_id, org_id) is None:
        return []
    if client_id is not None and _get_org_client(session, client_id, org_id) is None:
        return []

    stmt = select(DeliveryFile)
    if project_id is not None:
        stmt = stmt.where(DeliveryFile.project_id == project_id)
    if client_id is not None:
        stmt = stmt.where(DeliveryFile.client_id == client_id)
    if file_source is not None:
        stmt = stmt.where(DeliveryFile.file_source == file_source)
    rows = list(session.exec(stmt).all())
    return [row for row in rows if _delivery_file_in_org(session, row, org_id)]


@router.get("/{file_id}/download")
def download_file(
    file_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    row = session.get(DeliveryFile, file_id)
    if not row or not _delivery_file_in_org(session, row, current_actor.organization.id):
        raise HTTPException(status_code=404, detail="File not found")

    if row.file_source != FileSource.uploaded:
        normalized = _normalize_http_url(row.external_url)
        if not normalized:
            raise HTTPException(status_code=404, detail="External URL not available")
        return RedirectResponse(url=normalized, status_code=307)

    if not row.stored_filename:
        raise HTTPException(status_code=404, detail="Stored file path is missing")

    file_path = Path(settings.uploads_dir) / row.stored_filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored file not found")

    return FileResponse(
        path=file_path,
        media_type=row.mime_type or "application/octet-stream",
        filename=file_path.name,
    )


@router.get("/{file_id}/viewer-url", response_model=FileViewerUrlResponse)
def get_file_viewer_url(
    file_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    row = session.get(DeliveryFile, file_id)
    if not row or not _delivery_file_in_org(session, row, current_actor.organization.id):
        raise HTTPException(status_code=404, detail="File not found")
    return _build_viewer_payload(row)


@router.delete("/{file_id}")
def delete_file(
    file_id: UUID,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    row = session.get(DeliveryFile, file_id)
    if not row or not _delivery_file_in_org(session, row, current_actor.organization.id):
        raise HTTPException(status_code=404, detail="File not found")

    stored_path: Path | None = None
    if row.file_source == FileSource.uploaded and row.stored_filename:
        stored_path = Path(settings.uploads_dir) / row.stored_filename

    session.delete(row)
    session.commit()

    if stored_path and stored_path.is_file():
        stored_path.unlink(missing_ok=True)

    return {"ok": True, "id": str(file_id), "deleted_by": str(current_actor.person.id)}
