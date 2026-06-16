import zipfile
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from utils.file_manager import save_uploaded_file, get_temp_path, get_original_filename
from core import conversion

router = APIRouter()

def get_download_url(file_path: Path) -> str:
    return f"/temp/{file_path.name}"

@router.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    saved_path = save_uploaded_file(file)
    try:
        output_path = conversion.pdf_to_word(saved_path)
        return {
            "success": True,
            "filename": get_original_filename(output_path),
            "download_url": get_download_url(output_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    saved_path = save_uploaded_file(file)
    try:
        output_path = conversion.word_to_pdf(saved_path)
        return {
            "success": True,
            "filename": get_original_filename(output_path),
            "download_url": get_download_url(output_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/pdf-to-images")
async def pdf_to_images(
    file: UploadFile = File(...),
    dpi: int = Form(150),
    fmt: str = Form("png")
):
    saved_path = save_uploaded_file(file)
    try:
        img_paths = conversion.pdf_to_images(saved_path, dpi, fmt)
        if len(img_paths) > 1:
            zip_path = get_temp_path("images.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for path in img_paths:
                    zipf.write(path, arcname=path.name)
            return {
                "success": True,
                "filename": zip_path.name,
                "download_url": get_download_url(zip_path),
                "is_zip": True
            }
        elif len(img_paths) == 1:
            return {
                "success": True,
                "filename": get_original_filename(img_paths[0]),
                "download_url": get_download_url(img_paths[0]),
                "is_zip": False
            }
        else:
            raise HTTPException(status_code=500, detail="No images generated")
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/image-to-pdf")
async def image_to_pdf(file: UploadFile = File(...)):
    saved_path = save_uploaded_file(file)
    try:
        output_path = conversion.image_to_pdf(saved_path)
        return {
            "success": True,
            "filename": get_original_filename(output_path),
            "download_url": get_download_url(output_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/pdf-to-text")
async def pdf_to_text(file: UploadFile = File(...)):
    saved_path = save_uploaded_file(file)
    try:
        output_path, text_content = conversion.pdf_to_text(saved_path)
        return {
            "success": True,
            "filename": get_original_filename(output_path),
            "download_url": get_download_url(output_path),
            "text": text_content
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/text-to-pdf")
async def text_to_pdf(
    text: str = Form(...),
    output_name: str = Form("from_text.pdf")
):
    try:
        output_path = conversion.text_to_pdf(text, output_name)
        return {
            "success": True,
            "filename": get_original_filename(output_path),
            "download_url": get_download_url(output_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/excel-to-pdf")
async def excel_to_pdf(file: UploadFile = File(...)):
    saved_path = save_uploaded_file(file)
    try:
        output_path = conversion.excel_to_pdf(saved_path)
        return {
            "success": True,
            "filename": get_original_filename(output_path),
            "download_url": get_download_url(output_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/pdf-to-excel")
async def pdf_to_excel(file: UploadFile = File(...)):
    saved_path = save_uploaded_file(file)
    try:
        output_path = conversion.pdf_to_excel(saved_path)
        return {
            "success": True,
            "filename": get_original_filename(output_path),
            "download_url": get_download_url(output_path)
        }
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass
