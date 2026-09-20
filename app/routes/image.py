
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/ocr", tags=["OCR"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    extension = Path(file.filename).suffix
    filename = f"{uuid.uuid4()}{extension}"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "success": True,
        "filename": filename,
        "message": "Upload successful. OCR integration coming next."
    }
