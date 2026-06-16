"""
Temporary file management for the PDF Toolkit.
Handles saving uploads, generating unique filenames, and auto-cleanup.
"""

import time
import uuid
from pathlib import Path

from config import TEMP_DIR, TEMP_FILE_TTL_HOURS
from utils.logger import get_logger

logger = get_logger("file_manager")


def save_uploaded_file(uploaded_file) -> Path:
    """
    Save an uploaded file (supports Streamlit UploadedFile and FastAPI UploadFile)
    to the temp directory with a unique name.

    Args:
        uploaded_file: Uploaded file object.

    Returns:
        Path to the saved file.
    """
    unique_id = uuid.uuid4().hex[:8]
    if hasattr(uploaded_file, "filename") and uploaded_file.filename:
        name = uploaded_file.filename
    elif hasattr(uploaded_file, "name") and uploaded_file.name:
        name = uploaded_file.name
    else:
        name = "uploaded_file"
        
    safe_name = sanitize_filename(name)
    file_path = TEMP_DIR / f"{unique_id}_{safe_name}"

    if hasattr(uploaded_file, "getbuffer"):
        file_path.write_bytes(uploaded_file.getbuffer())
    elif hasattr(uploaded_file, "file"):
        uploaded_file.file.seek(0)
        file_path.write_bytes(uploaded_file.file.read())
    elif hasattr(uploaded_file, "read"):
        uploaded_file.seek(0)
        file_path.write_bytes(uploaded_file.read())
    else:
        raise ValueError("Unsupported uploaded file object type")

    logger.info(f"Saved uploaded file: {file_path.name} ({file_path.stat().st_size} bytes)")
    return file_path



def save_bytes(data: bytes, filename: str) -> Path:
    """
    Save raw bytes to a file in the temp directory.

    Args:
        data: Raw byte data.
        filename: Desired filename.

    Returns:
        Path to the saved file.
    """
    unique_id = uuid.uuid4().hex[:8]
    safe_name = sanitize_filename(filename)
    file_path = TEMP_DIR / f"{unique_id}_{safe_name}"

    file_path.write_bytes(data)
    logger.info(f"Saved bytes to: {file_path.name} ({len(data)} bytes)")
    return file_path


def get_temp_path(filename: str) -> Path:
    """
    Generate a unique temp file path without creating the file.

    Args:
        filename: Desired filename.

    Returns:
        Unique Path in temp directory.
    """
    unique_id = uuid.uuid4().hex[:8]
    safe_name = sanitize_filename(filename)
    return TEMP_DIR / f"{unique_id}_{safe_name}"


def sanitize_filename(filename: str) -> str:
    """
    Remove or replace unsafe characters in a filename.

    Args:
        filename: Original filename.

    Returns:
        Sanitized filename string.
    """
    # Keep only safe characters
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    sanitized = "".join(c if c in safe_chars else "_" for c in filename)
    # Remove leading dots/underscores
    sanitized = sanitized.lstrip("._")
    return sanitized or "unnamed_file"


def cleanup_temp_files() -> int:
    """
    Remove temp files older than TEMP_FILE_TTL_HOURS.

    Returns:
        Number of files removed.
    """
    if not TEMP_DIR.exists():
        return 0

    cutoff = time.time() - (TEMP_FILE_TTL_HOURS * 3600)
    removed = 0

    for file_path in TEMP_DIR.iterdir():
        if file_path.is_file() and file_path.stat().st_mtime < cutoff:
            try:
                file_path.unlink()
                removed += 1
                logger.debug(f"Cleaned up temp file: {file_path.name}")
            except OSError as e:
                logger.warning(f"Failed to remove {file_path.name}: {e}")

    if removed:
        logger.info(f"Cleaned up {removed} expired temp file(s)")
    return removed


def list_recent_files(limit: int = 10) -> list[dict]:
    """
    List recently created files in the temp directory.

    Args:
        limit: Maximum number of files to return.

    Returns:
        List of dicts with file info, sorted newest first.
    """
    if not TEMP_DIR.exists():
        return []

    files = []
    for file_path in TEMP_DIR.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "path": file_path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })

    files.sort(key=lambda f: f["modified"], reverse=True)
    return files[:limit]


def get_original_filename(path: Path | str) -> str:
    """
    Extract the original filename from a unique temp path.
    Removes the 8-character hex prefix and underscore if present.
    Also replaces intermediate dots with underscores to prevent Chrome extension spoofing warnings.
    """
    path_obj = Path(path)
    name = path_obj.name
    # Check if name starts with an 8-char hex followed by '_'
    if len(name) > 9 and name[8] == '_':
        try:
            int(name[:8], 16)  # Check if hex
            name = name[9:]
        except ValueError:
            pass

    # Replace intermediate dots with underscores (keep only the final extension dot)
    parts = name.split(".")
    if len(parts) > 2:
        name = "_".join(parts[:-1]) + "." + parts[-1]

    return name

