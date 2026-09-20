from pathlib import Path

import cv2

from app.config import PROCESSED_DIR


class PreprocessService:
    """
    Basic notebook image enhancement.
    """

    def enhance(self, image_path: Path) -> Path:

        image = cv2.imread(str(image_path))

        if image is None:
            raise ValueError("Unable to read image.")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        )

        enhanced = clahe.apply(gray)

        output_path = PROCESSED_DIR / image_path.name

        cv2.imwrite(str(output_path), enhanced)

        return output_path


preprocess_service = PreprocessService()
