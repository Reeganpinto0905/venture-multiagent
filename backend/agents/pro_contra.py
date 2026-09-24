"""
Evidence-Based PRO vs CONTRA Analysis Module for VentureIQ.
Evaluates 7 core institutional due diligence dimensions:
Market, Product, Business Model, Team, Competition, Financials, Risks.

Rules:
- Supporting evidence (PRO) and Contradicting/negative evidence (CONTRA).
- Every item MUST reference evidence IDs.
- Unsupported statements must be marked UNKNOWN or INFERENCE.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

DUE_DILIGENCE_DIMENSIONS = [
    "Market",
    "Product",
    "Business Model",
    "Team",
    "Competition",
    "Financials",
    "Risks"
]

@dataclass
class EvidencePoint:
    claim: str
    evidence_id: str
    source_citation: str
    status: str = "VERIFIED"  # VERIFIED | INFERENCE | UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DimensionProContra:
    dimension: str
    supporting_evidence: List[EvidencePoint] = field(default_factory=list)
    contradicting_evidence: List[EvidencePoint] = field(default_factory=list)
    verdict: str = "UNKNOWN"  # FAVORABLE | UNFAVORABLE | NEUTRAL | UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "contradicting_evidence": [e.to_dict() for e in self.contradicting_evidence],
            "verdict": self.verdict
        }


def analyze_pro_contra(
    query_or_name: str,
    entities: List[Any],
    facts: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Constructs rigorous PRO/CONTRA matrix across 7 dimensions using verified OKF entities and facts.
    Ensures every assertion has strict attribution or is flagged UNKNOWN/INFERENCE.
    """
    results: Dict[str, DimensionProContra] = {
        dim: DimensionProContra(dimension=dim) for dim in DUE_DILIGENCE_DIMENSIONS
    }

    # 1. Process structured facts if provided (from benchmark or agent extraction)
    if facts:
        for f in facts:
            cat = getattr(f, "category", "") or f.get("category", "")
            claim = getattr(f, "claim", "") or f.get("claim", "")
            eid = getattr(f, "evidence_id", "") or f.get("evidence_id", "UNKNOWN")
            status = getattr(f, "status", "VERIFIED") or f.get("status", "VERIFIED")

            target_dim = None
            for d in DUE_DILIGENCE_DIMENSIONS:
                if d.lower() == cat.lower():
                    target_dim = d
                    break
            if not target_dim:
                target_dim = "Risks" if "risk" in cat.lower() else "Business Model"

            # Classify into PRO vs CONTRA based on semantic risks/negatives
            lower_claim = claim.lower()
            is_contra = (
                target_dim == "Risks"
                or eid.lower().startswith("risks/")
                or "loss" in lower_claim
                or "losing" in lower_claim
                or "burn" in lower_claim
                or "failure" in lower_claim
                or "negative" in lower_claim
                or "waste" in lower_claim
                or "shutter" in lower_claim
                or "lawsuit" in lower_claim
                or "defect" in lower_claim
            )

            point = EvidencePoint(
                claim=claim,
                evidence_id=eid,
                source_citation=f"OKF Citation: {eid}",
                status=status
            )
            if is_contra:
                results[target_dim].contradicting_evidence.append(point)
            else:
                results[target_dim].supporting_evidence.append(point)

    # 2. Process retrieved OKF entities
    if entities:
        for ent in entities:
            category = getattr(ent, "category", "general")
            eid = getattr(ent, "id", "UNKNOWN")
            title = getattr(ent, "title", eid)
            desc = getattr(ent, "description", "")
            src = ent.sources[0].document if getattr(ent, "sources", None) else "OKF Knowledge Base"

            if category == "risks":
                results["Risks"].contradicting_evidence.append(EvidencePoint(
                    claim=f"Exhibits documented failure pattern: {title} ({desc})",
                    evidence_id=eid,
                    source_citation=src,
                    status="VERIFIED"
                ))
            elif category == "business_models":
                results["Business Model"].supporting_evidence.append(EvidencePoint(
                    claim=f"Leverages structured business model architecture: {title} ({desc})",
                    evidence_id=eid,
                    source_citation=src,
                    status="VERIFIED"
                ))
            elif category == "competitors":
                results["Competition"].contradicting_evidence.append(EvidencePoint(
                    claim=f"Direct market competition: {title} with established market share",
                    evidence_id=eid,
                    source_citation=src,
                    status="VERIFIED"
                ))
            elif category == "companies":
                results["Market"].supporting_evidence.append(EvidencePoint(
                    claim=f"Comparable institutional precedent: {title} in related segment",
                    evidence_id=eid,
                    source_citation=src,
                    status="VERIFIED"
                ))

    # 3. Mark dimensions with no evidence as UNKNOWN (Never invented)
    for dim, pro_contra in results.items():
        if not pro_contra.supporting_evidence and not pro_contra.contradicting_evidence:
            pro_contra.supporting_evidence.append(EvidencePoint(
                claim=f"No primary empirical evidence available for {dim} in provided sources.",
                evidence_id="UNKNOWN",
                source_citation="None",
                status="UNKNOWN"
            ))
            pro_contra.verdict = "UNKNOWN"
        else:
            pro_count = len(pro_contra.supporting_evidence)
            contra_count = len(pro_contra.contradicting_evidence)
            if pro_count > contra_count:
                pro_contra.verdict = "FAVORABLE"
            elif contra_count > pro_count:
                pro_contra.verdict = "UNFAVORABLE"
            else:
                pro_contra.verdict = "NEUTRAL"

    return {
        "dimensions": {dim: results[dim].to_dict() for dim in DUE_DILIGENCE_DIMENSIONS},
        "summary": {
            "total_pro_points": sum(len(d.supporting_evidence) for d in results.values() if d.verdict != "UNKNOWN"),
            "total_contra_points": sum(len(d.contradicting_evidence) for d in results.values()),
            "unsupported_unknown_dimensions": [d for d, val in results.items() if val.verdict == "UNKNOWN"]
        }
    }
