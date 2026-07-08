"""
FastAPI wrapper around the Founder Research Agent.

Exposes:
    GET  /health
    POST /api/founder-research/analyze   { "founder_name": "...", "company_name": "..." }
         -> SSE stream of reasoning-step events followed by a final result event.

Runnable standalone:
    uvicorn app:app --reload --port 8002
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.graph import run_research

app = FastAPI(title="Founder Research Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    founder_name: str
    company_name: str


@app.get("/health")
def health():
    return {"status": "ok", "tool": "founder-research-agent"}


@app.post("/api/founder-research/analyze")
def analyze(req: ResearchRequest):
    def event_stream():
        for event in run_research(req.founder_name, req.company_name):
            yield f"data: {json.dumps(event)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
