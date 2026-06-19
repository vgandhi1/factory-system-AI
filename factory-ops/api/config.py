"""Environment configuration for the FactoryOps API.

ClickHouse holds the live event stream (OEE / downtime). PostgreSQL holds the
RAG knowledge base. ANTHROPIC_API_KEY enables the real Claude Copilot; without
it the Copilot falls back to a deterministic responder so the stack still runs
end-to-end with `docker compose up`.
"""
from __future__ import annotations

import os


def _env(key: str, default: str = "") -> str:
    v = os.getenv(key)
    return v if v not in (None, "") else default


# ClickHouse HTTP interface (port 8123).
CLICKHOUSE_URL = _env("CLICKHOUSE_URL", "http://localhost:8123")
CLICKHOUSE_DB = _env("CLICKHOUSE_DB", "factory")
CLICKHOUSE_USER = _env("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = _env("CLICKHOUSE_PASSWORD", "")

# PostgreSQL knowledge base.
POSTGRES_DSN = _env(
    "POSTGRES_DSN",
    "postgresql://factory:factory@localhost:5432/factory_kb",
)

# Copilot.
ANTHROPIC_API_KEY = _env("ANTHROPIC_API_KEY")
COPILOT_MODEL = _env("COPILOT_MODEL", "claude-sonnet-4-6")
EMBED_MODEL = _env("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Default OEE horizon (seconds) when a request gives no explicit window. The
# Digital Twin's ground-truth calculator uses a fixed 24h horizon; matching it
# keeps the dashboard within the validator's 1% tolerance.
DEFAULT_HORIZON_S = int(_env("DEFAULT_HORIZON_S", str(24 * 3600)))

COPILOT_ENABLED = bool(ANTHROPIC_API_KEY)
