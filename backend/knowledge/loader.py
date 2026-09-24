"""
OKF v0.2 Bundle Loader: Loads, validates, and indexes an on-disk OKF knowledge bundle directory.
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from knowledge.schema import OKFEntity, OKFManifest
from knowledge.parser import parse_okf_markdown


class OKFBundle:
    """
    In-memory representation of an OKF Knowledge Bundle.
    """
    def __init__(self, bundle_dir: str):
        self.bundle_dir = os.path.abspath(bundle_dir)
        self.manifest: Optional[OKFManifest] = None
        self.entities: Dict[str, OKFEntity] = {}              # id -> OKFEntity
        self.categories: Dict[str, List[OKFEntity]] = {}      # category -> [OKFEntity]
        self.tag_index: Dict[str, List[OKFEntity]] = {}       # tag -> [OKFEntity]
        self.adjacency: Dict[str, List[Dict[str, str]]] = {}  # id -> [{target, relation}]
        self.catalog_markdown: str = ""
        self.loaded = False

    def load(self) -> "OKFBundle":
        """
        Loads all entities and manifest from bundle_dir.
        """
        if not os.path.isdir(self.bundle_dir):
            print(f"[OKF LOADER WARN] Bundle directory '{self.bundle_dir}' not found.")
            return self

        # 1. Load manifest
        manifest_path = os.path.join(self.bundle_dir, "manifest.yaml")
        if not os.path.exists(manifest_path):
            manifest_path = os.path.join(self.bundle_dir, "okf.yaml")

        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    m_data = yaml.safe_load(f) or {}
                self.manifest = OKFManifest.from_dict(m_data)
            except Exception as e:
                print(f"[OKF LOADER WARN] Error reading bundle manifest: {e}")

        # 2. Load index.md if present
        index_path = os.path.join(self.bundle_dir, "index.md")
        if os.path.exists(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    self.catalog_markdown = f.read()
            except Exception as e:
                print(f"[OKF LOADER WARN] Error reading index.md: {e}")

        # 3. Recursively find and load entity markdown files
        self.entities.clear()
        self.categories.clear()
        self.tag_index.clear()
        self.adjacency.clear()

        for root, _, files in os.walk(self.bundle_dir):
            for file in files:
                if file.endswith(".md") and file != "index.md" and not file.startswith("."):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            raw_content = f.read()
                        entity = parse_okf_markdown(raw_content)
                        if not entity.id or entity.id == "unknown":
                            # Derive id from relative path
                            rel_path = os.path.relpath(file_path, self.bundle_dir)
                            entity.id = rel_path.replace("\\", "/").rsplit(".", 1)[0]

                        self.entities[entity.id] = entity

                        # Category map
                        cat = entity.category or "general"
                        if cat not in self.categories:
                            self.categories[cat] = []
                        self.categories[cat].append(entity)

                        # Tag index
                        for tag in entity.tags:
                            tag_clean = tag.lower().strip()
                            if tag_clean not in self.tag_index:
                                self.tag_index[tag_clean] = []
                            self.tag_index[tag_clean].append(entity)

                        # Graph adjacency
                        if entity.id not in self.adjacency:
                            self.adjacency[entity.id] = []
                        for rel in entity.relationships:
                            self.adjacency[entity.id].append({
                                "target": rel.target,
                                "relation": rel.relation,
                                "description": rel.description
                            })

                    except Exception as exc:
                        print(f"[OKF LOADER ERROR] Failed to load entity file '{file_path}': {exc}")

        self.loaded = True
        print(f"[OKF LOADER INFO] Successfully loaded OKF bundle '{os.path.basename(self.bundle_dir)}' ({len(self.entities)} entities across {len(self.categories)} categories)")
        return self


_DEFAULT_BUNDLE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_data", "startup_diligence_bundle")
)
_BUNDLE_INSTANCE: Optional[OKFBundle] = None


def get_default_bundle(bundle_path: Optional[str] = None) -> OKFBundle:
    """
    Singleton accessor for the active OKF knowledge bundle.
    """
    global _BUNDLE_INSTANCE
    target_path = bundle_path or _DEFAULT_BUNDLE_PATH
    if _BUNDLE_INSTANCE is None or _BUNDLE_INSTANCE.bundle_dir != target_path:
        _BUNDLE_INSTANCE = OKFBundle(target_path).load()
    return _BUNDLE_INSTANCE
