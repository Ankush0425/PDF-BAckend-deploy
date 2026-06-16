"""
PDF Operations module — Merge, Split, Compress, Rotate, Extract, Delete,
Rearrange Pages, Add/Remove Watermark, Add Page Numbers.
"""

import io
from pathlib import Path

import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

from config import COMPRESS_DPI, WATERMARK_OPACITY, WATERMARK_FONT_SIZE, PAGE_NUMBER_FONT_SIZE
from utils.file_manager import get_temp_path
from utils.logger import get_logger

logger = get_logger("pdf_operations")


# ──────────────────────────────────────────────
# Merge PDFs
# ──────────────────────────────────────────────
def merge_pdfs(pdf_paths: list[Path], output_name: str = "merged.pdf") -> Path:
    """
    Merge multiple PDFs into a single file.

    Args:
        pdf_paths: List of paths to PDF files (in order).
        output_name: Name for the merged output file.

    Returns:
        Path to the merged PDF.
    """
    output_path = get_temp_path(output_name)
    merger = PdfWriter()

    try:
        for pdf_path in pdf_paths:
            merger.append(str(pdf_path))
            logger.debug(f"Added to merge: {pdf_path.name}")

        with open(output_path, "wb") as f:
            merger.write(f)
        merger.close()
        logger.info(f"Merged {len(pdf_paths)} PDFs → {output_path.name}")
        return output_path
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise RuntimeError(f"Failed to merge PDFs: {e}") from e


# ──────────────────────────────────────────────
# Split PDF
# ──────────────────────────────────────────────
def split_pdf_by_pages(pdf_path: Path, page_ranges: list[tuple[int, int]], output_prefix: str = "split") -> list[Path]:
    """
    Split a PDF into multiple files by page ranges.

    Args:
        pdf_path: Path to the source PDF.
        page_ranges: List of (start, end) tuples (1-indexed, inclusive).
        output_prefix: Prefix for output filenames.

    Returns:
        List of paths to the split PDF files.
    """
    reader = PdfReader(str(pdf_path))
    output_paths = []

    try:
        for i, (start, end) in enumerate(page_ranges):
            writer = PdfWriter()
            for page_num in range(start - 1, min(end, len(reader.pages))):
                writer.add_page(reader.pages[page_num])

            out_path = get_temp_path(f"{output_prefix}_pages_{start}-{end}.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
            output_paths.append(out_path)
            logger.debug(f"Split pages {start}-{end} → {out_path.name}")

        logger.info(f"Split PDF into {len(output_paths)} parts")
        return output_paths
    except Exception as e:
        logger.error(f"Split failed: {e}")
        raise RuntimeError(f"Failed to split PDF: {e}") from e


def split_pdf_every_n_pages(pdf_path: Path, n: int = 1) -> list[Path]:
    """
    Split a PDF into chunks of N pages each.

    Args:
        pdf_path: Path to the source PDF.
        n: Number of pages per chunk.

    Returns:
        List of paths to the split PDF files.
    """
    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    ranges = []

    for start in range(0, total_pages, n):
        end = min(start + n, total_pages)
        ranges.append((start + 1, end))

    return split_pdf_by_pages(pdf_path, ranges, output_prefix="chunk")


# ──────────────────────────────────────────────
# Compress PDF
# ──────────────────────────────────────────────
def compress_pdf(pdf_path: Path, quality: int = 80, dpi: int = COMPRESS_DPI) -> Path:
    """
    Compress a PDF by re-rendering pages at lower quality.

    Args:
        pdf_path: Path to the source PDF.
        quality: Image quality (1-100).
        dpi: Target DPI for images.

    Returns:
        Path to the compressed PDF.
    """
    output_path = get_temp_path("compressed.pdf")

    try:
        doc = fitz.open(str(pdf_path))
        new_doc = fitz.open()

        for page in doc:
            # Re-render page as image and add to new doc
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Create new page with same dimensions
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)

            # Convert pixmap to JPEG bytes for compression
            img_bytes = pix.tobytes("jpeg")

            # Insert compressed image into new page
            new_page.insert_image(new_page.rect, stream=img_bytes)

        new_doc.save(str(output_path), garbage=4, deflate=True, clean=True)
        new_doc.close()
        doc.close()

        original_size = pdf_path.stat().st_size
        compressed_size = output_path.stat().st_size
        ratio = (1 - compressed_size / original_size) * 100
        logger.info(f"Compressed PDF: {ratio:.1f}% reduction ({original_size} → {compressed_size} bytes)")
        return output_path
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        raise RuntimeError(f"Failed to compress PDF: {e}") from e


