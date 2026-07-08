# Together Fund Tools -- Shared Frontend

A single Next.js app with 3 tabs (Firm Brain, Deal Screening, Founder Research), styled to
match together.fund's own design system (cream background, deep dark-purple text, coral pill
buttons, thin serif display headings over a clean sans body -- colors and fonts pulled from the
live site's computed styles).

This is a thin UI shell only -- each tab calls its own independently runnable FastAPI backend
(ports 8000 / 8001 / 8002). The three backends are the actual "tools"; this app just gives you
one place to click through all three for the demo instead of three separate CLIs.

## Setup

```bash
cd "code/web-app"
npm install
cp .env.local.example .env.local   # defaults already match the three backends' default ports
```

## Run it

You need all three backends running at the same time (in 3 separate terminals), then the frontend
in a 4th:

```bash
# terminal 1
cd code/firm-brain-rag && uvicorn app:app --reload --port 8000

# terminal 2
cd code/deal-screening-agent && uvicorn app:app --reload --port 8001

# terminal 3
cd code/founder-research-agent && uvicorn app:app --reload --port 8002

# terminal 4
cd code/web-app && npm run dev
```

Then open http://localhost:3000 -- use the tabs at the top to switch between the three tools.
Each tab streams the agent's reasoning trace live (same events the CLIs print) followed by the
rendered final result.

## Notes

- This app has no backend of its own and stores no state beyond the current page session --
  it is a pure client over the three APIs.
- If a backend isn't running, that tab will show an error when you try to run it rather than
  hanging silently.
- Built and reviewed but not build-tested in the development sandbox (network/filesystem
  constraints there prevented `npm install` from completing) -- please run `npm install && npm
  run dev` locally and report back if anything doesn't compile.
