"""
Shared utility/helper functions for the PDF Toolkit.
"""

import math
from pathlib import Path

import fitz  # PyMuPDF

from utils.logger import get_logger

logger = get_logger("helpers")


def format_file_size(size_bytes: int) -> str:
    """
    Convert bytes to a human-readable string.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Formatted string like '2.4 MB'.
    """
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    i = min(i, len(units) - 1)
    value = size_bytes / (1024 ** i)
    return f"{value:.1f} {units[i]}"


def get_pdf_page_count(pdf_path: Path | str) -> int:
    """
    Get the number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Number of pages.
    """
    try:
        doc = fitz.open(str(pdf_path))
        count = len(doc)
        doc.close()
        return count
    except Exception as e:
        logger.error(f"Failed to get page count for {pdf_path}: {e}")
        return 0


def get_pdf_metadata(pdf_path: Path | str) -> dict:
    """
    Extract metadata from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Dictionary of metadata fields.
    """
    try:
        doc = fitz.open(str(pdf_path))
        metadata = doc.metadata or {}
        info = {
            "title": metadata.get("title", "Unknown"),
            "author": metadata.get("author", "Unknown"),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "page_count": len(doc),
            "file_size": Path(pdf_path).stat().st_size,
            "file_size_formatted": format_file_size(Path(pdf_path).stat().st_size),
        }
        doc.close()
        return info
    except Exception as e:
        logger.error(f"Failed to get metadata for {pdf_path}: {e}")
        return {}


def extract_text_from_pdf(pdf_path: Path | str, max_pages: int | None = None) -> str:
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum number of pages to extract (None = all).

    Returns:
        Extracted text as a string.
    """
    try:
        doc = fitz.open(str(pdf_path))
        pages_to_read = min(len(doc), max_pages) if max_pages else len(doc)
        text_parts = []

        for i in range(pages_to_read):
            page = doc[i]
            text_parts.append(page.get_text())

        doc.close()
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""


def render_pdf_page_as_image(pdf_path: Path | str, page_number: int = 0, dpi: int = 150) -> bytes | None:
    """
    Render a single PDF page as a PNG image.

    Args:
        pdf_path: Path to the PDF file.
        page_number: Zero-indexed page number.
        dpi: Resolution in DPI.

    Returns:
        PNG image bytes or None on failure.
    """
    try:
        doc = fitz.open(str(pdf_path))
        if page_number >= len(doc):
            doc.close()
            return None

        page = doc[page_number]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        doc.close()
        return img_bytes
    except Exception as e:
        logger.error(f"Failed to render page {page_number} from {pdf_path}: {e}")
        return None


def get_mime_type(filename: str) -> str:
    """
    Detect MIME type from filename extension.

    Args:
        filename: Filename with extension.

    Returns:
        MIME type string.
    """
    ext_map = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".bmp": "image/bmp",
        ".txt": "text/plain",
    }
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext, "application/octet-stream")
