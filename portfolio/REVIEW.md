# Factory Systems AI Portfolio — Comprehensive Review

**Review date:** June 3, 2026 (third pass — verified against current code)  
**Last reviewed:** 2026-06-17 (location + CI status updated)  
**Location:** `portfolio/REVIEW.md`  
**Scope:** [`Scoped_Executable_Portfolio.md`](Scoped_Executable_Portfolio.md), per-repo `SPEC.md` files, and codebases in `factory-digital-twin/`, `factory-ops/`, `visionguard/`.

---

## Executive Summary

This portfolio is **built, integrated, and demo-ready**. All three repos contain runnable code — not scaffolds. Since the second review, several high-priority integration items landed: **`scripts/demo-all.sh`**, **port-safe dual-stack compose**, **twin gated on gateway startup**, **`CLICKHOUSE_DB` fix**, **spec doc reconciliation**, and **README gap cleanup**.

| Project | Spec completeness | Implementation maturity | Demo readiness |
|---------|-------------------|-------------------------|----------------|
| **Factory Digital Twin** | ~95% | Strong enabler | ✅ Ready |
| **FactoryOps Command Center** | ~90% | Flagship E2E complete | ✅ Ready |
| **VisionGuard Quality Inspection** | ~74% | MVP with honest gaps | ⚠️ Ready with caveats |

**Verified baseline (seed 42, default 24h config):**

| Artifact | Count |
|----------|------:|
| MES events (`events.jsonl`) | 8,908 |
| Quality events | 8,574 |
| Defect quality events (with `image_ref`) | 402 |
| Synthetic labeled images in Twin `output/` | 260 |
| Ground-truth OEE | line-1 **0.677**, line-2 **0.686** |
| FactoryOps ingested (documented run) | 8,904 events, 0 dropped |
| Copilot golden eval | **25/25 (100%)** |

**One-command demo:**

```bash
factory-ops/scripts/demo-all.sh up        # both stacks
factory-ops/scripts/demo-all.sh seed-vg   # Twin images → VisionGuard MinIO
factory-ops/scripts/demo-all.sh down      # stop everything
```

**Overall verdict:** Coherent manufacturing-AI story, hireable at portfolio/demo level. Digital Twin is the architectural anchor. FactoryOps is the strongest E2E system. VisionGuard needs UI depth and the upload→retrain path more than new architecture.

**Remaining top risks:**

1. **OEE validator not in CI** — per-repo `test.yml` exists (June 2026); cross-repo `validator.py` still not wired (see [`ci/portfolio-validator.yml`](ci/portfolio-validator.yml))
2. **NATS at-most-once** — no JetStream consumer, no `event_id` dedup; twin `depends_on: gateway` mitigates but does not eliminate the race
3. **VisionGuard upload path broken** — file-upload corrections don't reach MinIO/retrain
4. **No committed NEU-DET `metrics.json`** — headline precision claim is script-gated, not proven in repo
5. **Prometheus/Grafana deferred** — honestly demoted to Tier 3 in scoped doc; not built

---

## Changes Since Second Pass (June 3, 2026)

| Item | Status | Where |
|------|--------|-------|
| Unified demo script | ✅ Done | `factory-ops/scripts/demo-all.sh` (`up` / `down` / `seed-vg`) |
| Port conflicts (Postgres 5432, MinIO 9000 vs ClickHouse) | ✅ Done | VisionGuard: Postgres **5433**, MinIO **9100/9101** |
| Twin startup race | ⚠️ Mitigated | `twin depends_on: gateway` (`service_started`) in `factory-ops/docker-compose.yml` |
| Gateway `CHDatabase` ignored | ✅ Fixed | `clickhouse.go` — `__DB__` token in schema + templated INSERTs |
| README stale OEE gap | ✅ Fixed | `factory-ops/README.md` — reconciliation marked resolved |
| Spec doc drift | ✅ Fixed | `*/SPEC.md` As-Built sections; scoped doc updated (LangChain→SDK, ONNX/DVC deferred, Prometheus Tier 3) |
| VisionGuard heatmap UI message | ✅ Fixed | Reworded to EigenCAM-unavailable (not ONNX blame) |
| `search_procedures` Copilot tool | ❌ Open | `kb.py` has it; `llm_tools.py` still exposes 5 tools only |
| CI + validator + NEU-DET metrics | ⚠️ Partial | Per-repo `.github/workflows/test.yml` added; OEE validator + NEU-DET metrics still open |
| Upload → MinIO for retrain | ❌ Open | `collect_corrections.py` still skips non-`minio://` refs |

