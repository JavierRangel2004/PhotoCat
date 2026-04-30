"""
cache.py — SQLite-backed result cache for PhotoCat.

Stores deterministic model outputs per image so re-runs after changing
genre_decision.py only recompute make_genre_decision(), not YOLO/BLIP/SigLIP.

Cache key: absolute image path
Invalidation: file mtime + size mismatch OR cache_version bump
"""

import json
import os
import sqlite3
from typing import Optional

# Bump this when the payload schema or model set changes.
# Old entries with a different version are treated as cache misses.
# v2: Phase 2 taxonomy migration — 6 categories + Other fallback gate.
CACHE_SCHEMA_VERSION = "2"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS image_cache (
    path         TEXT PRIMARY KEY,
    mtime        REAL NOT NULL,
    size         INTEGER NOT NULL,
    cache_version TEXT NOT NULL,
    payload      TEXT NOT NULL
)
"""

_GET_SQL = """
SELECT mtime, size, cache_version, payload
FROM image_cache
WHERE path = ?
"""

_SET_SQL = """
INSERT OR REPLACE INTO image_cache (path, mtime, size, cache_version, payload)
VALUES (?, ?, ?, ?, ?)
"""

_DELETE_SQL = "DELETE FROM image_cache WHERE path = ?"


class ImageCache:
    """
    Thread-unsafe single-connection cache.
    Designed for single-process sequential use (workers=1).
    For multi-process use, open a separate ImageCache per process.
    """

    def __init__(self, cache_dir: str):
        os.makedirs(cache_dir, exist_ok=True)
        db_path = os.path.join(cache_dir, "cache.db")
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()
        self._hits = 0
        self._misses = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, path: str) -> Optional[dict]:
        """
        Return cached payload dict if the file at `path` still matches
        the stored mtime, size, and schema version. Returns None on miss.
        """
        try:
            stat = os.stat(path)
        except OSError:
            return None

        cur = self._conn.execute(_GET_SQL, (os.path.abspath(path),))
        row = cur.fetchone()
        if row is None:
            self._misses += 1
            return None

        stored_mtime, stored_size, stored_version, payload_json = row
        if (stored_version != CACHE_SCHEMA_VERSION
                or abs(stored_mtime - stat.st_mtime) > 1e-3
                or stored_size != stat.st_size):
            self._misses += 1
            return None

        self._hits += 1
        return json.loads(payload_json)

    def set(self, path: str, payload: dict) -> None:
        """
        Write or overwrite a cache entry for `path` using its current
        mtime and size. `payload` must be JSON-serialisable.
        """
        try:
            stat = os.stat(path)
        except OSError:
            return
        self._conn.execute(
            _SET_SQL,
            (
                os.path.abspath(path),
                stat.st_mtime,
                stat.st_size,
                CACHE_SCHEMA_VERSION,
                json.dumps(payload, default=_json_default),
            ),
        )
        self._conn.commit()

    def delete(self, path: str) -> None:
        self._conn.execute(_DELETE_SQL, (os.path.abspath(path),))
        self._conn.commit()

    def stats(self) -> dict:
        return {"hits": self._hits, "misses": self._misses}

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ------------------------------------------------------------------
# Payload helpers
# ------------------------------------------------------------------

def build_full_payload(
    objects_detected: list,
    caption: str,
    siglip_result: dict,
    ocr_result: str,
    is_blurry: bool,
    exposure: str,
    rating: int,
    tags: list,
    title: str,
) -> dict:
    """Build the cache payload for a full-pipeline run."""
    return {
        "mode": "full",
        "objects_detected": objects_detected,
        "caption": caption,
        "siglip_result": _serialise_siglip(siglip_result),
        "ocr_result": ocr_result,
        "is_blurry": is_blurry,
        "exposure": exposure,
        "rating": rating,
        "tags": tags,
        "title": title,
    }


def build_genre_only_payload(siglip_result: dict) -> dict:
    """Build the cache payload for a genre-only run."""
    return {
        "mode": "genre_only",
        "siglip_result": _serialise_siglip(siglip_result),
    }


def _serialise_siglip(siglip_result: dict) -> dict:
    """Ensure top_k list-of-tuples survives JSON round-trip as list-of-lists."""
    if siglip_result is None:
        return {}
    result = dict(siglip_result)
    if "top_k" in result:
        result["top_k"] = [list(pair) for pair in result["top_k"]]
    return result


def restore_siglip(raw: dict) -> dict:
    """Restore siglip_result from JSON (top_k becomes list of [label, score])."""
    result = dict(raw)
    if "top_k" in result:
        result["top_k"] = [tuple(pair) for pair in result["top_k"]]
    return result


def _json_default(obj):
    """Fallback serialiser for non-standard types (e.g. numpy floats)."""
    try:
        return float(obj)
    except (TypeError, ValueError):
        return str(obj)
