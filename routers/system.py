import os
import json
import subprocess
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel

from config import TEMP_DIR, LOCAL_OLLAMA, LOCAL_OLLAMA_MODELS, GROQ_DEFAULT_API_KEY
from core.ai_features import check_ollama_available, get_ollama_models
from core.ocr_engine import is_paddle_available
from utils.file_manager import list_recent_files

router = APIRouter()

SETTINGS_FILE = TEMP_DIR / "api_settings.json"

class SettingsModel(BaseModel):
    ai_backend: str = "groq"
    ai_model: str = "llama-3.3-70b-versatile"
    groq_api_key: str = GROQ_DEFAULT_API_KEY
    openai_api_key: str = ""

def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "ai_backend": "groq",
        "ai_model": "llama-3.3-70b-versatile",
        "groq_api_key": GROQ_DEFAULT_API_KEY,
        "openai_api_key": ""
    }

def save_settings_dict(settings: dict):
    TEMP_DIR.mkdir(exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

@router.get("/status")
async def get_status():
    ollama_ok = check_ollama_available()
    ollama_models = get_ollama_models() if ollama_ok else []
    
    tesseract_ok = False
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        tesseract_ok = True
    except Exception:
        pass

    paddle_ok = False
    try:
        paddle_ok = is_paddle_available()
    except Exception:
        pass

    recent_files = list_recent_files(100)
    
    return {
        "ollama": {
            "online": ollama_ok,
            "models": ollama_models
        },
        "tesseract": {
            "ready": tesseract_ok
        },
        "paddleocr": {
            "ready": paddle_ok
        },
        "temp_files_count": len(recent_files)
    }

@router.post("/pull-model")
async def pull_model(model_name: str = Form(...)):
    if not LOCAL_OLLAMA.exists():
        raise HTTPException(status_code=400, detail="Bundled Ollama binary not found")
    
    try:
        env = os.environ.copy()
        env["OLLAMA_MODELS"] = str(LOCAL_OLLAMA_MODELS)
        result = subprocess.run(
            [str(LOCAL_OLLAMA), "pull", model_name],
            env=env,
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode == 0:
            return {"success": True, "message": f"{model_name} pulled successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Ollama pull failed: {result.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_settings():
    return load_settings()

@router.post("/settings/update")
async def update_settings(settings: SettingsModel):
    save_settings_dict(settings.dict())
    return {"success": True, "settings": load_settings()}

@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...)
):
    # Authenticate 'ankush' user session
    if username == "ankush" and password == "ankush": # Or any specific password
        return {
            "success": True,
            "username": "ankush",
            "is_logged_in": True,
            "message": "Login successful"
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")