---

## Portfolio Plan Assessment (`Scoped_Executable_Portfolio.md`)

### What the scoped plan gets right

1. **Scope reduction is credible** — FactoryOps at 4 core features; 12-month solo timeline realistic.
2. **Digital Twin as force multiplier** — validated: deterministic events, believable OEE, 402 defect `image_ref`s, proven FactoryOps ingestion.
3. **Go gets a real job** — NATS→ClickHouse gateway is built, documented, and contract-aligned.
4. **Honest success criteria** — NEU-DET for headline metrics; Twin synthetic for MLOps loop demo.
5. **Build order enforced** — Twin → FactoryOps → VisionGuard by dependency.

### Plan vs implementation (current)

| Portfolio claim | Actual state | Severity |
|-----------------|--------------|----------|
| One-command full factory demo | ✅ `demo-all.sh` | Resolved |
| Prometheus/Grafana (original Tier 1) | Deferred to Tier 3; not built | Low — documented |
| LangChain Copilot | Direct Anthropic SDK | Resolved in specs |
| ONNX Runtime inference | PyTorch `.pt`; ONNX export deferred | Medium — documented in `visionguard/SPEC.md` |
| DVC model versioning | Manual gitignore + promotion gate | Medium — documented |
| CI with `validator.py` | Manual reconciliation only | **High — still open** |
| Demo videos | Not in repo | Low |

### Portfolio narrative

> Digital Twin generates realistic factory events → FactoryOps ingests and explains them via a Copilot → VisionGuard inspects defect images from the same simulation and learns from inspector corrections.

**Pitch update:** You can now say *"Everything runs with one script — `demo-all.sh up` — and both stacks coexist on non-conflicting ports."*

---

## Project 1: Factory Digital Twin

**Spec:** `factory-digital-twin/SPEC.md`  
**Codebase:** `factory-digital-twin/`  
**Role:** Enabler — event contract, ground-truth OEE, synthetic defect images

### Completeness vs spec — ~95%

| Requirement | Status | Evidence |
|-------------|--------|----------|
| MES event generator | ✅ | `simulator/engine.py` |
| Downtime + cascade | ✅ Simplified | ~2 cascade events/run; no production reflow |
| OEE ground truth + validator | ✅ | `oee_calculator/` |
| Quality + tool wear | ✅ | `equipment_state: tool_worn` |
| Synthetic defect images | ✅ | PIL renderers, YOLO labels, MinIO upload |
| NATS + Compose | ✅ | 8,908 events/24h, seed 42 deterministic |
| 1000+ events | ✅ Exceeded | |

### Strengths

Contract-first (`EVENT_CONTRACT.md` + `twin/events.py` + Go mirror). Three RNG streams for determinism. Believable OEE ≈ 0.68. Domain stories align with FactoryOps KB seed data.

### Open limitations

- NATS core pub/sub only (no JetStream publish)
- `realtime_factor: 0.0` — burst publish, not wall-clock 24h replay
- No automated tests; `validator.py` not in CI
- 402 defect events vs 260 rendered images (generator limits/splits decouple counts)

### Recommendations

1. Wire `validator.py` into CI on seed-42 JSONL.
2. Add determinism unit test.
3. JetStream publish for replay/durability (V2).

---

## Project 2: FactoryOps AI Command Center

**Spec:** `factory-ops/SPEC.md`  
**Codebase:** `factory-ops/`  
**Role:** Flagship — operational intelligence + RAG Copilot

### Completeness vs spec — ~90% (↑ from ~88%)

