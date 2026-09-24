"""
OKF v0.2 Knowledge Index: High-speed in-memory indexing, inverted term matching, and graph traversal.
"""

import math
import re
from typing import Dict, List, Optional, Set, Tuple, Any
from knowledge.schema import OKFEntity
from knowledge.loader import OKFBundle


class OKFKnowledgeIndex:
    """
    Search and traversal index over an OKF Knowledge Bundle.
    Combines structured graph queries with term-frequency relevance matching.
    """
    def __init__(self, bundle: OKFBundle):
        self.bundle = bundle
        self.doc_term_freqs: Dict[str, Dict[str, int]] = {}   # entity_id -> {term: freq}
        self.doc_lengths: Dict[str, int] = {}                  # entity_id -> total_terms
        self.inverted_index: Dict[str, Set[str]] = {}          # term -> {entity_ids}
        self.avg_doc_length: float = 0.0
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """Simple, fast tokenizer for alphanumeric words, lowercase."""
        if not text:
            return []
        return [w.lower() for w in re.findall(r"\b[A-Za-z0-9_-]{2,}\b", text)]

    def _build_index(self):
        """Builds token-level inverted index for BM25-style relevance scoring."""
        total_tokens = 0
        self.inverted_index.clear()
        self.doc_term_freqs.clear()
        self.doc_lengths.clear()

        for entity_id, entity in self.bundle.entities.items():
            # Weight title heavily (3x), description (2x), tags (2x), body (1x)
            title_tokens = self._tokenize(entity.title) * 3
            desc_tokens = self._tokenize(entity.description) * 2
            tag_tokens = self._tokenize(" ".join(entity.tags)) * 2
            body_tokens = self._tokenize(entity.body[:3000])

            all_tokens = title_tokens + desc_tokens + tag_tokens + body_tokens
            doc_len = len(all_tokens)
            self.doc_lengths[entity_id] = max(1, doc_len)
            total_tokens += doc_len

            freqs: Dict[str, int] = {}
            for t in all_tokens:
                freqs[t] = freqs.get(t, 0) + 1
                if t not in self.inverted_index:
                    self.inverted_index[t] = set()
                self.inverted_index[t].add(entity_id)

            self.doc_term_freqs[entity_id] = freqs

        num_docs = len(self.bundle.entities)
        self.avg_doc_length = (total_tokens / num_docs) if num_docs > 0 else 1.0

    def get_entity(self, entity_id: str) -> Optional[OKFEntity]:
        """Direct lookup by entity ID."""
        return self.bundle.entities.get(entity_id)

    def get_by_category(self, category: str) -> List[OKFEntity]:
        """Returns all entities in a given category."""
        return self.bundle.categories.get(category, [])

    def get_by_tag(self, tag: str) -> List[OKFEntity]:
        """Returns all entities matching a given tag."""
        return self.bundle.tag_index.get(tag.lower().strip(), [])

    def get_related(self, entity_id: str, relation_type: Optional[str] = None) -> List[Tuple[OKFEntity, str]]:
        """
        Traverses knowledge graph relationships for an entity.
        Returns list of (target_entity, relation_name).
        """
        results = []
        relationships = self.bundle.adjacency.get(entity_id, [])
        for rel in relationships:
            target_id = rel["target"]
            rel_name = rel["relation"]
            if relation_type is None or relation_type == rel_name:
                target_entity = self.get_entity(target_id)
                if target_entity:
                    results.append((target_entity, rel_name))
        return results

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Tuple[OKFEntity, float]]:
        """
        Performs BM25-inspired term ranking over indexed entities, with category and tag filtering.
        """
        query_terms = self._tokenize(query)
        if not query_terms:
            # Fallback to returning top entities in category
            pool = self.get_by_category(category) if category else list(self.bundle.entities.values())
            return [(e, 1.0) for e in pool[:top_k]]

        scores: Dict[str, float] = {}
        num_docs = len(self.bundle.entities)
        k1 = 1.2
        b = 0.75

        # Filter candidate pool if category or tags specified
        candidate_ids: Optional[Set[str]] = None
        if category and category in self.bundle.categories:
            candidate_ids = {e.id for e in self.bundle.categories[category]}

        if tags:
            tag_candidates = set()
            for t in tags:
                for e in self.get_by_tag(t):
                    tag_candidates.add(e.id)
            if candidate_ids is None:
                candidate_ids = tag_candidates
            else:
                candidate_ids = candidate_ids.intersection(tag_candidates)

        for term in query_terms:
            if term not in self.inverted_index:
                continue
            matching_doc_ids = self.inverted_index[term]
            if candidate_ids is not None:
                matching_doc_ids = matching_doc_ids.intersection(candidate_ids)

            df = len(matching_doc_ids)
            idf = math.log(1.0 + (num_docs - df + 0.5) / (df + 0.5))

            for doc_id in matching_doc_ids:
                tf = self.doc_term_freqs[doc_id].get(term, 0)
                doc_len = self.doc_lengths[doc_id]
                denom = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_length))
                score = idf * (tf * (k1 + 1.0)) / denom if denom > 0 else 0
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for doc_id, score in ranked[:top_k]:
            entity = self.get_entity(doc_id)
            if entity:
                results.append((entity, round(score, 4)))

        # If zero results matched specific terms, fallback to category or general pool
        if not results:
            pool = self.get_by_category(category) if category else list(self.bundle.entities.values())
            for e in pool[:top_k]:
                results.append((e, 0.1))

        return results
