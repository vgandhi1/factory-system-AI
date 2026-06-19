-- FactoryOps knowledge base (PostgreSQL + pgvector).
--
-- Historical context for the Copilot's RAG layer. ClickHouse answers "what is
-- happening now" (live OEE / downtime); this answers "has this happened before
-- and what fixed it". The Copilot retrieves similar past incidents + the
-- relevant runbook procedure to ground its root-cause hypotheses.
--
-- Embeddings are 384-dim (sentence-transformers all-MiniLM-L6-v2), computed by
-- the API on startup (see api/kb.py). Seed rows ship with NULL embeddings and
-- get backfilled, so this file stays pure SQL with no model dependency.

CREATE EXTENSION IF NOT EXISTS vector;

-- Past incidents the Copilot can retrieve by semantic similarity. Mirrors the
-- event-contract vocabulary (line_id, station_id, category) so retrieved rows
-- line up with live ClickHouse data.
CREATE TABLE IF NOT EXISTS incidents (
    id            SERIAL PRIMARY KEY,
    occurred_at   TIMESTAMPTZ  NOT NULL,
    line_id       TEXT         NOT NULL,
    station_id    TEXT         NOT NULL DEFAULT '',
    category      TEXT         NOT NULL,          -- mechanical|electrical|material|quality|setup|break
    title         TEXT         NOT NULL,
    description   TEXT         NOT NULL,          -- what was observed
    root_cause    TEXT         NOT NULL,          -- diagnosed cause
    resolution    TEXT         NOT NULL,          -- what fixed it
    downtime_min  REAL         NOT NULL DEFAULT 0,
    embedding     vector(384)                     -- backfilled by api/kb.py
);

-- Standard operating procedures / runbooks per downtime category. Retrieved
-- alongside incidents so the Copilot can cite the recommended action.
CREATE TABLE IF NOT EXISTS procedures (
    id         SERIAL PRIMARY KEY,
    category   TEXT  NOT NULL,
    title      TEXT  NOT NULL,
    body       TEXT  NOT NULL,
    embedding  vector(384)
);

-- Cosine-distance ANN indexes. ivfflat needs ANALYZE after backfill; small seed
-- set means a flat scan is fine too, the index is here to show the pattern.
CREATE INDEX IF NOT EXISTS incidents_embedding_idx
    ON incidents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
CREATE INDEX IF NOT EXISTS procedures_embedding_idx
    ON procedures USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

CREATE INDEX IF NOT EXISTS incidents_line_cat_idx ON incidents (line_id, category);
