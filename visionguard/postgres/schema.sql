-- VisionGuard persistence schema (PostgreSQL + pgvector).
--
-- The inference server applies this on startup too (storage.ensure_schema), so
-- it stays in sync; this file is the canonical reference and the Compose init.
--
--   detections   one row per scored image, with a backbone feature embedding
--                (pgvector) for similar-defect retrieval.
--   corrections  inspector verdicts that feed retraining (the human-in-the-loop).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS detections (
    id            SERIAL PRIMARY KEY,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    image_ref     TEXT NOT NULL DEFAULT '',     -- minio://bucket/key or filename
    source        TEXT NOT NULL DEFAULT 'upload',
    model_path    TEXT NOT NULL DEFAULT '',
    latency_ms    REAL NOT NULL DEFAULT 0,
    n_detections  INT  NOT NULL DEFAULT 0,
    top_class     TEXT NOT NULL DEFAULT '',
    top_conf      REAL NOT NULL DEFAULT 0,
    detections    JSONB NOT NULL DEFAULT '[]',  -- [{class_name, confidence, bbox}]
    embedding     vector(256)                   -- EMBED_DIM in inference config
);

CREATE TABLE IF NOT EXISTS corrections (
    id                SERIAL PRIMARY KEY,
    detection_id      INT REFERENCES detections(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    inspector         TEXT NOT NULL DEFAULT '',
    verdict           TEXT NOT NULL,            -- confirm | correct | reject
    corrected_boxes   JSONB NOT NULL DEFAULT '[]',
    used_for_training BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS detections_embedding_idx
    ON detections USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);
CREATE INDEX IF NOT EXISTS corrections_pending_idx
    ON corrections (used_for_training) WHERE used_for_training = false;
