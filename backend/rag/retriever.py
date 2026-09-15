import os
import sys
from typing import Dict, Any, List
from dotenv import load_dotenv

from rag.embeddings import get_embedding

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cache.cache_store import cache_store
from agents.llm_utils import increment_telemetry

load_dotenv()

DEFAULT_INDEX_NAME = "ventureiq-index"
DEFAULT_NAMESPACE = "ventureiq-v2"
DEFAULT_HOST = "ventureiq-index-mi1o3hi.svc.aped-4627-b74a.pinecone.io"


def validate_rag_env() -> bool:
    """
    Validates presence of Pinecone & Gemini environment variables without exposing secret values.
    Returns True if fully configured, False otherwise.
    """
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX", DEFAULT_INDEX_NAME)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    missing = []
    if not PINECONE_API_KEY:
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
        company = metadata.get("company", "")

        text = (
            metadata.get("text")
            or metadata.get("content")
            or metadata.get("page_content")
            or metadata.get("body")
            or metadata.get("summary")
            or str(metadata)
        )
        source = metadata.get("source") or metadata.get("title") or f"Doc #{idx}"
        header = f"• [Verified Evidence #{idx} | Company: {company} | Source: {source} | Rel: {score:.3f}]" if company else f"• [Verified Evidence #{idx} | Source: {source} | Rel: {score:.3f}]"

        formatted_entry = f"{header}\n  {text.strip()}"
        documents.append(formatted_entry)

    return "\n\n".join(documents)


def _query_pinecone_rest(api_key: str, host: str, vector: List[float], top_k: int = 5, namespace: str = DEFAULT_NAMESPACE) -> List[Dict[str, Any]]:
    """
    Direct HTTPS REST query to Pinecone. Fast, lightweight, and robust against Windows SSL cert verification issues.
    """
    import urllib3
    import requests
    urllib3.disable_warnings()

    url = f"https://{host}/query"
    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "vector": vector,
        "topK": top_k,
        "includeMetadata": True,
        "namespace": namespace
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("matches", [])
    else:
        print(f"[RAG REST WARN] Pinecone REST query returned HTTP {resp.status_code}: {resp.text}")
        return []


def retrieve_context(query: str, top_k: int = 5) -> str:
    """
    Connects to Pinecone index, performs semantic similarity retrieval for the given query,
    and returns formatted evidence. Fails gracefully if Pinecone is unreachable or unconfigured.
    """
    clean_query = str(query).strip() if query else ""
    if not clean_query:
        return ""

    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX", DEFAULT_INDEX_NAME)
    namespace = os.getenv("PINECONE_NAMESPACE", DEFAULT_NAMESPACE)
    host = os.getenv("PINECONE_HOST", DEFAULT_HOST)

    if not PINECONE_API_KEY:
        print("[RAG WARN] PINECONE_API_KEY not found. Continuing with agent analysis.")
        return ""

    cache_key = cache_store.compute_key("pinecone_rag", index_name, namespace, clean_query)
    cached_res = cache_store.get(cache_key)
    if cached_res:
        print(f"[RAG CACHE HIT] Query: '{clean_query[:40]}...'")
        return str(cached_res)

    increment_telemetry("pinecone_calls")
    try:
        # 1. Generate query embedding
        query_vector = get_embedding(clean_query)

        # 2. Query Pinecone via REST (direct & resilient to Windows SSL issues)
        raw_matches = _query_pinecone_rest(PINECONE_API_KEY, host, query_vector, top_k=top_k, namespace=namespace)

        # 3. If REST returned empty, try official SDK as fallback
        if not raw_matches:
            try:
                from pinecone import Pinecone
                pc = Pinecone(api_key=PINECONE_API_KEY)
                index = pc.Index(index_name)
                response = index.query(
                    vector=query_vector,
                    top_k=top_k,
                    include_metadata=True,
                    namespace=namespace
                )
                matches = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])
                for item in matches:
                    if isinstance(item, dict):
                        raw_matches.append(item)
                    else:
                        raw_matches.append({
                            "id": getattr(item, "id", ""),
                            "score": getattr(item, "score", 0.0),
                            "metadata": getattr(item, "metadata", {}) or {}
                        })
            except Exception as sdk_err:
                print(f"[RAG SDK WARN] Pinecone SDK fallback failed: {sdk_err}")

        formatted_context = format_retrieved_context(raw_matches)
        if formatted_context:
            print(f"[RAG SUCCESS] Retrieved {len(raw_matches)} context documents from Pinecone index '{index_name}' (namespace '{namespace}')")
            cache_store.set(cache_key, formatted_context, ttl=86400)
        else:
            print(f"[RAG INFO] Pinecone index '{index_name}' returned 0 matching documents for query.")

        return formatted_context

    except Exception as err:
        print(f"[RAG WARN] RAG retrieval error: {err}. Continuing gracefully.")
        return ""


def retrieve_context_node(state: dict) -> dict:
    """
    LangGraph workflow node function that runs RAG retrieval and injects `retrieved_context` into state.
    """
    user_query = state.get("user_query", "")
    print(f"[RAG NODE] Initiating Pinecone context retrieval for query: {user_query[:50]}...")
    context = retrieve_context(user_query, top_k=5)
    return {"retrieved_context": context}

