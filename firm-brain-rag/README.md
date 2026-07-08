# Firm Brain RAG

Upload-only internal document Q&A: upload a deal memo, founder call notes, a
due diligence summary, or a portfolio update, then ask questions about it
instead of re-reading the whole thing. There is no pre-loaded corpus and no
build/ingest step -- answers come strictly from what you've uploaded in the
current session, nothing else.

## How it works (flow)

```
upload --> chunk + embed (session-scoped)
query  --> [classify] --> [retrieve] --> [synthesize] --> answer
```

1. **Upload** -- a document (.md/.txt/.pdf) is chunked (by markdown section,
   falling back to paragraph grouping for PDFs with no literal headings) and
   embedded into an in-memory vector store tied to that browser session only.
2. **Classify** -- an LLM call labels the query as lookup / compare /
   summarize / thesis / general, which controls how many chunks get
   retrieved next.
3. **Retrieve** -- the query is embedded locally (fastembed, no API call) and
   matched only against that session's own uploaded chunks -- never a shared
   corpus, never another session's uploads.
4. **Synthesize** -- an LLM call answers strictly from the retrieved chunks,
   in plain prose (no bracketed citation markers).

Every step is logged and streamed back in real time (both in the CLI and
over SSE in the API), so you can see exactly what was classified, what was
retrieved, and how the answer was built -- not just the final output.

## Session scoping

Each browser tab generates its own `session_id` on load and sends it with
every upload/query. This means:

- A different tab (different `session_id`) never sees your uploaded documents.
- Nothing is persisted to disk -- restarting the backend clears every
  session's uploads. That's intentional, not a bug: this tool is a working
  copy of whatever you just uploaded, not a permanent archive.
- If nothing has been uploaded yet in a session, querying returns a prompt to
  upload a document first, rather than falling back to any other source.

## Setup

All three tools in `code/` share one virtual environment and one Groq API
key -- that's the "shared infrastructure" allowed by the assignment brief.
Only this tool needs the extra ML dependencies (embeddings/vector search).

```bash
# from code/ (one level up from this folder)
python -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt   # shared requirements.txt at code/ level

cd firm-brain-rag
cp .env.example .env    # then add your GROQ_API_KEY (free at console.groq.com)
```

No ingest step needed -- there's nothing to pre-build. First run downloads
the ~130MB fastembed model on demand (falls back to a local TF-IDF backend
automatically if that download isn't reachable).

(This folder also ships its own `requirements.txt` if you'd rather run it
fully standalone with its own venv -- both work.)

## Run it -- two ways

**CLI (fastest way to see it work, no server needed) -- ingests one document
live and answers one question against just that document:**
```bash
python run_cli.py sample_uploads/setu_pay_memo.pdf "What is this company about?"
python run_cli.py sample_uploads/setu_pay_memo.pdf "What are the biggest risks?"
```

**API server (used by the shared frontend):**
```bash
uvicorn app:app --reload --port 8000
# upload a document first (multipart, needs a session_id), then:
curl -N -X POST http://localhost:8000/api/firm-brain/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this company about?", "session_id": "test-session-1"}'
```

## Notes

- Vector store is a local numpy index (`agent/store.py`), in-memory per
  session, not a hosted DB. In production this would swap to Postgres +
  pgvector; only `agent/store.py` would need to change since every other
  module just calls `store.search(...)`.
- Nothing under `data/` or `index/` is needed anymore and neither should be
  deployed -- this app has zero pre-built assets to ship.
- fastembed needs no per-corpus fitting, so its embedder is shared safely
  across all sessions. The TF-IDF fallback's vocabulary depends on whatever
  it was fit on, so each session gets its own fitted vectorizer instead of
  sharing one, to keep sessions from influencing each other's embeddings.
