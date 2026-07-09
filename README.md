# Together Tools

Three AI agents for a venture deal team, built for Together Fund's technical intern
take-home assignment: **Firm Brain** (internal document Q&A), **Deal Screening**
(pitch deck triage), and **Founder Research** (founder/company diligence) — plus a
shared Next.js frontend to demo all three from one place.

Every tool is a small [LangGraph](https://www.langchain.com/langgraph) state machine
(plan/classify → retrieve or search → verify → synthesize) served by its own FastAPI
backend, streaming its reasoning over Server-Sent Events so you see each step as it
happens, not just a final answer.

```
Repo:  https://github.com/Yash600/together-fund
```

## Live demo

| Service                | URL                              |
|-------------------------|-----------------------------------|
| Web app (frontend)      | _fill in your Vercel URL_        |
| Firm Brain RAG          | _fill in your Render URL_        |
| Deal Screening Agent    | _fill in your Render URL_        |
| Founder Research Agent  | _fill in your Render URL_        |

All three backends expose `GET /health` for a quick liveness check.

---

## The three tools

### 1. Firm Brain — internal document Q&A
Upload a document you (or a colleague) already wrote about a company — an
investment memo, founder call notes, a DD summary, a portfolio update — and ask it
questions in a chat instead of re-reading the whole thing.

- **Not a generic RAG chatbot.** Each browser tab gets its own isolated,
  session-scoped knowledge base — no pre-loaded corpus, no cross-session leakage.
  A query with nothing uploaded yet gets told to upload something, it never falls
  back to any other source.
- Query is classified (lookup / compare / summarize / thesis / general) before
  retrieval depth is decided — not a single fixed-`k` retrieval call.
- Answers are plain prose, no bracketed citation clutter.
- **Flow:** `upload → chunk + embed (session-scoped)` then `query → classify →
  retrieve → synthesize`.
- Details: [`firm-brain-rag/README.md`](firm-brain-rag/README.md)

### 2. Deal Screening — pitch deck triage
Upload a pitch deck PDF and get back a structured first-pass screening memo:
extracted claims, internal-consistency flags, a thesis-fit score, and a
recommendation — so partner time goes only to decks worth a full look.

- **Not a PDF summarizer.** A dedicated verification step cross-checks the deck's
  own claims against each other (e.g. traction numbers that don't arithmetically
  add up) — it does not fact-check against the outside world, and says so plainly
  in its own output.
- Falls back to Tesseract OCR per-page when a deck is an image-only PDF with no
  extractable text (common with real, image-exported decks) — verified against a
  real historical pitch deck with zero native characters across 13 pages.
- **Flow:** `PDF → parse → extract claims → verify consistency → score thesis fit
  → draft memo`.
- Details: [`deal-screening-agent/README.md`](deal-screening-agent/README.md)

### 3. Founder Research — founder & company diligence
Give it a founder's name and company; it plans web searches, actually runs them,
verifies which claims the results support, maps the competitive landscape on both
sides of the US–India corridor, and drafts a cited founder-market-fit brief.

- **Not "tell me about this founder."** Search queries are LLM-planned, not
  hardcoded, and results are run through a verification step that only asserts
  what's actually supported — including an identity-confidence check (is this
  really the same person) and a list of open questions the web couldn't resolve.
- Comparison step is Together Fund's specific lens: named competitors/comparables
  split explicitly by US vs. India.
- The most agentic of the three — real tool use (Tavily search), not simulated.
- **Flow:** `founder + company → plan searches → run searches → verify founder →
  compare US/India landscape → synthesize brief`.
- Details: [`founder-research-agent/README.md`](founder-research-agent/README.md)

### Shared frontend
One Next.js app, three tabs, styled to match together.fund's own design system.
Each tab is a thin client over its backend's API — the frontend holds no state of
its own beyond the current page session. Details:
[`web-app/README.md`](web-app/README.md)

---

## Why these three, and what they share

All three exist to remove a specific, repeated manual task from a deal team's week
(re-reading internal docs, first-pass deck triage, founder background-checking)
rather than being a generic "chat with your data" demo. They share one
architecture on purpose, so the pattern — not just the feature — is the thing
being evaluated:

- **LangGraph state machine per tool**, not a single prompt-response call — each
  node does one job (classify, retrieve, verify, score, synthesize) and the graph
  routes between them based on what came back.
- **Visible reasoning, always.** Every node logs a structured event (`step`,
  `detail`, optional `data`) as it runs; both the CLI and the API's SSE stream
  surface it live, and the frontend renders it as an expandable trace per tool —
  so any answer is auditable back to what was retrieved/searched and why.
- **Groq-hosted Llama 3.3 70B** for every LLM call, chosen for latency during a
  live demo.
