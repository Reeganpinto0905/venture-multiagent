from dotenv import load_dotenv
import os

from tavily import TavilyClient

load_dotenv()

def search_web(query: str):
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Web search is unavailable because TAVILY_API_KEY is not configured."

    try:
        response = TavilyClient(api_key=api_key).search(
            query=query,
            max_results=5,
        )
    except Exception as exc:
        print(f"Tavily request unavailable: {type(exc).__name__}")
        return "Web search is temporarily unavailable; use only known information."

    results = []

    for item in response.get("results", []):
        results.append(
            f"""
Title: {item.get('title', 'Untitled result')}

Content:
{item.get('content', '')}

URL:
{item.get('url', '')}
"""
        )

    return "\n\n".join(results) or "No web search results were returned."
