# Knowledge base (PostgreSQL + pgvector)

Historical context for the Copilot's RAG layer. ClickHouse answers *what is
happening now*; this answers *has this happened before and what fixed it*.

| File | Purpose |
|------|---------|
| [`schema.sql`](schema.sql) | `incidents` + `procedures` tables, `vector(384)` embeddings, ivfflat indexes |
| [`seed_data/incidents.sql`](seed_data/incidents.sql) | 12 past incidents matching the Twin's domain (line-1/line-2, tool wear, cascade) |
| [`seed_data/procedures.sql`](seed_data/procedures.sql) | runbook per downtime category |

Docker Compose applies these on first boot (init dir, alphabetical). Embeddings
ship as `NULL` and are backfilled by the API on startup
([`api/services/kb.py`](../api/services/kb.py)) using a local
`sentence-transformers` model — no embedding API key required.

Retrieval is cosine similarity (`embedding <=> query`), exposed through the
Copilot's `search_incidents` tool.
