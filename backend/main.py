import hashlib
import threading
import uuid
from typing import Dict, Any, Set

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.workflow import graph
from agents.supervisor import supervisor_chat
from agents.llm_utils import get_gemini_stats
from rag.retriever import validate_rag_env

app = FastAPI()

@app.on_event("startup")
def on_startup():
    print("[SERVER STARTUP] Initializing VentureIQ API Service...")
    validate_rag_env()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store & request deduplication locks
SESSIONS: Dict[str, Dict[str, Any]] = {}
IN_FLIGHT_REQUESTS: Set[str] = set()
IN_FLIGHT_LOCK = threading.Lock()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class AnalyzeRequest(BaseModel):
    session_id: str | None = None
    user_query: str | None = None
    startup_idea: str | None = None
    query: str | None = None


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

    with IN_FLIGHT_LOCK:
        if req_key in IN_FLIGHT_REQUESTS:
            print(f"[DEDUPLICATE] Suppressing duplicate concurrent /chat request for session {session_id}")
            existing_state = SESSIONS.get(session_id, {})
            return {
                "session_id": session_id,
                "reply": existing_state.get("last_reply", "Processing previous turn..."),
                "choices": existing_state.get("choices", []),
                "ready_for_analysis": existing_state.get("ready_for_analysis", False),
                "idea_context": existing_state.get("idea_context", {}),
            }
        IN_FLIGHT_REQUESTS.add(req_key)

    try:
        state = SESSIONS.get(session_id, {})
        result = supervisor_chat(state, clean_msg)

        SESSIONS[session_id] = {
            "user_query": result["user_query"],
            "conversation": result["conversation"],
            "idea_context": result["idea_context"],
            "questions_asked": result["questions_asked"],
            "ready_for_analysis": result["ready_for_analysis"],
            "last_reply": result["reply"],
            "choices": result["choices"],
        }

        return {
            "session_id": session_id,
            "reply": result["reply"],
            "choices": result["choices"],
            "ready_for_analysis": result["ready_for_analysis"],
            "idea_context": result["idea_context"],
        }

    except HTTPException:
        raise
    except Exception as e:
        print("\n========== /chat ERROR ==========")
        print(str(e))
        print("==================================\n")
        raise HTTPException(status_code=502, detail="The conversational supervisor is temporarily unavailable.")
    finally:
        with IN_FLIGHT_LOCK:
            IN_FLIGHT_REQUESTS.discard(req_key)


@app.post("/analyze")
def analyze(data: AnalyzeRequest):
    """
    Runs the full agent graph with in-flight request deduplication.
    """
    session_id = data.session_id
    initial_state = {}

    if session_id and session_id in SESSIONS:
        initial_state = dict(SESSIONS[session_id])

    user_query = (
        data.startup_idea
        or data.query
        or data.user_query
        or initial_state.get("user_query")
    )

    if not user_query:
        raise HTTPException(status_code=400, detail="Startup idea is required")

    req_key = f"analyze:{session_id or 'direct'}:{hashlib.sha256(user_query.encode('utf-8')).hexdigest()}"

    with IN_FLIGHT_LOCK:
        if req_key in IN_FLIGHT_REQUESTS:
            print(f"[DEDUPLICATE] Suppressing duplicate concurrent /analyze request for query")
            raise HTTPException(status_code=429, detail="Analysis is already in progress for this idea.")
        IN_FLIGHT_REQUESTS.add(req_key)

    try:
        initial_state["user_query"] = user_query
        result = graph.invoke(initial_state)

        return {
            "tasks": result.get("tasks", []),
            "market_analysis": result.get("market_analysis", ""),
            "competitor_analysis": result.get("competitor_analysis", ""),
            "business_analysis": result.get("business_analysis", ""),
            "risk_analysis": result.get("risk_analysis", ""),
            "scores": result.get("scores", {}),
            "summary": result.get("summary", ""),
            "retrieved_context": result.get("retrieved_context", "")
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
        with IN_FLIGHT_LOCK:
            IN_FLIGHT_REQUESTS.discard(req_key)
