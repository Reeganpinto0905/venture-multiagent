import os
import ssl
from typing import List, Optional
from dotenv import load_dotenv

try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

load_dotenv()

_embeddings_instance = None


def get_embedding(text: str) -> List[float]:
    """
    Generates embedding vector for query text using GoogleGenerativeAIEmbeddings (models/text-embedding-004).
    Fallback to google.generativeai direct embedding if needed.
    """
    global _embeddings_instance
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Neither GEMINI_API_KEY nor GOOGLE_API_KEY environment variable is set.")

    clean_text = str(text).strip() if text else ""
    if not clean_text:
        clean_text = "startup validation"

    if _embeddings_instance is None:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            _embeddings_instance = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=api_key
            )
        except Exception:
            _embeddings_instance = None

    if _embeddings_instance is not None:
        try:
            return _embeddings_instance.embed_query(clean_text)
        except Exception as err:
            print(f"[RAG EMBEDDINGS WARN] LangChain embedding failed: {err}. Trying direct genai fallback...")

    # Fallback directly using google.generativeai
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        res = genai.embed_content(
            model="models/text-embedding-004",
            content=clean_text,
            task_type="retrieval_query"
        )
        return res["embedding"]
    except Exception as err:
        raise RuntimeError(f"Failed to generate text embedding: {err}")
