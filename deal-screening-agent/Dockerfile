FROM python:3.11-slim

WORKDIR /app

# tesseract-ocr is the OCR fallback for image-only/scanned pitch decks (see
# agent/parser.py) -- this is the one thing that made a Dockerfile worth
# adding at all, since Render's plain Python runtime can't apt-get install
# system binaries.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8001
EXPOSE 8001

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8001}"]
