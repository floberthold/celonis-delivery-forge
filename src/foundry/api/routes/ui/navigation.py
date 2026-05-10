from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])

_UI_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "ui" / "templates"
_templates = Jinja2Templates(directory=str(_UI_TEMPLATE_DIR))


def _normalize_http_url(value: str | None) -> str:
    if not value:
        return ""
    candidate = value.strip()
    if not candidate:
        return ""
    parsed = urlparse(candidate)
    if not parsed.scheme:
        candidate = f"https://{candidate}"
        parsed = urlparse(candidate)
    if parsed.scheme.lower() not in {"http", "https"}:
        return ""
    return candidate


_templates.env.filters["normalized_url"] = _normalize_http_url


@router.get("/tenant-ui")
def tenant_ui(request: Request):
    return _templates.TemplateResponse(request, "tenant.html",
        {
            "request": request,
        },
    )


@router.get("/workspace-ui")
def workspace_ui(request: Request):
    tenant_url = request.query_params.get("url") or "https://id.celonis.cloud/user/ui/login"
    return _templates.TemplateResponse(request, "workspace.html",
        {
            "request": request,
            "tenant_url": tenant_url,
        },
    )

