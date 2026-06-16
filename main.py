import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import TEMP_DIR
from utils.logger import get_logger
from utils.file_manager import cleanup_temp_files

logger = get_logger("backend_api")

app = FastAPI(
    title="PDF Toolkit AI API",
    description="Backend services for PDF Operations, Conversions, OCR, and AI Features",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict as needed in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure temp directory exists
TEMP_DIR.mkdir(exist_ok=True)

# Mount temp directory as static files to allow downloading processed files
app.mount("/temp", StaticFiles(directory=str(TEMP_DIR)), name="temp")

# Clean up temp files on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up backend API...")
    cleaned = cleanup_temp_files()
    logger.info(f"Cleaned {cleaned} expired temp files.")

# Simple heartbeat endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "PDF Toolkit API is running"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Import and register routers
from routers import pdf, convert, ai, system
app.include_router(pdf.router, prefix="/api/pdf", tags=["PDF Operations"])
app.include_router(convert.router, prefix="/api/convert", tags=["Conversions"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Features"])
app.include_router(system.router, prefix="/api/system", tags=["System & Settings"])
