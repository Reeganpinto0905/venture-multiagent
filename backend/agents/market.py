from dotenv import load_dotenv
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def market_agent(state):
    idea = state.get("user_query", "")

    prompt = f"""
Startup Idea & Context:
{idea}

Write a concise, high-rigor market analysis (150-200 words) covering demand signals,
target segment size, and growth trends. Rate the market opportunity 0-100 (100 = huge, fast-growing, underserved).

Return ONLY valid JSON:
{{"analysis": "...", "score": 65}}
"""

    raw_response = invoke_gemini(prompt, phase="validation:market")
    parsed = parse_json_response(raw_response, default={})

    analysis = parsed.get("analysis") or raw_response or "Market analysis is unavailable right now."
    score = parsed.get("score")
    score = score if isinstance(score, (int, float)) else 60

    scores = {**state.get("scores", {}), "market": int(score)}

    return {
        "market_analysis": analysis,
        "scores": scores,
    }
