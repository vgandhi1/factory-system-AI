"""Persistence for the inference server.

PostgreSQL stores every detection (with its feature embedding) and the inspector
corrections that feed retraining. pgvector powers similar-defect retrieval. MinIO
holds the part images; a quality_event's `image_ref` (minio://bucket/key) resolves
straight here, so VisionGuard can score images the Digital Twin produced.
"""
from __future__ import annotations

import io
import json

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from PIL import Image

from config import (
    EMBED_DIM,
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
    POSTGRES_DSN,
)

SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS detections (
    id            SERIAL PRIMARY KEY,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    image_ref     TEXT NOT NULL DEFAULT '',
    source        TEXT NOT NULL DEFAULT 'upload',
    model_path    TEXT NOT NULL DEFAULT '',
    latency_ms    REAL NOT NULL DEFAULT 0,
    n_detections  INT  NOT NULL DEFAULT 0,
    top_class     TEXT NOT NULL DEFAULT '',
    top_conf      REAL NOT NULL DEFAULT 0,
    detections    JSONB NOT NULL DEFAULT '[]',
    needs_review  BOOLEAN NOT NULL DEFAULT false,
    embedding     vector({EMBED_DIM})
);

-- Idempotent for tables created before the human-review gate existed.
ALTER TABLE detections ADD COLUMN IF NOT EXISTS needs_review BOOLEAN NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS corrections (
    id               SERIAL PRIMARY KEY,
    detection_id     INT REFERENCES detections(id),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    inspector        TEXT NOT NULL DEFAULT '',
    verdict          TEXT NOT NULL,              -- confirm | correct | reject
    corrected_boxes  JSONB NOT NULL DEFAULT '[]',
    used_for_training BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS detections_embedding_idx
    ON detections USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);
"""


def _connect() -> psycopg.Connection:
    conn = psycopg.connect(POSTGRES_DSN)
    register_vector(conn)
    return conn


def ensure_schema() -> None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA)
        conn.commit()


def log_detection(image_ref: str, source: str, model_path: str,
                  latency_ms: float, detections: list[dict],
                  embedding: list[float], needs_review: bool = False) -> int:
    top = max(detections, key=lambda d: d["confidence"], default=None)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO detections
              (image_ref, source, model_path, latency_ms, n_detections,
               top_class, top_conf, detections, needs_review, embedding)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
            """,
            (image_ref, source, model_path, latency_ms, len(detections),
             top["class_name"] if top else "",
             top["confidence"] if top else 0.0,
             json.dumps(detections), needs_review,
             np.asarray(embedding, dtype=np.float32)),
        )
        det_id = cur.fetchone()[0]
        conn.commit()
        return det_id


def similar_defects(embedding: list[float], k: int = 3,
                    exclude_id: int | None = None) -> list[dict]:
    if not any(embedding):
        return []
    vec = np.asarray(embedding, dtype=np.float32)
    # Placeholder order: similarity-select, [id-filter], distance-order, limit.
    if exclude_id is not None:
        sql = """
            SELECT id, created_at, image_ref, top_class, top_conf,
                   1 - (embedding <=> %s) AS similarity
            FROM detections
            WHERE embedding IS NOT NULL AND id <> %s
            ORDER BY embedding <=> %s LIMIT %s
        """
        params = [vec, exclude_id, vec, k]
    else:
        sql = """
            SELECT id, created_at, image_ref, top_class, top_conf,
                   1 - (embedding <=> %s) AS similarity
            FROM detections
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s LIMIT %s
        """
        params = [vec, vec, k]
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [c.name for c in cur.description]
        rows = []
        for r in cur.fetchall():
            d = dict(zip(cols, r))
            d["created_at"] = d["created_at"].isoformat()
            d["similarity"] = round(float(d["similarity"]), 4)
            rows.append(d)
        return rows


def get_detection(det_id: int) -> dict | None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, created_at, image_ref, source, model_path, latency_ms, "
            "n_detections, top_class, top_conf, needs_review, detections "
            "FROM detections WHERE id = %s", (det_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [c.name for c in cur.description]
        d = dict(zip(cols, row))
        d["created_at"] = d["created_at"].isoformat()
        return d


def recent_detections(limit: int = 50,
                      needs_review: bool | None = None) -> list[dict]:
    where = "" if needs_review is None else "WHERE needs_review = %s "
    args: list = [] if needs_review is None else [needs_review]
    args.append(limit)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, created_at, image_ref, n_detections, top_class, top_conf, "
            "needs_review "
            f"FROM detections {where}ORDER BY id DESC LIMIT %s", args)
        cols = [c.name for c in cur.description]
        rows = []
        for r in cur.fetchall():
            d = dict(zip(cols, r))
            d["created_at"] = d["created_at"].isoformat()
            rows.append(d)
        return rows


def add_correction(detection_id: int, inspector: str, verdict: str,
                   corrected_boxes: list[dict]) -> int:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO corrections "
            "(detection_id, inspector, verdict, corrected_boxes) "
            "VALUES (%s,%s,%s,%s) RETURNING id",
            (detection_id, inspector, verdict, json.dumps(corrected_boxes)))
        cid = cur.fetchone()[0]
        conn.commit()
        return cid


def trends() -> dict:
    """Defect counts by class, first-pass yield, scrap rate, correction volume."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) AS total, "
            "count(*) FILTER (WHERE n_detections = 0) AS passes, "
            "count(*) FILTER (WHERE n_detections > 0) AS defects "
            "FROM detections")
        total, passes, defects = cur.fetchone()
        total = total or 0
        cur.execute(
            "SELECT top_class, count(*) FROM detections "
            "WHERE n_detections > 0 GROUP BY top_class ORDER BY count(*) DESC")
        by_class = [{"defect_type": c or "unknown", "count": n}
                    for c, n in cur.fetchall()]
        cur.execute("SELECT count(*), "
                    "count(*) FILTER (WHERE used_for_training) FROM corrections")
        corr_total, corr_used = cur.fetchone()
        return {
            "total_inspected": total,
            "passes": passes or 0,
            "defects": defects or 0,
            "first_pass_yield": round((passes or 0) / total, 4) if total else 0.0,
            "scrap_rate": round((defects or 0) / total, 4) if total else 0.0,
            "by_class": by_class,
            "corrections_total": corr_total or 0,
            "corrections_pending_training": (corr_total or 0) - (corr_used or 0),
        }


def ping() -> bool:
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except psycopg.Error:
        return False


# --------------------------------------------------------------------------- #
# MinIO
# --------------------------------------------------------------------------- #
_minio = None


def _minio_client():
    global _minio
    if _minio is None:
        from minio import Minio
        _minio = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY,
                       secret_key=MINIO_SECRET_KEY, secure=MINIO_SECURE)
    return _minio


def fetch_image(image_ref: str) -> Image.Image:
    """Resolve a `minio://bucket/key` reference to a PIL image."""
    if not image_ref.startswith("minio://"):
        raise ValueError(f"unsupported image_ref scheme: {image_ref}")
    bucket, _, key = image_ref[len("minio://"):].partition("/")
    resp = _minio_client().get_object(bucket, key)
    try:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")
    finally:
        resp.close()
        resp.release_conn()
