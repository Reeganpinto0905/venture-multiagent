import os
import sys
from dotenv import load_dotenv
from tavily import TavilyClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cache.cache_store import cache_store
from agents.llm_utils import increment_telemetry

load_dotenv()


def search_web(query: str, max_results: int = 5) -> str:
    clean_query = str(query).strip() if query else ""
    if not clean_query:
        return "No web search query provided."

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Web search is unavailable because TAVILY_API_KEY is not configured."

    cache_key = cache_store.compute_key("tavily_search", "web", clean_query)
    cached_result = cache_store.get(cache_key)
    if cached_result:
        print(f"[TAVILY CACHE HIT] Query: '{clean_query[:40]}...'")
        return str(cached_result)

    increment_telemetry("tavily_calls")
    try:
        response = TavilyClient(api_key=api_key).search(
            query=clean_query,
            max_results=max_results,
        )
    except Exception as exc:
        print(f"[TAVILY ERROR] Request unavailable: {type(exc).__name__}")
        return "Web search is temporarily unavailable; continuing with known information."

    results = []
    for item in response.get("results", []):
        results.append(
            f"• Title: {item.get('title', 'Untitled result')}\n"
            f"  Content: {item.get('content', '')}\n"
            f"  URL: {item.get('url', '')}"
        )

    formatted_output = "\n\n".join(results) or "No web search results were returned."
    cache_store.set(cache_key, formatted_output, ttl=86400)
    return formatted_output

