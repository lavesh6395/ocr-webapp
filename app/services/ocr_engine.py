from paddleocr import PaddleOCR

# Load model once when server starts
ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en",
    use_gpu=False
)


class OCRService:

    def extract_text(self, image_path):

        result = ocr.ocr(str(image_path), cls=True)

        lines = []

        confidences = []

        if result and result[0]:

            for item in result[0]:

                text = item[1][0]
                conf = item[1][1]

                lines.append(text)
                confidences.append(conf)

        confidence = (
            sum(confidences) / len(confidences)
            if confidences else 0
        )

        return {
            "success": True,
            "text": "\n".join(lines),
            "confidence": round(confidence, 3)
        }


ocr_service = OCRService()
