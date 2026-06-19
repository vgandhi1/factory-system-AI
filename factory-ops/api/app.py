"""FactoryOps API — the reasoning layer on top of the ingestion pipeline.

Go gateway lands events in ClickHouse; this FastAPI app serves the dashboard
metrics, the Copilot chat, and shift summaries. On startup it backfills the
knowledge-base embeddings (idempotent) so RAG is ready on first request.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import COPILOT_ENABLED
from db import clickhouse
from routes import copilot as copilot_routes
from routes import metrics as metrics_routes
from routes import shift_summary as shift_routes
from services import kb

log = logging.getLogger("factoryops.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        n = kb.backfill_embeddings()
        log.info("kb embeddings backfilled: %d rows", n)
    except Exception as exc:  # noqa: BLE001 - don't block startup on KB
        log.warning("kb backfill skipped: %s", exc)
    yield


app = FastAPI(title="FactoryOps API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # demo stack; tighten for real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics_routes.router)
app.include_router(copilot_routes.router)
app.include_router(shift_routes.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "clickhouse": clickhouse.ping(),
        "knowledge_base": kb.ping(),
        "copilot_backend": "claude" if COPILOT_ENABLED else "fallback",
    }
