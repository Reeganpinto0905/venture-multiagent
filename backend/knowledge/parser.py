"""
OKF v0.2 Parser: Serializes and deserializes OKF entity markdown files with YAML frontmatter.
"""

import re
import yaml
from knowledge.schema import OKFEntity, OKFSource, OKFRelationship


def parse_okf_markdown(text: str) -> OKFEntity:
    """
    Parses a Markdown string containing YAML frontmatter into an OKFEntity instance.
    """
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, text, re.DOTALL)
    
    if not match:
        # Fallback if no frontmatter found
        return OKFEntity(
            id="unknown",
            title="Untitled Concept",
            body=text.strip()
        )

    frontmatter_raw, body_raw = match.groups()
    try:
        data = yaml.safe_load(frontmatter_raw) or {}
    except Exception as e:
        print(f"[OKF PARSER WARN] Failed to parse YAML frontmatter: {e}")
        data = {}

    sources = [OKFSource.from_dict(s) for s in data.get("sources", [])]
    relationships = [OKFRelationship.from_dict(r) for r in data.get("relationships", [])]

    return OKFEntity(
        id=str(data.get("id", "concept")),
        type=str(data.get("type", "entity")),
        title=str(data.get("title", "")),
        description=str(data.get("description", "")),
        category=str(data.get("category", "general")),
        tags=list(data.get("tags", [])),
        relationships=relationships,
        sources=sources,
        verified=str(data.get("verified", "machine-confirmed")),
        status=str(data.get("status", "CURRENT")),
        generated=bool(data.get("generated", True)),
        created_at=str(data.get("created_at", "")),
        updated_at=str(data.get("updated_at", "")),
        attributes=dict(data.get("attributes", {})),
        body=body_raw.strip()
    )


def serialize_okf_markdown(entity: OKFEntity) -> str:
    """
    Serializes an OKFEntity into an official OKF v0.2 Markdown file with YAML frontmatter.
    """
    fm_dict = entity.to_frontmatter_dict()
    yaml_str = yaml.dump(fm_dict, sort_keys=False, allow_unicode=True, default_flow_style=False)
    
    return f"---\n{yaml_str}---\n\n{entity.body.strip()}\n"
