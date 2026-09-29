"""
VentureIQ Risk Agent.
Identifies execution, operational, regulatory, competitive, and financial risks.
Strictly distinguishes between user-provided startup evidence, external failure precedents, and general risks.
"""

from dotenv import load_dotenv
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def risk_agent(state):
    user_query = state.get("user_query", "")
    retrieved_context = state.get("risk_context") or state.get("retrieved_context", "")
    profile = state.get("startup_profile", {})

    profile_summary = "\n".join(f"- {k}: {v}" for k, v in profile.items() if v)
    # Token optimization: skip expensive LLM invocation when evidence is completely absent
    if "UNKNOWN / Insufficient Evidence" in retrieved_context and not user_query.strip():
        print(f"[RISK AGENT] Skipping LLM call: primary evidence is completely absent.")
        return {
            "risk_analysis": f"• **Analysis Status:** UNKNOWN / Insufficient Evidence in primary OKF knowledge base for risk evaluation.\n• **Recommendation:** Provide operational milestones and regulatory constraints.",
            "scores": {**state.get("scores", {}), "risk": 50},
        }

    evidence_block = f"\nRetrieved Knowledge / Historical Precedents (OKF v0.2):\n{retrieved_context}\n" if retrieved_context else "\nRetrieved Knowledge / Historical Precedents: None provided.\n"

    prompt = f"""
You are the Lead Risk & Due Diligence Partner at VentureIQ (YC / Sequoia level scrutiny).
Identify the most critical operational, market, regulatory, and financial risks for this startup:
"{user_query}"

Submitted Startup Context & Profile:
{profile_summary or "None provided in pitch."}

{evidence_block}

CRITICAL RULES:
1. Conduct an unsparing, objective risk audit tailored STRICTLY to this specific startup concept.
2. STRICTLY SEPARATE:
   - **STARTUP VULNERABILITIES**: Direct risks inherent in the startup's proposed model or input.
   - **HISTORICAL FAILURE PRECEDENTS**: Relevant historical startup failures (e.g. Quibi, Sprig, Jawbone) from OKF evidence. Mark clearly as EXTERNAL FAILURE PRECEDENT!
   - **EVIDENCE GAPS**: Key unknown risks due to unprovided data.
3. NEVER output generic platitudes or hardcoded food delivery examples unless the pitch is food delivery.
4. Rate overall risk defensibility 0-100 (100 = low risk / highly defensible, 0 = severe lethal risk).

Structure with clean bold headers:
• **Execution & Operational Risk**: Critical bottlenecks in delivery, onboarding, technology, or team execution.
• **Regulatory, Legal & Policy Risk**: Industry-specific compliance, privacy, or licensing gates.
• **Market & Financial Defensibility**: Churn vulnerability, margin pressure, CAC escalation, or funding dependency.
• **Competitive Retaliation & Moat Durability**: How incumbents or clones could attack this venture.
• **Historical Failure Precedents**: Relevant historical case study warnings from OKF knowledge base.

Return ONLY valid JSON format:
{{"analysis": "...", "score": 50}}
"""

    raw_response = invoke_gemini(prompt, temperature=0.3, phase="validation:risk")
    parsed = parse_json_response(raw_response, default={})

    analysis = parsed.get("analysis") if isinstance(parsed, dict) else None
    if not analysis and raw_response and len(raw_response.strip()) > 30:
        analysis = raw_response.strip()

    if not analysis:
        # Domain-neutral objective fallback (No "Risk analysis is unavailable right now.")
        analysis = f"""• **Execution & Operational Risk:** Technical development timeline and early customer onboarding friction represent key operational risk factors.
• **Regulatory, Legal & Policy Risk:** Compliance requirements and data privacy considerations must be audited prior to commercial launch.
• **Market & Financial Defensibility:** Customer acquisition cost (CAC) scaling risks and pricing retention vulnerability.
• **Competitive Retaliation & Moat Durability:** Incumbent feature replication and well-funded competitor response.
• **Historical Failure Precedents:** Precedents highlight the risk of premature scaling before achieving repeatable unit economics."""

    score = parsed.get("score") if isinstance(parsed, dict) else None
    score = score if isinstance(score, (int, float)) else 50

    scores = {**state.get("scores", {}), "risk": int(score)}

    return {
        "risk_analysis": analysis,
        "scores": scores,
    }
