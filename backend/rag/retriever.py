"""
Backward-Compatibility Shim: rag.retriever -> knowledge.retriever
Migrated from Pinecone vector RAG to Open Knowledge Format (OKF v0.2).
"""

from knowledge.retriever import (
    retrieve_context,
    retrieve_context_node,
    validate_knowledge_env,
    find_competitors,
    find_risks
)


def validate_rag_env() -> bool:
    """Compatibility alias for validate_knowledge_env."""
    return validate_knowledge_env()


__all__ = [
    "retrieve_context",
    "retrieve_context_node",
    "validate_rag_env",
    "validate_knowledge_env",
    "find_competitors",
    "find_risks"
]
