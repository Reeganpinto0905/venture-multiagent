from typing import TypedDict, Optional, List, Dict, Any


class VentureState(TypedDict, total=False):
    # --- Original fields (kept, contract-compatible with /analyze) ---
    user_query: str
    tasks: List[str]
    market_analysis: str
    competitor_analysis: str
    business_analysis: str

    # --- Risk + narrative summary ---
    risk_analysis: str
    summary: str

    # --- Conversation / Profile state ---
    conversation: List[Dict[str, Any]]
    idea_context: Dict[str, Any]
    startup_profile: Dict[str, Any]
    questions_asked: int
    ready_for_analysis: bool

    # --- Scoring & RAG context ---
    scores: Dict[str, int]
    retrieved_context: Optional[str]
    mode: str
    telemetry: Dict[str, Any]
    evidence_matrix: Dict[str, Any]

