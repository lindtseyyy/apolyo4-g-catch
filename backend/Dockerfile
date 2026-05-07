# ---------- Base image ----------
FROM python:3.11-slim

# ---------- System dependencies ----------
# tesseract-ocr  → OCR engine required by pytesseract
# libgl1         → OpenCV headless still needs libGL on some slim images
# libglib2.0-0   → GLib required by OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ---------- Working directory ----------
WORKDIR /app

# ---------- Python dependencies (cached layer) ----------
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Application code ----------
COPY backend/ .

# ---------- Create writable dirs for uploads / output ----------
RUN mkdir -p /app/uploads /app/output

# ---------- Runtime ----------
# Railway injects PORT env var; default to 8000 for local testing
ENV PORT=8000

EXPOSE ${PORT}

CMD uvicorn server.main:app --host 0.0.0.0 --port ${PORT}