| Requirement | Status | Notes |
|-------------|--------|-------|
| NATS → ClickHouse ingestion | ✅ | Go gateway; `CLICKHOUSE_DB` now drives DDL + INSERTs |
| OEE + downtime dashboard | ✅ Mostly | All endpoints + UI; no polling/time picker |
| Factory Copilot (RAG) | ✅ Mostly | Claude + pgvector; **`search_procedures` not a tool yet** |
| Shift handoff | ✅ Mostly | Rich API; UI shows narrative + production only |
| `docker compose up` | ✅ | 7 services; twin waits on gateway |
| Copilot 80%+ | ✅ | 25/25 golden eval |
| OEE vs Twin | ✅ | <0.1% after horizon parameterization |

### Architecture

```
Digital Twin ──NATS(factory.*)──> Go Gateway ──batch──> ClickHouse
                                                              │
PostgreSQL + pgvector                                         │
         └──────────────> FastAPI (metrics · Copilot · shift) ┘
                                    │
                             Next.js (:3000, API :8010)
```

### Resolved since second pass

| Issue | Resolution |
|-------|------------|
| `CHDatabase` env ignored | `__DB__` placeholder in `schema.sql`; `fmt.Sprintf` INSERTs use `c.db` |
| Compose startup race | `twin depends_on: gateway: service_started` + inline comment on JetStream as durable fix |
| README OEE gap stale | Marked ✅ resolved in README |

### Remaining bugs / tech debt

| Issue | Severity | Location |
|-------|----------|----------|
| Procedures not in Copilot tools | Medium | `kb.py` vs `llm_tools.py` |
| No time-window / live refresh UI | Medium | `frontend/` |
| NATS no dedup / JetStream | High (ops) | `runner.go` |
| Eval keywords not numbers | Medium | `eval/golden.json` |
| Shift-summary UI incomplete | Low | API returns oee/downtime/defects; UI omits |
| No auth, CORS `*` | Low (demo) | Acceptable for portfolio |
| `factory.oee` view vs API horizon | Low | Treat API as source of truth |

### UI vs API (accurate)

**Dashboard:** ✅ OEE A/P/Q, bottleneck badge, downtime with per-row planned/unplanned. ❌ `worst_stations`, aggregate `by_kind`, auto-refresh.

**Shift summary:** ✅ Narrative, action items, production table. ❌ OEE, downtime, top defects from API.

**Copilot:** ✅ Chat UX, sources, suggestion chips, offline fallback.

### Recommendations (priority)

1. Wire `search_procedures` into `llm_tools.py`.
2. Dashboard polling + shift time-range selector.
3. Expand shift-summary and dashboard UI to use full API payloads.
4. `.github/workflows/` — golden eval + OEE validator on seed-42.
5. JetStream durable consumer + optional `event_id` dedup (V2).

---

## Project 3: VisionGuard AI Quality Inspection

**Spec:** `visionguard/SPEC.md`  
**Codebase:** `visionguard/`  
**Role:** Computer vision + human-in-the-loop MLOps

### Completeness vs spec — ~74% (↑ from ~72% after doc/port fixes)

| Requirement | Status | Notes |
|-------------|--------|-------|
| YOLOv8 detection | ✅ Mostly | Twin 4-class + NEU-DET prep scripts |
| Inference <100ms | ⚠️ | Instrumented; no committed benchmark |
| Explainability | ⚠️ | EigenCAM + similarity; no source-image overlay |
| Inspector correction UI | ⚠️ | Label dropdown; no bbox edit; no detection overlay |
| Retraining loop | ✅ | Full pipeline; `--profile retrain` |
| Trends dashboard | ⚠️ | Lifetime KPIs; no time-series |
| PyTorch inference (spec-aligned) | ✅ | `.pt` via Ultralytics; ONNX deferred per SPEC |
| PostgreSQL + MinIO | ✅ | pgvector; ports 5433 / 9100-9101 on host |
| >90% / >80% metrics | ⚠️ | `evaluate.py` gates; no committed `metrics.json` |
| `docker compose up` | ✅ | Runs alongside FactoryOps |

### MLOps loop — working path

```
POST /detect/ref {"image_ref":"minio://defects/P-000931.png"}
  → inspector corrects in webui → POST /corrections
  → docker compose --profile retrain up retrainer
  → collect → train → compare (IMPROVE_MARGIN) → deploy best.pt
  → docker compose restart inference-server
```

