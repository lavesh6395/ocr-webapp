
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.routes.image import router as image_router
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="OCR WebApp",
    version="0.2.0",
    description="Notebook-to-PDF AI"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(image_router)

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"version": "0.2.0"}
    )
