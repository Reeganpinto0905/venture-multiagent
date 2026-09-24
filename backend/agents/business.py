"""
VentureIQ Business Agent.
Evaluates monetization mechanics, revenue streams, unit economics, and scalability.
Strictly distinguishes between user-provided startup evidence, external precedents, and general benchmarks.
"""

from dotenv import load_dotenv
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def business_agent(state):
    user_query = state.get("user_query", "")
    retrieved_context = state.get("business_context") or state.get("retrieved_context", "")
    profile = state.get("startup_profile", {})

    profile_summary = "\n".join(f"- {k}: {v}" for k, v in profile.items() if v)
    evidence_block = f"\nRetrieved Knowledge Base Evidence (OKF v0.2):\n{retrieved_context}\n" if retrieved_context else "\nRetrieved Knowledge Base Evidence: None provided.\n"

    prompt = f"""
You are the Lead Business Viability Analyst for VentureIQ (Sequoia level diligence).
Analyze the business model, unit economics, and monetization strategy for:
"{user_query}"

Submitted Startup Profile:
{profile_summary or "None provided in pitch."}

{evidence_block}

CRITICAL RULES:
1. STRICTLY SEPARATE:
   - **STARTUP EVIDENCE**: Revenue metrics or pricing models explicitly stated in the pitch.
   - **GENERAL BENCHMARKS**: Standard industry economics (e.g. "Typical SaaS Gross Margins: 70-85%"). Label explicitly as GENERAL BENCHMARK!
   - **EXTERNAL PRECEDENT**: Historical business models from OKF knowledge (e.g., Stripe, Airbnb). Mark clearly as external!
   - **MISSING FINANCIAL EVIDENCE**: Explicitly state if margins, CAC, LTV, or pricing are not provided in the pitch.
2. NEVER present general industry benchmarks (like "SaaS margins 75-88%" or "NRR >130%") as actual figures for the user's startup unless stated by the user.
3. If financial numbers are missing, explicitly state: "Not provided in submitted evidence."

Structure with clean bold headers:
• **Revenue Streams & Pricing**: Founder's proposed monetization model (or "Not provided in submitted evidence").
• **Unit Economics & Margins**: Analysis of gross margin expectations, CAC vs LTV dynamics, and payback period.
• **Scalability & Distribution Friction**: Channel friction, customer acquisition hurdles, or operational bottlenecks.
• **Financial Hypotheses to Validate**: Critical unit-economic assumptions to test.

Return ONLY valid JSON format:
{{"analysis": "...", "score": 75}}
"""

    raw_response = invoke_gemini(prompt, temperature=0.3, phase="validation:business")
    parsed = parse_json_response(raw_response, default={})

    analysis = parsed.get("analysis") if isinstance(parsed, dict) else None
    if not analysis and raw_response and len(raw_response.strip()) > 30:
        analysis = raw_response.strip()

    if not analysis:
        # Domain-neutral objective fallback
        analysis = f"""• **Revenue Streams & Pricing:** Proposed pricing structure not fully detailed in submitted pitch. Monetization strategy requires formal pricing validation.
• **Unit Economics & Margins:** Gross margin profile depends on direct cost structure and variable fulfillment/acquisition costs. General benchmarks indicate business model feasibility, but startup-specific CAC/LTV remains to be measured.
• **Scalability & Distribution Friction:** Customer acquisition costs and sales cycle length represent key scaling friction points.
• **Financial Hypotheses to Validate:** Conduct willingness-to-pay testing and calculate initial CAC payback period."""

    score = parsed.get("score") if isinstance(parsed, dict) else None
    score = score if isinstance(score, (int, float)) else 60

    scores = {**state.get("scores", {}), "business": int(score)}

    return {
        "business_analysis": analysis,
        "scores": scores,
    }
