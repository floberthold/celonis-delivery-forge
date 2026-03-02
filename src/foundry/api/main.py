from contextlib import asynccontextmanager

from fastapi import FastAPI

from foundry.api.routes import assets, auth, clients, projects, reviews, timeline, users
from foundry.db import init_db
from foundry.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def healthcheck():
    return {"status": "ok", "app": settings.app_name, "env": settings.env}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(assets.router)
app.include_router(reviews.router)
app.include_router(timeline.router)
