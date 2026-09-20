
from pathlib import Path

class OCRService:
    """
    OCR abstraction layer.
    Placeholder implementation for Sprint 3.
    Later this class will load PaddleOCR only once.
    """

    def extract_text(self, image_path: Path):
        return {
            "success": True,
            "text": (
                "OCR placeholder.\n\n"
                "Handwriting recognition will be enabled "
                "with PaddleOCR in the next milestone."
            ),
            "confidence": 1.0
        }


ocr_service = OCRService()
