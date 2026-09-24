"""
Historical Backtesting Engine with Strict Date Cutoff (No Look-Ahead Bias).
Enforces: source.publication_date <= evaluation_cutoff_date.
Ensures that future facts, post-mortems, or outcomes cannot leak into historical due diligence.
"""

from typing import List, Dict, Any, Optional
try:
    from evaluation.benchmark_schema import BenchmarkStartup, BenchmarkSource, BenchmarkFact
except ImportError:
    from backend.evaluation.benchmark_schema import BenchmarkStartup, BenchmarkSource, BenchmarkFact


def is_date_prior_or_equal(candidate_date_str: str, cutoff_date_str: str) -> bool:
    """
    Returns True if candidate_date_str <= cutoff_date_str.
    Accepts ISO formats (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
    If date is invalid or UNKNOWN, defaults to False (fail-safe against leakage).
    """
    if not candidate_date_str or candidate_date_str.upper() in ["UNKNOWN", ""]:
        return False
    try:
        cand = datetime.fromisoformat(candidate_date_str[:10])
        cutoff = datetime.fromisoformat(cutoff_date_str[:10])
        return cand <= cutoff
    except Exception:
        return False


def filter_startup_by_cutoff(startup: BenchmarkStartup, cutoff_date: Optional[str] = None) -> BenchmarkStartup:
    """
    Returns a copy of BenchmarkStartup with all sources and facts strictly filtered to:
    publication_date <= cutoff_date.
    The later_outcome is set to None during historical analysis to prevent label leakage.
    """
    active_cutoff = cutoff_date or startup.historical_cutoff
    filtered_sources = [
        s for s in startup.sources
        if is_date_prior_or_equal(s.publication_date, active_cutoff)
    ]
    filtered_facts = [
        f for f in startup.facts
        if is_date_prior_or_equal(f.publication_date, active_cutoff)
    ]
    return BenchmarkStartup(
        startup_id=startup.startup_id,
        name=startup.name,
        industry=startup.industry,
        historical_cutoff=active_cutoff,
        sources=filtered_sources,
        facts=filtered_facts,
        later_outcome=None  # Explicitly stripped during backtesting evaluation
    )


def verify_no_lookahead_bias(startup: BenchmarkStartup, cutoff_date: str) -> Dict[str, Any]:
    """
    Automated verification function that audits whether any filtered source or fact
    leaks information published after the historical cutoff date.
    """
    leaked_sources = [
        s.to_dict() for s in startup.sources
        if not is_date_prior_or_equal(s.publication_date, cutoff_date)
    ]
    leaked_facts = [
        f.to_dict() for f in startup.facts
        if not is_date_prior_or_equal(f.publication_date, cutoff_date)
    ]
    has_leakage = len(leaked_sources) > 0 or len(leaked_facts) > 0
    return {
        "cutoff_date": cutoff_date,
        "passed": not has_leakage,
        "leaked_sources_count": len(leaked_sources),
        "leaked_facts_count": len(leaked_facts),
        "leaked_sources": leaked_sources,
        "leaked_facts": leaked_facts
    }
