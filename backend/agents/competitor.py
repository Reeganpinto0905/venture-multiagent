"""
VentureIQ Competitor Agent.
Analyzes direct rivals, indirect substitutes, status-quo alternatives, and competitive whitespace.
Strictly distinguishes between user-provided startup evidence, external precedents, and general benchmarks.
"""

import re
from dotenv import load_dotenv
from tools.search_tool import search_web
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def competitor_agent(state):
    user_query = state.get("user_query", "")
    retrieved_context = state.get("competitor_context") or state.get("retrieved_context", "")

    clean_idea = user_query.split("\n")[0].strip() if user_query else "Startup Concept"

    search_query = f"{clean_idea} top competitors direct indirect status quo pricing positioning strategy"
    raw_results = search_web(search_query)

    # Token optimization: skip expensive LLM invocation when evidence is completely absent
    if "UNKNOWN / Insufficient Evidence" in retrieved_context and (not raw_results or "UNKNOWN" in raw_results):
        print(f"[COMPETITOR AGENT] Skipping LLM call: primary evidence is completely absent.")
        return {
            "competitor_analysis": f"• **Analysis Status:** UNKNOWN / Insufficient Evidence in primary OKF knowledge base or live search for {clean_idea}.\n• **Recommendation:** Identify primary incumbent competitors and existing alternatives.",
            "scores": {**state.get("scores", {}), "competitor": 50},
        }

    evidence_block = f"\nRetrieved Knowledge Base Evidence (OKF v0.2):\n{retrieved_context}\n" if retrieved_context else "\nRetrieved Knowledge Base Evidence: None provided.\n"

    synth_prompt = f"""
You are the Lead Competitor Strategy Analyst for VentureIQ (McKinsey level due diligence).
Analyze the competitive landscape for:
"{user_query}"

{evidence_block}

Live Web Research Findings:
{raw_results}

CRITICAL RULES:
1. STRICTLY SEPARATE:
   - **STARTUP EVIDENCE**: Features or claims explicitly stated in the submitted pitch.
   - **EXTERNAL COMPETITORS / PRECEDENTS**: Real rival companies discovered via search or OKF benchmarks (e.g. LeetCode, HackerRank, Stripe). Clearly mark them as external!
   - **MISSING COMPETITIVE DATA**: Explicitly state if competitor details are not in submitted pitch.
2. NEVER present external competitor features or benchmarks as properties of the user's startup.
3. NEVER invent fake competitor names. Use real companies from web research or state "To be identified".

Structure with clean bold headers:
• **Direct Competitors**: Actual rival companies, offerings, advantages, and vulnerabilities.
• **Indirect Competitors & Substitutes**: Alternative software, platforms, or manual solutions.
• **Status Quo Alternatives**: Current workarounds customers use today.
• **Competitive Whitespace & Gap**: Unaddressed customer pain points where startup can win.
• **Strategic Moat & Defensibility**: Moat durability (network effects, data flywheel, switching costs).
• **Strategic Verdict**: Direct, objective verdict on competitive position.

Return ONLY valid JSON format:
{{"analysis": "...", "score": 65}}
"""

    raw_response = invoke_gemini(synth_prompt, phase="validation:competitor")
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
        analysis = f"""• **Direct Competitors:** Established incumbents and specialized category players serving {clean_idea}.
• **Indirect Competitors & Substitutes:** Internal manual tools, spreadsheet workflows, or broad legacy software suites.
• **Status Quo Alternatives:** In-house manual processes or unautomated workflows.
• **Competitive Whitespace:** Unserved niche requiring targeted execution and lower friction onboarding.
• **Strategic Moat & Defensibility:** Defensibility hinges on speed of execution, proprietary data accumulation, and user switching costs.
• **Strategic Verdict:** Viable market entry if product differentiates clearly from incumbent feature sets."""

    score = parsed.get("score") if isinstance(parsed, dict) else None
    score = score if isinstance(score, (int, float)) else 60

    scores = {**state.get("scores", {}), "competition": int(score)}

    return {
        "competitor_analysis": analysis,
        "scores": scores,
    }
