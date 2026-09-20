import uuid

import fitz
from pathlib import Path

from app.config import PROCESSED_DIR


class PDFProcessor:

    def pdf_to_images(self, pdf_path):
        doc = fitz.open(pdf_path)
        pages = []

        output_dir = PROCESSED_DIR / pdf_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, page in enumerate(doc):

            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            image_path = output_dir / f"page_{i+1}.png"

            pix.save(image_path)

            pages.append(image_path)

        doc.close()

        return pages

    def create_searchable_pdf(
        self,
        image_path,
        detections,
        output_path
    ):
        """
        Create a searchable PDF from a single image with OCR detections.

        The original image is preserved as the visual layer.
        An invisible text layer is placed over detected text regions
        using render_mode=3 (invisible fill and stroke).

        Args:
            image_path: Path to the source image.
            detections: List of detection dicts with text, box, x, y,
                        width, height keys.
            output_path: Where to save the searchable PDF.
        """

        doc = fitz.open()

        self._add_searchable_page(doc, image_path, detections)

        doc.save(str(output_path))
        doc.close()

    def create_searchable_pdf_multi(
        self,
        page_data,
        output_path
    ):
        """
        Create a multi-page searchable PDF.

        Args:
            page_data: List of (image_path, detections) tuples.
            output_path: Where to save the searchable PDF.
        """

        doc = fitz.open()

        for image_path, detections in page_data:
            self._add_searchable_page(doc, image_path, detections)

        doc.save(str(output_path))
        doc.close()

    def _add_searchable_page(self, doc, image_path, detections):
        """
        Add one page to the document: image background + invisible text overlay.
        """

        # Read image dimensions
        image = fitz.Pixmap(str(image_path))
        width = image.width
        height = image.height
        image = None  # release pixmap memory

        page = doc.new_page(width=width, height=height)

        # Insert original image as visual background
        page.insert_image(
            page.rect,
            filename=str(image_path)
        )

        # Overlay invisible text at detected positions
        for item in detections:

            text = item.get("text", "")
            if not text:
                continue

            det_x = item.get("x", 0)
            det_y = item.get("y", 0)
            det_w = item.get("width", 100)
            det_h = item.get("height", 20)

            # Calculate font size to fit text within the bounding box width
            # Approximate: each character takes ~0.6 * fontsize in width
            char_count = max(len(text), 1)
            fontsize_by_width = det_w / (char_count * 0.6)
            fontsize_by_height = det_h * 0.85

            fontsize = min(fontsize_by_width, fontsize_by_height)
            fontsize = max(fontsize, 4)   # floor at 4pt
            fontsize = min(fontsize, 72)  # cap at 72pt

            # Place text at bottom-left of bounding box
            # (PyMuPDF insert_text uses baseline coordinates)
            insert_point = (det_x, det_y + det_h)

            try:
                page.insert_text(
                    insert_point,
                    text,
                    fontsize=fontsize,
                    render_mode=3,   # invisible fill and stroke
                )
            except Exception:
                # Skip individual text placement failures
                continue

    @staticmethod
    def generate_output_path(suffix=".pdf"):
        """Generate a unique output path for a searchable PDF."""
        return PROCESSED_DIR / f"searchable_{uuid.uuid4()}{suffix}"


pdf_processor = PDFProcessor()