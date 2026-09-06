import hashlib
import json
import os
import re
import time
from typing import Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI

# Centralized Model Configuration
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DISCOVERY_MODEL = os.getenv("GEMINI_DISCOVERY_MODEL", DEFAULT_MODEL)
VALIDATION_MODEL = os.getenv("GEMINI_VALIDATION_MODEL", DEFAULT_MODEL)

# In-memory Cache & Usage Observability
_RESPONSE_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = 3600  # 1 hour TTL
_STATS = {
    "total_calls": 0,
    "cache_hits": 0,
    "total_input_chars": 0,
    "total_output_chars": 0
}


def _compute_cache_key(prompt: str, model: str, temperature: float) -> str:
    normalized = prompt.strip().lower()
    raw_key = f"{model}:{temperature:.2f}:{normalized}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def invoke_gemini(
    prompt: str,
    temperature: float = 0.4,
    phase: str = "general",
    use_cache: bool = True,
    model: Optional[str] = None,
) -> Optional[str]:
    """
    Executes a Gemini LLM request with caching, usage observability logging,
    and model centralization.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        print("[GEMINI] Warning: GOOGLE_API_KEY is not set.")
        return None

    selected_model = model or (DISCOVERY_MODEL if "discovery" in phase else VALIDATION_MODEL)
    cache_key = _compute_cache_key(prompt, selected_model, temperature)
    now = time.time()

    # Check cache
    if use_cache and cache_key in _RESPONSE_CACHE:
        entry = _RESPONSE_CACHE[cache_key]
        if now - entry["timestamp"] < _CACHE_TTL:
            _STATS["cache_hits"] += 1
            print(
                f"[GEMINI] phase: {phase} | model: {selected_model} | cache_hit: TRUE | "
                f"total_calls: {_STATS['total_calls']} (hits: {_STATS['cache_hits']})"
            )
            return entry["response"]
        else:
            del _RESPONSE_CACHE[cache_key]

    # Clean old cache entries periodically if cache grows large
    if len(_RESPONSE_CACHE) > 500:
        expired = [k for k, v in _RESPONSE_CACHE.items() if now - v["timestamp"] >= _CACHE_TTL]
        for k in expired:
            del _RESPONSE_CACHE[k]

    _STATS["total_calls"] += 1
    _STATS["total_input_chars"] += len(prompt)

    try:
        response = ChatGoogleGenerativeAI(
            model=selected_model,
            temperature=temperature,
        ).invoke(prompt)

        content = response.content if hasattr(response, "content") else str(response)
        
        if content:
            _STATS["total_output_chars"] += len(content)
            if use_cache:
                _RESPONSE_CACHE[cache_key] = {
                    "response": content,
                    "timestamp": now
                }

        est_in_tokens = len(prompt) // 4
        est_out_tokens = len(content or "") // 4

        print(
            f"[GEMINI] phase: {phase} | model: {selected_model} | cache_hit: FALSE | "
            f"est_in_tokens: ~{est_in_tokens} | est_out_tokens: ~{est_out_tokens} | "
            f"session_calls: {_STATS['total_calls']} (hits: {_STATS['cache_hits']})"
        )
        return content

    except Exception as exc:
        print(f"[GEMINI] Request failed ({phase}): {type(exc).__name__} - {exc}")
        return None


def parse_json_response(raw: str, default=None):
    """
    Strips markdown code fences and parses JSON securely.
    """
    if not raw:
        return default

    text = raw.strip()
    text = re.sub(r"^```(json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()

    match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
    if match:
        text = match.group(1)

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def get_gemini_stats() -> Dict[str, Any]:
    return dict(_STATS)
