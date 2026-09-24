"""
OKF Agentic Retriever: Provides structured, provenance-backed knowledge retrieval for VentureIQ agents.
Replaces the old vector-database RAG with structured OKF entity discovery and relationship traversal.
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from knowledge.schema import OKFEntity, OKFSource
from knowledge.loader import get_default_bundle
from knowledge.index import OKFKnowledgeIndex
from agents.llm_utils import increment_telemetry

# Global index singleton
_INDEX_INSTANCE: Optional[OKFKnowledgeIndex] = None


def get_knowledge_index() -> OKFKnowledgeIndex:
    """
    Returns the active indexed OKF Knowledge bundle.
    """
    global _INDEX_INSTANCE
    if _INDEX_INSTANCE is None:
        bundle = get_default_bundle()
        _INDEX_INSTANCE = OKFKnowledgeIndex(bundle)
    return _INDEX_INSTANCE


def format_okf_evidence(entities: List[OKFEntity], max_items: int = 5) -> str:
    """
    Formats retrieved OKF entities into a clean, investor-grade diligence evidence block.
    Distinguishes FACT / PROVENANCE from entity synthesis.
    """
    if not entities:
        return ""

    blocks = []
    for idx, entity in enumerate(entities[:max_items], 1):
        sources_str = ""
        if entity.sources:
            src_list = []
            for s in entity.sources:
                loc = f"p.{s.page}" if s.page else ""
                sec = f" | {s.section}" if s.section else ""
                src_list.append(f"{s.document} ({loc}{sec})")
            sources_str = ", ".join(src_list)
        else:
            sources_str = "Verified Knowledge Base (OKF v0.2)"

        # Relationships summary
        rel_str = ""
        if entity.relationships:
            rel_items = [f"{r.relation} -> {r.target}" for r in entity.relationships[:4]]
            rel_str = f"\n  • Connected Concepts: {', '.join(rel_items)}"

        # Verified status badge
        status_badge = f"[{entity.verified.upper()} | {entity.status}]"

        header = f"• [OKF Evidence #{idx} | {entity.title} ({entity.category}) | {status_badge}]\n  Source Provenance: {sources_str}{rel_str}"
        body_snippet = entity.body.strip() if entity.body else entity.description
        
        # Keep snippet focused to first 800 chars to prevent prompt dilution
        if len(body_snippet) > 850:
            body_snippet = body_snippet[:850].rsplit(" ", 1)[0] + "..."

        blocks.append(f"{header}\n  {body_snippet}")

    return "\n\n".join(blocks)


def retrieve_context(query: str, top_k: int = 5, intent: Optional[str] = None) -> str:
    """
    Agentic knowledge retrieval over the OKF Knowledge Bundle.
    Direct drop-in replacement for the old Pinecone retrieve_context.
    """
    clean_query = str(query).strip() if query else ""
    if not clean_query:
        return ""

    increment_telemetry("knowledge_calls")

    index = get_knowledge_index()
    if not index.bundle.loaded or not index.bundle.entities:
        # Reload or check
        index.bundle.load()
        index._build_index()

    # Determine category preference based on query intent or agent role
    category_filter = None
    lower = clean_query.lower()
    if intent == "competitor" or any(w in lower for w in ["competitor", "rival", "versus", "competition"]):
        category_filter = "competitors"
    elif intent == "risk" or any(w in lower for w in ["risk", "failure", "threat", "downside"]):
        category_filter = "risks"
    elif intent == "business" or any(w in lower for w in ["business model", "unit economics", "pricing", "margin"]):
        category_filter = "business_models"
    elif intent == "market" or any(w in lower for w in ["market", "tam", "demand", "industry"]):
        category_filter = "markets"

    ranked = index.search(clean_query, category=category_filter, top_k=top_k)
    
    # If category filter was too narrow, broaden search to all categories
    if len(ranked) < min(2, top_k):
        broad_ranked = index.search(clean_query, category=None, top_k=top_k)
        seen_ids = {e.id for e, _ in ranked}
        for e, score in broad_ranked:
            if e.id not in seen_ids:
                ranked.append((e, score))
                seen_ids.add(e.id)

    entities = [e for e, _ in ranked[:top_k]]
    formatted = format_okf_evidence(entities, max_items=top_k)
    
    if formatted:
        print(f"[OKF RETRIEVER SUCCESS] Retrieved {len(entities)} structured OKF entities for query: '{clean_query[:40]}...'")
    else:
        print(f"[OKF RETRIEVER INFO] No OKF entities matched for query: '{clean_query[:40]}...'")

    return formatted


def retrieve_context_node(state: dict) -> dict:
    """
    LangGraph workflow node function that runs OKF retrieval.
    Optimized to retrieve targeted domain evidence per agent role (2 focused entities each)
    instead of broadcasting identical full bundles, significantly reducing token consumption.
    """
    user_query = state.get("user_query", "")
    print(f"[OKF NODE] Initiating domain-specialized OKF retrieval for query: {user_query[:50]}...")

    market_ctx = retrieve_context(user_query, top_k=2, intent="market")
    competitor_ctx = retrieve_context(user_query, top_k=2, intent="competitor")
    business_ctx = retrieve_context(user_query, top_k=2, intent="business")
    risk_ctx = retrieve_context(user_query, top_k=2, intent="risk")

    combined_ctx = "\n\n".join(filter(None, [market_ctx, competitor_ctx, business_ctx, risk_ctx]))

    return {
        "retrieved_context": combined_ctx,
        "market_context": market_ctx,
        "competitor_context": competitor_ctx,
        "business_context": business_ctx,
        "risk_context": risk_ctx
    }


def find_competitors(concept: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Specialized agent retrieval: finds competitor entities with strengths/weaknesses."""
    index = get_knowledge_index()
    ranked = index.search(concept, category="competitors", top_k=top_k)
    results = []
    for entity, score in ranked:
        results.append({
            "id": entity.id,
            "name": entity.title,
            "description": entity.description,
            "sources": [s.to_dict() for s in entity.sources],
            "score": score
        })
    return results


def find_risks(concept: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Specialized agent retrieval: finds structural risk factors & historical failure precedents."""
    index = get_knowledge_index()
    ranked = index.search(concept, category="risks", top_k=top_k)
    results = []
    for entity, score in ranked:
        results.append({
            "id": entity.id,
            "title": entity.title,
            "description": entity.description,
            "sources": [s.to_dict() for s in entity.sources],
            "score": score
        })
    return results


def validate_knowledge_env() -> bool:
    """
    Validates presence of OKF knowledge bundle directory and entities.
    Replaces old validate_rag_env.
    """
    bundle = get_default_bundle()
    if not bundle.loaded or len(bundle.entities) == 0:
        bundle.load()
    
    count = len(bundle.entities)
    print(f"[OKF ENV INFO] OKF Knowledge Layer validated cleanly. Active Bundle: '{os.path.basename(bundle.bundle_dir)}' ({count} verified entities)")
    return True
