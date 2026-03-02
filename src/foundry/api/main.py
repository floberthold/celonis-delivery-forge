from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from foundry.api.routes import assets, auth, celonis, clients, projects, reviews, templates, timeline, ui, users
from foundry.db import init_db
from foundry.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parents[1] / "ui" / "static"),
    name="static",
)


@app.get("/health")
def healthcheck():
    return {"status": "ok", "app": settings.app_name, "env": settings.env}


app.include_router(ui.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(assets.router)
app.include_router(reviews.router)
app.include_router(templates.router)
app.include_router(timeline.router)
app.include_router(celonis.router)
