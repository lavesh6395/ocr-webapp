from pathlib import Path

import fitz

from app.config import PROCESSED_DIR


class PDFProcessor:

    def pdf_to_images(self, pdf_path: Path):

        doc = fitz.open(pdf_path)

        output_files = []

        for page_number, page in enumerate(doc):

            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            output_path = (
                PROCESSED_DIR /
                f"{pdf_path.stem}_page_{page_number+1}.png"
            )

            pix.save(output_path)

            output_files.append(output_path)

        doc.close()

        return output_files


pdf_processor = PDFProcessor()
