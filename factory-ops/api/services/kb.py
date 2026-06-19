"""Knowledge-base retrieval over PostgreSQL + pgvector.

Embeds incident/procedure text with a local sentence-transformers model (no
external API, so RAG works offline) and serves cosine-similarity search. The
embedding model loads lazily on first use; `backfill_embeddings()` runs once at
startup to populate any seed rows that shipped with NULL embeddings.
"""
from __future__ import annotations

import threading

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

from config import EMBED_MODEL, POSTGRES_DSN

_model = None
_model_lock = threading.Lock()


def _embedder():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed(text: str) -> np.ndarray:
    # Return a numpy array: pgvector's psycopg adapter binds ndarray as a vector
    # parameter (a plain Python list would be sent as double precision[]).
    return _embedder().encode(text, normalize_embeddings=True)


def _connect() -> psycopg.Connection:
    conn = psycopg.connect(POSTGRES_DSN)
    register_vector(conn)
    return conn


def backfill_embeddings() -> int:
    """Compute embeddings for any rows missing them. Returns rows updated."""
    updated = 0
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, description, root_cause, resolution "
            "FROM incidents WHERE embedding IS NULL"
        )
        for row in cur.fetchall():
            iid, title, desc, cause, res = row
            vec = embed(f"{title}. {desc} Cause: {cause} Fix: {res}")
            cur.execute("UPDATE incidents SET embedding = %s WHERE id = %s",
                        (vec, iid))
            updated += 1

        cur.execute(
            "SELECT id, title, body FROM procedures WHERE embedding IS NULL"
        )
        for row in cur.fetchall():
            pid, title, body = row
            vec = embed(f"{title}. {body}")
            cur.execute("UPDATE procedures SET embedding = %s WHERE id = %s",
                        (vec, pid))
            updated += 1

        conn.commit()
        if updated:
            cur.execute("ANALYZE incidents")
            cur.execute("ANALYZE procedures")
    return updated


def search_incidents(query: str, k: int = 3,
                     line_id: str | None = None) -> list[dict]:
    """Top-k past incidents most similar to the query text."""
    vec = embed(query)
    # The query vector appears twice: once in the SELECT similarity expression,
    # once in the ORDER BY distance. Optionally constrain to one line.
    if line_id:
        sql = """
            SELECT occurred_at, line_id, station_id, category, title,
                   description, root_cause, resolution, downtime_min,
                   1 - (embedding <=> %s) AS similarity
            FROM incidents WHERE line_id = %s
            ORDER BY embedding <=> %s LIMIT %s
        """
        params = [vec, line_id, vec, k]
    else:
        sql = """
            SELECT occurred_at, line_id, station_id, category, title,
                   description, root_cause, resolution, downtime_min,
                   1 - (embedding <=> %s) AS similarity
            FROM incidents
            ORDER BY embedding <=> %s LIMIT %s
        """
        params = [vec, vec, k]
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [c.name for c in cur.description]
        return [_rowdict(cols, r) for r in cur.fetchall()]


def search_procedures(query: str, k: int = 1) -> list[dict]:
    vec = embed(query)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT category, title, body,
                   1 - (embedding <=> %s) AS similarity
            FROM procedures
            ORDER BY embedding <=> %s LIMIT %s
            """,
            [vec, vec, k],
        )
        cols = [c.name for c in cur.description]
        return [_rowdict(cols, r) for r in cur.fetchall()]


def ping() -> bool:
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            return cur.fetchone() is not None
    except psycopg.Error:
        return False


def _rowdict(cols: list[str], row: tuple) -> dict:
    d = {}
    for c, v in zip(cols, row):
        d[c] = v.isoformat() if hasattr(v, "isoformat") else (
            round(float(v), 4) if isinstance(v, float) else v)
    return d
