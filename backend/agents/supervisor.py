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
    """Helper to detect off-topic execution requests deterministically."""
    lower = text.lower().strip()
    return any(pat in lower for pat in OFF_TOPIC_PATTERNS)


def _format_context_summary(idea_context: dict) -> str:
    """Format structured facts into a compact, token-efficient string."""
    items = [f"{k}: {v}" for k, v in idea_context.items() if v]
    return "; ".join(items) if items else "No structured facts extracted yet."


def supervisor_chat(state: dict, user_message: str) -> dict:
    """
    Runs one turn of the discovery conversation using compact structured context,
    strict topic validation, and deterministic progression checks.
    """
    conversation = state.get("conversation", [])
    idea_context = {**DEFAULT_IDEA_CONTEXT, **state.get("idea_context", {})}
    questions_asked = state.get("questions_asked", 0)

    clean_msg = user_message.strip()
    conversation.append({"role": "user", "content": clean_msg})

    # Fast pattern match check for common off-topic requests (e.g. "buil me a website")
    if _is_off_topic_query(clean_msg):
        print(f"[SUPERVISOR] Fast pattern match flagged off-topic input: '{clean_msg}'")
        conversation.append({"role": "assistant", "content": OUT_OF_SCOPE_MESSAGE})
        initial_query = state.get("user_query") or (conversation[0]["content"] if len(conversation) > 0 else clean_msg)
        return {
            "conversation": conversation,
            "idea_context": idea_context,
            "questions_asked": questions_asked,
            "ready_for_analysis": False,
            "reply": OUT_OF_SCOPE_MESSAGE,
            "choices": state.get("choices", []),
            "user_query": initial_query,
        }

    lower_msg = clean_msg.lower()

    # Fast deterministic checks for readiness
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

    # Compact prompt: pass only the structured state + recent message with topic validation instructions
    context_summary = _format_context_summary(idea_context)
    
    prompt = f"""
You are the Lead Validation Analyst for VentureIQ (a top YC-level startup advisor).
Conduct a discovery conversation strictly focused on startup due diligence and pitch validation.

Current Known Context:
{context_summary}

Latest Founder Response:
"{clean_msg}"

Questions Asked So Far: {questions_asked}/{MAX_QUESTIONS}

STEP 1: STRICT TOPIC VALIDATION
Determine if the Latest Founder Response is relevant to startup due diligence, pitch validation, or the startup idea being evaluated.
- RELEVANT (is_off_topic = false):
  * Direct answers or follow-up details about the startup idea (problem, target customer, solution, pricing, market, competitors, technology stack for the startup, GTM strategy, etc.).
  * Relevant follow-up questions from the founder about their startup, customers, competitors, business model, market sizing, or pitch validation.
  * Similar startup-related questions.
- OUT OF SCOPE / UNRELATED (is_off_topic = true):
  * Unrelated service requests (e.g. "build me a website", "write code for me", "create an app for me", "design a logo for me").
  * General knowledge trivia, math problems, jokes, coding assignments, or arbitrary chat completely unrelated to startup due diligence or the startup idea.

IF OUT OF SCOPE (is_off_topic = true):
Set "is_off_topic": true, "ready_for_analysis": false, "message": "{OUT_OF_SCOPE_MESSAGE}", "choices": [].

IF RELEVANT (is_off_topic = false):
1. Extract new facts from the response into `extracted_facts` (e.g. {{"target_customer": "B2B SMBs", "problem": "high churn"}}).
2. Evaluate if we have clear signals for: core problem, target user, solution, and monetization.
3. If ready: set `ready_for_analysis`: true, `message`: "VentureIQ has collected sufficient context to validate this idea.", `choices`: [].
4. If NOT ready: set `ready_for_analysis`: false, `message`: 1 concise strategic response + follow-up question (explain WHY it matters), and `choices`: 3-5 short strategic options (2-4 words each).

Rules:
- NO generic filler ("Got it", "That's interesting", "Sure", "Thanks").
- NO questions about already known facts.
- Return ONLY valid JSON:
{{
  "is_off_topic": false,
  "extracted_facts": {{"key": "value"}},
  "ready_for_analysis": false,
  "message": "...",
  "choices": ["...", "..."]
}}
"""

    raw_response = invoke_gemini(prompt, temperature=0.3, phase="discovery")
    parsed = parse_json_response(raw_response, default={})

    # Topic validation check from LLM response or deterministic helper
    is_off_topic = _is_off_topic_query(clean_msg)
    if parsed:
        if parsed.get("is_off_topic") is True:
            is_off_topic = True
        elif "outside the scope" in str(parsed.get("message")).lower():
            is_off_topic = True

    if is_off_topic:
        reply = OUT_OF_SCOPE_MESSAGE
        conversation.append({"role": "assistant", "content": reply})
        initial_query = state.get("user_query") or (conversation[0]["content"] if len(conversation) > 0 else clean_msg)
        return {
            "conversation": conversation,
            "idea_context": idea_context,
            "questions_asked": questions_asked,
            "ready_for_analysis": False,
            "reply": reply,
            "choices": state.get("choices", []),
            "user_query": initial_query,
        }

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
