
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File

from app.services.ocr_engine import ocr_service

router = APIRouter(prefix="/ocr", tags=["OCR"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):

    extension = Path(file.filename).suffix.lower()

    allowed = {".png", ".jpg", ".jpeg"}

    if extension not in allowed:
        return {
            "success": False,
            "message": "Only PNG, JPG and JPEG files are supported."
        }

    filename = f"{uuid.uuid4()}{extension}"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = ocr_service.extract_text(filepath)

    return {
        "success": True,
        "filename": filename,
        "ocr": result
    }