# ──────────────────────────────────────────────
# Rotate PDF
# ──────────────────────────────────────────────
def rotate_pdf(pdf_path: Path, rotation: int = 90, pages: list[int] | None = None) -> Path:
    """
    Rotate pages of a PDF.

    Args:
        pdf_path: Path to the source PDF.
        rotation: Degrees to rotate (90, 180, 270).
        pages: List of page numbers (1-indexed) to rotate. None = all pages.

    Returns:
        Path to the rotated PDF.
    """
    output_path = get_temp_path("rotated.pdf")
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    try:
        for i, page in enumerate(reader.pages):
            if pages is None or (i + 1) in pages:
                page.rotate(rotation)
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        pages_desc = "all" if pages is None else str(pages)
        logger.info(f"Rotated pages {pages_desc} by {rotation}°")
        return output_path
    except Exception as e:
        logger.error(f"Rotation failed: {e}")
        raise RuntimeError(f"Failed to rotate PDF: {e}") from e


# ──────────────────────────────────────────────
# Extract Pages
# ──────────────────────────────────────────────
def extract_pages(pdf_path: Path, page_numbers: list[int]) -> Path:
    """
    Extract specific pages from a PDF.

    Args:
        pdf_path: Path to the source PDF.
        page_numbers: List of page numbers to extract (1-indexed).

    Returns:
        Path to the new PDF with extracted pages.
    """
    output_path = get_temp_path("extracted_pages.pdf")
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    try:
        for page_num in page_numbers:
            if 1 <= page_num <= len(reader.pages):
                writer.add_page(reader.pages[page_num - 1])

        with open(output_path, "wb") as f:
            writer.write(f)

        logger.info(f"Extracted {len(page_numbers)} pages")
        return output_path
    except Exception as e:
        logger.error(f"Page extraction failed: {e}")
        raise RuntimeError(f"Failed to extract pages: {e}") from e


# ──────────────────────────────────────────────
# Delete Pages
# ──────────────────────────────────────────────
def delete_pages(pdf_path: Path, page_numbers: list[int]) -> Path:
    """
    Delete specific pages from a PDF.

    Args:
        pdf_path: Path to the source PDF.
        page_numbers: List of page numbers to delete (1-indexed).

    Returns:
        Path to the new PDF with pages removed.
    """
    output_path = get_temp_path("pages_deleted.pdf")
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    pages_to_delete = set(page_numbers)

    try:
        for i, page in enumerate(reader.pages):
            if (i + 1) not in pages_to_delete:
                writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        logger.info(f"Deleted {len(pages_to_delete)} pages")
        return output_path
    except Exception as e:
        logger.error(f"Page deletion failed: {e}")
        raise RuntimeError(f"Failed to delete pages: {e}") from e


# ──────────────────────────────────────────────
# Rearrange Pages
# ──────────────────────────────────────────────
def rearrange_pages(pdf_path: Path, new_order: list[int]) -> Path:
    """
    Rearrange pages in a PDF according to the specified order.

    Args:
        pdf_path: Path to the source PDF.
        new_order: List of page numbers (1-indexed) in desired order.

    Returns:
        Path to the rearranged PDF.
    """
    output_path = get_temp_path("rearranged.pdf")
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    try:
        for page_num in new_order:
            if 1 <= page_num <= len(reader.pages):
                writer.add_page(reader.pages[page_num - 1])

        with open(output_path, "wb") as f:
            writer.write(f)

        logger.info(f"Rearranged {len(new_order)} pages")
        return output_path
    except Exception as e:
        logger.error(f"Rearrange failed: {e}")
        raise RuntimeError(f"Failed to rearrange pages: {e}") from e


