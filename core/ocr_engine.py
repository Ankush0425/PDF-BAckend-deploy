"""
OCR Engine — Tesseract & PaddleOCR support with multi-language and handwriting OCR.
"""

import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from config import OCR_LANGUAGES, PADDLE_OCR_LANGUAGES
from utils.file_manager import get_temp_path
from utils.logger import get_logger

logger = get_logger("ocr_engine")

# ── Check PaddleOCR availability ──
_paddle_available = False
try:
    from paddleocr import PaddleOCR
    _paddle_available = True
    logger.info("PaddleOCR is available")
except ImportError:
    logger.info("PaddleOCR not installed — using Tesseract only")


def is_paddle_available() -> bool:
    """Check if PaddleOCR is installed."""
    return _paddle_available


# ──────────────────────────────────────────────
# Tesseract OCR
# ──────────────────────────────────────────────
def ocr_image_tesseract(image_path: Path, language: str = "eng") -> str:
    """
    Extract text from an image using Tesseract OCR.

    Args:
        image_path: Path to the image file.
        language: Tesseract language code (e.g., 'eng', 'hin').

    Returns:
        Extracted text.
    """
    try:
        import pytesseract
        img = Image.open(str(image_path))
        text = pytesseract.image_to_string(img, lang=language)
        logger.info(f"Tesseract OCR: extracted {len(text)} chars from {image_path.name}")
        return text.strip()
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        raise RuntimeError(f"Tesseract OCR failed: {e}") from e


def ocr_pdf_tesseract(pdf_path: Path, language: str = "eng", dpi: int = 300) -> str:
    """
    Extract text from a scanned PDF using Tesseract.

    Args:
        pdf_path: Path to the PDF file.
        language: Tesseract language code.
        dpi: DPI for rendering PDF pages.

    Returns:
        Extracted text from all pages.
    """
    try:
        import pytesseract
        doc = fitz.open(str(pdf_path))
        text_parts = []

        for i, page in enumerate(doc):
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            img = Image.open(io.BytesIO(pix.tobytes("png")))
            page_text = pytesseract.image_to_string(img, lang=language)
            text_parts.append(f"--- Page {i + 1} ---\n{page_text}")

        doc.close()
        full_text = "\n\n".join(text_parts)
        logger.info(f"Tesseract PDF OCR: {len(doc)} pages, {len(full_text)} chars")
        return full_text
    except Exception as e:
        logger.error(f"Tesseract PDF OCR failed: {e}")
        raise RuntimeError(f"Tesseract PDF OCR failed: {e}") from e


# ──────────────────────────────────────────────
# PaddleOCR
# ──────────────────────────────────────────────
def ocr_image_paddle(image_path: Path, language: str = "en") -> str:
    """
    Extract text from an image using PaddleOCR.

    Args:
        image_path: Path to the image file.
        language: PaddleOCR language code.

    Returns:
        Extracted text.
    """
    if not _paddle_available:
        raise RuntimeError("PaddleOCR is not installed. Install with: pip install paddleocr paddlepaddle")

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang=language, show_log=False)
        results = ocr.ocr(str(image_path), cls=True)

        text_parts = []
        if results and results[0]:
            for line in results[0]:
                text_parts.append(line[1][0])

        text = "\n".join(text_parts)
        logger.info(f"PaddleOCR: extracted {len(text)} chars from {image_path.name}")
        return text
    except Exception as e:
        logger.error(f"PaddleOCR failed: {e}")
        raise RuntimeError(f"PaddleOCR failed: {e}") from e


def ocr_pdf_paddle(pdf_path: Path, language: str = "en", dpi: int = 300) -> str:
    """
    Extract text from a scanned PDF using PaddleOCR.

    Args:
        pdf_path: Path to the PDF file.
        language: PaddleOCR language code.
        dpi: DPI for rendering PDF pages.

    Returns:
        Extracted text from all pages.
    """
    if not _paddle_available:
        raise RuntimeError("PaddleOCR is not installed.")

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang=language, show_log=False)
        doc = fitz.open(str(pdf_path))
        text_parts = []

        for i, page in enumerate(doc):
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            img_path = get_temp_path(f"ocr_page_{i}.png")
            pix.save(str(img_path))

            results = ocr.ocr(str(img_path), cls=True)
            page_texts = []
            if results and results[0]:
                for line in results[0]:
                    page_texts.append(line[1][0])

            text_parts.append(f"--- Page {i + 1} ---\n" + "\n".join(page_texts))

        doc.close()
        full_text = "\n\n".join(text_parts)
        logger.info(f"PaddleOCR PDF: {len(doc)} pages, {len(full_text)} chars")
        return full_text
    except Exception as e:
        logger.error(f"PaddleOCR PDF failed: {e}")
        raise RuntimeError(f"PaddleOCR PDF OCR failed: {e}") from e


# ──────────────────────────────────────────────
# Unified OCR Interface
# ──────────────────────────────────────────────
def perform_ocr(
    file_path: Path,
    engine: str = "tesseract",
    language: str = "eng",
    dpi: int = 300,
) -> str:
    """
    Unified OCR interface supporting both engines and file types.

    Args:
        file_path: Path to PDF or image file.
        engine: 'tesseract' or 'paddle'.
        language: Language code (engine-appropriate).
        dpi: DPI for PDF rendering.

    Returns:
        Extracted text.
    """
    is_pdf = file_path.suffix.lower() == ".pdf"

    if engine == "paddle":
        if is_pdf:
            return ocr_pdf_paddle(file_path, language=language, dpi=dpi)
        else:
            return ocr_image_paddle(file_path, language=language)
    else:
        if is_pdf:
            return ocr_pdf_tesseract(file_path, language=language, dpi=dpi)
        else:
            return ocr_image_tesseract(file_path, language=language)
