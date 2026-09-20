from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File

from app.config import UPLOAD_DIR
from app.services.ocr_engine import ocr_service
from app.services.preprocess import preprocess_service
from app.services.pdf_processor import pdf_processor

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload endpoint.

    Supported inputs:
    - PNG
    - JPG
    - JPEG
    - PDF
    """

    extension = Path(file.filename).suffix.lower()

    allowed = {".png", ".jpg", ".jpeg", ".pdf"}

    if extension not in allowed:
        return {
            "success": False,
            "message": "Only PNG, JPG, JPEG and PDF files are supported."
        }

    # Save uploaded file
    filename = f"{uuid.uuid4()}{extension}"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ----------------------------
    # PDF Pipeline
    # ----------------------------
    if extension == ".pdf":

        pages = pdf_processor.pdf_to_images(filepath)

        extracted_text = []

        for page in pages:
            processed_page = preprocess_service.enhance(page)
            result = ocr_service.extract_text(processed_page)

            if result.get("success"):
                extracted_text.append(result.get("text", ""))

        return {
            "success": True,
            "filename": filename,
            "pages": len(pages),
            "ocr": {
                "success": True,
                "text": "\n\n".join(extracted_text),
                "confidence": 1.0
            }
        }

    # ----------------------------
    # Image Pipeline
    # ----------------------------

    processed_path = preprocess_service.enhance(filepath)

    result = ocr_service.extract_text(processed_path)

    return {
        "success": True,
        "filename": filename,
        "ocr": result
    }
