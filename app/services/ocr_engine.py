import logging
from paddleocr import PaddleOCR
from app.services.formatter import formatter

logger = logging.getLogger("notebook-ai.ocr")


class OCRService:
    """Singleton OCR service with explicit startup initialization."""

    def __init__(self):
        self.ocr = None
        self.ready = False

    def initialize(self):
        """Load PaddleOCR once when FastAPI starts."""
        if self.ready:
            return

        logger.info("Initializing PaddleOCR (lang=latin, angle_cls=True)...")

        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="latin",
            show_log=False,
            det_db_thresh=0.2,
            det_db_box_thresh=0.4,
            rec_batch_num=6,
        )

        self.ready = True
        logger.info("PaddleOCR initialized successfully.")

    def extract_text(self, image_path):
        """
        Run OCR on a preprocessed image.

        Returns dict with keys:
            success, text, confidence, detections
        """

        if not self.ready:
            raise RuntimeError("OCR engine has not been initialized.")

        try:

            result = self.ocr.ocr(str(image_path), cls=True)

            detections = []
            confidences = []

            if result and result[0]:

                for item in result[0]:

                    box = item[0]      # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                    text = item[1][0]
                    score = float(item[1][1])

                    x = min(p[0] for p in box)
                    y = min(p[1] for p in box)
                    width = max(p[0] for p in box) - x
                    height = max(p[1] for p in box) - y

                    detections.append({
                        "text": text,
                        "score": score,
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "box": box,
                    })

                    confidences.append(score)

            cleaned_text = formatter.format(detections)

            avg_conf = (
                round(sum(confidences) / len(confidences), 4)
                if confidences else 0.0
            )

            logger.info(
                "OCR complete: %d detections, avg confidence %.2f",
                len(detections), avg_conf
            )

            return {
                "success": True,
                "text": cleaned_text,
                "confidence": avg_conf,
                "detections": detections,
            }

        except Exception as e:
            logger.error("OCR failed: %s", str(e))

            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "detections": [],
                "error": str(e)
            }


ocr_service = OCRService()