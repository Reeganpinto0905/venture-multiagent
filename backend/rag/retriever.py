import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from rag.embeddings import get_embedding

load_dotenv()

DEFAULT_INDEX_NAME = "rag-main"


def validate_rag_env() -> bool:
    """
    Validates presence of Pinecone & Gemini environment variables without exposing secret values.
    Returns True if fully configured, False otherwise.
    """
    pinecone_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX", DEFAULT_INDEX_NAME)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    missing = []
    if not pinecone_key:
        missing.append("PINECONE_API_KEY")
    if not gemini_key:
        missing.append("GEMINI_API_KEY / GOOGLE_API_KEY")

    if missing:
        print(f"[RAG ENV WARN] RAG capability disabled due to missing environment variables: {', '.join(missing)}")
        return False

    print(f"[RAG ENV INFO] RAG environment validated cleanly. Target Pinecone Index: '{index_name}'")
    return True


def format_retrieved_context(matches: List[Dict[str, Any]]) -> str:
    """
    Formats raw Pinecone match results into a clean, structured evidence block.
    """
    if not matches:
        return ""

    documents = []
    for idx, match in enumerate(matches, 1):
        metadata = match.get("metadata") or {}
        score = match.get("score", 0.0)
        
        # Extract text content from metadata fields commonly used (text, content, page_content, body)
        text = (
            metadata.get("text")
            or metadata.get("content")
            or metadata.get("page_content")
            or metadata.get("body")
            or metadata.get("summary")
            or str(metadata)
        )
        source = metadata.get("source") or metadata.get("title") or f"Doc #{idx}"
        
        formatted_entry = f"• [Evidence #{idx} | Source: {source} | Rel: {score:.2f}]\n  {text.strip()}"
        documents.append(formatted_entry)

    return "\n\n".join(documents)


def retrieve_context(query: str, top_k: int = 5) -> str:
    """
    Connects to Pinecone index, performs semantic similarity retrieval for the given query,
    and returns formatted evidence. Fails gracefully if Pinecone is unreachable or unconfigured.
    """
    clean_query = str(query).strip() if query else ""
    if not clean_query:
        return ""

    pinecone_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX", DEFAULT_INDEX_NAME)

    if not pinecone_key:
        print("[RAG WARN] PINECONE_API_KEY not found. RAG retrieval unavailable; continuing with agent analysis.")
        return ""

    try:
        from pinecone import Pinecone

        # 1. Generate query embedding
        query_vector = get_embedding(clean_query)

        # 2. Connect to Pinecone
        pc = Pinecone(api_key=pinecone_key)
        index = pc.Index(index_name)

        # 3. Perform semantic vector query
        response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )

        matches = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])
        raw_matches = []
        for item in matches:
            if isinstance(item, dict):
                raw_matches.append(item)
            else:
                raw_matches.append({
                    "id": getattr(item, "id", ""),
                    "score": getattr(item, "score", 0.0),
                    "metadata": getattr(item, "metadata", {}) or {}
                })

        formatted_context = format_retrieved_context(raw_matches)
        if formatted_context:
            print(f"[RAG SUCCESS] Retrieved {len(raw_matches)} context documents from Pinecone index '{index_name}'")
        else:
            print(f"[RAG INFO] Pinecone index '{index_name}' returned 0 matching documents for query.")

        return formatted_context

    except Exception as err:
        print(f"[RAG WARN] RAG retrieval error: {err}. Continuing with agent analysis.")
        return ""


def retrieve_context_node(state: dict) -> dict:
    """
    LangGraph workflow node function that runs RAG retrieval and injects `retrieved_context` into state.
    """
    user_query = state.get("user_query", "")
    print(f"[RAG NODE] Initiating Pinecone context retrieval for query...")
    context = retrieve_context(user_query, top_k=5)
    return {"retrieved_context": context}
