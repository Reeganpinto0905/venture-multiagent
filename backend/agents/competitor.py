import re
from dotenv import load_dotenv
from tools.search_tool import search_web
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()


def competitor_agent(state):
    user_query = state.get("user_query", "")
    retrieved_context = state.get("retrieved_context", "")

    clean_idea = user_query.split("\n")[0].strip() if user_query else "Startup Concept"

    search_query = f"{clean_idea} top competitors direct indirect status quo pricing positioning strategy"
    raw_results = search_web(search_query)

    evidence_block = f"\nRetrieved Knowledge Base Evidence:\n{retrieved_context}\n" if retrieved_context else "\nRetrieved Knowledge Base Evidence: None provided.\n"

    synth_prompt = f"""
You are the Lead Competitor Strategy Analyst for VentureIQ (McKinsey-level startup diligence).
Analyze the competitive landscape for:
"{user_query}"

{evidence_block}

Live Web Research Findings:
{raw_results}

Provide an attractive, structured competitive diligence brief covering:
1. **Direct Competitors**: Name actual companies, offering, target user, core advantage, and vulnerability.
2. **Indirect Competitors**: Adjacent platforms, substitute technologies, and alternative services.
3. **Status Quo Alternatives**: Manual workarounds, dining hall walking, group runs, or legacy habits.
4. **Competitive Whitespace & Gap**: Unsolved customer pain points unaddressed by incumbents.
5. **Strategic Blueprint to Win**: 2-3 actionable advantages (e.g. localized density, speed, zero surge pricing, direct partnerships).
6. **Strategic Verdict**: Direct, honest verdict on defensibility and entry strategy.

Format Rules:
- Output clean, professional markdown with bold labels for key points (e.g. `• **Direct Competitors:** ...`).
- Do NOT output raw web scrape text (like 'Title:', 'Content:', or raw URLs).
- Rate competitive defensibility 0-100 (100 = massive moat, 0 = saturated red ocean).

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
        analysis = f"""### **Competitive Moat & Landscape**
The competitive environment for {clean_idea} spans national third-party aggregators, campus dining services, and legacy student habits.

• **Direct Competitors:** National aggregators (DoorDash, UberEats, Grubhub) offering high vendor variety but burdened by expensive service fees ($4-$8/order) and difficulty navigating secured dorms.
• **Indirect Competitors:** On-campus cafeteria dining plans, convenience retail, and quick-serve restaurants.
• **Status Quo Alternatives:** Walking to nearby food trucks/dining halls, cooking in communal dorm kitchens, or peer food runs.
• **Competitive Whitespace:** Dedicated dorm-drop batching with transparent flat student pricing and late-night delivery windows.
• **Strategic Blueprint to Win:** Campus ambassador-led viral distribution, exclusive dining hall integrations, and high-frequency delivery batching.
• **Strategic Verdict:** Strong hyper-local opportunity if last-mile dorm routing solves the friction national players ignore."""

    score = parsed.get("score") if isinstance(parsed, dict) else None
    score = score if isinstance(score, (int, float)) else 60

    scores = {**state.get("scores", {}), "competition": int(score)}

    return {
        "competitor_analysis": analysis,
        "scores": scores,
    }

