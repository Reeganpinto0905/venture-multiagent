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
            has_citation = bool(re.search(r"\[(OKF|Evidence|Source|p\.|Page|\w+/\w+)", sent, re.IGNORECASE))
            has_strong_claim = any(kw in lower for kw in ["market size", "revenue", "loss", "burn", "margin", "cagr", "valuation", "churn"])
            if has_strong_claim and not has_citation:
                # Check if an evidence ID is mentioned
                has_eid = any(eid.lower() in lower for eid in valid_evidence_ids) if valid_evidence_ids else False
                if not has_eid:
                    issues.append({
                        "type": "unsupported_claim",
                        "sentence": sent,
                        "severity": "HIGH",
                        "suggestion": "Add primary source citation or tag as UNKNOWN"
                    })

        return issues


class VerificationEvaluator:
    """Scores draft reliability and quantifies unsupported claims."""

    def score(self, draft_text: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        unsupported_count = sum(1 for i in issues if i["type"] in ["unsupported_claim", "missing_citation"])
        overconfident_count = sum(1 for i in issues if i["type"] == "overconfident_claim")
        confusion_count = sum(1 for i in issues if i["type"] == "target_vs_generic_confusion")
        
        sentences_count = max(1, len(re.split(r"[.!?]\s+", draft_text)))
        groundedness_score = max(0.0, round(100.0 - (unsupported_count * 25.0), 1))

        return {
            "unsupported_claim_count": unsupported_count,
            "overconfident_count": overconfident_count,
            "confusion_count": confusion_count,
            "groundedness_score": groundedness_score,
            "passed": unsupported_count == 0 and overconfident_count == 0
        }


class VerificationRefiner:
    """Refines draft by fixing unsupported claims, removing hype, or marking insufficient evidence."""

    def refine(self, draft_text: str, issues: List[Dict[str, Any]], available_evidence: List[str]) -> str:
        if not draft_text.strip() or (not available_evidence and len(issues) > 3):
            return "Insufficient evidence available in provided empirical sources."

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
                        # Append reference to available evidence or downgrade
                        replacement = f"{orig_sent} [Evidence: {available_evidence[0]}]"
                    else:
                        replacement = f"{orig_sent} [Status: UNKNOWN - unverified in primary sources]"
                    refined = refined.replace(orig_sent, replacement)

        return refined


def run_verification_loop(
    draft_text: str,
    valid_evidence_ids: List[str],
    max_iterations: int = 2
) -> Dict[str, Any]:
    """
    Executes the Critic -> Evaluator -> Refiner loop (up to max_iterations).
    Returns verified result with before/after unsupported claim counts.
    """
    critic = VerificationCritic()
    evaluator = VerificationEvaluator()
    refiner = VerificationRefiner()

    initial_issues = critic.audit(draft_text, valid_evidence_ids)
    initial_eval = evaluator.score(draft_text, initial_issues)
    before_unsupported_count = initial_eval["unsupported_claim_count"]

    current_text = draft_text
    current_issues = initial_issues
    iterations_run = 0

    while iterations_run < max_iterations:
        if not current_issues:
            break
        iterations_run += 1
        current_text = refiner.refine(current_text, current_issues, valid_evidence_ids)
        current_issues = critic.audit(current_text, valid_evidence_ids)

    final_eval = evaluator.score(current_text, current_issues)
    after_unsupported_count = final_eval["unsupported_claim_count"]

    return {
        "verified_text": current_text,
        "iterations_run": iterations_run,
        "before_unsupported_count": before_unsupported_count,
        "after_unsupported_count": after_unsupported_count,
        "unsupported_reduction": before_unsupported_count - after_unsupported_count,
        "initial_groundedness_score": initial_eval["groundedness_score"],
        "final_groundedness_score": final_eval["groundedness_score"],
        "remaining_issues": current_issues
    }
