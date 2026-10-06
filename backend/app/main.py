import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.deps import get_store
from app.errors import StoreError
from app.routers import issues, sites, studies

DEFAULT_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def static_dir() -> Path:
    configured = os.environ.get("STATIC_DIR")
    return Path(configured) if configured else DEFAULT_STATIC_DIR


def mount_frontend(application: FastAPI, directory: Path | None = None) -> bool:
    """Serve the Vite build if present. Register last so /api keeps priority."""
    root = directory if directory is not None else static_dir()
    if not root.is_dir() or not (root / "index.html").is_file():
        return False
    root = root.resolve()
    index = root / "index.html"
    assets = root / "assets"
    if assets.is_dir():
        application.mount("/assets", StaticFiles(directory=assets), name="assets")

    @application.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"error": "Not found"})
        candidate = (root / full_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)

    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    override = app.dependency_overrides.get(get_store)
    current = override() if override else get_store()
    if not current.list_studies():
        current.seed()
    yield


app = FastAPI(
    title="Site Issue Triage API",
    version="0.1.0",
    description="Implements openapi.yaml. No authentication.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(studies.router)
app.include_router(sites.router)
app.include_router(issues.router)


@app.exception_handler(StoreError)
async def store_error(_request: Request, exc: StoreError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"error": exc.error})


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    location = " ".join(str(part) for part in first.get("loc", []) if part != "body")
    message = first.get("msg", "Invalid request")
    error = f"{location}: {message}" if location else message
    return JSONResponse(status_code=400, content={"error": error})


mount_frontend(app)