**Broken path:** file upload → correction → retrain (image never stored in MinIO).

### Critical gaps

| Gap | Severity |
|-----|----------|
| Upload corrections don't feed retrain | **High** |
| No source image + bbox overlay in UI | Medium |
| Trends not temporal | Medium |
| No model hot-reload after deploy | Low |
| No automated tests | Medium |
| NEU-DET not in retrain taxonomy | Medium (by design for loop demo) |

### Recommendations (priority)

1. Persist uploads to MinIO before logging detection.
2. Source image + detection overlay on Inspect page.
3. Commit NEU-DET `metrics.json` with honest numbers.
4. Temporal trends (group by day/shift).
5. Integration test: MinIO ref correction → retrain → deploy.

---

## Cross-Project Integration

### Integration matrix (current)

| Integration point | Status |
|-------------------|--------|
| Event contract (Python ↔ Go) | ✅ schema v1 |
| NATS subjects | ✅ `factory.production`, `.downtime`, `.quality` |
| OEE reconciliation | ✅ API vs Twin <0.1% |
| Defect taxonomy (4 classes) | ✅ aligned |
| `image_ref` → MinIO keys | ✅ `minio://defects/{part_id}.png` |
| FactoryOps includes Twin | ✅ in FactoryOps compose |
| Unified demo | ✅ `factory-ops/scripts/demo-all.sh` |
| Both stacks simultaneously | ✅ non-conflicting ports |
| FactoryOps → VisionGuard quality bridge | ❌ no event-driven scoring |
| VisionGuard MinIO seeding | ✅ `demo-all.sh seed-vg` |

### Demo port map (verified)

| Service | FactoryOps (host) | VisionGuard (host) |
|---------|-------------------|---------------------|
| Frontend | 3000 | 3001 |
| API | 8010 | 8001 |
| Postgres | 5432 | **5433** |
| NATS | 4222 | — |
| ClickHouse | 8123, **9000** | — |
| MinIO | — | **9100**, **9101** |

### Recommended demo flow

