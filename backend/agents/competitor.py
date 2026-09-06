from dotenv import load_dotenv
from tools.search_tool import search_web
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def competitor_agent(state):
    user_query = state.get("user_query", "")
    retrieved_context = state.get("retrieved_context", "")

    # Perform web search
    search_query = f"{user_query} top competitors pricing features"
    raw_results = search_web(search_query)

    evidence_block = f"\nRetrieved Knowledge Base Evidence:\n{retrieved_context}\n" if retrieved_context else "\nRetrieved Knowledge Base Evidence: None provided.\n"

    synth_prompt = f"""
Startup Idea:
{user_query}
{evidence_block}
Live Web Search Results:
{raw_results}

Summarize the competitive landscape in 150-200 words: main competitors found,
their pricing/positioning, and where this startup can differentiate.

RAG & Synthesis Rules:
- Complement live web search results with retrieved knowledge base evidence.
- Differentiate empirical search findings from vector evidence vs analytical inference.
- Do not invent non-existent competitors or fake market stats.
- If evidence is insufficient, explicitly state the gap.

Rate the startup's competitive position 0-100 (100 = wide open space, low saturation).

Return ONLY valid JSON:
{{"analysis": "...", "score": 55}}
"""

    raw_response = invoke_gemini(synth_prompt, phase="validation:competitor")
    parsed = parse_json_response(raw_response, default={})

    analysis = parsed.get("analysis") or raw_results
    score = parsed.get("score")
    score = score if isinstance(score, (int, float)) else 55

    scores = {**state.get("scores", {}), "competition": int(score)}

    return {
        "competitor_analysis": analysis,
        "scores": scores,
    }
