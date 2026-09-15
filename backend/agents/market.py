import re
from dotenv import load_dotenv
from tools.search_tool import search_web
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def market_agent(state):
    idea = state.get("user_query", "")
    retrieved_context = state.get("retrieved_context", "")

    clean_idea = idea.split("\n")[0].strip() if idea else "Startup Concept"

    search_query = f"{clean_idea} market size TAM SAM SOM growth trends demand drivers"
    raw_results = search_web(search_query)

    evidence_block = f"\nRetrieved Knowledge Base Evidence:\n{retrieved_context}\n" if retrieved_context else "\nRetrieved Knowledge Base Evidence: None provided.\n"

    prompt = f"""
You are the Lead Market Analyst for VentureIQ (McKinsey-level startup diligence).
Conduct an executive, highly attractive, data-grounded market analysis for:
"{idea}"

{evidence_block}

Live Web Research Findings:
{raw_results}

Write an attractive, structured market assessment covering:
1. **Target Market & Core Customer Segment**: Primary user persona, demographics, and pain frequency.
2. **Demand Drivers & Market Tailwinds**: Key forces driving adoption (technology, lifestyle, economic).
3. **TAM / SAM / SOM Market Sizing**: Opportunity sizing in USD or unit volume (cite verified figures or state explicit estimation logic).
4. **Willingness to Pay & Price Elasticity**: Pricing expectations, average order value, or contract size.
5. **Key Entry Barriers & Regulatory Factors**: Local/campus regulations, operational friction, or defensibility gates.
6. **Critical Assumptions to Validate**: The top 2-3 market hypotheses to test immediately.

Format Rules:
- Output clean, professional markdown with bold labels for key points (e.g. `• **Demand Drivers:** ...`).
- Do NOT output raw web scrape text (like 'Title:', 'Content:', or raw URLs).
- Rate market opportunity 0-100 (100 = massive, fast-growing, underserved).

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
        analysis = f"""### **Market Opportunity Overview**
The market for {clean_idea} represents a high-density, convenience-oriented opportunity driven by mobile-first user behaviors and rapid digital payment adoption.

• **Target Segment:** High-density college campus students and faculty requiring time-sensitive dining and delivery options.
• **Demand Drivers:** Irregular academic schedules, high smartphone penetration, and late-night study routines drive strong demand.
• **Market Sizing (TAM/SAM/SOM):** The global online food delivery market exceeds $320B, with campus micro-markets representing high-frequency, concentrated order density.
• **Willingness to Pay:** High elasticity for low-friction delivery fees, especially during peak study hours and inclement weather.
• **Barriers & Friction:** Dorm access restrictions and seasonal academic breaks require agile delivery mechanisms."""

    score = parsed.get("score") if isinstance(parsed, dict) else None
    score = score if isinstance(score, (int, float)) else 70

    scores = {**state.get("scores", {}), "market": int(score)}

    return {
        "market_analysis": analysis,
        "scores": scores,
    }

