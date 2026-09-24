"""
VentureIQ Market Agent.
Evaluates TAM/SAM/SOM market sizing, customer segments, demand drivers, and price elasticity.
Strictly distinguishes between user-provided startup evidence, external precedents, and general benchmarks.
"""

import re
from dotenv import load_dotenv
from tools.search_tool import search_web
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def market_agent(state):
    idea = state.get("user_query", "")
    retrieved_context = state.get("market_context") or state.get("retrieved_context", "")
    profile = state.get("startup_profile", {})

    clean_idea = idea.split("\n")[0].strip() if idea else "Startup Concept"
    profile_summary = "\n".join(f"- {k}: {v}" for k, v in profile.items() if v)

    search_query = f"{clean_idea} market size TAM SAM SOM growth trends demand drivers"
    raw_results = search_web(search_query)

    evidence_block = f"\nRetrieved Knowledge Base Evidence (OKF v0.2):\n{retrieved_context}\n" if retrieved_context else "\nRetrieved Knowledge Base Evidence: None provided.\n"

    prompt = f"""
You are the Lead Market Analyst at VentureIQ (McKinsey/Sequoia level diligence).
Conduct an executive, evidence-grounded market analysis for:
"{idea}"

Submitted Startup Context & Profile:
{profile_summary or "No extra profile parameters supplied by founder."}

{evidence_block}

Live Web Research Findings:
{raw_results}

CRITICAL RULES:
1. STRICTLY SEPARATE:
   - **STARTUP EVIDENCE**: Facts explicitly stated in the submitted pitch/profile.
   - **EXTERNAL PRECEDENT**: Historical case studies from retrieved knowledge (e.g. Airbnb, Canva, Stripe). Mark clearly as external!
   - **GENERAL INDUSTRY BENCHMARK**: Standard industry metrics (e.g. general TAM estimates).
   - **MISSING EVIDENCE / UNKNOWN**: Explicitly state any market data not provided in the user input.
2. NEVER claim an external benchmark or precedent is a property of the user's startup.
3. NEVER invent fake TAM/SAM/SOM figures or customer claims for the user's startup.
4. If TAM/SAM/SOM or pricing is not specified in the pitch, explicitly write "Not provided in submitted evidence. Estimated general benchmark: ..."

Structure with clean bold headers:
• **Target Customer & Persona**: Segment identified in startup pitch (or state if missing).
• **Demand Drivers & Market Tailwinds**: Forces driving customer adoption for this specific product.
• **Market Sizing (TAM / SAM / SOM)**: User figures if provided, or explicit general industry estimation logic.
• **Willingness to Pay & Price Elasticity**: Founder's pricing model or industry comparable.
• **Market Entry Barriers & Regulatory Friction**: Specific friction points for this sector.
• **Evidence Gaps & Market Assumptions**: Top hypotheses needing validation.

Return ONLY valid JSON format:
{{"analysis": "...", "score": 75}}
"""

    raw_response = invoke_gemini(prompt, phase="validation:market")
    parsed = parse_json_response(raw_response, default={})

    analysis = None
    if isinstance(parsed, dict) and parsed.get("analysis"):
        analysis = parsed.get("analysis")
    elif raw_response and len(raw_response.strip()) > 30:
        cleaned = raw_response.strip()
        cleaned = re.sub(r'^\s*\{\s*"analysis"\s*:\s*"?', '', cleaned)
        cleaned = re.sub(r'"?\s*,\s*"score".*$', '', cleaned, flags=re.DOTALL)
        analysis = cleaned

    if not analysis:
        # Domain-neutral objective fallback (No hardcoded food delivery!)
        analysis = f"""• **Target Customer & Persona:** Target user segment based on submitted pitch for {clean_idea}. Specific demographic breakdown not fully specified in input.
• **Demand Drivers:** Technology adoption and operational efficiency demand.
• **Market Sizing (TAM / SAM / SOM):** Specific TAM/SAM metrics not provided in submitted input. General industry market size requires validation.
• **Willingness to Pay:** Monetization model to be confirmed via customer interviews.
• **Barriers & Friction:** Incumbent adoption and go-to-market distribution gates.
• **Evidence Gaps & Market Assumptions:** Validate primary target persona and willingness to pay."""

    score = parsed.get("score") if isinstance(parsed, dict) else None
    score = score if isinstance(score, (int, float)) else 70

    scores = {**state.get("scores", {}), "market": int(score)}

    return {
        "market_analysis": analysis,
        "scores": scores,
    }
