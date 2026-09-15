from dotenv import load_dotenv
from tools.search_tool import search_web
from rag.retriever import retrieve_context
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()

VALID_AGENTS = {"market", "competitor", "business", "risk"}
MAX_QUESTIONS = 4

# 20+ Dimension Persistent Startup Intelligence Profile
DEFAULT_STARTUP_PROFILE = {
    "idea": None,
    "problem": None,
    "target_customer": None,
    "geography": None,
    "industry": None,
    "existing_alternatives": None,
    "competitors": None,
    "pain_points": None,
    "proposed_solution": None,
    "uvp": None,
    "differentiation": None,
    "business_model": None,
    "pricing": None,
    "willingness_to_pay": None,
    "acquisition_distribution": None,
    "market": None,
    "regulatory_considerations": None,
    "risks": None,
    "validation_evidence": None,
    "assumptions": None,
    "open_critical_questions": None,
}

OUT_OF_SCOPE_MESSAGE = (
    "⚠️ This is outside the scope of your startup analysis. Please ask something related to your idea, customers, problem, solution, market, competitors, business model, or validation."
)

OFF_TOPIC_PATTERNS = [
    "buil me a website", "build me a website", "make me a website", "create a website", "build a website",
    "buil me an app", "build me an app", "make me an app", "create an app", "build an app",
    "write code", "write python", "write a script", "code me a", "create a script", "write a program",
    "tell me a joke", "what is the capital", "who is the president", "solve this math", "solve this equation",
    "do my homework", "what is the weather", "write an essay"
]


def _is_off_topic_query(text: str) -> bool:
    lower = text.lower().strip()
    return any(pat in lower for pat in OFF_TOPIC_PATTERNS)


def _format_profile_summary(profile: dict) -> str:
    items = [f"{k.replace('_', ' ').title()}: {v}" for k, v in profile.items() if v]
    return "; ".join(items) if items else "No structured profile established yet."


def _detect_intent(msg: str) -> str:
    lower = msg.lower()
    comp_kws = ["competitor", "competition", "rival", "versus", "vs ", "who are my competitors", "market leader"]
    market_kws = ["market", "tam", "sam", "som", "market size", "sizing", "demand", "cagr", "growth rate"]
    
    if any(k in lower for k in comp_kws):
        return "competitor"
    if any(k in lower for k in market_kws):
        return "market"
    if "germany" in lower or "dealer" in lower or "industry" in lower:
        return "research"
    return "conversational"


