# Factory AI Portfolio — Implementation Plan

**Status:** Active development — demo-ready, polish in progress  
**Last updated:** 2026-06-17  
**Tier:** T1 Dev (each sub-repo); T2 Release-ready deferred until publish decision

---

## Goal

Three integrated repos that tell a coherent manufacturing-AI story without a real
plant: a Digital Twin generates realistic events and defect images; FactoryOps
ingests and explains them via an agentic Copilot; VisionGuard inspects images and
learns from inspector corrections. All runnable locally with one demo script.

---

## Current status

| Area | Status | Notes |
|------|--------|-------|
| Digital Twin — event generation | ✅ Done | ~8.9k events/24h, seed 42 deterministic |
| Digital Twin — OEE ground truth | ✅ Done | line-1 **0.677**, line-2 **0.686** |
| Digital Twin — synthetic defect images | ✅ Done | 260 labeled images, MinIO upload |
| FactoryOps — NATS → ClickHouse gateway | ✅ Done | Go gateway, 0 dropped on documented run |
| FactoryOps — OEE/downtime dashboard | ✅ Done | Next.js + FastAPI |
| FactoryOps — Copilot (RAG + tools) | ✅ Done | 25/25 golden eval; `search_procedures` not wired |
| FactoryOps — shift summary | ✅ Done | API complete; UI partial |
| VisionGuard — YOLO inference | ✅ Done | PyTorch `.pt` via Ultralytics |
| VisionGuard — inspector correction UI | ⚠️ MVP | Label dropdown; no bbox overlay |
| VisionGuard — retrain loop | ✅ Done | `--profile retrain`; upload path broken |
| Cross-repo demo script | ✅ Done | `factory-ops/scripts/demo-all.sh` |
| Per-repo CI (lint + unit tests) | ✅ Done | `.github/workflows/test.yml` in each repo |
| OEE validator in CI | ⏳ Planned | `validator.py` exists; not wired cross-repo |
| NEU-DET committed metrics | ⏳ Planned | `metrics.json` not in repo |
| Git remotes / public publish | ⏳ Deferred | 3 repos have no `origin`; decide in each SPEC |

**Legend:** ✅ done · 🔄 in progress · ⏳ planned · ❌ blocked

---

## Scope

### In scope (this portfolio)

Aligned with [`GUARDRAILS.md`](GUARDRAILS.md) and
`factory-ai-portfolio-guardrails.md`:

- Synthetic MES events via NATS (`factory.production`, `.downtime`, `.quality`)
- OEE calculation, downtime classification, bottleneck identification (FactoryOps)
- Agentic Copilot: NL → parameterized ClickHouse queries + pgvector RAG
- YOLO defect classification with human-review routing below 0.70 confidence
- Inspector correction loop with retrain **flag**, not AutoML
- Docker Compose local dev; mock endpoints only (no real MES/ERP)

### Out of scope (permanent — do not build)

| Exclusion | Rationale |
|-----------|-----------|
| Real MES/ERP (SAP, Oracle, Tulip) | Guardrails hard NO #1 |
| Kubernetes-as-showcase | Guardrails hard NO #3 — document architecture only |
| Embedded systems / firmware / ROS2 / VLA robotics | Guardrails hard NO #2; separate vertical |
| Deep learning training pipelines / LoRA fine-tuning / Isaac Sim | Guardrails hard NO #5 — Stage 2 only |
| AutoML / continuous retraining automation | Guardrails hard NO #6 — flag for retrain, don't build pipeline |
| LLM raw SQL execution | Guardrails hard NO #7 — Go/Python layer owns query construction |
| Standalone predictive maintenance | Guardrails hard NO #4 |
| 3D physics simulation / digital twin visualization | Digital Twin scope: data generation only |

---

## Milestones

### M1 — Dev baseline ✅

- [x] Runnable locally with Docker Compose
- [x] Event contract v1 (`EVENT_CONTRACT.md` + `twin/events.py`)
- [x] Ground-truth OEE validator (`oee_calculator/validator.py`)
- [x] Copilot golden eval harness (25 cases)
- [x] One-command demo (`demo-all.sh`)

### M2 — Integration demo ✅

- [x] Twin → FactoryOps ingestion verified (<0.1% OEE drift)
- [x] Twin defect images → VisionGuard MinIO seeding
- [x] Both stacks run on non-conflicting ports
- [x] Per-repo CI with ruff + pytest

### M3 — Release-ready ⏳

- [ ] Wire OEE `validator.py` into CI (see [`ci/portfolio-validator.yml`](ci/portfolio-validator.yml))
- [ ] Commit NEU-DET `metrics.json` with honest numbers
- [ ] Fix VisionGuard upload → MinIO → retrain path
- [ ] Wire `search_procedures` into Copilot tools
- [ ] Decide publish vs private for each sub-repo; add LICENSE if public
- [ ] `presentation.html` + Pages CI per T2 standard (if publishing)

### M4 — Production hardening (deferred)

- [ ] NATS JetStream + `event_id` dedup
- [ ] Auth / RBAC on APIs
- [ ] Prometheus/Grafana (Tier 3 in scoped doc)
- [ ] FactoryOps → VisionGuard quality-event bridge

---

## Architecture decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Event contract SSOT | `factory-digital-twin/twin/events.py` | Producer owns schema; consumers import |
| Ingestion language | Go gateway | NATS subscribe + ClickHouse batch insert |
| Copilot framework | Direct Anthropic SDK | Five tools; no LangChain overhead |
| Vision inference | PyTorch `.pt` (Ultralytics) | MVP path; ONNX export deferred |
| Model versioning | Gitignored weights + promotion gate | DVC deferred; `IMPROVE_MARGIN` gate |
| Local orchestration | Docker Compose | K8s documented, not built |
| Demo orchestration | `factory-ops/scripts/demo-all.sh` | Single entry point for interview demos |

---

## Dependencies between repos

| Producer | Consumer | Integration | Status |
|----------|----------|-------------|--------|
| Digital Twin | FactoryOps | NATS `factory.*` → Go gateway → ClickHouse | ✅ |
| Digital Twin | VisionGuard | `image_ref` → MinIO defect keys | ✅ |
| Digital Twin | FactoryOps | OEE ground truth vs dashboard | ✅ <0.1% |
| FactoryOps | VisionGuard | Quality event bridge | ❌ not built |

---

## Verified baseline (seed 42, 24h config)

| Artifact | Count |
|----------|------:|
| MES events | 8,908 |
| Quality events | 8,574 |
| Defect events (with `image_ref`) | 402 |
| Synthetic labeled images | 260 |
| FactoryOps ingested | 8,904 events, 0 dropped |
| Copilot golden eval | 25/25 (100%) |

---

## Open questions

- Publish all three repos publicly, or keep VisionGuard local due to Twin coupling?
- Target T2 (LICENSE + presentation) before or after NEU-DET metrics commit?

---

## Change log

| Date | Change |
|------|--------|
| 2026-06-17 | Renamed `new/` → `portfolio/`; replaced out-of-scope VLA/robotics drafts with execution-aligned docs; added container README |
| 2026-06-03 | Third-pass review (`REVIEW.md`); demo-all.sh, port remap, gateway fixes |
| 2026-05 | Initial three-repo build complete |
