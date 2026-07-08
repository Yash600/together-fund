"""
FastAPI wrapper around the Deal Screening Agent.

Exposes:
    GET  /health
    POST /api/deal-screening/analyze   (multipart file upload, field name "file")
         -> SSE stream of reasoning-step events followed by a final result event.

Runnable standalone:
    uvicorn app:app --reload --port 8001
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agent.graph import run_screening
from agent.parser import extract_text_from_bytes

app = FastAPI(title="Deal Screening Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "tool": "deal-screening-agent"}


@app.post("/api/deal-screening/analyze")
async def analyze(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    raw_text, used_ocr = extract_text_from_bytes(pdf_bytes)

    def event_stream():
        parse_detail = f"Extracted {len(raw_text)} characters from {file.filename}"
        if used_ocr:
            parse_detail += " (some/all pages had no text layer -- ran OCR to recover text)"
        yield f"data: {json.dumps({'type': 'log', 'step': 'parse', 'detail': parse_detail})}\n\n"

        if len(raw_text.strip()) < 100:
            warning = (
                "Very little text could be extracted from this PDF. If it's a scanned or "
                "image-only deck, OCR "
                + ("ran but recovered almost nothing" if used_ocr else "isn't available in this environment")
                + " -- the resulting memo below will be low-confidence."
            )
            yield f"data: {json.dumps({'type': 'log', 'step': 'parse', 'detail': warning})}\n\n"

        for event in run_screening(raw_text):
            yield f"data: {json.dumps(event)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
