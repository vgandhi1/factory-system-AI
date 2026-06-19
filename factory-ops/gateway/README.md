# FactoryOps Ingestion Gateway

Go service: subscribes to the Digital Twin's NATS stream, decodes the event
contract, and batch-writes to ClickHouse.

```
main.go                          wiring, signals, connect-with-retry
internal/
├── config/   config.go          env-driven settings
├── model/    event.go           Go mirror of twin/events.py + Decode()
├── sink/     clickhouse.go      buffered batch insert + schema bootstrap
│             schema.sql         embedded DDL (tables + factory.oee view)
└── ingest/   runner.go          subscribe -> decode -> buffer -> flush
```

## Design notes

- **Decode is a tagged union** (`model.Decoded`): one event → one typed row for
  exactly one table. Unknown `event_type` or wrong `schema_version` is dropped
  and counted, not fatal.
- **Batching**: rows buffer in the sink and flush on `GATEWAY_BATCH_SIZE` or
  every `GATEWAY_FLUSH_MS`, whichever first. Final flush on shutdown drains the
  buffer.
- **Schema bootstrap**: `schema.sql` is `go:embed`ded and applied on startup,
  statement-by-statement (idempotent `IF NOT EXISTS`). Comment lines are stripped
  before splitting on `;` so semicolons inside comments don't break parsing.
- **Resilience**: retries the ClickHouse connection (it may still be starting in
  compose) and reconnects to NATS indefinitely.

## Local dev

```bash
go build ./...
go vet ./...
NATS_URL=nats://localhost:4222 CLICKHOUSE_ADDR=localhost:9000 ./gateway
```

Contract source of truth: [`../../factory-digital-twin/EVENT_CONTRACT.md`](../../factory-digital-twin/EVENT_CONTRACT.md).
Keep `model.SchemaVersion` in lockstep with the Twin's `SCHEMA_VERSION`.
