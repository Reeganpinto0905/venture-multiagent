"""
Benchmark Dataset Schema and Public Pilot Dataset for VentureIQ.
Public sources only, strictly verifiable, tracks publication dates, historical cutoffs,
and public startup outcomes. Unknown information is recorded as UNKNOWN.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import datetime
import json
import os

@dataclass
class BenchmarkSource:
    document: str
    publication_date: str  # YYYY-MM-DD
    url_or_citation: str
    source_type: str = "public_filing_or_press"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class BenchmarkFact:
    fact_id: str
    category: str  # Market, Product, Business Model, Team, Competition, Financials, Risks
    claim: str
    evidence_id: str
    publication_date: str  # YYYY-MM-DD
    status: str = "VERIFIED"  # VERIFIED | INFERENCE | UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class StartupOutcome:
    status: str  # SUCCESS | FAILURE | ACQUIRED | UNKNOWN
    outcome_date: str  # YYYY-MM-DD
    summary: str
    public_reference: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class BenchmarkStartup:
    startup_id: str
    name: str
    industry: str
    historical_cutoff: str  # YYYY-MM-DD: evaluation date prior to final outcome
    sources: List[BenchmarkSource] = field(default_factory=list)
    facts: List[BenchmarkFact] = field(default_factory=list)
    later_outcome: Optional[StartupOutcome] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "startup_id": self.startup_id,
            "name": self.name,
            "industry": self.industry,
            "historical_cutoff": self.historical_cutoff,
            "sources": [s.to_dict() for s in self.sources],
            "facts": [f.to_dict() for f in self.facts],
            "later_outcome": self.later_outcome.to_dict() if self.later_outcome else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkStartup":
        sources = [BenchmarkSource(**s) for s in data.get("sources", [])]
        facts = [BenchmarkFact(**f) for f in data.get("facts", [])]
        outcome_data = data.get("later_outcome")
        outcome = StartupOutcome(**outcome_data) if outcome_data else None
        return cls(
            startup_id=data["startup_id"],
            name=data["name"],
            industry=data["industry"],
            historical_cutoff=data["historical_cutoff"],
            sources=sources,
            facts=facts,
            later_outcome=outcome
        )


def load_benchmark_dataset(path: Optional[str] = None) -> List[BenchmarkStartup]:
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "benchmark_dataset.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [BenchmarkStartup.from_dict(item) for item in data.get("startups", [])]
