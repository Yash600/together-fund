# Deal Screening Agent

Takes a pitch deck PDF and produces a structured first-pass screening memo,
so partner time goes only to decks worth a full look.

## How it works (flow)

```
PDF --> [parse] --> [extract claims] --> [verify consistency] --> [score thesis fit] --> [draft memo]
```

1. **Parse** -- raw text pulled from the PDF (PyMuPDF), no LLM call.
2. **Extract claims** -- an LLM call pulls structured claims (market size,
   traction, team, ask) into a typed schema, extracting only what's
   literally stated -- no inference or fabrication.
3. **Verify consistency** -- a second LLM call checks those claims for
   internal consistency and unsupported specificity (e.g. a market-size
   figure with no basis given, traction numbers that don't arithmetically
   add up, vague team claims). This does **not** fact-check against the
   outside world -- it only catches internal inconsistency. See the
   writeup for why that distinction matters.
4. **Score thesis fit** -- scores the company 1-5 on AI-native fit,
   vertical-agent fit, and US-India corridor fit against Together Fund's
   stated thesis (`agent/thesis.py`).
5. **Draft memo** -- compiles everything into a markdown screening memo
   with a recommendation (advance / advance with reservations / pass).

Every step logs what it did and is streamed in real time (CLI prints as it
happens; the API streams over SSE) -- so you see what was extracted, what
was flagged, and how the score was reached, not just the final memo.

## Sample decks (`sample_decks/`)

Three synthetic pitch decks (fictional companies) built to exercise
different parts of the pipeline:

- `kavach_ai.pdf` -- clean corridor fit (US fintech customers, India-based
  team), internally consistent claims. Should score well and produce few
  flags.
- `growthpilot_ai.pdf` -- horizontal/generic AI tool, inflated TAM claim
  with no basis, and an arithmetic inconsistency (500 customers + $500/mo
  enterprise plan implied vs. $8K MRR stated). Should trigger flags and
  score poorly on thesis fit.
- `bhasha_health.pdf` -- good vertical AI fit, but India-only market (no
  US/global buyer) -- tests that the corridor-fit score can differ from
  the AI-native/vertical-agent scores rather than everything moving
  together.

Regenerate them any time with `python sample_decks/generate_decks.py`.

## Setup

```bash
# from code/ (shared venv across all three tools)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt   # shared requirements.txt at code/ level

cd deal-screening-agent
cp .env.example .env    # then add your GROQ_API_KEY (free at console.groq.com)
```

(This folder also ships its own `requirements.txt` for a fully standalone
run with its own venv.)

## Run it -- two ways

**CLI:**
```bash
python run_cli.py sample_decks/kavach_ai.pdf
python run_cli.py sample_decks/growthpilot_ai.pdf
python run_cli.py sample_decks/bhasha_health.pdf
```
Saves the generated memo to `output/<deck_name>_memo.md` as well as printing it.

**API server (used by the shared frontend):**
```bash
uvicorn app:app --reload --port 8001
# then: curl -N -X POST http://localhost:8001/api/deal-screening/analyze \
#   -F "file=@sample_decks/kavach_ai.pdf"
```

## Honest limitation

This agent checks claims for *internal* consistency, not ground truth --
it has no way to verify a stated market size or traction number against
reality. Framed correctly in the memo output as "flags to verify in the
founder call," not as fact-checking. See `writeup.md` for more on this
tradeoff and what real-world verification (e.g. calling the Founder
Research Agent) would add.
