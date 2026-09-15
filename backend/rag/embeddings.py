import json
import os
import urllib.request
import urllib.error
from typing import List
from dotenv import load_dotenv

load_dotenv()


def get_embedding(text: str) -> List[float]:
    """
    Generates embedding vector for query text using direct HTTPS REST (models/gemini-embedding-001).
    Fast, reliable, and completely eliminates gRPC / DLL initialization hangs on Windows.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Neither GEMINI_API_KEY nor GOOGLE_API_KEY environment variable is set.")

    clean_text = str(text).strip() if text else ""
    if not clean_text:
        clean_text = "startup validation"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
    payload = json.dumps({
        "model": "models/gemini-embedding-001",
        "content": {
            "parts": [{"text": clean_text[:2000]}]
        },
        "outputDimensionality": 1024
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    import ssl
    ctx = ssl.create_default_context()
    try:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    except Exception:
        pass

    try:
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            embedding_values = data.get("embedding", {}).get("values", [])
            if embedding_values:
                return embedding_values
            raise ValueError("No embedding values returned in response.")
    except Exception as exc:
        print(f"[RAG EMBEDDINGS WARN] REST embedding failed: {exc}")
        return [0.0] * 1024