- **Honest about limitations.** Each tool's README has a section on what it
  deliberately does *not* do (Deal Screening doesn't fact-check against reality;
  Founder Research's identity match is heuristic, not a verified unique-ID match) —
  called out up front rather than discovered by a user.

---

## Repository structure

```
code/
├── firm-brain-rag/           # Tool 1 -- FastAPI + LangGraph, port 8000
│   ├── agent/                #   chunking, embeddings, vector store, graph
│   ├── sample_uploads/       #   sample docs to upload and query
│   ├── run_cli.py            #   one-shot CLI: ingest + ask one question
│   └── app.py                #   API server (upload + query endpoints)
├── deal-screening-agent/     # Tool 2 -- FastAPI + LangGraph, port 8001
│   ├── agent/                #   parsing (+OCR), extraction, verification, scoring, memo
│   ├── sample_decks/         #   synthetic pitch decks exercising different scores
│   ├── run_cli.py
│   └── app.py
├── founder-research-agent/   # Tool 3 -- FastAPI + LangGraph, port 8002
│   ├── agent/                #   planning, search, verification, comparison, synthesis
│   ├── run_cli.py
│   └── app.py
├── web-app/                  # Shared Next.js frontend, 3 tabs, port 3000
│   ├── app/components/       #   one component per tab + shared ReasoningLog
│   └── lib/                  #   SSE client, markdown renderer
├── render.yaml                # Render Blueprint -- all 3 backends + frontend
├── requirements.txt           # shared Python deps (superset across all 3 backends)
└── .gitignore
```

---

## Tech stack

| Layer          | Choice                                                              |
|----------------|----------------------------------------------------------------------|
| Agent orchestration | LangGraph (`langgraph`, `langchain-core`)                      |
| LLM            | Groq API, Llama 3.3 70B Versatile                                    |
| Embeddings     | fastembed (ONNX BGE-small), TF-IDF fallback (scikit-learn)           |
| Vector store   | In-memory numpy index, session-scoped (`agent/store.py`)             |
| PDF parsing    | PyMuPDF, with Tesseract OCR fallback (`pytesseract` + Pillow)         |
| Web search     | Tavily API                                                            |
| Backend        | FastAPI + Uvicorn, one process per tool, SSE streaming                |
| Frontend       | Next.js 14 (App Router), plain CSS (no Tailwind), React 18            |
| Deployment     | Render (Docker, one service per backend) + Vercel (frontend)          |

---

## Quick start (local)

All three backends share one virtual environment and Python dependency set; the
frontend is a separate Node app that talks to all three over HTTP.

```bash
# 1. Python env (from code/)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Add API keys (one .env per backend -- see table below)
cp firm-brain-rag/.env.example firm-brain-rag/.env
cp deal-screening-agent/.env.example deal-screening-agent/.env
cp founder-research-agent/.env.example founder-research-agent/.env
# edit each .env and fill in GROQ_API_KEY (and TAVILY_API_KEY for founder-research-agent)

# 3. Run all three backends (3 separate terminals)
cd firm-brain-rag         && uvicorn app:app --reload --port 8000
cd deal-screening-agent   && uvicorn app:app --reload --port 8001
cd founder-research-agent && uvicorn app:app --reload --port 8002

# 4. Run the frontend (4th terminal)
cd web-app
npm install
cp .env.local.example .env.local   # defaults already match the ports above
npm run dev
```

Open `http://localhost:3000` and use the tabs to switch between the three tools.

**No frontend?** Each backend also has a one-shot CLI that needs no server:
```bash
python firm-brain-rag/run_cli.py firm-brain-rag/sample_uploads/setu_pay_memo.pdf "What is this company about?"
python deal-screening-agent/run_cli.py deal-screening-agent/sample_decks/kavach_ai.pdf
python founder-research-agent/run_cli.py "Priya Raman" "Kavach AI"
```

---

## Environment variables

| Variable                          | Where            | Required | Notes                                            |
|------------------------------------|------------------|:--------:|---------------------------------------------------|
| `GROQ_API_KEY`                     | all 3 backends   | Yes      | Free at [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL`                       | all 3 backends   | No       | Defaults to `llama-3.3-70b-versatile`             |
| `PORT`                             | all 3 backends   | No       | Defaults 8000 / 8001 / 8002 respectively          |
| `TAVILY_API_KEY`                   | founder-research-agent | Yes | Free tier ~1,000 searches/mo at [tavily.com](https://tavily.com) |
| `NEXT_PUBLIC_FIRM_BRAIN_URL`       | web-app          | Yes      | Points at the Firm Brain backend                  |
| `NEXT_PUBLIC_DEAL_SCREENING_URL`   | web-app          | Yes      | Points at the Deal Screening backend              |
| `NEXT_PUBLIC_FOUNDER_RESEARCH_URL` | web-app          | Yes      | Points at the Founder Research backend            |

`NEXT_PUBLIC_*` variables are baked into the Next.js build at build time, not
read at runtime — set them before the frontend's first build, and rebuild if you
change them afterward (relevant when deploying, see below).

---

## Deployment

`render.yaml` at this level is a Render Blueprint defining all four services;
you can either point Render at this repo and let it read the Blueprint, or
create the four services manually in the Render dashboard (this project was
deployed the manual way):

1. **Deploy the three backends first**, each as a Docker web service with
   **Root Directory** set to its folder (`firm-brain-rag`, `deal-screening-agent`,
   `founder-research-agent`) — Dockerfile path and build context resolve relative
   to Root Directory, not the repo root. Add each service's required env vars from
   the table above. Render auto-injects `PORT`; no manual `PORT` env var needed.
2. **Confirm all three are live** via their `/health` endpoints.
3. **Deploy the frontend to Vercel** with Root Directory `web-app`, setting the
   three `NEXT_PUBLIC_*_URL` vars to the live Render URLs from step 1 *before*
   the first build (see the note above on build-time vs. runtime env vars).

---

## Notes for reviewers

- Nothing is pre-loaded anywhere — Firm Brain has zero base corpus, Deal
  Screening and Founder Research have zero cached results. Every run in the demo
  is a live call against whatever you upload or type in.
- Each tool's own README documents what it deliberately doesn't do (see "Honest
  limitations" in Deal Screening and Founder Research's READMEs) — worth reading
  before assuming a gap is a bug.
- `sample_uploads/` (Firm Brain) and `sample_decks/` (Deal Screening) contain
  ready-to-use test documents, including a detailed real-company investment memo
  and pitch deck pair (Sarvam AI) sized like an actual internal document rather
  than a short synthetic sample.
