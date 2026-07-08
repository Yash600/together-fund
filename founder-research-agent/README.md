# Founder Research Agent

Given just a founder's name and company, researches the open web to build
context a pitch deck won't contain -- prior background, identity
disambiguation, and specifically who else is building similar things on
both sides of the US-India corridor.

## How it works (flow)

```
founder + company --> [plan searches] --> [run searches] --> [verify founder]
                                                            --> [compare US/India landscape]
                                                            --> [synthesize brief]
```

1. **Plan searches** -- an LLM call decides what to search for (founder
   background, company/press, US competitors, India competitors) and flags
   if the founder's name is common enough to be confused with someone else.
2. **Run searches** -- the planned queries are actually executed against
   the Tavily search API (real tool use, not simulated) and raw results are
   collected.
3. **Verify founder** -- an LLM call extracts only claims actually
   supported by the search results, with a confidence level and cited
   source per claim, plus an explicit identity-confidence assessment (are
   these results really about the right person) and a list of open
   questions the web couldn't resolve.
4. **Compare landscape** -- a separate LLM call maps competing/comparable
   companies found in the search results, split by US vs. India --
   Together Fund's specific corridor lens.
5. **Synthesize brief** -- compiles everything into a markdown
   founder-market-fit brief with inline citation links.

This is the most agentic of the three tools: the search *queries themselves*
are LLM-planned, not hardcoded, and results feed back into an LLM
verification step rather than being trusted at face value.

Every step logs what it did (queries planned, results returned per query,
confidence levels reached) and streams in real time -- CLI prints as it
happens, the API streams over SSE.

## Setup

```bash
# from code/ (shared venv across all three tools)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt   # shared requirements.txt at code/ level

cd founder-research-agent
cp .env.example .env    # add GROQ_API_KEY and TAVILY_API_KEY
```

(This folder also ships its own `requirements.txt` for a fully standalone
run with its own venv.)

## Run it -- two ways

**CLI:**
```bash
python run_cli.py "Priya Raman" "Kavach AI"
```
Saves the brief to `output/<founder>_<company>_brief.md` as well as printing it.

**API server (used by the shared frontend):**
```bash
uvicorn app:app --reload --port 8002
# then: curl -N -X POST http://localhost:8002/api/founder-research/analyze \
#   -H "Content-Type: application/json" \
#   -d '{"founder_name": "Priya Raman", "company_name": "Kavach AI"}'
```

## Honest limitations

- Search quality depends entirely on what's publicly indexed -- an early
  founder with little online footprint will legitimately produce a
  low-confidence brief. That's a correct output, not a bug.
- Identity disambiguation is heuristic (LLM judgment over search snippets),
  not a verified match against a unique identifier -- a common name is a
  real failure mode worth testing during your demo.
- Tavily's free tier has a monthly search cap; each research run uses
  4-6 searches.
