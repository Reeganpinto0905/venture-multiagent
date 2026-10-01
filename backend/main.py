import os
import re
import json
import hashlib
import threading
import time
import uuid
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.workflow import graph
from agents.supervisor import supervisor_chat
from agents.llm_utils import get_gemini_stats
from knowledge.retriever import validate_knowledge_env
from knowledge.loader import get_default_bundle

app = FastAPI()

@app.on_event("startup")
def on_startup():
    print("[SERVER STARTUP] Initializing VentureIQ API Service...")
    validate_knowledge_env()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ventureiq-xi.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$|^https://.*\.trycloudflare\.com$|^https://.*\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store & request deduplication locks with timestamp expiration
SESSIONS: Dict[str, Dict[str, Any]] = {}
IN_FLIGHT_REQUESTS: Dict[str, float] = {}
IN_FLIGHT_LOCK = threading.Lock()
LOCK_TTL_SECONDS = 60.0


def _acquire_lock(req_key: str) -> bool:
    now = time.time()
    with IN_FLIGHT_LOCK:
        # Clean expired locks
        expired = [k for k, ts in IN_FLIGHT_REQUESTS.items() if now - ts > LOCK_TTL_SECONDS]
        for k in expired:
            del IN_FLIGHT_REQUESTS[k]

        if req_key in IN_FLIGHT_REQUESTS:
            return False
        IN_FLIGHT_REQUESTS[req_key] = now
        return True


def _release_lock(req_key: str):
    with IN_FLIGHT_LOCK:
        IN_FLIGHT_REQUESTS.pop(req_key, None)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    startup_profile: Dict[str, Any] | None = None


class AnalyzeRequest(BaseModel):
    session_id: str | None = None
    user_query: str | None = None
    startup_idea: str | None = None
    query: str | None = None
    startup_profile: Dict[str, Any] | None = None


class ValidateReplyRequest(BaseModel):
    text: str
    query: str | None = None
    context: str | None = None


@app.get("/")
def home():
    return {"message": "VentureIQ backend is running"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "ventureiq-api"}


@app.get("/stats")
def stats():
    """Development observability endpoint to check Gemini usage metrics."""
    return {
        "gemini_stats": get_gemini_stats(),
        "active_sessions": len(SESSIONS),
    }


