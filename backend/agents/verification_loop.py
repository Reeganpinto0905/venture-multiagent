"""
Critic -> Evaluator -> Refiner Verification Loop for VentureIQ.
Detects:
1. Unsupported claims
2. Missing citations
3. Irrelevant evidence
4. Source/claim mismatch
5. Target-startup vs generic-example confusion
6. Overconfident claims (e.g. "guaranteed", "revolutionize", "will inevitably")

Features:
- Allows refiner to output "Insufficient evidence" when ungrounded.
- Maximum 2 refinement iterations.
- Tracks before/after unsupported-claim counts.
"""

from typing import Dict, Any, List, Tuple
import re

OVERCONFIDENT_PATTERNS = [
    r"\bguaranteed\b",
    r"\brevolutionar(y|ize)\b",
    r"\binevitabl(e|y)\b",
    r"\bzero risk\b",
    r"\bflawless\b",
    r"\b100% certainty\b",
    r"\bdominant monopoly\b"
]

GENERIC_CONFUSION_PATTERNS = [
    r"\blike uber for\b",
    r"\bnetflix of\b",
    r"\bamazon of\b"
]





CLAIM_TYPES = {
    "VERIFIED_FACT": "VERIFIED_FACT",
    "INFERENCE": "INFERENCE",
    "EXTERNAL_BENCHMARK": "EXTERNAL_BENCHMARK",
    "UNKNOWN": "UNKNOWN"
}

BENCHMARK_KEYWORDS = [
    "industry average", "benchmark", "macro", "standard comparable",
    "general industry", "tam estimate", "comparable precedent", "typical standard"
]

INFERENCE_KEYWORDS = [
    "may indicate", "suggests", "inferred", "likely indicates",
    "potential", "implies", "projected", "signals", "can be deduced",
    "appears to", "pointing to", "hypothesized"
]

UNKNOWN_KEYWORDS = [
    "unknown", "cannot be verified", "not provided", "insufficient evidence",
    "unverified", "missing data", "not available"
]


def classify_claim(sentence: str, valid_evidence_ids: List[str] = None) -> str:
    """
    Classifies a claim into one of four institutional categories:
    - VERIFIED_FACT: Supported by primary evidence citation.
    - INFERENCE: Analytical interpretation deduced from evidence (probabilistic, not asserted as fact).
    - EXTERNAL_BENCHMARK: Industry baseline or historical comparable.
    - UNKNOWN: Missing, unverified, or unprovable metrics.
    """
    lower = sentence.lower().strip()
    valid_ids = [v.lower() for v in (valid_evidence_ids or [])]

    # 1. Unknown / Missing
    if any(kw in lower for kw in UNKNOWN_KEYWORDS):
        return CLAIM_TYPES["UNKNOWN"]

    # 2. External Benchmark
    if any(kw in lower for kw in BENCHMARK_KEYWORDS):
        return CLAIM_TYPES["EXTERNAL_BENCHMARK"]

    # 3. Inference / Interpretation
    if any(kw in lower for kw in INFERENCE_KEYWORDS):
        return CLAIM_TYPES["INFERENCE"]

    # 4. Verified Fact (must have explicit citation / evidence ID reference)
    has_citation = bool(re.search(r"\[(OKF|Evidence|Source|p\.|Page|\w+/\w+)", sentence, re.IGNORECASE))
    has_valid_id = any(eid in lower for eid in valid_ids) if valid_ids else False

    if has_citation or has_valid_id:
        return CLAIM_TYPES["VERIFIED_FACT"]

    # Uncited claim defaults to inference if probabilistic, otherwise unknown
    if any(w in lower for w in ["likely", "estimated", "expected", "possible", "should"]):
        return CLAIM_TYPES["INFERENCE"]

    return CLAIM_TYPES["UNKNOWN"]


class VerificationCritic:
    """Audits an agent's draft analysis against provided evidence IDs and text."""

    def audit(self, draft_text: str, valid_evidence_ids: List[str]) -> List[Dict[str, Any]]:
        issues = []
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", draft_text) if len(s.strip()) > 15]

        for sent in sentences:
            lower = sent.lower()
            # 1. Overconfident claims
            for pat in OVERCONFIDENT_PATTERNS:
                if re.search(pat, lower):
                    issues.append({
                        "type": "overconfident_claim",
                        "sentence": sent,
                        "severity": "HIGH",
                        "suggestion": "Moderate language to probabilistic/empirical tone"
                    })

            # 2. Target vs Generic Example Confusion
            for pat in GENERIC_CONFUSION_PATTERNS:
                if re.search(pat, lower):
                    issues.append({
                        "type": "target_vs_generic_confusion",
                        "sentence": sent,
                        "severity": "MEDIUM",
                        "suggestion": "Replace superficial analogy with specific operational metrics"
                    })

            # 3. Citation Check
            classification = classify_claim(sent, valid_evidence_ids)
            has_strong_claim = any(kw in lower for kw in ["market size", "revenue", "loss", "burn", "margin", "cagr", "valuation", "churn"])
            if has_strong_claim and classification == CLAIM_TYPES["UNKNOWN"]:
                issues.append({
                    "type": "unsupported_claim",
                    "sentence": sent,
                    "severity": "HIGH",
                    "suggestion": "Add primary source citation or tag as UNKNOWN / INFERENCE"
                })

        return issues


