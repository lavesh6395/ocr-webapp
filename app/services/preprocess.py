import uuid
import logging
from pathlib import Path

import cv2
import numpy as np

from app.config import PROCESSED_DIR

logger = logging.getLogger("notebook-ai.preprocess")


class PreprocessService:
    """
    Smart image preprocessing for OCR.

    Auto-detects image type and applies the optimal pipeline:
    - Handwritten notebook photos: rotation correction, ink isolation,
      ruled-line removal, adaptive thresholding
    - Clean scanned documents / screenshots: minimal processing,
      preserve quality for PaddleOCR's internal pipeline
    """

    def enhance(self, image_path: Path) -> Path:
        """
        Preprocess image for OCR with automatic mode detection.

        Args:
            image_path: Path to the input image.

        Returns:
            Path to the processed image saved in PROCESSED_DIR.
        """

        image = cv2.imread(str(image_path))

        if image is None:
            raise ValueError(f"Unable to read image: {image_path}")

        # Auto-detect: is this a handwritten notebook or a clean scan?
        mode = self._detect_mode(image)
        logger.info("Detected image mode: %s", mode)

        if mode == "handwritten":
            processed = self._handwriting_pipeline(image)
        elif mode == "scanned":
            processed = self._scanned_pipeline(image)
        else:
            # High-quality digital screenshot — minimal processing
            processed = self._digital_pipeline(image)

        # UUID-based filename for concurrency safety
        output_name = f"{uuid.uuid4()}.png"
        output_path = PROCESSED_DIR / output_name
        cv2.imwrite(str(output_path), processed)

        return output_path

    # ------------------------------------------------------------------
    # Auto-detection
    # ------------------------------------------------------------------

    def _detect_mode(self, image: np.ndarray) -> str:
        """
        Classify the image into one of three categories:
        - "handwritten": notebook page with handwriting (color, ruled lines)
        - "scanned": B&W or grayscale scanned document
        - "digital": clean digital screenshot or printed document photo

        Heuristics:
        1. Mean saturation: high → color photo (likely handwritten)
        2. Edge density: very low → scanned/digital; moderate → handwriting
        3. Horizontal line frequency: many → ruled notebook paper
        """

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mean_saturation = np.mean(hsv[:, :, 1])

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Edge density as proxy for content type
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size

        # Detect ruled lines via horizontal morphological opening
        h_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (max(image.shape[1] // 10, 80), 1)
        )
        h_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, h_kernel)
        h_line_density = np.sum(h_lines > 0) / h_lines.size

        logger.info(
            "Detection heuristics: sat=%.1f edge=%.4f hlines=%.4f",
            mean_saturation, edge_density, h_line_density
        )

        # Ruled notebook paper with color ink
        if mean_saturation > 25 and h_line_density > 0.002:
            return "handwritten"

        # Color photo but no ruled lines — could still be handwriting
        if mean_saturation > 25 and edge_density > 0.02:
            return "handwritten"

        # Low saturation, clean content — scanned document
        if mean_saturation < 15 and edge_density < 0.05:
            return "scanned"

        # Default: treat as digital/printed
        return "digital"

    # ------------------------------------------------------------------
    # Pipeline: Handwritten notebook pages
    # ------------------------------------------------------------------

    def _handwriting_pipeline(self, image: np.ndarray) -> np.ndarray:
        """
        Full pipeline for handwritten notebook photos.

        Steps:
        1. Auto-rotate if 90°/270° rotation detected
        2. HSV ink isolation (separate ink from ruled lines)
        3. Adaptive thresholding for clean binarization
        """

        rotated = self._auto_rotate(image)
        ink_isolated = self._isolate_ink(rotated)
        cleaned = self._adaptive_clean(ink_isolated)

        return cleaned

    def _auto_rotate(self, image: np.ndarray) -> np.ndarray:
        """
        Detect if text is rotated 90° or 270° and correct it.

        Uses contour aspect-ratio voting: if most significant contours
        are taller than wide, the text is sideways.
        """

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Dilate horizontally to merge characters into word/line blobs
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return image

        horizontal_count = 0
        vertical_count = 0

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Skip noise
            if w * h < 200:
                continue

            aspect = w / h if h > 0 else 1

            if aspect > 1.5:
                horizontal_count += 1
            elif aspect < 0.67:
                vertical_count += 1

        total = horizontal_count + vertical_count
        if total > 0 and vertical_count / total > 0.6:
            logger.info("Rotation detected — rotating 90° clockwise")
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

        return image

    def _isolate_ink(self, image: np.ndarray) -> np.ndarray:
        """
        Separate ink from ruled lines using HSV color space.

        Strategy:
        1. Extract dark pixels (inverted V-channel) — captures all ink
        2. Extract blue-hue pixels — captures blue ink specifically
        3. Combine into ink mask
        4. Detect and remove long horizontal ruled lines
        5. Restore ink at intersection points (where text crosses lines)
        """

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mean_saturation = np.mean(hsv[:, :, 1])

        if mean_saturation < 20:
            # Near-grayscale image — skip color processing
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        _, _, v_channel = cv2.split(hsv)

        # Dark ink becomes bright after inversion
        ink_mask = cv2.bitwise_not(v_channel)

        # Blue ink range in OpenCV HSV (H: 90-135)
        lower_blue = np.array([90, 40, 0])
        upper_blue = np.array([135, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        combined = cv2.bitwise_or(ink_mask, blue_mask)

        # Detect ruled lines (long horizontal structures)
        h_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (max(image.shape[1] // 20, 40), 1)
        )
        lines = cv2.morphologyEx(combined, cv2.MORPH_OPEN, h_kernel)

        # Remove lines but preserve where ink crosses them
        result = cv2.subtract(combined, lines)

        cross_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        ink_dilated = cv2.dilate(ink_mask, cross_kernel, iterations=1)
        crossings = cv2.bitwise_and(ink_dilated, lines)
        result = cv2.bitwise_or(result, crossings)

        return result

    def _adaptive_clean(self, gray: np.ndarray) -> np.ndarray:
        """
        Adaptive threshold with bilateral denoising.
        Handles uneven lighting from phone cameras.
        """

        denoised = cv2.bilateralFilter(gray, 5, 50, 50)

        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=21,
            C=10
        )

        return binary

    # ------------------------------------------------------------------
    # Pipeline: Scanned documents (B&W / grayscale)
    # ------------------------------------------------------------------

    def _scanned_pipeline(self, image: np.ndarray) -> np.ndarray:
        """
        Minimal processing for clean scanned documents.
        Scans typically have good contrast already — just clean noise.
        """

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Otsu's binarization works well on clean scans with
        # bimodal histogram (white paper + black text)
        _, binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        return binary

    # ------------------------------------------------------------------
    # Pipeline: Digital screenshots / printed documents
    # ------------------------------------------------------------------

    def _digital_pipeline(self, image: np.ndarray) -> np.ndarray:
        """
        Preserve quality for high-clarity digital images.
        PaddleOCR handles these well natively — just ensure grayscale.
        """

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Light CLAHE to normalize any brightness variation
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        return enhanced


# Singleton instance
preprocess_service = PreprocessService()
