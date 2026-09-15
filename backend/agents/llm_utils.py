import hashlib
import json
import os
import re
import sys
import time
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cache.cache_store import cache_store

# Centralized Model Configuration & Resilient Fallback Cascade
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
DISCOVERY_MODEL = os.getenv("GEMINI_DISCOVERY_MODEL", DEFAULT_MODEL)
VALIDATION_MODEL = os.getenv("GEMINI_VALIDATION_MODEL", DEFAULT_MODEL)

# Multi-model quota-resilient cascade
MODEL_FALLBACK_ORDER = [
    DEFAULT_MODEL,
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-latest",
    "gemini-2.5-flash",
]

# Usage Observability & Telemetry Counters
_STATS = {
    "total_calls": 0,
    "gemini_calls": 0,
    "tavily_calls": 0,
    "pinecone_calls": 0,
    "cache_hits": 0,
    "total_input_chars": 0,
    "total_output_chars": 0,
}


def increment_telemetry(key: str, delta: int = 1):
    if key in _STATS:
        _STATS[key] += delta


def _call_gemini_rest(model_name: str, prompt: str, temperature: float, api_key: str) -> Optional[str]:
    """
    Direct HTTPS REST invocation of Gemini generateContent.
    Bypasses gRPC channel setup issues on Windows and responds in 2-3 seconds.
    """
    import urllib.request
    import urllib.error

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": float(temperature),
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    import ssl
    ctx = ssl.create_default_context()
    try:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    except Exception:
        pass

    try:
        with urllib.request.urlopen(req, timeout=14, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return None
    except urllib.error.HTTPError as http_err:
        err_body = ""
        try:
            err_body = http_err.read().decode("utf-8")
        except Exception:
            pass
        if http_err.code == 429 or "RESOURCE_EXHAUSTED" in err_body:
            raise PermissionError(f"HTTP 429 Quota Exhausted: {err_body}")
        if http_err.code == 404:
            raise LookupError(f"HTTP 404 Model Not Found: {model_name}")
        raise RuntimeError(f"HTTP {http_err.code}: {err_body}")


def invoke_gemini(
    prompt: str,
    temperature: float = 0.3,
    phase: str = "general",
    use_cache: bool = True,
    model: Optional[str] = None,
) -> Optional[str]:
    """
    Executes a Gemini LLM request with SQLite caching, high-speed direct REST execution,
    usage observability logging, and an automatic multi-model fallback cascade to prevent
    quota exhaustion.
    """
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[GEMINI] Warning: GOOGLE_API_KEY / GEMINI_API_KEY is not set.")
        return None

    primary_model = model or (DISCOVERY_MODEL if "discovery" in phase else VALIDATION_MODEL)

    # Build unique ordered fallback candidates
    candidates = [primary_model]
    for m in MODEL_FALLBACK_ORDER:
        if m not in candidates:
            candidates.append(m)

    cache_key = cache_store.compute_key(phase, primary_model, f"{temperature:.2f}:{prompt}")

    if use_cache:
        cached_res = cache_store.get(cache_key)
        if cached_res:
            _STATS["cache_hits"] += 1
            print(f"[GEMINI CACHE HIT] phase: {phase} | model: {primary_model}")
            return str(cached_res)

    _STATS["total_calls"] += 1
    _STATS["gemini_calls"] += 1
    _STATS["total_input_chars"] += len(prompt)

    # Attempt execution across candidate models
    for candidate_model in candidates:
        try:
            # First attempt high-speed direct REST (2-3s, no gRPC hang)
            content = _call_gemini_rest(candidate_model, prompt, temperature, api_key)
            if content:
                _STATS["total_output_chars"] += len(content)
                if use_cache:
                    cache_store.set(cache_key, content, ttl=86400)

                est_in = len(prompt) // 4
                est_out = len(content) // 4
                print(
                    f"[GEMINI REST OK] phase: {phase} | model: {candidate_model} | "
                    f"est_in: ~{est_in} | est_out: ~{est_out}"
                )
                return content

        except (PermissionError, LookupError) as quota_or_model_err:
            print(f"[GEMINI FAILOVER] Model '{candidate_model}' unavailable ({type(quota_or_model_err).__name__}). Trying next model...")
            continue
        except Exception as rest_err:
            # Fallback to LangChain invoke if REST encountered unexpected transport error
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                response = ChatGoogleGenerativeAI(
                    model=candidate_model,
                    temperature=temperature,
                    google_api_key=api_key,
                ).invoke(prompt)
                
                # Handle list content in newer LangChain versions
                raw_c = getattr(response, "content", response)
                if isinstance(raw_c, list):
                    content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in raw_c)
                else:
                    content = str(raw_c)

                if content:
                    _STATS["total_output_chars"] += len(content)
                    if use_cache:
                        cache_store.set(cache_key, content, ttl=86400)
                    return content
            except Exception as lc_err:
                err_str = str(lc_err)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print(f"[GEMINI QUOTA EXHAUSTED] {candidate_model} rate limited. Falling back...")
                    continue
                print(f"[GEMINI ERROR] Model '{candidate_model}' failed: {lc_err}")
                continue

    _STATS["quota_exceeded"] = True
    print(f"[GEMINI ALL MODELS EXHAUSTED] All candidate models exhausted for phase {phase}.")
    return None


def parse_json_response(raw: Any, default=None):
    """
    Strips markdown code fences, unescapes strings, and parses JSON or Python dict securely.
    """
    if not raw:
        return default

    if isinstance(raw, dict):
        return raw

    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and "text" in item:
                return parse_json_response(item["text"], default=default)

    text = str(raw).strip()

    # If it's a stringified python list like "[{'type': 'text', 'text': '...'}]"
    if text.startswith("[{") and ("'text':" in text or '"text":' in text):
        import ast
        try:
            evaluated = ast.literal_eval(text)
            if isinstance(evaluated, list) and len(evaluated) > 0 and isinstance(evaluated[0], dict):
                inner_text = evaluated[0].get("text", "")
                if inner_text:
                    return parse_json_response(inner_text, default=default)
        except Exception:
            pass

    # If it's a stringified python dict like "{'analysis': '...'}"
    if text.startswith("{") and ("'analysis':" in text or "'score':" in text):
        import ast
        try:
            evaluated = ast.literal_eval(text)
            if isinstance(evaluated, dict):
                return evaluated
        except Exception:
            pass

    text = re.sub(r"^```(json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()

    match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
    if match:
        candidate = match.group(1)
        try:
            return json.loads(candidate, strict=False)
        except Exception:
            pass

    # Regex extraction for analysis and score
    analysis_match = re.search(r'["\']analysis["\']\s*:\s*(?:["\']|""")([\s\S]*?)(?:["\']|""")(?=\s*,\s*["\']score|\s*\})', text)
    score_match = re.search(r'["\']score["\']\s*:\s*(\d+)', text)

    if analysis_match:
        extracted = analysis_match.group(1)
        try:
            extracted = extracted.encode().decode('unicode_escape', errors='ignore')
        except Exception:
            pass
        res = {"analysis": extracted}
        if score_match:
            res["score"] = int(score_match.group(1))
        return res

    return default


def get_gemini_stats() -> Dict[str, Any]:
    stats = dict(_STATS)
    stats["cache_stats"] = cache_store.get_stats()
    return stats