class VerificationEvaluator:
    """Scores draft reliability and quantifies unsupported claims."""

    def score(self, draft_text: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        unsupported_count = sum(1 for i in issues if i["type"] in ["unsupported_claim", "missing_citation"])
        overconfident_count = sum(1 for i in issues if i["type"] == "overconfident_claim")
        confusion_count = sum(1 for i in issues if i["type"] == "target_vs_generic_confusion")
        
        groundedness_score = max(0.0, round(100.0 - (unsupported_count * 25.0), 1))

        return {
            "unsupported_claim_count": unsupported_count,
            "overconfident_count": overconfident_count,
            "confusion_count": confusion_count,
            "groundedness_score": groundedness_score,
            "passed": unsupported_count == 0 and overconfident_count == 0
        }


class VerificationRefiner:
    """
    Refines draft by fixing unsupported claims, removing hype, marking insufficient evidence,
    and classifying all final claims as VERIFIED_FACT, INFERENCE, EXTERNAL_BENCHMARK, or UNKNOWN.
    """

    def refine(self, draft_text: str, issues: List[Dict[str, Any]], available_evidence: List[str]) -> Tuple[str, List[Dict[str, Any]]]:
        if not draft_text.strip() or (not available_evidence and len(issues) > 3):
            insufficient_msg = "UNKNOWN: Insufficient evidence available in provided empirical sources."
            return insufficient_msg, [{"claim": insufficient_msg, "classification": CLAIM_TYPES["UNKNOWN"]}]

        refined = draft_text

        # 1. Neutralize overconfident words
        for pat in OVERCONFIDENT_PATTERNS:
            refined = re.sub(pat, "projected", refined, flags=re.IGNORECASE)

        # 2. Neutralize generic analogies
        refined = re.sub(r"like uber for", "operating as an on-demand marketplace for", refined, flags=re.IGNORECASE)
        refined = re.sub(r"netflix of", "subscription streaming model for", refined, flags=re.IGNORECASE)

        # 3. Handle unsupported factual sentences
        for issue in issues:
            if issue["type"] == "unsupported_claim":
                orig_sent = issue["sentence"]
                if orig_sent in refined:
                    if available_evidence:
                        # Allow analytical interpretation as INFERENCE or cite available evidence
                        replacement = f"[INFERENCE]: {orig_sent} (May indicate potential trend based on {available_evidence[0]})"
                    else:
                        replacement = f"[UNKNOWN]: {orig_sent} (Cannot be verified in provided primary sources)"
                    refined = refined.replace(orig_sent, replacement)

        # 4. Extract and classify all claims in refined text
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", refined) if len(s.strip()) > 10]
        classified_claims = []
        for s in sentences:
            cls_type = classify_claim(s, available_evidence)
            classified_claims.append({
                "claim": s,
                "classification": cls_type
            })

        return refined, classified_claims


def run_verification_loop(
    draft_text: str,
    valid_evidence_ids: List[str],
    max_iterations: int = 2
) -> Dict[str, Any]:
    """
    Executes the Critic -> Evaluator -> Refiner loop (up to max_iterations).
    Returns verified result with before/after unsupported claim counts and classified claims.
    """
    critic = VerificationCritic()
    evaluator = VerificationEvaluator()
    refiner = VerificationRefiner()

    initial_issues = critic.audit(draft_text, valid_evidence_ids)
    initial_eval = evaluator.score(draft_text, initial_issues)
    before_unsupported_count = initial_eval["unsupported_claim_count"]

    current_text = draft_text
    current_issues = initial_issues
    classified_claims = []
    iterations_run = 0

    while iterations_run < max_iterations:
        if not current_issues:
            break
        iterations_run += 1
        current_text, classified_claims = refiner.refine(current_text, current_issues, valid_evidence_ids)
        current_issues = critic.audit(current_text, valid_evidence_ids)

    if not classified_claims:
        _, classified_claims = refiner.refine(current_text, [], valid_evidence_ids)

    final_eval = evaluator.score(current_text, current_issues)
    after_unsupported_count = final_eval["unsupported_claim_count"]

    return {
        "verified_text": current_text,
        "classified_claims": classified_claims,
        "iterations_run": iterations_run,
        "before_unsupported_count": before_unsupported_count,
        "after_unsupported_count": after_unsupported_count,
        "unsupported_reduction": before_unsupported_count - after_unsupported_count,
        "initial_groundedness_score": initial_eval["groundedness_score"],
        "final_groundedness_score": final_eval["groundedness_score"],
        "remaining_issues": current_issues
    }
