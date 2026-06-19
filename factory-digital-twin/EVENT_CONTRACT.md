# Factory Digital Twin — Event Contract (v1)

This is the **shared interface** between the Digital Twin (producer) and all
consumers (FactoryOps, VisionGuard). Treat it as a stable API. Breaking changes
require a version bump (`schema_version`).

All events are JSON, published to NATS subjects under the `factory.` namespace.

## Common envelope

Every event has these fields:

| Field            | Type   | Description                                  |
|------------------|--------|----------------------------------------------|
| `schema_version` | int    | Contract version. Currently `1`.             |
| `event_id`       | string | UUID4, unique per event.                     |
| `event_type`     | string | One of the types below.                      |
| `ts`             | string | ISO-8601 UTC timestamp of the event.         |
| `line_id`        | string | Production line, e.g. `line-1`.              |
| `station_id`     | string | Station within the line, e.g. `line-1-cnc`.  |
| `payload`        | object | Type-specific fields (below).                |

## NATS subjects

| Subject                   | Event type            |
|---------------------------|-----------------------|
| `factory.production`      | `production_started`, `production_completed` |
| `factory.downtime`        | `downtime_started`, `downtime_ended`         |
| `factory.quality`         | `quality_event`       |

## Event types

### `production_started`
```json
{ "order_id": "ORD-00042", "product_sku": "SKU-A", "target_qty": 100 }
```

### `production_completed`
```json
{ "order_id": "ORD-00042", "good_qty": 94, "scrap_qty": 6,
  "ideal_cycle_time_s": 12.0, "actual_cycle_time_s": 13.4 }
```
`ideal_cycle_time_s` / `actual_cycle_time_s` drive OEE **Performance**.
`good_qty` / `scrap_qty` drive OEE **Quality**.

### `downtime_started`
```json
{ "downtime_id": "DT-0007", "category": "mechanical", "planned": false,
  "reason": "Bearing seizure on conveyor" }
```
`category` ∈ `mechanical | electrical | setup | quality | material | break`.

### `downtime_ended`
```json
{ "downtime_id": "DT-0007", "duration_s": 480.0 }
```
Correlates to a prior `downtime_started` via `downtime_id`. Drives OEE
**Availability**.

### `quality_event`
```json
{ "part_id": "P-000931", "result": "defect",
  "defect_type": "surface", "confidence": 1.0,
  "image_ref": "minio://defects/P-000931.png",
  "equipment_state": "tool_worn" }
```
`result` ∈ `pass | defect`. `defect_type` ∈
`surface | dimension | color | missing_component | none`.
`image_ref` points at a synthetic image in MinIO (consumed by VisionGuard).
`equipment_state` lets consumers correlate defect rate with machine condition.

## OEE definition (ground truth)

```
Availability = run_time / planned_production_time
Performance  = (ideal_cycle_time * total_count) / run_time
Quality      = good_count / total_count
OEE          = Availability * Performance * Quality
```

The `oee-calculator/` module computes these from the raw event stream and is the
**ground truth** that FactoryOps' dashboard must match (see `validator.py`).
