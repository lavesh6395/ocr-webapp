from paddleocr import PaddleOCR

# Load once at startup
_ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en",
    show_log=False
)


class OCRService:
    """Singleton wrapper around PaddleOCR."""

    def extract_text(self, image_path):
        try:
            result = _ocr.ocr(str(image_path), cls=True)

            lines = []
            confidences = []

            if result and result[0]:
                for item in result[0]:
                    text = item[1][0]
                    score = float(item[1][1])

                    lines.append(text)
                    confidences.append(score)

            return {
                "success": True,
                "text": "\n".join(lines),
                "confidence": (
                    sum(confidences) / len(confidences)
                    if confidences else 0.0
                )
            }

        except Exception as e:
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "error": str(e)
            }


# Export singleton service
ocr_service = OCRService()
