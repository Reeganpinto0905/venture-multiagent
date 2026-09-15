from dotenv import load_dotenv
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def risk_agent(state):
    user_query = state.get("user_query", "")
    retrieved_context = state.get("retrieved_context", "")
    profile = state.get("startup_profile", {})

    profile_summary = "\n".join(f"- {k}: {v}" for k, v in profile.items() if v)
    evidence_block = f"\nRetrieved Knowledge / Evidence:\n{retrieved_context}\n" if retrieved_context else "\nRetrieved Knowledge / Evidence: None provided.\n"

    prompt = f"""
Startup Idea & Context:
{user_query}

Extracted Startup Profile:
{profile_summary or "None provided."}
{evidence_block}
Identify top startup risks and mitigation strategies.

Provide 1-2 concise bullet points per category:
• **Execution Risk**: Operational bottlenecks, driver/courier reliability, dorm security access.
• **Regulatory & Campus Policy**: University commercial solicitation rules, health inspections, vehicle restrictions.
• **Seasonal & Financial Risk**: Revenue drops during summer/winter breaks, order density volatility.
• **Competitive Retaliation**: Incumbent aggregators cutting local fees or exclusivity deals with campus vendors.

Rules: Ground in realistic startup dynamics (under 180 words). Do not output raw scrape strings.
Rate overall risk defensibility 0-100 (100 = very LOW risk / highly safe, 0 = very HIGH risk).

Return ONLY valid JSON format:
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
