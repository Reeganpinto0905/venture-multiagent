"""
Evidence Utilization Analysis Module for VentureIQ.
Tracks evidence pipeline health per knowledge category:
- available: Total empirical items in knowledge base
- retrieved: Items selected by retriever
- used: Items synthesized into agent reasoning / pro-contra
- cited: Items formally referenced with source citation in final report

Formulas:
- retrieval_rate = retrieved / available
- utilization_rate = used / available
- citation_rate = cited / used
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict


def calculate_evidence_utilization(
    available_entities: List[Dict[str, Any]],
    retrieved_entities: List[Dict[str, Any]],
    used_entities: List[Dict[str, Any]],
    cited_ids: List[str]
) -> Dict[str, Any]:
    """
    Computes per-category and macro-level evidence utilization metrics.
    All calculations derive purely from empirical runtime counts.
    """
    categories = ["companies", "competitors", "risks", "business_models", "markets"]

    counts = {
        cat: {
            "available": 0,
            "retrieved": 0,
            "used": 0,
            "cited": 0
        }
        for cat in categories
    }
    counts["other"] = {"available": 0, "retrieved": 0, "used": 0, "cited": 0}

    # Helper for category resolution
    def get_cat(item):
        cat = item.get("category", "other")
        return cat if cat in counts else "other"

    # 1. Available
    for ent in available_entities:
        counts[get_cat(ent)]["available"] += 1

    # 2. Retrieved
    retrieved_ids = set()
    for ent in retrieved_entities:
        eid = ent.get("id") or ent.get("evidence_id")
        if eid and eid not in retrieved_ids:
            retrieved_ids.add(eid)
            counts[get_cat(ent)]["retrieved"] += 1

    # 3. Used
    used_ids = set()
    for ent in used_entities:
        eid = ent.get("id") or ent.get("evidence_id")
        if eid and eid not in used_ids:
            used_ids.add(eid)
            counts[get_cat(ent)]["used"] += 1

    # 4. Cited
    normalized_cited = {cid.lower() for cid in cited_ids}
    for ent in used_entities:
        eid = (ent.get("id") or ent.get("evidence_id") or "").lower()
        if eid in normalized_cited:
            counts[get_cat(ent)]["cited"] += 1

    # Calculate per-category rates
    per_category_metrics = {}
    macro = {"available": 0, "retrieved": 0, "used": 0, "cited": 0}

    for cat, data in counts.items():
        avail = data["available"]
        ret = data["retrieved"]
        usd = data["used"]
        cit = data["cited"]

        macro["available"] += avail
        macro["retrieved"] += ret
        macro["used"] += usd
        macro["cited"] += cit

        r_rate = round((ret / avail * 100), 2) if avail > 0 else 0.0
        u_rate = round((usd / avail * 100), 2) if avail > 0 else 0.0
        c_rate = round((cit / usd * 100), 2) if usd > 0 else 0.0

        per_category_metrics[cat] = {
            "available": avail,
            "retrieved": ret,
            "used": usd,
            "cited": cit,
            "retrieval_rate_percent": r_rate,
            "utilization_rate_percent": u_rate,
            "citation_rate_percent": c_rate
        }

    macro_retrieval_rate = round((macro["retrieved"] / macro["available"] * 100), 2) if macro["available"] > 0 else 0.0
    macro_utilization_rate = round((macro["used"] / macro["available"] * 100), 2) if macro["available"] > 0 else 0.0
    macro_citation_rate = round((macro["cited"] / macro["used"] * 100), 2) if macro["used"] > 0 else 0.0

    return {
        "macro_metrics": {
            "total_available": macro["available"],
            "total_retrieved": macro["retrieved"],
            "total_used": macro["used"],
            "total_cited": macro["cited"],
            "retrieval_rate": {
                "value_percent": macro_retrieval_rate,
                "formula": "retrieved / available * 100",
                "numerator": macro["retrieved"],
                "denominator": macro["available"]
            },
            "utilization_rate": {
                "value_percent": macro_utilization_rate,
                "formula": "used / available * 100",
                "numerator": macro["used"],
                "denominator": macro["available"]
            },
            "citation_rate": {
                "value_percent": macro_citation_rate,
                "formula": "cited / used * 100",
                "numerator": macro["cited"],
                "denominator": macro["used"]
            }
        },
        "per_category": per_category_metrics
    }
