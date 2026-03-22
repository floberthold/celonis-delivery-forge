from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote_plus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from foundry.api.routes import (
    assets,
    auth,
    celonis,
    clients,
    forum_insights,
    gitlab,
    ingest,
    kpi_book,
    kpis,
    orgs,
    projects,
    quests,
    reviews,
    snapshots,
    templates,
    timeline,
    todos,
    ui,
    use_cases,
    users,
    files,
)
from foundry.db import get_database_backend, get_database_startup_mode, init_db
from foundry.settings import get_settings

settings = get_settings()

_API_PATH_PREFIXES = (
    "/auth",
    "/people",
    "/orgs",
    "/clients",
    "/projects",
    "/quests",
    "/assets",
    "/reviews",
    "/templates",
    "/timeline",
    "/files",
    "/todos",
    "/forum-insights",
    "/kpis",
    "/celonis",
    "/gitlab",
    "/use-cases",
    "/ingest",
    "/snapshots",
    "/kpi-book",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/static",
    "/docu",
)


def _is_ui_browser_request(request: Request, exc: StarletteHTTPException) -> bool:
    if exc.status_code != 401 or request.method.upper() != "GET":
        return False

    path = request.url.path
    if path.startswith(_API_PATH_PREFIXES):
        return False

    accept_header = request.headers.get("accept", "").lower()
    if "application/json" in accept_header and "text/html" not in accept_header and "*/*" not in accept_header:
        return False

    return True


async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    if _is_ui_browser_request(request, exc):
        next_path = request.url.path
        if request.url.query:
            next_path += f"?{request.url.query}"
        return RedirectResponse(
            url=f"/login?next_path={quote_plus(next_path)}",
            status_code=303,
        )

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_exception_handler(StarletteHTTPException, handle_http_exception)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parents[1] / "ui" / "static"),
    name="static",
)


@app.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.env,
        "database_backend": get_database_backend(),
        "database_startup_mode": get_database_startup_mode(),
    }


app.include_router(ui.router)
app.include_router(auth.router)
app.include_router(orgs.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(quests.router)
app.include_router(assets.router)
app.include_router(reviews.router)
app.include_router(templates.router)
app.include_router(timeline.router)
app.include_router(files.router)
app.include_router(todos.router)
app.include_router(forum_insights.router)
app.include_router(kpis.router)
app.include_router(celonis.router)
app.include_router(gitlab.router)
app.include_router(use_cases.router)
app.include_router(ingest.router)
app.include_router(snapshots.router)
app.include_router(kpi_book.router)