def supervisor_chat(state: dict, user_message: str) -> dict:
    """
    Runs one turn of the VentureIQ analyst conversation using persistent startup profile,
    intent-based research mode, and McKinsey-style Answer-First responses.
    """
    conversation = state.get("conversation", [])
    profile = {**DEFAULT_STARTUP_PROFILE, **state.get("startup_profile", {}), **state.get("idea_context", {})}
    questions_asked = state.get("questions_asked", 0)

    clean_msg = user_message.strip()
    conversation.append({"role": "user", "content": clean_msg})

    if _is_off_topic_query(clean_msg):
        print(f"[SUPERVISOR] Flagged off-topic input: '{clean_msg}'")
        conversation.append({"role": "assistant", "content": OUT_OF_SCOPE_MESSAGE})
        initial_query = state.get("user_query") or (conversation[0]["content"] if len(conversation) > 0 else clean_msg)
        return {
            "conversation": conversation,
            "idea_context": profile,
            "startup_profile": profile,
            "questions_asked": questions_asked,
            "ready_for_analysis": False,
            "reply": OUT_OF_SCOPE_MESSAGE,
            "choices": state.get("choices", []),
            "user_query": initial_query,
            "mode": "off_topic",
        }

    lower_msg = clean_msg.lower()
    intent = _detect_intent(clean_msg)

    # Fast check for explicit validation triggers
    explicit_trigger = any(
        kw in lower_msg
        for kw in ["start validation", "analyze now", "ready for analysis", "run analysis", "validate idea", "ready to validate"]
    )
    force_ready = questions_asked >= MAX_QUESTIONS or explicit_trigger

    if force_ready:
        reply = "VentureIQ has collected sufficient context to validate this idea."
        conversation.append({"role": "assistant", "content": reply})
        compiled_query = state.get("user_query") or clean_msg
        if profile:
            details = _format_profile_summary(profile)
            compiled_query = f"{compiled_query}\n\nStructured Profile: {details}"

        return {
            "conversation": conversation,
            "idea_context": profile,
            "startup_profile": profile,
            "questions_asked": questions_asked,
            "ready_for_analysis": True,
            "reply": reply,
            "choices": [],
            "user_query": compiled_query,
            "mode": "validation",
        }

    # If user asks a competitor/market query OR research intent: ALWAYS research & answer first!
    if intent in ("competitor", "market", "research"):
        print(f"[SUPERVISOR] Triggering RESEARCH MODE for intent '{intent}': '{clean_msg}'")
        
        search_query = f"{clean_msg} competitors market size companies alternatives"
        web_findings = search_web(search_query, max_results=5)
        rag_context = retrieve_context(clean_msg, top_k=3)

        evidence_block = f"\nRetrieved Knowledge Base Evidence:\n{rag_context}\n" if rag_context else ""
        profile_summary = _format_profile_summary(profile)

        research_prompt = f"""
You are the Lead Startup Analyst at VentureIQ (McKinsey-level rigor + YC partner sharpness).
The user is asking:
"{clean_msg}"

Known Startup Profile:
{profile_summary}

Live Web Research Findings:
{web_findings}
{evidence_block}

RULES (ANSWER-FIRST CONVERSATIONAL PATTERN):
1. ALWAYS answer the user's question directly in the VERY FIRST sentence. No throat-clearing, no stock openers ("Understanding...", "To help us validate...").
2. DO NOT withhold named competitors or market data to ask a clarifying question. NAME ACTUAL COMPANIES (e.g. Mobile.de, AutoScout24, HeyCar, DAT, etc.).
3. DO NOT invent fictitious hypothetical examples (e.g. "if your startup was meal planning software...") that the user never mentioned.
4. DO NOT use bolded meta-section headers like `**Follow-up:**`, `**Strategic Verdict:**`, or `**Competitive Gap:**` in conversational replies. Write as natural prose or clean plain bullet points.
5. Target 100-200 words. Format response cleanly:
   - Direct answer/verdict first.
   - Named direct & indirect competitors or status-quo alternatives with key strengths/weaknesses.
   - Concrete strategic recommendations to win.
   - End with ONE sharp follow-up question ONLY if something material is missing.

Return ONLY valid JSON:
{{
  "extracted_facts": {{"industry": "...", "geography": "...", "competitors": "..."}},
  "reply": "...",
  "choices": ["...", "..."]
}}
"""
        raw_res = invoke_gemini(research_prompt, temperature=0.2, phase="discovery:research")
        parsed = parse_json_response(raw_res, default={})

        reply_text = parsed.get("reply")
        if not reply_text:
            if web_findings and "Web search is" not in web_findings:
                # Synthesize clean concise response without dumping raw web scrape blocks
                lines = [line.strip() for line in web_findings.split("\n") if line.strip().startswith("• Title:")]
                titles = [line.replace("• Title:", "").strip() for line in lines[:3]]
                comp_str = ", ".join(titles) if titles else "established industry players and regional platforms"
                reply_text = (
                    f"Based on market data for '{clean_msg}', major established players include {comp_str}. "
                    "Key strategic priorities in this market revolve around digital lead response times and localized pricing intelligence. "
                    "Which specific customer segment or workflow are you targeting to differentiate?"
                )
            else:
                reply_text = (
                    f"Evaluating '{clean_msg}' indicates a competitive market where execution speed and specialized targeting are crucial. "
                    "Which primary customer segment or geographical region are you prioritizing for your initial launch?"
                )

        extracted = parsed.get("extracted_facts") or {}
        if isinstance(extracted, dict):
            for k, v in extracted.items():
                if v:
                    profile[k] = v

        conversation.append({"role": "assistant", "content": reply_text})

        compiled_query = state.get("user_query") or clean_msg
        if profile:
            details = _format_profile_summary(profile)
            compiled_query = f"{compiled_query}\n\nStructured Profile: {details}"

        # Evaluate if profile has enough info for validation
        ready = bool(profile.get("problem") and profile.get("target_customer") and profile.get("proposed_solution"))

        return {
            "conversation": conversation,
            "idea_context": profile,
            "startup_profile": profile,
            "questions_asked": questions_asked + 1,
            "ready_for_analysis": ready,
            "reply": reply_text,
            "choices": parsed.get("choices") if isinstance(parsed.get("choices"), list) else [],
            "user_query": compiled_query,
            "mode": "research",
        }

    # Conversational Mode (Default Discovery Turn)
    profile_summary = _format_profile_summary(profile)

    # Automatically extract turn input into persistent profile
    if not profile.get("idea") or not profile.get("problem"):
        profile["idea"] = clean_msg
        profile["problem"] = clean_msg
    elif not profile.get("target_customer"):
        profile["target_customer"] = clean_msg
    elif not profile.get("business_model"):
        profile["business_model"] = clean_msg
    elif not profile.get("differentiation"):
        profile["differentiation"] = clean_msg

    conv_prompt = f"""
You are the Lead Validation Analyst for VentureIQ (a top YC-level startup advisor).
Conduct a high-rigor discovery conversation to refine the founder's pitch before multi-agent validation.

Known Startup Profile:
{profile_summary}

Latest User Input:
"{clean_msg}"

Questions Asked So Far: {questions_asked}/{MAX_QUESTIONS}

INSTRUCTIONS (ANSWER-FIRST CONVERSATIONAL PATTERN):
1. Understand what's actually being asked.
2. Answer it directly in the first 1-2 sentences. If context is insufficient to answer specifically, ask ONE short direct question about a MISSING dimension (target customer, business model, or differentiation).
3. DO NOT repeat a question that has already been answered. Check the Known Startup Profile first.
4. DO NOT use bolded meta headers like `**Follow-up:**`, `**Strategic Verdict:**`, or `**Competitive Gap:**`.
5. Connect the answer to this startup's context and add 1 concrete strategic insight.
6. Target 100-180 words in natural, fluent prose.
7. Extract new startup profile attributes into `extracted_facts`.

Return ONLY valid JSON:
{{
  "extracted_facts": {{"problem": "...", "target_customer": "...", "business_model": "..."}},
  "ready_for_analysis": false,
  "reply": "...",
  "choices": ["...", "..."]
}}
"""

    raw_response = invoke_gemini(conv_prompt, temperature=0.3, phase="discovery:chat")
    parsed = parse_json_response(raw_response, default={})

    # Determine remaining uncollected key
    if not profile.get("target_customer"):
        next_key = "target_customer"
    elif not profile.get("business_model"):
        next_key = "business_model"
    elif not profile.get("differentiation"):
        next_key = "differentiation"
    else:
        next_key = None

    if not parsed or not parsed.get("reply"):
        if not next_key or force_ready:
            parsed = {
                "ready_for_analysis": True,
                "reply": "VentureIQ has collected sufficient context to validate this idea.",
                "choices": []
            }
        elif next_key == "target_customer":
            parsed = {
                "extracted_facts": {"problem": profile.get("problem") or clean_msg},
                "ready_for_analysis": False,
                "reply": f"Focusing on '{profile.get('problem') or clean_msg}' defines your core problem scope. Which primary customer segment are you targeting to validate initial willingness to pay?",
                "choices": ["B2B Enterprise", "SMBs & Local Businesses", "Direct Consumers (B2C)", "Niche Professionals"]
            }
        elif next_key == "business_model":
            parsed = {
                "extracted_facts": {"target_customer": clean_msg},
                "ready_for_analysis": False,
                "reply": f"Targeting {clean_msg} shapes your go-to-market strategy. What is your proposed monetization or pricing model?",
                "choices": ["Subscription (SaaS)", "Transaction / Commission Fee", "Freemium + Upsell", "Direct Sales"]
            }
        elif next_key == "differentiation":
            parsed = {
                "extracted_facts": {"business_model": clean_msg},
                "ready_for_analysis": False,
                "reply": f"With a {clean_msg} revenue model, what key competitive advantage or unique technology sets your startup apart?",
                "choices": ["Proprietary AI / Tech", "Network Effects", "Lower CAC & Speed", "Exclusive Partnerships"]
            }
        else:
            parsed = {
                "ready_for_analysis": True,
                "reply": "VentureIQ has collected sufficient context to validate this idea.",
                "choices": []
            }

    extracted_facts = parsed.get("extracted_facts") or {}
    if isinstance(extracted_facts, dict):
        for k, v in extracted_facts.items():
            if v:
                profile[k] = v

    ready = bool(parsed.get("ready_for_analysis")) or force_ready or bool(profile.get("problem") and profile.get("target_customer") and profile.get("business_model"))
    reply = parsed.get("reply") or "VentureIQ has collected sufficient context to validate this idea."
    choices = parsed.get("choices") if isinstance(parsed.get("choices"), list) else []

    conversation.append({"role": "assistant", "content": reply})
    questions_asked += (0 if ready else 1)

    compiled_query = state.get("user_query") or clean_msg
    if profile:
        details = _format_profile_summary(profile)
        compiled_query = f"{compiled_query}\n\nStructured Profile: {details}"

    return {
        "conversation": conversation,
        "idea_context": profile,
        "startup_profile": profile,
        "questions_asked": questions_asked,
        "ready_for_analysis": ready,
        "reply": reply,
        "choices": choices,
        "user_query": compiled_query,
        "mode": "conversational",
    }


def supervisor_agent(state: dict) -> dict:
    existing_tasks = state.get("tasks")
    if existing_tasks and isinstance(existing_tasks, list) and len(existing_tasks) > 0:
        tasks = [t for t in existing_tasks if t in VALID_AGENTS]
    else:
        tasks = ["market", "competitor", "business", "risk"]

    print(f"[SUPERVISOR] Routing tasks deterministically: {tasks}")
    return {"tasks": tasks}

