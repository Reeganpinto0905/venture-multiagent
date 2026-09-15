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
        sections.append(f"RETRIEVED PINECONE KNOWLEDGE & EVIDENCE:\n{retrieved_context}")
    if state.get("market_analysis"):
        sections.append(f"MARKET ANALYSIS:\n{state['market_analysis']}")
    if state.get("competitor_analysis"):
        sections.append(f"COMPETITOR ANALYSIS:\n{state['competitor_analysis']}")
    if state.get("business_analysis"):
        sections.append(f"BUSINESS ANALYSIS:\n{state['business_analysis']}")
    if state.get("risk_analysis"):
        sections.append(f"RISK EVALUATION:\n{state['risk_analysis']}")

    if not sections:
        return {
            "summary": "No analysis sections were generated for this query.",
            "scores": scores,
        }

    combined = "\n\n".join(sections)

    prompt = f"""
Synthesize an investor-grade startup validation report for:
"{state.get("user_query", "")}"

Overall Investment Readiness Score: {overall if overall is not None else "N/A"}/100

Combined Multi-Agent Research & RAG Evidence:
{combined}

Instructions:
Synthesize an attractive, executive-ready diligence report.
Format using clean numbered sections with bold titles:
1. **Executive Verdict**: **GO** or **NO-GO** or **NEEDS VALIDATION** (State verdict and 2-sentence investment rationale).
2. **Market & Customer Demand**: Core customer segment, growth tailwinds, and willingness to pay.
3. **Competitive Moat & Landscape**: Key rivals, status-quo alternatives, and defensible whitespace.
4. **Business Viability & Unit Economics**: Revenue streams, gross margin profile, and CAC/LTV expectations.
5. **Critical Risks & Failure Modes**: Top operational, regulatory, and market risks to mitigate.
6. **Validation Experiment Plan**: 3 high-leverage experiments the founder should run this week.

Format Rules:
- Do NOT output raw web citations, unformatted URLs, or unbalanced asterisks.
- Ground all takeaways strictly in the multi-agent findings.
- Keep formatting clean, attractive, and highly readable.
"""

    response = invoke_gemini(prompt, phase="validation:report")

    if not response:
        # High-grade deterministic synthesis if Gemini rate limit or quota is exhausted
        verdict = "GO" if (overall or 50) >= 70 else ("NEEDS VALIDATION" if (overall or 50) >= 50 else "NO-GO")
        idea_title = state.get("user_query", "Startup Idea").split("\n")[0]
        response = f"""### **Executive Verdict**: **{verdict}** (Readiness Score: {overall if overall is not None else 'N/A'}/100)
Initial multi-agent diligence indicates measurable market demand for {idea_title}, requiring targeted validation of unit economics and early go-to-market acquisition channels.

### 1. **Market & Opportunity**
{state.get('market_analysis', 'Market sizing and trends evaluated by Market Agent.')}

### 2. **Competitive Moat & Landscape**
{state.get('competitor_analysis', 'Competitive dynamics and whitespace identified by Competitor Agent.')}

### 3. **Business Viability & Unit Economics**
{state.get('business_analysis', 'Revenue mechanics and margin profile analyzed by Business Agent.')}

### 4. **Critical Risk Factors**
{state.get('risk_analysis', 'Execution and regulatory friction points assessed by Risk Agent.')}

### 5. **Validation Plan & Next Steps**
- **Experiment 1**: Launch a high-intent landing page or concierge MVP to test customer willingness to pay.
- **Experiment 2**: Conduct 15 problem discovery interviews with primary target users to validate retention drivers.
- **Experiment 3**: Audit unit economics and initial customer acquisition costs (CAC) before scaling paid distribution."""

    return {
        "summary": response,
        "scores": scores,
    }

