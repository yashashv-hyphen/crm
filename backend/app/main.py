import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import auth, users, activities, leads, uploads, dashboard, reports, templates, events
from app.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CRM Backend started")
    yield


app = FastAPI(
    title="Global Sales SSR Team CRM",
    version="1.0.0",
    lifespan=lifespan,
)

_default_origins = [
    "http://localhost:5173",
    "http://localhost:80",
    "http://localhost",
    "http://127.0.0.1:5173",
]
_extra = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
_origins = list(dict.fromkeys(_default_origins + _extra))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(activities.router)
app.include_router(leads.router)
app.include_router(uploads.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(templates.router)
app.include_router(events.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve built React frontend (production only — not present in dev)
_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
if os.path.isdir(_STATIC):
    _assets = os.path.join(_STATIC, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="static-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        return FileResponse(os.path.join(_STATIC, "index.html"))
