from fastapi import APIRouter
from app.services.ocr_engine import ocr_service
from app.config import APP_VERSION

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():

    return {
        "status": "healthy",
        "ocr_loaded": ocr_service.ready,
        "version": APP_VERSION
    }