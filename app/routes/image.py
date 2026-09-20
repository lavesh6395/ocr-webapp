import logging
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File

from app.config import UPLOAD_DIR, MAX_UPLOAD_MB
from app.services.ocr_engine import ocr_service
from app.services.preprocess import preprocess_service
from app.services.pdf_processor import pdf_processor

logger = logging.getLogger("notebook-ai.routes")

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/image")
def upload_image(file: UploadFile = File(...)):
    """
    Unified upload endpoint for images and PDFs.

    Accepts PNG, JPG, JPEG, PDF.
    Returns extracted text + searchable PDF download link.
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

    # Backend file size validation
    file_size_mb = filepath.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_MB:
        filepath.unlink(missing_ok=True)
        return {
            "success": False,
            "message": f"File exceeds {MAX_UPLOAD_MB} MB limit."
        }

    logger.info(
        "Upload received: %s (%.1f MB, type: %s)",
        file.filename, file_size_mb, extension
    )

    # ----------------------------
    # PDF Pipeline
    # ----------------------------
    if extension == ".pdf":
        return _process_pdf(filepath, filename)

    # ----------------------------
    # Image Pipeline
    # ----------------------------
    return _process_image(filepath, filename)


def _process_image(filepath: Path, filename: str) -> dict:
    """Process a single image: preprocess → OCR → searchable PDF."""

    processed_path = preprocess_service.enhance(filepath)

    result = ocr_service.extract_text(processed_path)

    # Generate searchable PDF
    searchable_url = None
    if result.get("success") and result.get("detections"):
        try:
            output_path = pdf_processor.generate_output_path()
            pdf_processor.create_searchable_pdf(
                filepath, result["detections"], output_path
            )
            searchable_url = f"/download/{output_path.name}"
            logger.info("Searchable PDF generated: %s", output_path.name)
        except Exception as e:
            logger.warning("Searchable PDF generation failed: %s", e)

    response = {
        "success": True,
        "filename": filename,
        "ocr": {
            "success": result.get("success", False),
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0.0),
        }
    }

    if searchable_url:
        response["searchable_pdf"] = searchable_url

    return response


def _process_pdf(filepath: Path, filename: str) -> dict:
    """Process a multi-page PDF: split → preprocess → OCR → searchable PDF."""

    pages = pdf_processor.pdf_to_images(filepath)

    logger.info("PDF split into %d pages", len(pages))

    extracted_text = []
    confidences = []
    failed_pages = []
    page_data = []

    for i, page in enumerate(pages):
        processed_page = preprocess_service.enhance(page)
        result = ocr_service.extract_text(processed_page)

        if result.get("success"):
            extracted_text.append(result.get("text", ""))
            confidences.append(result.get("confidence", 0.0))
            page_data.append((page, result.get("detections", [])))
        else:
            logger.warning("OCR failed on page %d: %s", i + 1, result.get("error"))
            failed_pages.append(i + 1)
            page_data.append((page, []))

    avg_confidence = (
        round(sum(confidences) / len(confidences), 4)
        if confidences else 0.0
    )

    # Generate multi-page searchable PDF
    searchable_url = None
    if page_data:
        try:
            output_path = pdf_processor.generate_output_path()
            pdf_processor.create_searchable_pdf_multi(page_data, output_path)
            searchable_url = f"/download/{output_path.name}"
            logger.info("Multi-page searchable PDF generated: %s", output_path.name)
        except Exception as e:
            logger.warning("Searchable PDF generation failed: %s", e)

    response = {
        "success": True,
        "filename": filename,
        "pages": len(pages),
        "ocr": {
            "success": True,
            "text": "\n\n".join(extracted_text),
            "confidence": avg_confidence,
        }
    }

    if searchable_url:
        response["searchable_pdf"] = searchable_url

    if failed_pages:
        response["ocr"]["failed_pages"] = failed_pages

    return response
