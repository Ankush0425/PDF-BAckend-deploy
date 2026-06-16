import json
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel

from utils.file_manager import save_uploaded_file, get_temp_path
from core import ai_features, document_analysis, ocr_engine

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

@router.post("/chat")
async def chat_with_pdf(
    file: UploadFile = File(...),
    question: str = Form(...),
    history: Optional[str] = Form("[]"), # JSON string of ChatMessage list
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        try:
            parsed_history = json.loads(history)
        except Exception:
            parsed_history = []
        
        result = ai_features.chat_with_pdf(
            pdf_path=saved_path,
            question=question,
            chat_history=parsed_history,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/summarize")
async def summarize_pdf(
    file: UploadFile = File(...),
    style: str = Form("detailed"), # "concise", "detailed", "bullets", "executive"
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        result = ai_features.summarize_pdf(
            pdf_path=saved_path,
            style=style,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/explain")
async def explain_pdf(
    file: UploadFile = File(...),
    complexity: str = Form("moderate"), # "simple", "moderate", "detailed"
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        result = ai_features.explain_pdf(
            pdf_path=saved_path,
            complexity=complexity,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/notes")
async def generate_notes(
    file: UploadFile = File(...),
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        result = ai_features.generate_notes(
            pdf_path=saved_path,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/questions")
async def generate_questions(
    file: UploadFile = File(...),
    count: int = Form(5),
    difficulty: str = Form("medium"), # "easy", "medium", "hard"
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        result = ai_features.generate_questions(
            pdf_path=saved_path,
            num_questions=count,
            difficulty=difficulty,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/translate")
async def translate_pdf(
    file: UploadFile = File(...),
    language: str = Form(...),
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        result = ai_features.translate_pdf(
            pdf_path=saved_path,
            target_language=language,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/ocr")
async def perform_ocr(
    file: UploadFile = File(...),
    engine: str = Form("tesseract"), # "tesseract" or "paddle"
    language: str = Form("eng"),
    dpi: int = Form(300)
):
    saved_path = save_uploaded_file(file)
    try:
        result = ocr_engine.perform_ocr(
            file_path=saved_path,
            engine=engine,
            language=language,
            dpi=dpi
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

# Specialized Document Analysis
@router.post("/analyze/resume")
async def analyze_resume(
    file: UploadFile = File(...),
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        result = document_analysis.analyze_resume(
            pdf_path=saved_path,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/analyze/invoice")
async def analyze_invoice(
    file: UploadFile = File(...),
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        result = document_analysis.analyze_invoice(
            pdf_path=saved_path,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/analyze/contract")
async def analyze_contract(
    file: UploadFile = File(...),
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        result = document_analysis.analyze_contract(
            pdf_path=saved_path,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/analyze/paper")
async def analyze_paper(
    file: UploadFile = File(...),
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    saved_path = save_uploaded_file(file)
    try:
        result = document_analysis.analyze_research_paper(
            pdf_path=saved_path,
            backend=backend,
            api_key=api_key or "",
            model=model or ""
        )
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if saved_path.exists():
            try: saved_path.unlink()
            except: pass

@router.post("/generate-pdf")
async def generate_pdf(
    prompt: str = Form(...),
    doc_type: str = Form("generic"), # "resume", "invoice", "proposal", "checklist", "story", "generic"
    output_name: str = Form("generated_document.pdf"),
    backend: str = Form("groq"),
    api_key: Optional[str] = Form(""),
    model: Optional[str] = Form("")
):
    try:
        # Import conversion helper inline
        from core import conversion
        
        system_prompt = (
            f"You are a professional document generator. The user wants to generate a document of type: {doc_type}.\n"
            "Format the output text beautifully, with clear section headers, paragraphs, lists, and tables if needed.\n"
            "Generate ONLY the document text itself. Do not include markdown block ticks, code indicators, or intro/outro conversational remarks."
        )
        
        generated_text = ai_features._call_ai(prompt, system_prompt, backend, api_key or "", model or "")
        
        output_path = conversion.text_to_pdf(generated_text, output_name)
        
        return {
            "success": True,
            "filename": output_path.name,
            "download_url": f"/temp/{output_path.name}",
            "generated_text": generated_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