1. `factory-ops/scripts/demo-all.sh up`
2. Open FactoryOps dashboard (http://localhost:3000) — OEE, downtime, bottleneck
3. Copilot chat — *"Why is line-1 OEE low?"* (optional `ANTHROPIC_API_KEY`)
4. `factory-ops/scripts/demo-all.sh seed-vg`
5. VisionGuard UI (http://localhost:3001) — detect by `minio://defects/...`, correct label
6. Optional: `cd visionguard && docker compose --profile retrain up retrainer`
7. `factory-ops/scripts/demo-all.sh down`

Train/deploy a custom `best.pt` before step 5 if you want meaningful defect classes (default is YOLOv8n fallback).

---

## Spec Document Cross-Check

Per-repo specs live at `factory-ops/SPEC.md`, `visionguard/SPEC.md`, `factory-digital-twin/SPEC.md`. Each FactoryOps and VisionGuard spec includes an **As-Built (June 2026)** section aligned with implementation.

| Topic | Spec (current) | Implementation |
|-------|----------------|----------------|
| Copilot | Direct Anthropic SDK | ✅ matches |
| VisionGuard inference | PyTorch `.pt`; ONNX deferred | ✅ matches |
| Explainability | EigenCAM | ✅ matches |
| Retrain success | Loop completion, not guaranteed gain | ✅ matches |
| Observability | Prometheus deferred (Tier 3 in scoped doc) | ✅ honest |

**Doc reconciliation: complete.** Remaining roadmap is code, not documentation.

---

## Maturity Scorecard (third pass)

| Dimension | Digital Twin | FactoryOps | VisionGuard | Portfolio |
|-----------|:------------:|:----------:|:-----------:|:---------:|
| Spec completeness | 9.5 | 9.0 | 7.5 | 8.7 |
| Code quality | 8.5 | 8.5 | 7.5 | 8.2 |
| Architecture clarity | 9.0 | 9.0 | 8.0 | 8.7 |
| Demo readiness | 9.0 | 9.5 | 7.5 | 8.7 |
| Test / CI coverage | 1.5 | 3.0 | 1.5 | 2.0 |
| Production hardening | 4.0 | 5.5 | 4.0 | 4.5 |
| Documentation honesty | 9.0 | 9.0 | 9.5 | 9.2 |
| Cross-repo integration | 8.5 | 8.5 | 7.5 | 8.2 |
| Resume / interview signal | 8.5 | 9.5 | 8.0 | 9.0 |

**Grade: B+ → low A- for demo readiness.** Production hardening (CI, JetStream, auth) still V2.

---

## Priority Roadmap

### Done ✅

- [x] `scripts/demo-all.sh` (`up` / `down` / `seed-vg`)
- [x] VisionGuard port remap (5433, 9100/9101)
- [x] Twin `depends_on: gateway`
- [x] Gateway `CLICKHOUSE_DB` fix
- [x] README + SPEC As-Built reconciliation
- [x] Prometheus demoted to Tier 3 in scoped doc

### Next (Weeks 1–2) — proof artifacts

- [ ] `.github/workflows/` — golden eval + `validator.py` on seed-42
- [ ] Run NEU-DET eval; commit `metrics.json`
- [ ] Record 2-minute demo video (use `demo-all.sh` flow)

### Next (Weeks 3–4) — FactoryOps polish

- [ ] `search_procedures` Copilot tool
- [ ] Dashboard polling + time-range selector
- [ ] Shift-summary + dashboard: render full API payloads
- [ ] Deepen golden eval with numeric assertions

### Next (Weeks 5–6) — VisionGuard closure

- [ ] Upload → MinIO persistence
- [ ] Source image + bbox overlay on Inspect page
- [ ] Temporal trends
- [ ] Integration test: correction → retrain → deploy

### Deferred (V2+)

- NATS JetStream + `event_id` dedup
- Prometheus/Grafana
- FactoryOps → VisionGuard quality-event bridge
- Auth / RBAC / Kubernetes
- Full bbox drag-edit UI
- DVC or permanent removal from narrative

---

## Interview Talking Points

### Lead with

1. **Contract-first digital twin** — `EVENT_CONTRACT.md`, seed-42 determinism, 8,908 events, OEE validator, 402 defect images.
2. **Copilot grounded in live + historical data** — shared metrics layer, pgvector RAG, 25-case golden eval, offline fallback.
3. **One-command full factory demo** — `demo-all.sh up`; both stacks, port-safe.
4. **VisionGuard MLOps loop** — corrections → retrain → mAP gate → conditional deploy; NEU-DET for headline metric, Twin synthetic for loop demo.

### If probed on gaps

| Question | Honest answer |
|----------|---------------|
| "Can I run everything at once?" | Yes — `factory-ops/scripts/demo-all.sh up`; VisionGuard uses remapped ports 5433 and 9100. |
| "Why not LangChain?" | Five tools don't need a framework; direct Anthropic tool-use is simpler to debug. |
| "Why PyTorch not ONNX at inference?" | Spec-aligned MVP; Ultralytics `.pt` path; ONNX export exists, Runtime deferred for latency work. |
| "Where's Prometheus / DVC?" | Deferred and documented; Docker Compose + promotion gate cover the demo. |
| "How do you know OEE is correct?" | Twin ground-truth engine; FactoryOps SQL mirrors contract; verified <0.1% on seed 42. |
| "Does retraining always improve the model?" | No — promotion gated on holdout mAP; loop completion is the deliverable. |

---

## Conclusion

Third-pass review confirms substantial progress since the initial assessment. Integration glue that blocked the "full factory" story — **demo script, port safety, gateway ordering, config bugs, spec honesty** — is largely done. What remains is **proof** (CI, committed metrics, demo video) and **VisionGuard UX closure** (upload path, image overlay, temporal trends), plus FactoryOps Copilot polish (`search_procedures`, live dashboard).

The portfolio is ready to demo today with `demo-all.sh`. The next increment of value is making that demo **repeatable and auditable** for reviewers who won't run it themselves.

---

*Third pass: verified `demo-all.sh`, compose port maps, gateway `clickhouse.go` DB templating, twin `depends_on`, `*/SPEC.md` As-Built sections, scoped doc Next Steps, and unchanged open items (`llm_tools.py`, CI, upload→MinIO).*