# ──────────────────────────────────────────────
# Add Watermark
# ──────────────────────────────────────────────
def add_text_watermark(
    pdf_path: Path,
    watermark_text: str = "CONFIDENTIAL",
    opacity: float = WATERMARK_OPACITY,
    font_size: int = WATERMARK_FONT_SIZE,
    rotation: int = 45,
    color: tuple = (0.5, 0.5, 0.5),
) -> Path:
    """
    Add a text watermark to all pages of a PDF.

    Args:
        pdf_path: Path to the source PDF.
        watermark_text: Text for the watermark.
        opacity: Watermark opacity (0.0 - 1.0).
        font_size: Font size for the watermark text.
        rotation: Rotation angle for the watermark.
        color: RGB color tuple (0-1 range).

    Returns:
        Path to the watermarked PDF.
    """
    output_path = get_temp_path("watermarked.pdf")

    try:
        doc = fitz.open(str(pdf_path))

        for page in doc:
            rect = page.rect
            # Create text with rotation at center of page
            text_length = fitz.get_text_length(watermark_text, fontsize=font_size)
            x = (rect.width - text_length) / 2
            y = rect.height / 2

            # Insert watermark text
            tw = fitz.TextWriter(page.rect)
            tw.append(
                pos=(x, y),
                text=watermark_text,
                fontsize=font_size,
            )
            tw.write_text(
                page,
                opacity=opacity,
                color=color,
                morph=(fitz.Point(x, y), fitz.Matrix(rotation))
            )

        doc.save(str(output_path))
        doc.close()

        logger.info(f"Added watermark '{watermark_text}' to all pages")
        return output_path
    except Exception as e:
        logger.error(f"Watermark addition failed: {e}")
        raise RuntimeError(f"Failed to add watermark: {e}") from e


# ──────────────────────────────────────────────
# Remove Watermark (Best-effort)
# ──────────────────────────────────────────────
def remove_watermark(pdf_path: Path, watermark_text: str = "") -> Path:
    """
    Attempt to remove text watermarks from a PDF (best-effort).

    Works by searching for and removing text matching the watermark pattern.
    May not work for image-based or complex watermarks.

    Args:
        pdf_path: Path to the source PDF.
        watermark_text: Known watermark text to search for. If empty, tries common patterns.

    Returns:
        Path to the cleaned PDF.
    """
    output_path = get_temp_path("watermark_removed.pdf")
    common_watermarks = ["CONFIDENTIAL", "DRAFT", "SAMPLE", "COPY", "WATERMARK"]

    try:
        doc = fitz.open(str(pdf_path))

        search_terms = [watermark_text] if watermark_text else common_watermarks

        for page in doc:
            for term in search_terms:
                if not term:
                    continue
                areas = page.search_for(term)
                for area in areas:
                    # Redact (white-out) the watermark area
                    page.add_redact_annot(area)
            page.apply_redactions()

        doc.save(str(output_path))
        doc.close()

        logger.info("Attempted watermark removal")
        return output_path
    except Exception as e:
        logger.error(f"Watermark removal failed: {e}")
        raise RuntimeError(f"Failed to remove watermark: {e}") from e


# ──────────────────────────────────────────────
# Add Page Numbers
# ──────────────────────────────────────────────
def add_page_numbers(
    pdf_path: Path,
    position: str = "bottom-center",
    start_number: int = 1,
    font_size: int = PAGE_NUMBER_FONT_SIZE,
    format_str: str = "Page {n} of {total}",
) -> Path:
    """
    Add page numbers to a PDF.

    Args:
        pdf_path: Path to the source PDF.
        position: Position of page numbers ('bottom-center', 'bottom-right', 'bottom-left',
                  'top-center', 'top-right', 'top-left').
        start_number: Starting page number.
        font_size: Font size for page numbers.
        format_str: Format string with {n} and {total} placeholders.

    Returns:
        Path to the numbered PDF.
    """
    output_path = get_temp_path("page_numbered.pdf")

    try:
        doc = fitz.open(str(pdf_path))
        total = len(doc)

        for i, page in enumerate(doc):
            rect = page.rect
            page_num = start_number + i
            text = format_str.format(n=page_num, total=total)

            # Calculate position
            margin = 36  # 0.5 inch
            text_width = fitz.get_text_length(text, fontsize=font_size)

            positions = {
                "bottom-center": ((rect.width - text_width) / 2, rect.height - margin),
                "bottom-right": (rect.width - text_width - margin, rect.height - margin),
                "bottom-left": (margin, rect.height - margin),
                "top-center": ((rect.width - text_width) / 2, margin + font_size),
                "top-right": (rect.width - text_width - margin, margin + font_size),
                "top-left": (margin, margin + font_size),
            }

            x, y = positions.get(position, positions["bottom-center"])

            tw = fitz.TextWriter(page.rect)
            tw.append(pos=(x, y), text=text, fontsize=font_size)
            tw.write_text(page, color=(0.3, 0.3, 0.3))

        doc.save(str(output_path))
        doc.close()

        logger.info(f"Added page numbers (position={position})")
        return output_path
    except Exception as e:
        logger.error(f"Page numbering failed: {e}")
        raise RuntimeError(f"Failed to add page numbers: {e}") from e
