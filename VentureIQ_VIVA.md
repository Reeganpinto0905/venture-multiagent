# VentureIQ — Comprehensive Viva Questions & Answers

> **Purpose**: Quick reference guide for viva defense, project presentation, and external evaluation.

---

### Q1: What is VentureIQ?
**Answer**: VentureIQ is an AI-powered startup due-diligence engine that uses a multi-agent state graph (LangGraph) and vector retrieval (RAG) to validate early-stage startup ideas, analyze market demand, map competitors, evaluate unit economics, and calculate an Investor Readiness Index.

---

### Q2: What problem does VentureIQ solve?
**Answer**: Early-stage founders waste months building products without knowing if real market demand or defensibility exists. Generic AI tools give polite, unstructured responses. VentureIQ provides structured, objective due diligence powered by specialized agents and vector-retrieved evidence.

---

### Q3: Why use multiple AI agents instead of a single LLM prompt?
**Answer**: A single LLM prompt suffers from context pollution, superficial responses, and lack of domain specialization. By using specialized agents (*Market, Competitor, Business, Risk, Report*), each agent focuses strictly on one analytical discipline with dedicated prompts, tools, and evidence context.

---

### Q4: What is LangGraph and why is it used?
**Answer**: LangGraph is a stateful orchestration framework built on top of LangChain. It manages complex agent workflows as directed state graphs, enabling state persistence, conditional task routing, parallel execution, and structured agent transitions.

---

### Q5: What is RAG (Retrieval-Augmented Generation) and why is it included?
**Answer**: RAG retrieves relevant external knowledge from a vector database before an LLM generates an answer. In VentureIQ, RAG retrieves relevant startup case studies, benchmark failure patterns, and industry metrics from Pinecone so agents ground their evaluations on empirical evidence rather than static training data.

---

### Q6: What are embeddings and how do they work in VentureIQ?
**Answer**: Embeddings are dense numerical vector representations of text where semantically similar concepts are close together in vector space. VentureIQ uses Google's `models/text-embedding-004` (768 dimensions) to convert startup queries into vectors for similarity searching against Pinecone.

---

### Q7: What is Pinecone and what is top-k retrieval?
**Answer**: Pinecone is a cloud-native vector database designed for fast vector similarity search. `top-k` (e.g. `k=5`) specifies the number of nearest-neighbor vector documents to retrieve based on cosine similarity score.

---

### Q8: What does Tavily do in your architecture?
**Answer**: Tavily is a search API built specifically for AI agents. It performs real-time live web searches to find competitor pricing, market news, and recent player updates, complementing Pinecone's internal vector knowledge base.

---

### Q9: How does VentureIQ reduce AI hallucinations?
**Answer**:
1. **RAG Grounding**: Passes retrieved vector evidence into agent prompts.
2. **Explicit Prompt Rules**: Instructs agents to separate empirical evidence from analytical inference and state assumptions explicitly.
3. **Deterministic Scoring Rules**: Business agent uses heuristic keyword signal checks combined with model scoring.
4. **Graceful Fallbacks**: If retrieval fails, the system logs a warning and proceeds transparently without fabricating data.

---

### Q10: What happens if Pinecone or the network connection fails during the demo?
**Answer**: VentureIQ implements graceful fallback handling. If `PINECONE_API_KEY` is missing or Pinecone is offline, `retrieve_context()` logs a warning (`[RAG WARN] RAG retrieval unavailable; continuing with agent analysis`) and sets `retrieved_context = ""`. The LangGraph workflow continues running standard multi-agent analysis without crashing.

---

### Q11: How is conversation state maintained across turns?
**Answer**:
* **Backend**: Managed via `SESSIONS` dictionary and `VentureState` keeping `idea_context` structured facts.
* **Frontend**: Saved in `localStorage` (`ventureiq_conversations`) grouped by relative date (*Today, Yesterday, Last 7 days, Older*).

---

### Q12: Why not simply use ChatGPT?
**Answer**:
1. **Structured Methodology**: Enforces YC-style due-diligence criteria across 4 dedicated domain agents.
2. **Hybrid Intelligence**: Combines internal vector retrieval (Pinecone RAG) with external live web research (Tavily).
3. **Quantitative Scoring**: Computes an Investor Readiness Index score (0–100) across 4 pillars.
4. **Visual State Machine**: Features an interactive Three.js 3D Core reacting dynamically to workflow execution phases.
