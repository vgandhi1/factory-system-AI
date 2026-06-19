# Shared Event Schema

**Do not duplicate Pydantic models here.** The single source of truth for the
factory event contract lives in the Digital Twin repo:

| Artifact | Location |
|----------|----------|
| Human-readable spec | [`factory-digital-twin/EVENT_CONTRACT.md`](../factory-digital-twin/EVENT_CONTRACT.md) |
| Executable models (Pydantic) | [`factory-digital-twin/twin/events.py`](../factory-digital-twin/twin/events.py) |
| Go mirror (gateway) | [`factory-ops/gateway/internal/model/event.go`](../factory-ops/gateway/internal/model/event.go) |

---

## Why the Twin owns the schema

Per [`GUARDRAILS.md`](../GUARDRAILS.md) and portfolio guardrails, the Digital Twin
*produces* events; FactoryOps and VisionGuard *consume* them. The producer defines
the contract; consumers import or mirror it.

Breaking changes require:

1. Bump `SCHEMA_VERSION` in `twin/events.py`
2. Update `EVENT_CONTRACT.md`
3. Update Go gateway models
4. Note the change in [`plan.md`](../plan.md)

---

## Defect taxonomy (aligned across repos)

| Class | Twin `DefectType` | VisionGuard label |
|-------|-------------------|-------------------|
| Surface | `surface` | surface |
| Dimension | `dimension` | dimension |
| Color | `color` | color |
| Missing component | `missing_component` | missing_component |

Quality events carry `image_ref` as `minio://defects/{part_id}.png` when
`result == "defect"`.
