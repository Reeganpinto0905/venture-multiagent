# VentureIQ — AI Startup Due Diligence Engine

[![Open Knowledge Format](https://img.shields.io/badge/Knowledge%20Layer-OKF%20v0.2-00df82.svg)](https://github.com/GoogleCloudPlatform/open-knowledge-format)
[![LangGraph Multi-Agent](https://img.shields.io/badge/Orchestrator-LangGraph-blue.svg)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61dafb.svg)](https://react.dev/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

**VentureIQ** is an institutional-grade, multi-agent AI system designed to conduct rigorous due diligence on startup ideas. It moves beyond naive conversational chatbots by orchestrating specialized agents (Market, Competitor, Business Model, Risk) guided by an auditable, provenance-backed **Open Knowledge Format (OKF v0.2)** empirical knowledge base.

---

## Architecture Overview

```
[ Founder Input / Idea Pitch ]
             │
             ▼
   [ Supervisor Agent ]
   ├── Discovery Chat (Turn-by-turn interactive qualification)
   ├── Intent Classification (Research vs. Validation)
   └── Dynamic Gating (Autonomous readiness detection)
             │
             ▼
   [ OKF Knowledge Layer ] ◄── Open Knowledge Format (OKF v0.2)
   ├── Bundle Catalog (`index.md`) & Manifest (`manifest.yaml`)
   ├── Category Filtering (companies, competitors, risks, business models)
   ├── Inverted Index & BM25 Scoring
   └── Relational Graph Adjacency (`exhibits_risk`, `competes_with`, `implements_model`)
             │
             ▼
   [ Parallel Multi-Agent Swarm (LangGraph) ]
   ├── Market Agent       ──► TAM/SAM/SOM sizing, CAGR, willingness-to-pay
   ├── Competitor Agent   ──► Live Tavily web search + OKF competitor benchmarking
   ├── Business Agent     ──► CAC/LTV audit, unit economics, payback periods
   └── Risk Agent         ──► Historical failure precedent mapping & lethal traps
             │
             ▼
   [ Lead Partner Diligence Report Agent ]
   ├── Investment Decision (Invest / Pass / Dig Deeper)
   ├── Objective Scoring Matrix (0 - 100)
   ├── Red Flag & Risk Audit
   └── Provenance-Backed Citations (Source Document, Page, Section)
```

---

## Open Knowledge Format (OKF v0.2) Migration

VentureIQ previously relied on a vector-database-centric (Pinecone) RAG architecture. While vector databases offer broad semantic similarity, they present severe drawbacks for financial due diligence:
- **Opaque retrieval black-box:** Vector cosine similarity fails to guarantee exact empirical citations or explain *why* a document was retrieved.
- **Hallucination risk:** LLMs frequently blend fragments of unverified text without clear provenance.
- **Vendor dependency:** Requires external managed cloud vector services with recurring token/vector costs and network latency.

### The OKF Solution
VentureIQ migrated to Google Cloud's **Open Knowledge Format (OKF v0.2)**:
1. **Human & Machine Auditable:** Knowledge is organized as a versioned repository of Markdown files with structured YAML frontmatter.
2. **Empirical Provenance Tracking:** Every fact, metric, and case study retains exact citations:
   ```yaml
   sources:
     - document: startup_failures_detailedv2.pdf
       page: 1
       section: 'Empirical Profile: Quibi'
       confidence: 0.98
   verified: machine-confirmed
   status: CURRENT
   ```
3. **Structured Relationship Graph:** Entities natively define relational links (`exhibits_risk`, `implements_model`, `competes_with`), enabling agents to traverse from a startup to its underlying risks and rivals.
4. **Agentic Hybrid Retrieval:** An in-memory inverted index combines BM25 relevance scoring with metadata filtering and relational graph hops, running with zero external API calls or vector latency.

---

## Knowledge Bundle Structure

The active knowledge bundle is stored in `backend/knowledge_data/startup_diligence_bundle/`:

```
backend/knowledge_data/startup_diligence_bundle/
├── manifest.yaml             # Bundle metadata, version, entry points, and schema compliance
├── index.md                  # Comprehensive root knowledge catalog linking all entities
├── companies/                # 40 empirical startup failure post-mortems and success playbooks
│   ├── quibi.md
│   ├── sprig.md
│   ├── jawbone.md
│   ├── airbnb.md
│   ├── stripe.md
│   └── ... (40 total)
├── competitors/              # 20 competitor intelligence and benchmarking profiles
│   ├── leetcode.md
│   ├── interviewing-io.md
│   ├── hackerrank.md
│   └── ... (20 total)
├── risks/                    # Synthesized structural risk entities with case precedents
│   ├── unit-economics-failure.md
│   ├── premature-geographic-scaling.md
│   ├── hardware-manufacturing-delay.md
│   └── customer-acquisition-cost-trap.md
└── business_models/          # Validated business model patterns with margin benchmarks
    ├── two-sided-marketplace.md
    ├── freemium-developer-api.md
    └── enterprise-seat-saas.md
```

---

## Ingestion Pipeline

To ingest raw documents into the OKF bundle:

```bash
cd backend
python -u knowledge/ingest.py
```

The ingestion pipeline:
1. Extracts text and structural sections from source PDFs (`startup_failures_detailedv2.pdf`, `startup_successes_detailed.pdf`, `competitor_intelligence_detailed.pdf`).
2. Isolates entities and preserves exact page numbers and section boundaries.
3. Automatically generates YAML frontmatter with trust signals (`verified: machine-confirmed`, `status: CURRENT`).
4. Cross-links entities to related risks and business models.
5. Rebuilds `manifest.yaml` and `index.md`.

---

## Verification & Testing

### Running the OKF Diagnostic Test Suite
Verifies manifest compliance, provenance citations, BM25 ranking, graph traversals, and LangGraph workflow node contracts:
```bash
cd backend
python -u knowledge/test_knowledge.py
```

### Running the End-to-End Multi-Agent Integration Tests
Verifies multi-turn discovery chat, research routing, and full 4-agent parallel validation:
```bash
cd backend
python -u tests/test_conversational_upgrade.py
```

---

## Running the Application

### Backend (FastAPI)
```bash
cd backend
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start server
uvicorn main:app --reload --port 8000
```

### Frontend (React + Vite)
```bash
cd frontend
# 1. Install packages
npm install

# 2. Run development server
npm run dev

# 3. Production build
npm run build
```

---

## Environment Configuration

Create a `.env` file in `backend/`:

```env
GOOGLE_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
OKF_BUNDLE_PATH=knowledge_data/startup_diligence_bundle
```

*(Note: Pinecone keys and dependencies have been completely removed. No vector database credentials are required.)*
