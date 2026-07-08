FROM python:3.11-slim

WORKDIR /app

# libgomp1 is a runtime dependency of onnxruntime (used by fastembed) on slim
# base images -- without it, fastembed import fails at container start.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
