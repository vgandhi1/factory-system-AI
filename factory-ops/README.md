<div align="center">

# FactoryOps AI Command Center

### Real-time OEE, downtime analytics, and an agentic Copilot over the factory event stream

[![Go](https://img.shields.io/badge/Go-gateway-00ADD8?style=for-the-badge&logo=go&logoColor=white)](https://go.dev/)
[![Python](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-analytics-FFCC01?style=for-the-badge)](https://clickhouse.com/)
[![Next.js](https://img.shields.io/badge/Next.js-dashboard-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)

<br />

<img src="https://img.shields.io/badge/Copilot_eval-25%2F25-emerald?style=flat-square" alt="25/25 eval" />
<img src="https://img.shields.io/badge/OEE_drift-<0.1%25-sky?style=flat-square" alt="OEE reconciled" />
<img src="https://img.shields.io/badge/role-portfolio_flagship-violet?style=flat-square" alt="flagship" />

<br />

*Demo:* [`scripts/demo-all.sh`](scripts/demo-all.sh) · *Portfolio:* [`../README.md`](../README.md) · [`../portfolio/plan.md`](../portfolio/plan.md)

</div>

---

Real-time operational intelligence over the factory event stream. Consumes the [Factory Digital Twin](../factory-digital-twin)'s NATS events, lands them in ClickHouse, and serves an OEE/downtime dashboard plus a RAG Copilot.

---

## Status

| Component | Status |
|-----------|:------:|
| Ingestion gateway (Go: NATS → ClickHouse) | ✅ verified E2E |
| ClickHouse schema + ground-truth OEE view | ✅ |
| FastAPI metrics / Copilot / shift-summary | ✅ |
| PostgreSQL + pgvector knowledge base | ✅ |
| Copilot golden eval (25 cases) | ✅ 100% |
| React/Next.js dashboard + chat + shift summary | ✅ |

---

## Architecture

```
Digital Twin ──NATS(factory.*)──> gateway (Go) ──batch insert──> ClickHouse
                                                                     │
                       PostgreSQL + pgvector (RAG knowledge base)    │
                              │                                      │
                              └────────> FastAPI (Python) <──────────┘
                                  metrics · Copilot · shift summary
                                              │
                                       Next.js dashboard
```

Go owns ingestion; Python owns reasoning. ClickHouse answers *what is happening now*; pgvector answers *has this happened before*.

---

## Run the full stack

```bash
docker compose up --build
```

| Surface | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| Copilot chat | http://localhost:3000/chat |
| Shift summary | http://localhost:3000/shift-summary |
| API docs | http://localhost:8010/docs |

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # optional — enables real Copilot
docker compose up --build
```

Without a key, the Copilot falls back to deterministic tool calls (full stack runs offline).

### Spot-check

```bash
curl 'http://localhost:8010/metrics/oee'
curl -XPOST localhost:8010/copilot/chat -H 'content-type: application/json' \
     -d '{"question":"Why is line-1 OEE low?"}'
```

---

## API layer

| Endpoint | What |
|----------|------|
| `GET /metrics/oee` | Per-line OEE (A/P/Q) |
| `GET /metrics/downtime` | Downtime by category |
| `GET /metrics/bottleneck` | Lowest-OEE line + worst stations |
| `GET /metrics/defects` | Quality defects by type |
| `POST /copilot/chat` | RAG Copilot (Claude tool-use or fallback) |
| `GET /shift/summary` | Shift handoff narrative + action items |

### Copilot golden eval

```bash
docker compose up -d
cd api && python eval/run_eval.py --api http://localhost:8010
```

### Verified run

| Check | Result |
|-------|--------|
| Events ingested | 8904 (0 dropped) |
| API OEE vs Twin | < 0.1% per line |
| Golden eval | **25/25 = 100%** |

---

## Gateway

See [`gateway/`](gateway). Key env vars:

| Env | Default | Meaning |
|-----|---------|---------|
| `NATS_URL` | `nats://localhost:4222` | Broker |
| `CLICKHOUSE_ADDR` | `localhost:9000` | Native protocol |
| `CLICKHOUSE_DB` | `factory` | Database |
| `GATEWAY_BATCH_SIZE` | `500` | Batch flush size |

```bash
cd gateway && go build ./... && go vet ./...
```

---

## Why Go for the gateway

Subscribes to `factory.*`, decodes the [event contract](../factory-digital-twin/EVENT_CONTRACT.md), batches, and writes to ClickHouse — the job Go does in this portfolio.

---

## Known gaps

- **NATS at-most-once** — no JetStream dedup yet; twin `depends_on: gateway` mitigates startup race
- **Copilot windowing** — dashboard doesn't pass time-range to API yet
- **`search_procedures` tool** — seeded in KB but not exposed in `llm_tools.py`

---

## Portfolio links

Spec: [`SPEC.md`](SPEC.md) · Plan: [`../portfolio/plan.md`](../portfolio/plan.md) · Demo: [`scripts/demo-all.sh`](scripts/demo-all.sh)
