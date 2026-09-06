# VentureIQ — System Architecture & Technical Specification

> **Project Name**: VentureIQ  
> **Tagline**: AI-Powered Multi-Agent Startup Due Diligence & Validation Engine  
> **Target Environment**: FastAPI + React 19 + LangGraph + Gemini + Pinecone RAG + Tavily Search  

---

## 1. Problem Statement
Early-stage founders and venture evaluators face significant challenges when assessing new startup concepts:
* **Superficial Feedback**: Generic LLMs provide polite, uncritical answers without probing risk factors.
* **Information Asymmetry**: Manual due diligence requires hours of researching market size, competitor positioning, unit economics, and regulatory constraints.
* **Lack of Repeatable Rigor**: Informal evaluations fail to follow consistent, structured due-diligence criteria.

---

## 2. Proposed Solution
**VentureIQ** is an autonomous multi-agent validation engine designed to stress-test startup concepts before code is written or capital is deployed. It combines:
1. **Interactive Conversational Discovery**: A Lead Supervisor agent interviews the founder to refine the core value proposition, target customer, and business model.
2. **Vector Retrieval (RAG)**: Retrieves empirical startup case studies, benchmark failure patterns, and domain knowledge from a Pinecone vector database.
3. **Parallel Multi-Agent Analytics**: LangGraph orchestrates specialized agents (*Market, Competitor, Business, Risk*) that evaluate distinct dimensions of the venture.
4. **Investor Readiness Index**: Produces quantitative 0–100 scores across 4 key pillars alongside a structured executive verdict report.

---

## 3. Technology Stack & Key Libraries

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend UI** | React 19, Vite 7, Tailwind CSS 4 | Responsive, dark-themed Single Page Application (SPA) |
| **3D Core Engine** | Three.js (r185), `@react-three/fiber` | Interactive animated icosahedron core reacting to workflow states |
| **Backend API** | FastAPI (Python 3.10), Uvicorn, Pydantic | High-performance asynchronous REST API with in-flight deduplication |
| **AI Orchestration** | LangGraph, LangChain (`langchain-google-genai`) | State graph workflow management and prompt chain execution |
| **LLM Model** | Google Gemini (2.5 / 3.6 Flash) | Multi-turn discovery conversation and agent analytical reasoning |
| **Vector DB (RAG)** | Pinecone (`rag-main`), `models/text-embedding-004` | Semantic vector retrieval for domain knowledge & benchmark evidence |
| **Web Research** | Tavily API (`tavily-python`) | Real-time live web search for competitive market research |

---

## 4. Multi-Agent System & LangGraph Workflow

```
                   [ User Input / Idea ]
                             │
                             ▼
              [ Phase 1: Conversational Supervisor ]
                             │ (Context Complete)
                             ▼
              [ Phase 2: RAG Vector Retrieval Node ]
                             │ (Pinecone rag-main)
                             ▼
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  [ Market Agent ]   [ Competitor Agent ]  [ Business Agent ]   [ Risk Agent ]
   (TAM & Demand)     (Moat + Tavily Web)  (Unit Economics)     (Regulatory)
         └───────────────────┬───────────────────┘
                             ▼
              [ Phase 3: Synthesis Report Agent ]
                             │
                             ▼
             [ Investor Readiness Index Dashboard ]
```

### Agent Responsibilities:
1. **Supervisor Agent**: Manages multi-turn context gathering. Validates readiness once core facts (problem, customer, solution, monetization) are established.
2. **Retrieval Node**: Generates 768-dim query embeddings and fetches top-k (`k=5`) relevant vector records from Pinecone index `rag-main`.
3. **Market Agent**: Evaluates TAM, target customer size, growth pull, and market demand signals.
4. **Competitor Agent**: Combines internal RAG knowledge with Tavily live web research to map incumbent positioning and defensibility moats.
5. **Business Agent**: Analyzes revenue model viability, CAC/LTV indicators, and monetization dynamics.
6. **Risk Agent**: Identifies execution, regulatory, competitive, and financial risks.
7. **Report Agent**: Synthesizes all agent outputs and scorecards into a structured **VERDICT** report.

---

## 5. RAG Mechanism & Pinecone Integration
* **Embeddings**: Generated using Google's `models/text-embedding-004` (768 dimensions).
* **Pinecone Vector Database**: Connects via `pinecone.Pinecone(api_key=...)` querying index `rag-main` using cosine semantic similarity search.
* **Graceful Fallback**: If `PINECONE_API_KEY` is missing or Pinecone is unreachable, the system logs a warning (`[RAG WARN] RAG retrieval unavailable; continuing with agent analysis`) and safely completes the multi-agent workflow without crashing.

---

## 6. Why Not Simply Use ChatGPT?
When asked during viva or evaluation why a dedicated multi-agent system is necessary instead of a single prompt in ChatGPT:

1. **Structured Workflow vs. Generic Response**: ChatGPT produces unstructured conversational prose. VentureIQ enforces deterministic due-diligence methodology across 4 distinct analytical domain agents.
2. **Grounding & Reduced Hallucination**: VentureIQ combines curated vector database evidence (Pinecone RAG) with live market research (Tavily), instructing agents to separate empirical facts from AI inference.
3. **Repeatable Quantitative Scoring**: Generates benchmarked 0–100 Investor Readiness index scores across Market, Competitor, Business, and Risk dimensions.
4. **Interactive 3D Visual Feedback**: Reacts visually to workflow lifecycle states (`idle`, `thinking`, `question`, `retrieving`, `analyzing`, `complete`).
