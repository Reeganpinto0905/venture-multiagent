from dotenv import load_dotenv
from agents.llm_utils import invoke_gemini

load_dotenv()


def report_agent(state):
    scores = state.get("scores", {})
    sub_scores = [v for v in scores.values() if isinstance(v, (int, float))]
    overall = round(sum(sub_scores) / len(sub_scores)) if sub_scores else None

    if overall is not None:
        scores = {**scores, "overall": overall}

    sections = []
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
Write an executive summary for a startup validation report.

Startup idea:
{state.get("user_query", "")}

Overall score: {overall if overall is not None else "N/A"}/100

Analysis sections:
{combined}

Write 150-220 words of plain prose (no headers, no bullet lists): open with the overall verdict,
name the single strongest signal and single biggest concern, and close with one concrete next step
the founder should take this week.
"""

    response = invoke_gemini(prompt, phase="validation:report")

    return {
        "summary": response or f"Overall opportunity score: {overall if overall is not None else 'N/A'}/100. Review the analysis sections and validate the largest assumptions with prospective customers this week.",
        "scores": scores,
    }
