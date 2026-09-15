from dotenv import load_dotenv
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def business_agent(state):
    user_query = state.get("user_query", "")
    retrieved_context = state.get("retrieved_context", "")
    profile = state.get("startup_profile", {})

    profile_summary = "\n".join(f"- {k}: {v}" for k, v in profile.items() if v)
    evidence_block = f"\nRetrieved Knowledge / Evidence:\n{retrieved_context}\n" if retrieved_context else ""

    prompt = f"""
Startup Idea & User Query:
{user_query}

Extracted Startup Profile:
{profile_summary or "None provided."}
{evidence_block}
Conduct an executive business viability and unit economics analysis.

Structure clearly with bold headers:
1. **Revenue Streams**: Primary pricing model (e.g. 15-20% commission fee, delivery fee) and secondary revenue (e.g. monthly campus pass, vendor ads).
2. **Unit Economics & Margins**: Estimated gross margins, CAC vs LTV expectations, and operational leverage from delivery density.
3. **Scalability & GTM Friction**: Key distribution bottlenecks (e.g. dorm access, seasonal breaks, partner lock-in).
4. **Financial Hypotheses to Test**: 2-3 critical assumptions regarding order frequency, batch efficiency, and retention.

Rules: Keep analysis punchy, structured, and under 250 words. Do not output raw citations or fake exact statistics.
Rate overall business model viability 0-100 (100 = highly viable/scalable).

Return ONLY valid JSON format:
{{"analysis": "...", "score": 75}}
"""

    raw_response = invoke_gemini(prompt, temperature=0.3, phase="validation:business")
    parsed = parse_json_response(raw_response, default={})

    analysis = parsed.get("analysis") or raw_response or "Business analysis unavailable."
    score = parsed.get("score")
    score = score if isinstance(score, (int, float)) else 60

    scores = {**state.get("scores", {}), "business": int(score)}

    return {
        "business_analysis": analysis,
        "scores": scores,
    }

