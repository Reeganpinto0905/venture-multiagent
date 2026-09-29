import os
import sys
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from tavily import TavilyClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cache.cache_store import cache_store
from agents.llm_utils import increment_telemetry

load_dotenv()


def search_web(query: str, max_results: int = 3, max_retries: int = 2) -> str:
    clean_query = str(query).strip() if query else ""
    if not clean_query:
        return "UNKNOWN / Insufficient Evidence: No search query provided."

    # 1. Check existing search cache first
    cache_key = cache_store.compute_key("tavily_search", "web", clean_query)
    cached_result = cache_store.get(cache_key)
    if cached_result:
        print(f"[TAVILY CACHE HIT] Query: '{clean_query[:40]}...'")
        return str(cached_result)

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("[TAVILY UNAVAILABLE] TAVILY_API_KEY not configured.")
        return ""

    increment_telemetry("tavily_calls")

    # 2. Retry with exponential backoff for temporary failures/rate limits
    response = None
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            client = TavilyClient(api_key=api_key)
            response = client.search(
                query=clean_query,
                max_results=max_results,
            )
            if response:
                break
        except Exception as exc:
            last_err = exc
            if attempt < max_retries:
                backoff_sec = 0.5 * (2 ** attempt)
                print(f"[TAVILY RETRY] Attempt {attempt + 1} failed ({type(exc).__name__}). Retrying in {backoff_sec:.1f}s...")
                time.sleep(backoff_sec)
            else:
                print(f"[TAVILY EXHAUSTED] All {max_retries + 1} attempts failed: {type(exc).__name__}")

    if not response or not response.get("results"):
        return ""

    fetch_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []
    for item in response.get("results", [])[:max_results]:
        snippet = str(item.get("content", "")).strip()
        if len(snippet) > 250:
            snippet = snippet[:250].rsplit(" ", 1)[0] + "..."
        url = item.get("url", "N/A")
        title = item.get("title", "Untitled Web Result")
        results.append(
            f"• [Live Web Evidence | Fetched: {fetch_time}]\n"
            f"  Title: {title}\n"
            f"  Content: {snippet}\n"
            f"  Source URL: {url}"
        )

    formatted_output = "\n\n".join(results)
    if formatted_output:
        cache_store.set(cache_key, formatted_output, ttl=86400)
    return formatted_output


