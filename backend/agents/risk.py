from dotenv import load_dotenv
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def risk_agent(state):
    user_query = state.get("user_query", "")

    prompt = f"""
Startup Idea & Context:
{user_query}

Identify top risks (market, execution, regulatory, financial, competitive).
Provide 1-2 concise bullet points per applicable category (keep total under 180 words).
Rate overall risk exposure 0-100 (100 = very LOW risk / safe, 0 = very HIGH risk).

Return ONLY valid JSON:
{{"analysis": "...", "score": 50}}
"""

    raw_response = invoke_gemini(prompt, temperature=0.3, phase="validation:risk")
    parsed = parse_json_response(raw_response, default={})

    analysis = parsed.get("analysis") or raw_response or "Risk analysis is unavailable right now."
    score = parsed.get("score")
    score = score if isinstance(score, (int, float)) else 50

    scores = {**state.get("scores", {}), "risk": int(score)}

    return {
        "risk_analysis": analysis,
        "scores": scores,
    }
