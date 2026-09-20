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
            raise ValueError(f"Unable to read image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Mild denoising
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        # Improve local contrast
        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        )

        enhanced = clahe.apply(gray)

        output_path = PROCESSED_DIR / image_path.name
        cv2.imwrite(str(output_path), enhanced)

        return output_path


# Singleton instance imported by routes
preprocess_service = PreprocessService()
