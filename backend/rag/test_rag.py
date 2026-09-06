import os
import sys

# Ensure backend directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from rag.retriever import validate_rag_env, retrieve_context
from rag.embeddings import get_embedding


def test_rag_pipeline():
    print("==================================================")
    print("VENTUREIQ RAG & PINECONE DIAGNOSTIC TEST")
    print("==================================================")

    # 1. Environment Validation
    is_valid = validate_rag_env()
    print(f"RAG Environment Valid: {is_valid}")

    # 2. Test Embedding Generation
    test_query = "AI-powered interview preparation platform for college students"
    print(f"\n[TEST 1] Generating embedding vector for query: '{test_query}'...")
    try:
        vec = get_embedding(test_query)
        print(f"SUCCESS: Generated embedding vector with dimension {len(vec)}")
    except Exception as e:
        print(f"FAILED: Embedding generation error: {e}")

    # 3. Test Pinecone Retrieval
    print(f"\n[TEST 2] Executing Pinecone retrieval for query...")
    context = retrieve_context(test_query, top_k=5)
    
    if context:
        print("\n--- RETRIEVED EVIDENCE CONTEXT ---")
        print(context)
        print("----------------------------------")
    else:
        print("\n[NOTICE] RAG retrieval returned empty context (either missing API key, index empty, or offline). Fallback mode active.")

    print("\n==================================================")
    print("DIAGNOSTIC COMPLETE")
    print("==================================================")


if __name__ == "__main__":
    test_rag_pipeline()
