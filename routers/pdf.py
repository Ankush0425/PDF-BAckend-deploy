import shutil
import zipfile
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

from utils.file_manager import save_uploaded_file, get_temp_path, get_original_filename
from core import pdf_operations

router = APIRouter()

def get_download_url(file_path: Path) -> str:
    """Helper to convert local file path to relative HTTP download URL."""
    return f"/temp/{file_path.name}"

@router.post("/merge")
async def merge_pdfs(
    files: List[UploadFile] = File(...),
    output_name: str = Form("merged.pdf")
):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload at least 2 files to merge")
    
    saved_paths = []
    try:
        for file in files:
            path = save_uploaded_file(file)
            saved_paths.append(path)
            
        merged_path = pdf_operations.merge_pdfs(saved_paths, output_name)
        return {
            "success": True,
            "filename": get_original_filename(merged_path),
            "download_url": get_download_url(merged_path),
            "size": merged_path.stat().st_size
        }
    finally:
        # Clean up temporary uploaded files (but keep the merged result)
        for path in saved_paths:
            if path.exists():
                try: path.unlink()
                except: pass

@router.post("/split")
async def split_pdf(
    file: UploadFile = File(...),
    split_type: str = Form("range"), # "range" or "every_n"
    ranges: Optional[str] = Form(None), # e.g. "1-3,4-5"
    n_pages: Optional[int] = Form(1)
):
    saved_path = save_uploaded_file(file)
    try:
        if split_type == "range":
            if not ranges:
                raise HTTPException(status_code=400, detail="Ranges string is required for range split")
            # Parse ranges like "1-3, 4-5"
            parsed_ranges = []
            for item in ranges.split(","):
                item = item.strip()
                if "-" in item:
                    start, end = map(int, item.split("-"))
                    parsed_ranges.append((start, end))
                else:
                    val = int(item)
                    parsed_ranges.append((val, val))
            split_paths = pdf_operations.split_pdf_by_pages(saved_path, parsed_ranges)
        else:
            split_paths = pdf_operations.split_pdf_every_n_pages(saved_path, n_pages)

        # If multiple files are generated, create a zip file
        if len(split_paths) > 1:
            zip_path = get_temp_path("split_files.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for path in split_paths:
                    zipf.write(path, arcname=path.name)
            return {
                "success": True,
                "filename": zip_path.name,
                "download_url": get_download_url(zip_path),
                "is_zip": True,
                "files": [get_original_filename(p) for p in split_paths]
            }
        elif len(split_paths) == 1:
            return {
                "success": True,
                "filename": get_original_filename(split_paths[0]),
                "download_url": get_download_url(split_paths[0]),
                "is_zip": False
            }
        else:
            raise HTTPException(status_code=500, detail="No split files generated")
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/compress")
async def compress_pdf(
    file: UploadFile = File(...),
    quality: int = Form(80),
    dpi: int = Form(150)
):
    saved_path = save_uploaded_file(file)
    try:
        compressed_path = pdf_operations.compress_pdf(saved_path, quality, dpi)
        return {
            "success": True,
            "filename": get_original_filename(compressed_path),
            "download_url": get_download_url(compressed_path),
            "original_size": saved_path.stat().st_size,
            "compressed_size": compressed_path.stat().st_size
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/rotate")
async def rotate_pdf(
    file: UploadFile = File(...),
    rotation: int = Form(90),
    pages: Optional[str] = Form(None) # e.g. "1,3,5"
):
    saved_path = save_uploaded_file(file)
    try:
        parsed_pages = None
        if pages:
            parsed_pages = list(map(int, pages.split(",")))
        rotated_path = pdf_operations.rotate_pdf(saved_path, rotation, parsed_pages)
        return {
            "success": True,
            "filename": get_original_filename(rotated_path),
            "download_url": get_download_url(rotated_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/extract-pages")
async def extract_pages(
    file: UploadFile = File(...),
    pages: str = Form(...) # e.g. "1,2,5"
):
    saved_path = save_uploaded_file(file)
    try:
        parsed_pages = list(map(int, pages.split(",")))
        result_path = pdf_operations.extract_pages(saved_path, parsed_pages)
        return {
            "success": True,
            "filename": get_original_filename(result_path),
            "download_url": get_download_url(result_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/delete-pages")
async def delete_pages(
    file: UploadFile = File(...),
    pages: str = Form(...) # e.g. "1,2,5"
):
    saved_path = save_uploaded_file(file)
    try:
        parsed_pages = list(map(int, pages.split(",")))
        result_path = pdf_operations.delete_pages(saved_path, parsed_pages)
        return {
            "success": True,
            "filename": get_original_filename(result_path),
            "download_url": get_download_url(result_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/rearrange-pages")
async def rearrange_pages(
    file: UploadFile = File(...),
    order: str = Form(...) # e.g. "3,2,1,4"
):
    saved_path = save_uploaded_file(file)
    try:
        parsed_order = list(map(int, order.split(",")))
        result_path = pdf_operations.rearrange_pages(saved_path, parsed_order)
        return {
            "success": True,
            "filename": get_original_filename(result_path),
            "download_url": get_download_url(result_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/watermark")
async def add_watermark(
    file: UploadFile = File(...),
    text: str = Form("CONFIDENTIAL"),
    opacity: float = Form(0.15),
    font_size: int = Form(50),
    rotation: int = Form(45),
    color_rgb: str = Form("0.5,0.5,0.5") # Comma separated
):
    saved_path = save_uploaded_file(file)
    try:
        color_tuple = tuple(map(float, color_rgb.split(",")))
        result_path = pdf_operations.add_text_watermark(
            saved_path, text, opacity, font_size, rotation, color_tuple
        )
        return {
            "success": True,
            "filename": get_original_filename(result_path),
            "download_url": get_download_url(result_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/page-numbers")
async def add_page_numbers(
    file: UploadFile = File(...),
    position: str = Form("bottom-center"),
    start_number: int = Form(1),
    font_size: int = Form(10),
    format_str: str = Form("Page {n} of {total}")
):
    saved_path = save_uploaded_file(file)
    try:
        result_path = pdf_operations.add_page_numbers(
            saved_path, position, start_number, font_size, format_str
        )
        return {
            "success": True,
            "filename": get_original_filename(result_path),
            "download_url": get_download_url(result_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass
