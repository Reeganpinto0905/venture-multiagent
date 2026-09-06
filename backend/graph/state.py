from typing import TypedDict, Optional


class VentureState(TypedDict, total=False):
    # --- Original fields (kept, contract-compatible with /analyze) ---
    user_query: str
    tasks: list[str]
    market_analysis: str
    competitor_analysis: str
    business_analysis: str

    # --- New: risk + narrative summary ---
    risk_analysis: str
    summary: str

    # --- New: conversation / clarification state ---
    # conversation: full turn history, e.g. [{"role": "user", "content": "..."}, ...]
    conversation: list[dict]
    # idea_context: structured facts the supervisor has extracted so far
    # e.g. {"category": "Cloud Kitchen", "target_user": "College Students", "problem": "..."}
    idea_context: dict
    questions_asked: int
    ready_for_analysis: bool

    # --- New: scoring for the results dashboard ---
    scores: dict  # {"market": 86, "competition": 71, "business": 79, "risk": 58, "overall": 78}

    # --- New: optional RAG context injected into agent prompts ---
    retrieved_context: Optional[str]
