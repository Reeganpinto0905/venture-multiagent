# VentureIQ — what changed and how to run it

I could not run `npm install` or the dev server myself — my environment has
no network access and your `components/` folder, `package.json`, and other
project files weren't part of the upload, so I don't have a full copy of
your repo to build against. Everything below is written and internally
consistent (imports match, braces/parens balance), but **please run it
locally and tell me what breaks** — I'll fix it fast from the actual error.

## 1. Copy files into your project

```
backend/
  main.py                  → replace
  graph/state.py            → replace
  graph/workflow.py         → replace
  agents/supervisor.py      → replace
  agents/market.py          → replace
  agents/competitor.py      → replace
  agents/business.py        → replace
  agents/risk.py            → new (was empty)
  agents/report.py          → new (was empty)
  agents/llm_utils.py       → new, shared JSON-parsing helper
  tools/search_tool.py      → unchanged, included for completeness

frontend/src/
  index.css                 → replace
  App.jsx, main.jsx, App.css → unchanged, included for completeness
  pages/Home.jsx             → replace
  services/api.js            → replace
  components/Navbar.jsx      → replace your existing one
  components/Footer.jsx      → replace your existing one
  components/IntelligenceCore.jsx  → new (the 3D core)
  components/ChatConsole.jsx       → new (replaces SearchBox/AgentStatus/etc. as the conversation UI)
  components/ChoiceChips.jsx       → new
  components/AnalysisPipeline.jsx  → new (replaces Loading.jsx)
  components/AgentNode.jsx         → new
  components/ResultsDashboard.jsx  → new (replaces ResultCard/SummaryCard)
  components/ScoreBar.jsx          → new
  components/ExpandableSection.jsx → new
```

Your old `Hero.jsx`, `SearchBox.jsx`, `Loading.jsx`, `AgentStatus.jsx`,
`ResultCard.jsx`, `SummaryCard.jsx` are superseded by the components above —
delete them once you've confirmed the new flow works, or keep them
unreferenced if you'd rather diff later.

## 2. Install the three new frontend dependencies

```
cd frontend
npm install three @react-three/fiber framer-motion
```

I deliberately skipped `@react-three/drei` to keep the dependency count
down — the 3D core is built from raw three.js primitives.

## 3. Backend — no new pip packages

Everything new (`agents/risk.py`, `agents/report.py`, `agents/llm_utils.py`)
only uses `langchain_google_genai`, which you already have.

## 4. Run it

```
# backend
cd backend
uvicorn main:app --reload

# frontend
cd frontend
npm run dev
```

## What's simulated vs. real

- **Conversation** (`/chat`) is fully real: each turn calls Gemini, extracts
  facts into `idea_context`, and decides readiness.
- **Analysis** (`/analyze`) is fully real: LangGraph now actually branches
  on the supervisor's chosen tasks (it didn't before), and a new `report`
  node produces the executive summary that was previously always empty.
- **The pipeline diagram's live per-agent progress is simulated
  client-side** while waiting on the single `/analyze` response, because
  your backend returns one response at the end rather than streaming
  per-agent events. It settles into the correct final state (skipped vs.
  complete) once the real response arrives. If you want genuinely live
  per-agent status, that needs Server-Sent Events or a WebSocket from
  `/analyze` — happy to build that next if it matters for the demo.

## Known gaps I did not implement (flagging rather than guessing)

- Session storage is a plain in-memory Python dict in `main.py` — fine for
  a single dev-server demo, but resets on restart and won't work with
  multiple backend workers. Fine for your professor demo; not
  production-ready.
- `rag.py` / `pinecone_tool.py` (from your earlier request) are not wired
  into this conversational flow — they weren't mentioned in this brief, so
  I left them out to avoid scope creep. Say the word if you want retrieval
  injected into the market/competitor prompts.
- I could not visually screenshot or run the 3D core, so double check its
  performance on your machine — if the icosahedron wireframe or satellite
  count feels like too much, `STATE_CONFIG` in `IntelligenceCore.jsx` is
  the one place to tune it.
