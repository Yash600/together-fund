"""
FastAPI wrapper around the Firm Brain RAG agent.

There is no pre-loaded document corpus and no build step required -- this
service starts from nothing and only ever answers from documents uploaded
during the requesting browser session. That also means there's nothing to
`ingest.py` and nothing under data/ or index/ to ship when deploying this.

Exposes:
    GET  /health
    POST /api/firm-brain/query   { "query": "...", "session_id": "..." }  ->
         SSE stream of reasoning-step events followed by a final answer event.
    POST /api/firm-brain/upload  (multipart: file, session_id)

Runnable standalone:
    uvicorn app:app --reload --port 8000
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agent.chunking import chunk_uploaded_text
from agent.embeddings import Embedder
from agent.graph import run_query
from agent.store import VectorStore
from pydantic import BaseModel

app = FastAPI(title="Firm Brain RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_shared_embedder: Embedder | None = None


def get_shared_embedder() -> Embedder:
    """One embedder detection/load per process. For fastembed (the common
    case) this instance is stateless and safe to share across every session.
    For the TF-IDF fallback it's only used to remember which backend is
    active process-wide -- each session gets its OWN fitted vectorizer (see
    SessionState) since TF-IDF's vocabulary depends on the text it was fit
    on, and sessions must never influence each other's embeddings."""
    global _shared_embedder
    if _shared_embedder is None:
        _shared_embedder = Embedder()
        _shared_embedder.init_for_ingest()
        if _shared_embedder.backend == "tfidf":
            # Skip fastembed's ~40s download retry/timeout for every
            # subsequent per-session Embedder() created below.
            os.environ["FIRM_BRAIN_EMBEDDING_BACKEND"] = "tfidf"
    return _shared_embedder


class SessionState:
    """One browser session's own knowledge base: an in-memory list of chunks
    plus a VectorStore. Not persisted to disk, not shared with any other
    session_id.

    fastembed needs no fitting, so new chunks are just embedded with the
    shared model and appended incrementally.

    TF-IDF's vocabulary/IDF weights depend on the whole corpus they were fit
    on, so each session owns its own TfidfVectorizer (via its own Embedder
    instance) and refits on ALL of that session's chunks -- old and new --
    every time a document is added, then rebuilds the store from scratch.
    Cheap at the scale of a handful of uploaded documents per session."""

    def __init__(self, shared_embedder: Embedder):
        self.shared_embedder = shared_embedder
        self.own_embedder: Embedder | None = None  # only allocated for tfidf
        self.chunks: list = []
        self.store = VectorStore()

    def add_chunks(self, new_chunks: list) -> None:
        if self.shared_embedder.backend == "fastembed":
            vectors = self.shared_embedder.embed([c.text for c in new_chunks])
            self.store.add(new_chunks, vectors)
            self.chunks.extend(new_chunks)
        else:
            self.chunks.extend(new_chunks)
            if self.own_embedder is None:
                self.own_embedder = Embedder()
                self.own_embedder.init_for_ingest()  # short-circuits straight to tfidf
            texts = [c.text for c in self.chunks]
            self.own_embedder.fit(texts)
            vectors = self.own_embedder.embed(texts)
            self.store.build(self.chunks, vectors)

    @property
    def query_embedder(self) -> Embedder:
        return self.own_embedder if self.own_embedder is not None else self.shared_embedder

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)


# session_id -> SessionState. In-memory only: a different session_id never
# sees these documents, and restarting the process clears everyone's uploads.
_session_states: dict[str, SessionState] = {}


def get_session_state(session_id: str) -> SessionState:
    if session_id not in _session_states:
        _session_states[session_id] = SessionState(get_shared_embedder())
    return _session_states[session_id]


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "tool": "firm-brain-rag"}


NO_UPLOAD_MESSAGE = (
    "I don't have any document to work with yet in this session. Please upload a document "
    "using the box above, then ask your question again."
)


@app.post("/api/firm-brain/query")
def query(req: QueryRequest):
    get_shared_embedder()  # ensures backend detection has happened at least once
    session = _session_states.get(req.session_id or "")
    has_docs = bool(session and session.chunk_count > 0)

    def event_stream():
        if not has_docs:
            yield f"data: {json.dumps({'type': 'log', 'step': 'scope', 'detail': 'No documents uploaded this session yet.'})}\n\n"
            yield f"data: {json.dumps({'type': 'answer', 'answer': NO_UPLOAD_MESSAGE, 'retrieved': []})}\n\n"
            yield "event: done\ndata: {}\n\n"
            return

        scope_note = f"Querying {session.chunk_count} chunk(s) uploaded this session"
        yield f"data: {json.dumps({'type': 'log', 'step': 'scope', 'detail': scope_note})}\n\n"
        for event in run_query(session.store, session.query_embedder, req.query):
            yield f"data: {json.dumps(event)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _extract_upload_text(filename: str, raw: bytes) -> str:
    """Best-effort text extraction for uploaded docs: .md/.txt are decoded
    directly; .pdf uses PyMuPDF if it's installed (optional dependency --
    only needed for this upload path, not the core query flow)."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        try:
            import fitz  # PyMuPDF
        except ImportError as e:
            raise RuntimeError(
                "PDF upload requires PyMuPDF. Install it with `pip install pymupdf` "
                "or upload a .md/.txt file instead."
            ) from e
        doc = fitz.open(stream=raw, filetype="pdf")
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    return raw.decode("utf-8", errors="replace")


@app.post("/api/firm-brain/upload")
async def upload(file: UploadFile = File(...), session_id: str = Form(...)):
    """Adds an uploaded document to THIS SESSION's knowledge base only. Not
    persisted to disk and not visible to any other session_id."""
    get_shared_embedder()
    session = get_session_state(session_id)

    raw = await file.read()
    text = _extract_upload_text(file.filename, raw)
    chunks = chunk_uploaded_text(file.filename, text)
    if not chunks:
        return {"added_chunks": 0, "filename": file.filename, "message": "No content extracted from file."}

    session.add_chunks(chunks)

    return {
        "added_chunks": len(chunks),
        "filename": file.filename,
        "sections": [c.metadata["section"] for c in chunks],
        "session_total_chunks": session.chunk_count,
    }
