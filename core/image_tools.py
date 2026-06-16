"""
Image Tools — Convert JPG/PNG/WEBP to PDF, merge multiple images into single PDF.
"""

from pathlib import Path

from PIL import Image

from utils.file_manager import get_temp_path
from utils.logger import get_logger

logger = get_logger("image_tools")


def single_image_to_pdf(image_path: Path, page_size: str = "A4") -> Path:
    """
    Convert a single image to a PDF, fitting it to the specified page size.

    Args:
        image_path: Path to the image file.
        page_size: Page size ('A4', 'Letter', 'Original').

    Returns:
        Path to the output PDF.
    """
    output_path = get_temp_path(f"{image_path.stem}.pdf")

    try:
        img = Image.open(str(image_path))
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        page_sizes = {
            "A4": (595, 842),  # 72 DPI
            "Letter": (612, 792),
            "Original": img.size,
        }

        target_w, target_h = page_sizes.get(page_size, page_sizes["A4"])

        if page_size != "Original":
            # Scale image to fit page while maintaining aspect ratio
            img_ratio = img.width / img.height
            page_ratio = target_w / target_h

            if img_ratio > page_ratio:
                new_w = int(target_w * 0.9)  # 90% of page width (margins)
                new_h = int(new_w / img_ratio)
            else:
                new_h = int(target_h * 0.9)
                new_w = int(new_h * img_ratio)

            img = img.resize((new_w, new_h), Image.LANCZOS)

            # Create white page and paste image centered
            page = Image.new('RGB', (int(target_w), int(target_h)), (255, 255, 255))
            x = (int(target_w) - new_w) // 2
            y = (int(target_h) - new_h) // 2
            page.paste(img, (x, y))
            img = page

        img.save(str(output_path), "PDF", resolution=150)
        logger.info(f"Converted {image_path.name} to PDF")
        return output_path
    except Exception as e:
        logger.error(f"Image to PDF failed: {e}")
        raise RuntimeError(f"Failed to convert image to PDF: {e}") from e


def multiple_images_to_pdf(image_paths: list[Path], page_size: str = "A4") -> Path:
    """
    Merge multiple images into a single PDF (one image per page).

    Args:
        image_paths: List of paths to image files.
        page_size: Page size for all pages.

    Returns:
        Path to the merged PDF.
    """
    output_path = get_temp_path("images_merged.pdf")

    try:
        page_sizes = {
            "A4": (595, 842),
            "Letter": (612, 792),
        }
        target_w, target_h = page_sizes.get(page_size, page_sizes["A4"])

        pdf_pages = []
        for img_path in image_paths:
            img = Image.open(str(img_path))
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Scale and center
            img_ratio = img.width / img.height
            page_ratio = target_w / target_h

            if img_ratio > page_ratio:
                new_w = int(target_w * 0.9)
                new_h = int(new_w / img_ratio)
            else:
                new_h = int(target_h * 0.9)
                new_w = int(new_h * img_ratio)

            img = img.resize((new_w, new_h), Image.LANCZOS)

            page = Image.new('RGB', (int(target_w), int(target_h)), (255, 255, 255))
            x = (int(target_w) - new_w) // 2
            y = (int(target_h) - new_h) // 2
            page.paste(img, (x, y))
            pdf_pages.append(page)

        if pdf_pages:
            pdf_pages[0].save(
                str(output_path), "PDF", resolution=150,
                save_all=True, append_images=pdf_pages[1:]
            )

        logger.info(f"Merged {len(image_paths)} images into PDF")
        return output_path
    except Exception as e:
        logger.error(f"Multiple images to PDF failed: {e}")
        raise RuntimeError(f"Failed to merge images to PDF: {e}") from e


def get_image_info(image_path: Path) -> dict:
    """Get image metadata."""
    try:
        img = Image.open(str(image_path))
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "size": image_path.stat().st_size,
        }
    except Exception as e:
        logger.error(f"Failed to get image info: {e}")
        return {}
