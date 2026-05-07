import base64
import os
import uuid
from pathlib import Path
from typing import Optional

import cv2

# Vercel serverless has a read-only filesystem; only /tmp is writable
if os.environ.get("VERCEL"):
    UPLOAD_DIR = Path("/tmp/uploads")
    OUTPUT_DIR = Path("/tmp/output")
else:
    UPLOAD_DIR = Path("uploads")
    OUTPUT_DIR = Path("output")

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/bmp",
    "image/webp",
}

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def ensure_directories():
    """Create upload and output directories if they don't exist."""
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)


def validate_upload(content_type: str, size: int) -> Optional[str]:
    """Validate uploaded file type and size.

    Returns an error message string on failure, or None if valid.
    """
    if content_type not in ALLOWED_CONTENT_TYPES:
        return f"Unsupported file type: {content_type}. Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
    if size > MAX_UPLOAD_SIZE:
        return f"File too large: {size} bytes. Maximum: {MAX_UPLOAD_SIZE} bytes."
    return None


def save_upload(file_bytes: bytes, original_filename: str) -> Path:
    """Save an uploaded file to the uploads directory with a UUID-based name.

    Returns the absolute path to the saved file.
    """
    ext = os.path.splitext(original_filename)[1].lower() or ".jpg"
    safe_name = f"{uuid.uuid4()}{ext}"
    dest = UPLOAD_DIR / safe_name
    dest.write_bytes(file_bytes)
    return dest.resolve()


def cleanup(*paths):
    """Delete files at the given paths. Silently ignores missing files."""
    for p in paths:
        if p and os.path.exists(str(p)):
            os.remove(str(p))


def image_to_base64(image_path) -> Optional[str]:
    """Encode an image file as a base64 data URI string.

    Returns None if the file does not exist or cannot be read.
    """
    if not image_path or not os.path.exists(str(image_path)):
        return None
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"
