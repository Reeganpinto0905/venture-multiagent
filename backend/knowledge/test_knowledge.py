"""
Test suite for VentureIQ Open Knowledge Format (OKF v0.2) Architecture.
Verifies bundle loading, schema conformance, provenance signals, BM25 indexing,
graph relationship traversal, and LangGraph workflow node compatibility.
"""

import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from knowledge.loader import get_default_bundle
from knowledge.retriever import (
    retrieve_context,
    retrieve_context_node,
    find_competitors,
    find_risks,
    validate_knowledge_env,
    get_knowledge_index
)


def run_okf_diagnostic():
    print("=" * 60)
    print("VENTUREIQ OPEN KNOWLEDGE FORMAT (OKF v0.2) DIAGNOSTIC TEST")
    print("=" * 60)

    # 1. Environment & Bundle Validation
    print("\n[TEST 1] Validating OKF Environment & Manifest...")
    is_valid = validate_knowledge_env()
    assert is_valid, "validate_knowledge_env() failed"

    bundle = get_default_bundle()
    assert bundle.loaded, "Bundle failed to load"
    assert bundle.manifest is not None, "Bundle manifest is missing"
    print(f"  Bundle Name: {bundle.manifest.name}")
    print(f"  OKF Schema: v{bundle.manifest.schema_version}")
    print(f"  Entity Count: {len(bundle.entities)}")
    print(f"  Categories: {list(bundle.categories.keys())}")
    assert len(bundle.entities) >= 60, f"Expected at least 60 entities, found {len(bundle.entities)}"

    # 2. Entity Schema & Provenance Check
    print("\n[TEST 2] Verifying Empirical Provenance Signals (OKF v0.2)...")
    sample_entities = ["companies/quibi", "companies/airbnb", "competitors/leetcode"]
    for eid in sample_entities:
        e = bundle.entities.get(eid)
        assert e is not None, f"Entity {eid} not found in bundle"
        assert len(e.sources) > 0, f"Entity {eid} missing source citations"
        src = e.sources[0]
        print(f"  Entity '{e.title}' -> Doc: {src.document}, Page: {src.page}, Section: {src.section}, Trust: {e.verified}")
        assert src.document.endswith(".pdf"), f"Invalid source document format: {src.document}"
        assert src.page is not None and src.page >= 1, f"Missing or invalid page: {src.page}"

    # 3. Relationship Graph Traversal
    print("\n[TEST 3] Verifying Graph Adjacency & Traversal...")
    index = get_knowledge_index()
    unit_risk = bundle.entities.get("risks/unit-economics-failure")
    assert unit_risk is not None, "unit-economics-failure risk entity missing"
    assert len(unit_risk.relationships) > 0, "No relationships linked to unit economics risk"
    print(f"  'Unit Economics Failure' exhibits connections to:")
    for rel in unit_risk.relationships:
        print(f"    - [{rel.relation}] -> {rel.target} ({rel.description})")

    # 4. Agentic BM25 Search
    print("\n[TEST 4] Testing Agentic OKF BM25 Search...")
    queries = [
        ("food delivery unit economics driver burn", "risks/companies"),
        ("coding interview practice technical assessment", "competitors"),
        ("developer infrastructure API billing", "business_models/companies")
    ]
    for q, desc in queries:
        ranked = index.search(q, top_k=3)
        print(f"  Query: '{q}' ({desc}) ->")
        for ent, score in ranked:
            print(f"    • [{score:.2f}] {ent.title} ({ent.id}) - Category: {ent.category}")

    # 5. Drop-in Context Retrieval for Agents
    print("\n[TEST 5] Testing retrieve_context() Formatting for LLM Prompt Injection...")
    ctx = retrieve_context("AI interview prep platform for engineering students", top_k=3)
    assert ctx, "retrieve_context returned empty string"
    assert "OKF Evidence" in ctx, "Context missing OKF Evidence header"
    assert "Source Provenance:" in ctx, "Context missing Source Provenance header"
    print("  Evidence excerpt preview:")
    lines = ctx.split("\n")[:8]
    for line in lines:
        print(f"    {line}")

    # 6. LangGraph State Node Compatibility
    print("\n[TEST 6] Testing LangGraph retrieve_context_node State Contract...")
    dummy_state = {"user_query": "B2B SaaS churn and CAC payback benchmarking"}
    node_out = retrieve_context_node(dummy_state)
    assert isinstance(node_out, dict), "Node output must be a dict"
    assert "retrieved_context" in node_out, "Node output must contain 'retrieved_context'"
    assert len(node_out["retrieved_context"]) > 0, "retrieved_context must not be empty"
    print(f"  Node successfully returned {len(node_out['retrieved_context'])} chars of retrieved_context")

    # 7. Specialized Agent Discovery
    print("\n[TEST 7] Testing Specialized Agent Endpoints...")
    comps = find_competitors("software engineer technical coding tests", top_k=3)
    assert len(comps) > 0, "find_competitors returned empty"
    print(f"  find_competitors returned: {[c['name'] for c in comps]}")

    risks = find_risks("rapid geographic expansion negative unit margins", top_k=2)
    assert len(risks) > 0, "find_risks returned empty"
    print(f"  find_risks returned: {[r['title'] for r in risks]}")

    print("\n" + "=" * 60)
    print("ALL 7 OKF DIAGNOSTIC TESTS PASSED CLEANLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_okf_diagnostic()