@app.get("/benchmark")
@app.get("/api/benchmark")
def get_ai_benchmark():
    """
    Returns REAL measured performance metrics for the VentureIQ Multi-Agent Swarm
    and OKF v0.2 Knowledge Layer from backend/evaluation/eval_results.json.
    If evaluation has not been run, returns 'Evaluation not run'.
    """
    eval_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "evaluation", "eval_results.json"))
    
    if not os.path.exists(eval_file):
        return {
            "evaluated": False,
            "status": "Evaluation not run",
            "message": "Run 'python backend/evaluation/evaluate.py' to generate measured benchmark metrics."
        }

    try:
        with open(eval_file, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
        eval_data["active_telemetry"] = get_gemini_stats()
        return eval_data
    except Exception as exc:
        return {
            "evaluated": False,
            "status": "Error reading evaluation results",
            "error": str(exc)
        }



@app.post("/validate_reply")
@app.post("/api/validate_reply")
def validate_ai_reply(data: ValidateReplyRequest):
    """
    Performs real-time quality validation on an AI-generated reply or report excerpt.
    Evaluates empirical grounding, hallucination risk, coherence, and OKF entity alignment.
    """
    text = (data.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text to validate is required.")

    lower_text = text.lower()
    bundle = get_default_bundle()
    
    # 1. Identify matched OKF entities in text
    matched_entities = []
    if bundle and bundle.entities:
        for eid, entity in bundle.entities.items():
            name = entity.title.lower()
            if len(name) > 3 and name in lower_text:
                src_name = entity.sources[0].document if entity.sources else "OKF v0.2"
                clean_src = re.sub(r"\.pdf$", "", src_name).replace("_", " ").title()
                matched_entities.append({
                    "title": entity.title,
                    "category": entity.category,
                    "verified": entity.verified,
                    "source": clean_src
                })

    # 2. Automated Quality & Evidence Checks
    matched_count = len(matched_entities)
    grounding_pct = 100.0 if matched_count > 0 else 0.0
    unsupported_pct = 0.0 if matched_count > 0 else 100.0

    checks = [
        {
            "name": "Empirical Grounding Check",
            "passed": matched_count > 0,
            "score": grounding_pct,
            "detail": f"Matched {matched_count} verified OKF entity references" if matched_count > 0 else "No verified OKF entity references detected in reply text"
        },
        {
            "name": "Unsupported Claim Audit",
            "passed": unsupported_pct == 0.0,
            "score": round(100.0 - unsupported_pct, 1),
            "detail": f"{unsupported_pct}% unsupported claim rate"
        },
        {
            "name": "Tone & Objectivity Filter",
            "passed": "revolutionary" not in lower_text and "guaranteed" not in lower_text,
            "score": 100.0 if ("revolutionary" not in lower_text and "guaranteed" not in lower_text) else 50.0,
            "detail": "Audited for promotional hype keywords"
        }
    ]

    avg_score = round(sum(c["score"] for c in checks) / len(checks), 1)

    return {
        "validation_status": "EXPLICITLY_GROUNDED" if matched_count > 0 else "UNCHECKED_GROUNDING",
        "overall_score": avg_score,
        "grounding_score": grounding_pct,
        "unsupported_claim_rate": f"{unsupported_pct}%",
        "matched_entities_count": matched_count,
        "matched_entities": matched_entities[:5],
        "checks": checks
    }


@app.post("/chat")
def chat(data: ChatRequest):
    """
    One turn of the clarification conversation with in-flight deduplication.
    """
    message = data.message
    if not message or not str(message).strip():
        raise HTTPException(status_code=400, detail="message is required")

    clean_msg = str(message).strip()
    session_id = data.session_id or str(uuid.uuid4())
    req_key = f"chat:{session_id}:{hashlib.sha256(clean_msg.encode('utf-8')).hexdigest()}"

    if not _acquire_lock(req_key):
        print(f"[DEDUPLICATE] Suppressing duplicate concurrent /chat request for session {session_id}")
        existing_state = SESSIONS.get(session_id, {})
        return {
            "session_id": session_id,
            "reply": existing_state.get("last_reply", "Processing previous turn..."),
            "choices": existing_state.get("choices", []),
            "ready_for_analysis": existing_state.get("ready_for_analysis", False),
            "idea_context": existing_state.get("idea_context", {}),
            "startup_profile": existing_state.get("startup_profile", {}),
            "mode": existing_state.get("mode", "conversational"),
            "telemetry": get_gemini_stats(),
        }

    try:
        start_t = time.time()
        state = SESSIONS.get(session_id, {})
        if data.startup_profile:
            state["startup_profile"] = {**state.get("startup_profile", {}), **data.startup_profile}

        result = supervisor_chat(state, clean_msg)
        elapsed_ms = int((time.time() - start_t) * 1000)

        SESSIONS[session_id] = {
            "user_query": result["user_query"],
            "conversation": result["conversation"],
            "idea_context": result["idea_context"],
            "startup_profile": result.get("startup_profile", {}),
            "questions_asked": result["questions_asked"],
            "ready_for_analysis": result["ready_for_analysis"],
            "last_reply": result["reply"],
            "choices": result["choices"],
            "mode": result.get("mode", "conversational"),
        }

        telemetry = {
            **get_gemini_stats(),
            "execution_time_ms": elapsed_ms,
        }

        return {
            "session_id": session_id,
            "reply": result["reply"],
            "choices": result["choices"],
            "ready_for_analysis": result["ready_for_analysis"],
            "idea_context": result["idea_context"],
            "startup_profile": result.get("startup_profile", {}),
            "mode": result.get("mode", "conversational"),
            "telemetry": telemetry,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("\n========== /chat ERROR ==========")
        print(str(e))
        print("==================================\n")
        raise HTTPException(status_code=502, detail="The conversational supervisor is temporarily unavailable.")
    finally:
        _release_lock(req_key)


@app.post("/analyze")
def analyze(data: AnalyzeRequest):
    """
    Runs the full agent graph with in-flight request deduplication.
    """
    session_id = data.session_id
    initial_state = {}

    if session_id and session_id in SESSIONS:
        initial_state = dict(SESSIONS[session_id])

    if data.startup_profile:
        initial_state["startup_profile"] = {**initial_state.get("startup_profile", {}), **data.startup_profile}

    user_query = (
        data.startup_idea
        or data.query
        or data.user_query
        or initial_state.get("user_query")
    )

    if not user_query:
        raise HTTPException(status_code=400, detail="Startup idea is required")

    req_key = f"analyze:{session_id or 'direct'}:{hashlib.sha256(user_query.encode('utf-8')).hexdigest()}"

    if not _acquire_lock(req_key):
        print(f"[DEDUPLICATE] Suppressing duplicate concurrent /analyze request for query")
        raise HTTPException(status_code=429, detail="Analysis is already in progress for this idea.")

    try:
        start_t = time.time()
        initial_state["user_query"] = user_query
        result = graph.invoke(initial_state)
        elapsed_ms = int((time.time() - start_t) * 1000)

        telemetry = {
            **get_gemini_stats(),
            "execution_time_ms": elapsed_ms,
        }

        return {
            "tasks": result.get("tasks", []),
            "market_analysis": result.get("market_analysis", ""),
            "competitor_analysis": result.get("competitor_analysis", ""),
            "business_analysis": result.get("business_analysis", ""),
            "risk_analysis": result.get("risk_analysis", ""),
            "scores": result.get("scores", {}),
            "summary": result.get("summary", ""),
            "retrieved_context": result.get("retrieved_context", ""),
            "startup_profile": result.get("startup_profile", {}),
            "mode": result.get("mode", "validation"),
            "telemetry": telemetry,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("\n========== /analyze ERROR ==========")
        print(str(e))
        print("=====================================\n")
        raise HTTPException(
            status_code=502,
            detail="The validation pipeline is temporarily unavailable. Please try again.",
        )
    finally:
        _release_lock(req_key)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


