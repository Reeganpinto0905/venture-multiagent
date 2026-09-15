import hashlib
import json
import os
import sqlite3
import time
from typing import Any, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "ventureiq_cache.db")
CACHE_VERSION = "v1.0"


class CacheStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._stats = {"hits": 0, "misses": 0, "sets": 0}
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)")
            conn.commit()

    @staticmethod
    def compute_key(context: str, task: str, query: str, version: str = CACHE_VERSION) -> str:
        raw = f"{version}:{task.strip().lower()}:{context.strip().lower()}:{query.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value, expires_at FROM cache_entries WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row:
                self._stats["misses"] += 1
                return None
            if row["expires_at"] < now:
                cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            try:
                return json.loads(row["value"])
            except Exception:
                return row["value"]

    def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        now = time.time()
        expires_at = now + ttl
        serialized = json.dumps(value) if isinstance(value, (dict, list, bool, int, float)) else str(value)

        for secret_env in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "PINECONE_API_KEY", "TAVILY_API_KEY"):
            val = os.getenv(secret_env)
            if val and len(val) > 8:
                serialized = serialized.replace(val, "[REDACTED_SECRET]")

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO cache_entries (key, value, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
            """, (key, serialized, now, expires_at))
            conn.commit()
            self._stats["sets"] += 1

    def get_stats(self) -> Dict[str, Any]:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = round((self._stats["hits"] / total) * 100, 1) if total > 0 else 0.0
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "total_requests": total,
            "hit_rate_pct": hit_rate,
        }


cache_store = CacheStore()

