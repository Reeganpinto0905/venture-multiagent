from dotenv import load_dotenv
from agents.llm_utils import invoke_gemini

load_dotenv()


def report_agent(state):
    scores = state.get("scores", {})
    sub_scores = [v for v in scores.values() if isinstance(v, (int, float))]
    overall = round(sum(sub_scores) / len(sub_scores)) if sub_scores else None

    if overall is not None:
        scores = {**scores, "overall": overall}

    retrieved_context = state.get("retrieved_context", "")

    sections = []
    if retrieved_context:
        sections.append(f"RETRIEVED KNOWLEDGE & EVIDENCE:\n{retrieved_context}")
    if state.get("market_analysis"):
        sections.append(f"MARKET ANALYSIS:\n{state['market_analysis']}")
    if state.get("competitor_analysis"):
        sections.append(f"COMPETITOR ANALYSIS:\n{state['competitor_analysis']}")
    if state.get("business_analysis"):
        sections.append(f"BUSINESS ANALYSIS:\n{state['business_analysis']}")
    if state.get("risk_analysis"):
        sections.append(f"RISK ANALYSIS:\n{state['risk_analysis']}")

    if not sections:
        return {
            "summary": "No analysis sections were generated for this query.",
            "scores": scores,
        }

    combined = "\n\n".join(sections)

    prompt = f"""
Write an executive summary synthesis for a startup validation report.

Startup idea:
{state.get("user_query", "")}

Overall Validation Score: {overall if overall is not None else "N/A"}/100

Combined Analysis & Evidence:
{combined}

Instructions:
Synthesize the findings explaining WHY VentureIQ reached its conclusion. Use the following structured outline:
- VERDICT (1 sentence overall verdict)
- Market & Customer Strength (1-2 sentences)
- Competitive Moat & Positioning (1-2 sentences)
- Business Viability & Revenue Model (1-2 sentences)
- Major Risks & Execution Exposure (1-2 sentences)
- Supporting Evidence & Assumptions (Highlight key evidence vs assumptions)
- Recommended Validation Steps (1-2 next actions for the founder)

Rules:
- Do not fabricate numerical market statistics.
- Clearly ground conclusions on retrieved evidence and agent evaluations.

Keep the summary clear, high-rigor, and professional.
"""

    response = invoke_gemini(prompt, phase="validation:report")

    return {
        "summary": response or f"Overall opportunity score: {overall if overall is not None else 'N/A'}/100. Review the analysis sections and validate the largest assumptions with prospective customers this week.",
        "scores": scores,
    }
