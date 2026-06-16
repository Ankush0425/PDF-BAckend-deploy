"""
Application configuration and constants for the AI-Powered PDF Toolkit.
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# Application Metadata
# ──────────────────────────────────────────────
APP_NAME = "PDF Toolkit AI"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-Powered PDF Toolkit — Merge, Split, Convert, OCR, Chat & Analyze"
APP_ICON = "📄"

# ──────────────────────────────────────────────
# Directory Paths
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Create directories on import
TEMP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────
# File Constraints
# ──────────────────────────────────────────────
MAX_FILE_SIZE_MB = 200
TEMP_FILE_TTL_HOURS = 2  # Auto-cleanup after 2 hours

SUPPORTED_PDF_TYPES = ["application/pdf"]
SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/tiff", "image/bmp"]
SUPPORTED_DOC_TYPES = [
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
]
SUPPORTED_EXCEL_TYPES = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
]

# ──────────────────────────────────────────────
# AI Configuration
# ──────────────────────────────────────────────
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
OLLAMA_DEFAULT_MODEL = "llama3.2"
OLLAMA_BASE_URL = "http://localhost:11434"

GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"
GROQ_DEFAULT_API_KEY = os.environ.get("GROQ_API_KEY", "")

AI_MAX_CONTEXT_LENGTH = 12000  # Characters to send to AI
AI_CHUNK_SIZE = 3000  # Characters per chunk for long documents
AI_CHUNK_OVERLAP = 300  # Overlap between chunks

# Configure local Tesseract if available
LOCAL_TESSERACT = BASE_DIR / "bin" / "tesseract"
if LOCAL_TESSERACT.exists():
    os.environ["TESSDATA_PREFIX"] = str(BASE_DIR / "bin")
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = str(LOCAL_TESSERACT)
    except ImportError:
        pass

# Configure local Ollama if available
LOCAL_OLLAMA = BASE_DIR / "bin" / "ollama"
LOCAL_OLLAMA_MODELS = BASE_DIR / "bin" / "models"
if LOCAL_OLLAMA.exists():
    try:
        LOCAL_OLLAMA_MODELS.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# ──────────────────────────────────────────────
# OCR Configuration
# ──────────────────────────────────────────────
OCR_LANGUAGES = {
    "English": "eng",
    "Hindi": "hin",
    "Spanish": "spa",
    "French": "fra",
    "German": "deu",
    "Chinese (Simplified)": "chi_sim",
    "Chinese (Traditional)": "chi_tra",
    "Japanese": "jpn",
    "Korean": "kor",
    "Arabic": "ara",
    "Portuguese": "por",
    "Russian": "rus",
    "Italian": "ita",
}

PADDLE_OCR_LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Chinese": "ch",
    "Japanese": "japan",
    "Korean": "korean",
    "French": "fr",
    "German": "german",
    "Arabic": "ar",
    "Spanish": "es",
    "Portuguese": "pt",
    "Russian": "ru",
    "Italian": "it",
}

# ──────────────────────────────────────────────
# PDF Operations Defaults
# ──────────────────────────────────────────────
DEFAULT_DPI = 150
COMPRESS_DPI = 100
WATERMARK_OPACITY = 0.3
WATERMARK_FONT_SIZE = 48
PAGE_NUMBER_FONT_SIZE = 10


