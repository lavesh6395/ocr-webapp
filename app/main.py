import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import APP_NAME, APP_VERSION, PROCESSED_DIR
from app.routes.health import router as health_router
from app.routes.image import router as image_router
from app.services.ocr_engine import ocr_service

logger = logging.getLogger("notebook-ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)
    ocr_service.initialize()
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Convert handwritten notebooks and scanned documents into searchable PDFs.",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(image_router)
app.include_router(health_router)


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"version": APP_VERSION},
    )


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Serve generated searchable PDFs for download."""

    # Sanitize: only allow safe characters
    safe_chars = set("abcdefghijklmnopqrstuvwxyz0123456789-_.")
    if not all(c in safe_chars for c in filename.lower()):
        return {"success": False, "message": "Invalid filename."}

    filepath = PROCESSED_DIR / filename

    if not filepath.exists() or not filepath.is_file():
        return {"success": False, "message": "File not found."}

    # Path traversal guard
    try:
        filepath.resolve().relative_to(PROCESSED_DIR.resolve())
    except ValueError:
        return {"success": False, "message": "Invalid path."}

    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=f"notebook_searchable.pdf",
    )
