"""
Historical Outcome Prediction Metrics for VentureIQ.
Evaluates model risk assessment / diligence verdict against verifiable public historical outcomes.

Metrics:
- Precision
- Recall
- F1 Score
- AUC-PR (Area Under Precision-Recall Curve)
- Confusion Matrix: TP, FP, TN, FN
- Total Labeled Cases

Rules:
- Strictly only calculated for startups with verified public outcomes.
- If total labeled cases < MIN_REQUIRED_LABELED_CASES, outputs "Not experimentally verified".
- Never invents or hardcodes numbers.
"""

from typing import Dict, Any, List, Optional

MIN_REQUIRED_LABELED_CASES = 4  # Minimum threshold for statistical reporting


def compute_auc_pr(precisions: List[float], recalls: List[float]) -> float:
    """
    Computes Area Under Precision-Recall curve using trapezoidal rule.
    """
    if not precisions or not recalls or len(precisions) != len(recalls):
        return 0.0
    # Sort by recall ascending
    points = sorted(zip(recalls, precisions), key=lambda x: x[0])
    area = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        avg_y = (points[i][1] + points[i - 1][1]) / 2.0
        area += dx * avg_y
    return max(0.0, min(1.0, round(area, 4)))


def evaluate_outcome_prediction(
    cases: List[Dict[str, Any]],
    positive_label: str = "FAILURE"
) -> Dict[str, Any]:
    """
    Evaluates predictions against ground truth public outcomes.
    
    Each case is a dict with:
    - startup_id: str
    - predicted_verdict: "FAILURE" | "SUCCESS" | "UNKNOWN"
    - risk_score: float (0.0 to 100.0)
    - actual_outcome: "FAILURE" | "SUCCESS" | "UNKNOWN"
    """
    # 1. Filter only cases with known ground truth
    labeled_cases = [
        c for c in cases
        if c.get("actual_outcome") and c["actual_outcome"].upper() not in ["UNKNOWN", ""]
        and c.get("predicted_verdict") and c["predicted_verdict"].upper() not in ["UNKNOWN", ""]
    ]

    total_labeled = len(labeled_cases)

    # If insufficient labeled data, fail-safe to "Not experimentally verified"
    if total_labeled < MIN_REQUIRED_LABELED_CASES:
        return {
            "status": "Not experimentally verified",
            "reason": f"Insufficient verified labeled historical cases (N = {total_labeled}, required >= {MIN_REQUIRED_LABELED_CASES})",
            "total_labeled_cases": total_labeled,
            "min_required_cases": MIN_REQUIRED_LABELED_CASES,
            "metrics": {
                "precision": "Not experimentally verified",
                "recall": "Not experimentally verified",
                "f1": "Not experimentally verified",
                "auc_pr": "Not experimentally verified"
            }
        }

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for c in labeled_cases:
        actual_pos = (c["actual_outcome"].upper() == positive_label.upper())
        pred_pos = (c["predicted_verdict"].upper() == positive_label.upper())

        if actual_pos and pred_pos:
            tp += 1
        elif not actual_pos and pred_pos:
            fp += 1
        elif not actual_pos and not pred_pos:
            tn += 1
        elif actual_pos and not pred_pos:
            fn += 1

    precision = round(tp / (tp + fp) * 100, 2) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn) * 100, 2) if (tp + fn) > 0 else 0.0
    f1 = round(2 * (precision * recall) / (precision + recall), 2) if (precision + recall) > 0 else 0.0

    # Calculate AUC-PR points across probability/risk thresholds
    thresholds = [10, 30, 50, 70, 90]
    p_curve = []
    r_curve = []
    for th in thresholds:
        th_tp = sum(1 for c in labeled_cases if c["actual_outcome"].upper() == positive_label.upper() and c.get("risk_score", 0) >= th)
        th_fp = sum(1 for c in labeled_cases if c["actual_outcome"].upper() != positive_label.upper() and c.get("risk_score", 0) >= th)
        th_fn = sum(1 for c in labeled_cases if c["actual_outcome"].upper() == positive_label.upper() and c.get("risk_score", 0) < th)

        p = (th_tp / (th_tp + th_fp)) if (th_tp + th_fp) > 0 else 1.0
        r = (th_tp / (th_tp + th_fn)) if (th_tp + th_fn) > 0 else 0.0
        p_curve.append(p)
        r_curve.append(r)

    auc_pr = compute_auc_pr(p_curve, r_curve)

    return {
        "status": "EXPERIMENTALLY_VERIFIED",
        "target_class": positive_label,
        "total_labeled_cases": total_labeled,
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        },
        "metrics": {
            "precision": {
                "value_percent": precision,
                "formula": "TP / (TP + FP) * 100",
                "numerator": tp,
                "denominator": tp + fp
            },
            "recall": {
                "value_percent": recall,
                "formula": "TP / (TP + FN) * 100",
                "numerator": tp,
                "denominator": tp + fn
            },
            "f1": {
                "value_percent": f1,
                "formula": "2 * (Precision * Recall) / (Precision + Recall)",
                "precision": precision,
                "recall": recall
            },
            "auc_pr": {
                "value": auc_pr,
                "formula": "trapezoidal_integration(precision_recall_curve)",
                "thresholds_evaluated": thresholds
            }
        },
        "raw_cases": labeled_cases
    }
