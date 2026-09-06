from dotenv import load_dotenv
from agents.llm_utils import invoke_gemini, parse_json_response

load_dotenv()

VALID_AGENTS = {"market", "competitor", "business", "risk"}
MAX_QUESTIONS = 4

# Structured initial context schema
DEFAULT_IDEA_CONTEXT = {
    "problem": None,
    "target_customer": None,
    "solution": None,
    "geography": None,
    "differentiation": None,
    "business_model": None,
    "pricing": None,
    "traction": None,
}


def _format_context_summary(idea_context: dict) -> str:
    """Format structured facts into a compact, token-efficient string."""
    items = [f"{k}: {v}" for k, v in idea_context.items() if v]
    return "; ".join(items) if items else "No structured facts extracted yet."


def supervisor_chat(state: dict, user_message: str) -> dict:
    """
    Runs one turn of the discovery conversation using compact structured context
    and deterministic progression checks to minimize Gemini API calls and token count.
    """
    conversation = state.get("conversation", [])
    idea_context = {**DEFAULT_IDEA_CONTEXT, **state.get("idea_context", {})}
    questions_asked = state.get("questions_asked", 0)

    clean_msg = user_message.strip()
    conversation.append({"role": "user", "content": clean_msg})

    # Fast deterministic checks for readiness
    lower_msg = clean_msg.lower()
    explicit_trigger = any(
        kw in lower_msg
        for kw in ["start validation", "analyze now", "ready for analysis", "run analysis", "validate idea", "ready to validate"]
    )
    force_ready = questions_asked >= MAX_QUESTIONS or explicit_trigger

    if force_ready:
        reply = "VentureIQ has collected sufficient context to validate this idea."
        conversation.append({"role": "assistant", "content": reply})
        compiled_query = state.get("user_query") or clean_msg
        if idea_context:
            details = _format_context_summary(idea_context)
            compiled_query = f"{compiled_query}\n\nStructured Context: {details}"

        return {
            "conversation": conversation,
            "idea_context": idea_context,
            "questions_asked": questions_asked,
            "ready_for_analysis": True,
            "reply": reply,
            "choices": [],
            "user_query": compiled_query,
        }

    # Compact prompt: pass only the structured state + recent message (not raw historical transcripts)
    context_summary = _format_context_summary(idea_context)
    
    prompt = f"""
You are the Lead Validation Analyst for VentureIQ (a top YC-level startup advisor).
Conduct a discovery conversation to refine the founder's idea before multi-agent validation.

Current Known Context:
{context_summary}

Latest Founder Response:
"{clean_msg}"

Questions Asked So Far: {questions_asked}/{MAX_QUESTIONS}

Instructions:
1. Extract new facts from the founder's response into `extracted_facts` (e.g. {{"target_customer": "B2B SMBs", "problem": "high churn"}}).
2. Evaluate if we have clear signals for: core problem, target user, solution, and monetization.
3. If ready: set `ready_for_analysis`: true, `message`: "VentureIQ has collected sufficient context to validate this idea.", `choices`: [].
4. If NOT ready: set `ready_for_analysis`: false, `message`: 1 concise strategic response + follow-up question (explain WHY it matters), and `choices`: 3-5 short strategic options (2-4 words each).

Rules:
- NO generic filler ("Got it", "That's interesting", "Sure", "Thanks").
- NO questions about already known facts.
- Return ONLY valid JSON:
{{
  "extracted_facts": {{"key": "value"}},
  "ready_for_analysis": false,
  "message": "...",
  "choices": ["...", "..."]
}}
"""

    raw_response = invoke_gemini(prompt, temperature=0.3, phase="discovery")
    parsed = parse_json_response(raw_response, default={})

    if not parsed or not parsed.get("message"):
        # Deterministic fallback logic if LLM is unavailable or malformed
        missing_keys = [k for k in ("target_customer", "differentiation", "business_model") if not idea_context.get(k)]
        
        if not missing_keys or force_ready or len(conversation) >= 8:
            parsed = {
                "ready_for_analysis": True,
                "message": "VentureIQ has collected sufficient context to validate this idea.",
                "choices": []
            }
        elif not idea_context.get("target_customer"):
            parsed = {
                "extracted_facts": {"problem_area": clean_msg},
                "ready_for_analysis": False,
                "message": f"Focusing on '{clean_msg}' establishes the core scope. To define your addressable market size, which customer segment are you prioritizing first?",
                "choices": ["B2B / Enterprise", "SMBs & Local Businesses", "Direct Consumers (B2C)", "Niche Professionals"]
            }
        elif not idea_context.get("differentiation"):
            parsed = {
                "extracted_facts": {"target_customer": clean_msg},
                "ready_for_analysis": False,
                "message": "That specifies your target audience. How do you plan to build a defensible competitive moat against existing alternatives?",
                "choices": ["Proprietary AI Tech", "Lower Cost Model", "Exclusive Distribution", "Superior UX & Automation"]
            }
        else:
            parsed = {
                "extracted_facts": {"differentiation": clean_msg},
                "ready_for_analysis": False,
                "message": "Defensibility is key. What primary revenue model will drive customer willingness to pay?",
                "choices": ["Monthly SaaS Subscription", "Transaction Commission", "Freemium + Add-ons", "Usage-Based Tier"]
            }

    extracted_facts = parsed.get("extracted_facts") or {}
    if isinstance(extracted_facts, dict):
        for k, v in extracted_facts.items():
            if v:
                idea_context[k] = v

    ready = bool(parsed.get("ready_for_analysis")) or force_ready
    reply = parsed.get("message") or "VentureIQ has collected sufficient context to validate this idea."
    choices = parsed.get("choices") if isinstance(parsed.get("choices"), list) else []

    conversation.append({"role": "assistant", "content": reply})
    questions_asked += (0 if ready else 1)

    compiled_query = state.get("user_query") or clean_msg
    if idea_context:
        details = _format_context_summary(idea_context)
        compiled_query = f"{compiled_query}\n\nStructured Context: {details}"

    return {
        "conversation": conversation,
        "idea_context": idea_context,
        "questions_asked": questions_asked,
        "ready_for_analysis": ready,
        "reply": reply,
        "choices": choices,
        "user_query": compiled_query,
    }


def supervisor_agent(state: dict) -> dict:
    """
    Task router node for LangGraph. Runs deterministically for standard validation requests
    to eliminate unnecessary Gemini routing API calls.
    """
    existing_tasks = state.get("tasks")
    if existing_tasks and isinstance(existing_tasks, list) and len(existing_tasks) > 0:
        tasks = [t for t in existing_tasks if t in VALID_AGENTS]
    else:
        # Standard validation runs all 4 core agents (market, competitor, business, risk)
        tasks = ["market", "competitor", "business", "risk"]

    print(f"[SUPERVISOR] Routing tasks deterministically: {tasks}")
    return {"tasks": tasks}
