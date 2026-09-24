"""
Open Knowledge Format (OKF) v0.2 Schema Definitions.
Conforms to the Open Knowledge Format specification for AI-consumable organizational knowledge bundles.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import datetime


@dataclass
class OKFSource:
    """
    Provenance & Trust Signal (OKF v0.2)
    Tracks the empirical origin, citation, and page number of extracted knowledge.
    """
    document: str
    page: Optional[int] = None
    section: Optional[str] = None
    extracted_date: str = field(default_factory=lambda: datetime.date.today().isoformat())
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OKFSource":
        return cls(
            document=str(data.get("document", "unknown")),
            page=data.get("page"),
            section=data.get("section"),
            extracted_date=str(data.get("extracted_date", datetime.date.today().isoformat())),
            confidence=float(data.get("confidence", 1.0))
        )


@dataclass
class OKFRelationship:
    """
    Structured relationship link to other entities/concepts in the knowledge bundle.
    """
    target: str          # e.g., 'risks/unit-economics-failure' or 'competitors/doordash'
    relation: str        # e.g., 'competes_with', 'exhibits_risk', 'implements_model', 'targets_market'
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OKFRelationship":
        return cls(
            target=str(data.get("target", "")),
            relation=str(data.get("relation", "related_to")),
            description=data.get("description")
        )


@dataclass
class OKFEntity:
    """
    Represents an OKF v0.2 knowledge entity/concept with YAML frontmatter metadata and Markdown body.
    """
    id: str                               # Unique identifier / path (e.g. 'companies/sprig')
    type: str = "entity"                  # entity | concept | case_study | metric | reference
    title: str = ""                       # Human-readable title (e.g. 'Sprig')
    description: str = ""                 # Concise 1-2 sentence executive summary
    category: str = "general"             # companies | competitors | risks | business_models | markets
    tags: List[str] = field(default_factory=list)
    relationships: List[OKFRelationship] = field(default_factory=list)
    sources: List[OKFSource] = field(default_factory=list)
    
    # Trust Signals (OKF v0.2)
    verified: str = "machine-confirmed"   # unverified | machine-confirmed | human-reviewed
    status: str = "CURRENT"               # CURRENT | HISTORICAL | DRAFT | ARCHIVED
    generated: bool = True                # True if extracted by automated ingestion
    created_at: str = field(default_factory=lambda: datetime.date.today().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.date.today().isoformat())

    # Structured Domain Attributes (for startup due diligence)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Markdown Content
    body: str = ""

    def to_frontmatter_dict(self) -> Dict[str, Any]:
        """Converts metadata to YAML frontmatter dictionary."""
        d = {
            "type": self.type,
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "relationships": [r.to_dict() for r in self.relationships],
            "sources": [s.to_dict() for s in self.sources],
            "verified": self.verified,
            "status": self.status,
            "generated": self.generated,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.attributes:
            d["attributes"] = self.attributes
        return d


@dataclass
class OKFManifest:
    """
    Bundle-level manifest (manifest.yaml / okf.yaml) describing the knowledge bundle.
    """
    bundle_id: str
    name: str
    version: str = "1.0.0"
    schema_version: str = "0.2"
    description: str = ""
    author: str = "VentureIQ Ingestion Pipeline"
    created_at: str = field(default_factory=lambda: datetime.date.today().isoformat())
    entity_count: int = 0
    categories: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OKFManifest":
        return cls(
            bundle_id=str(data.get("bundle_id", "startup_diligence_bundle")),
            name=str(data.get("name", "Startup Due Diligence Knowledge Bundle")),
            version=str(data.get("version", "1.0.0")),
            schema_version=str(data.get("schema_version", "0.2")),
            description=str(data.get("description", "")),
            author=str(data.get("author", "VentureIQ Ingestion Pipeline")),
            created_at=str(data.get("created_at", datetime.date.today().isoformat())),
            entity_count=int(data.get("entity_count", 0)),
            categories=list(data.get("categories", []))
        )
