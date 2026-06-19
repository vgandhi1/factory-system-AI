# Scoped Factory AI Portfolio (Executable Version)

**Core Insight:** Reduce scope by 50%, add digital twin as force multiplier.

---

## The Problem With Original Plan

| Aspect | Original | Realistic |
|--------|----------|-----------|
| **FactoryOps scope** | 11 features | 4 core features |
| **Tech stack** | 10+ technologies | 6–7 essential ones |
| **Timeline** | 18 months | 12 months |
| **Solo execution** | 6.5/10 | 8.5/10 |
| **Demo capability** | Need real factory | Simulator provides it |

**Original FactoryOps scope:**
- Dashboard, OEE, Downtime, Bottlenecks, Copilot, RAG, Shift Summary, RCA, Forecasting, Optimization, Kubernetes, MES Integration

**Is too ambitious.** Skip the ambitious parts.

---

## Three-Repo Architecture (Focused)

### Repository 1: FactoryOps AI Command Center (Flagship)
**Timeline:** 3–4 months  
**Scope:** Core operational intelligence

#### Core Features (Ship These)
1. **Data ingestion layer**
   - Consume synthetic MES events from Factory Digital Twin
   - Real-time processing (Kafka/NATS)
   - Store in ClickHouse

2. **OEE + Downtime dashboard**
   - Real-time OEE breakdown (Availability, Performance, Quality)
   - Downtime events (planned vs. unplanned, by reason)
   - Bottleneck identification (which station limits throughput)
   - React dashboard, <1 second query latency

3. **Factory Copilot (RAG-based)**
   - Chat interface: "Why is Line 3 at 80% OEE?"
   - Queries ClickHouse for live data + PostgreSQL for historical context
   - Uses Claude with structured prompts
   - Returns: root cause hypothesis + supporting data
   - Example: "Line 3 OEE dropped due to [Reason A] at 2:30 PM. Similar incident happened 3 weeks ago (see link)."

4. **Shift handoff intelligence**
   - Summarize shift: production vs. target, downtime events, quality issues
   - NLP-based (Claude) or template-based
   - Key metrics, action items, trends

#### Skip (Add in V2+)
- ❌ Forecasting
- ❌ Multi-agent workflows
- ❌ Advanced RCA
- ❌ Optimization engine
- ❌ Kubernetes deployment (use Docker Compose first)
- ❌ MES integration (use simulator instead)

#### Tech Stack (Lean)

| Layer | Technology |
|-------|-----------|
| Data ingestion | NATS (from your 6-month plan) |
| Analytics DB | ClickHouse (from your 6-month plan) |
| Knowledge base | PostgreSQL + pgvector |
| API | FastAPI (Python) |
| Copilot | Claude API (direct Anthropic SDK, no LangChain) |
| Frontend | React/Next.js |
| Local dev | Docker Compose |

#### Deliverables

```
factory-ops-command-center/
├── data-layer/
│   ├── nats_consumer.py       # Consume events from simulator
│   ├── clickhouse_schema.sql  # OEE, downtime tables
│   └── Dockerfile
├── api/
│   ├── fastapi_app.py
│   ├── routes/
│   │   ├─ metrics.py          # Query OEE, downtime, bottlenecks
│   │   ├─ copilot.py          # Chat endpoint
│   │   └─ shift_summary.py    # Summarize shift
│   ├── llm_tools.py           # Tool definitions for Claude
│   └── Dockerfile
├── frontend/
│   ├── pages/
│   │   ├─ dashboard.tsx       # OEE, downtime, bottlenecks
│   │   ├─ chat.tsx            # Copilot interface
│   │   └─ shift-summary.tsx
│   ├── api/query-metrics.ts
│   └── package.json
├── knowledge-base/
│   ├── schema.sql             # Historical incidents, procedures
│   └── seed_data/             # Sample data from simulator
├── docker-compose.yml         # NATS, ClickHouse, PostgreSQL, FastAPI, React
└── README.md
```

#### Success Criteria
- ✅ Ingest synthetic MES data from Digital Twin (events validated against shared `twin/events.py` schema)
- ✅ Dashboard OEE matches Digital Twin's ground-truth calculator within 1% (run `validator.py` in CI)
- ✅ Copilot scores 80%+ on a **golden eval set** of 20–30 operational questions with known answers (measurable, not vibes)
- ✅ Shift summary captures key events + action items
- ✅ Can run entire system with `docker-compose up`

---

### Repository 2: VisionGuard AI Quality Inspection
**Timeline:** 3–4 months  
**Scope:** Core vision + continuous learning

#### Core Features (Ship These)
1. **Defect detection + classification**
   - YOLO v8 fine-tuned on synthetic or public defect dataset
   - Inference: <100ms per image
   - Multi-class classification (surface, dimension, color, missing component)

2. **Explainability**
   - Grad-CAM heatmaps (show where in image is defect)
   - Confidence scores
   - Similar past defects (embedding similarity search)

3. **Inspector correction UI**
   - Web UI: view image + detection → inspector verifies/corrects → feedback logged
   - Correction stored in PostgreSQL
   - Used for retraining

4. **Automated retraining loop**
   - Weekly trigger (or on-demand)
   - Collect corrections from PostgreSQL
   - Fine-tune YOLO on corrections + original training data
   - Validate on holdout test set
   - A/B test (old vs. new model)
   - If better, update inference service

5. **Trend dashboard**
   - Defect counts by shift, machine, type
   - First-pass yield calculation
   - Scrap rate trend

#### Skip (Add in V2+)
- ❌ MES integration
- ❌ Real-time camera feed (use batch images initially)
- ❌ Advanced anomaly detection on defects
- ❌ Supplier quality alerting
- ❌ Kubernetes deployment

#### Tech Stack (Lean)

| Layer | Technology |
|-------|-----------|
| Model | YOLO v8 (PyTorch) |
| Inference server | FastAPI + ONNX Runtime |
| Storage | PostgreSQL + MinIO (local S3-like) |
| Frontend | React |
| Retraining | PyTorch (DVC deferred — gitignored models + promotion gate) |
| Local dev | Docker Compose |

#### Deliverables

```
visionguard-quality-inspection/
├── model-training/
│   ├── notebooks/
│   │   ├─ 01-prepare-dataset.ipynb
│   │   ├─ 02-train-yolo.ipynb
│   │   └─ 03-evaluate.ipynb
│   ├── data/
│   │   ├─ raw/               # Synthetic or public defect images
│   │   └─ processed/
│   ├── models/
│   │   ├─ yolo_v8_custom.pt
│   │   └─ quantized.onnx
│   └── requirements.txt
├── inference-server/
│   ├── inference.py          # FastAPI endpoint
│   ├── yolo_wrapper.py
│   ├── explainability.py     # Grad-CAM
│   └── Dockerfile
├── correction-ui/            # Inspector feedback
│   ├── pages/
│   │   ├─ viewer.tsx         # View image + detections
│   │   └─ correction.tsx     # Correct bboxes, labels
│   ├── api/submit-correction.ts
│   └── package.json
├── retraining-pipeline/
│   ├── collect_corrections.py
│   ├── train.py
│   ├── evaluate.py
│   ├── compare_models.py
│   ├── deploy_if_better.py
│   └── scheduler.py          # Weekly trigger
├── dashboard/
│   ├── pages/
│   │   ├─ defects.tsx
│   │   └─ trends.tsx
│   ├── api/query-defects.ts
│   └── package.json
├── postgres/
│   ├── schema.sql
│   └── migrations/
├── minio/
│   └── docker-compose-minio.yml
├── docker-compose.yml
└── README.md
```

#### Dataset (state it explicitly)
Train/test on a **named public defect set** (NEU-DET surface defects or MVTec AD)
so precision/accuracy numbers are meaningful. Digital Twin's synthetic images
exercise the *pipeline* (correction → retrain → deploy), not the headline metric.

#### Success Criteria
- ✅ Detect defects with >90% precision on the public test set (named above)
- ✅ Classify defect type with >80% accuracy
- ✅ Inference <100ms per image
- ✅ Inspector UI functional (view → correct → submit)
- ✅ **MLOps loop demonstrated**: corrections → retrain → validate on holdout → conditional deploy if better (the loop is the deliverable; accuracy gain on synthetic corrections is not promised)
- ✅ Grad-CAM heatmaps match inspector intuition
- ✅ Can run entire system with `docker-compose up`

---

### Repository 3: Factory Digital Twin (Enabler)
**Timeline:** 4–6 weeks  
**Scope:** Synthetic data generation platform

#### What It Does
Generates realistic factory events so you don't need access to real factory data.

#### Features

1. **MES event generator**
   - Simulates production orders, equipment states, line throughput
   - Outputs: JSON events (production started, production completed, downtime, quality event)
   - Configurable: line speed, downtime frequency, quality rate

2. **Downtime simulator**
   - Realistic downtime scenarios: mechanical, electrical, setup, quality
   - Duration distributions (some quick fixes, some long repairs)
   - Cascading effects (Line A breaks → Line B backs up)

3. **OEE calculator**
   - Ground truth OEE based on simulated events
   - Validates your dashboard calculations

4. **Quality event generator**
   - Simulates defective parts on assembly line
   - Defect types: surface, dimension, color, missing component
   - Correlates with equipment state (worn tool → higher defect rate)

5. **Defect image generator** (synthetic)
   - Option A: Use public defect datasets (Kaggle, SIL dataset)
   - Option B: Generate synthetic images (PIL, albumentations)
   - Creates labeled dataset for YOLO training

#### Tech Stack

| Component | Technology |
|-----------|-----------|
| Event generator | Python (faker, random) |
| Defect images | PIL or Albumentations |
| Output | NATS events, images to MinIO |
| Orchestration | Docker Compose |

#### Deliverables

```
factory-digital-twin/
├── simulator/
│   ├── mes_generator.py       # Production events
│   ├── downtime_generator.py  # Downtime scenarios
│   ├── quality_generator.py   # Quality events
│   ├── config.yaml            # Simulation parameters
│   └── Dockerfile
├── synthetic-images/
│   ├── defect_generator.py    # Create synthetic defect images
│   ├── templates/             # Base images for defects
│   └── output/
├── oee-calculator/
│   ├── oee_engine.py          # Ground truth OEE
│   └── validator.py           # Validate dashboard matches
├── docker-compose.yml         # Simulator + NATS broadcaster
└── README.md
```

#### Success Criteria
- ✅ Generate 1000+ realistic MES events
- ✅ Simulate 24-hour factory operation
- ✅ Output events to NATS (consumed by FactoryOps)
- ✅ Generate labeled defect images (used by VisionGuard)
- ✅ OEE calculator matches dashboard OEE calculations
- ✅ Repeatable (seed for reproducibility)

---

## Consolidated Tech Stack (Lean)

**Tier 1 (Core, from your 6-month plan):**
- Go (already learning) — **give it a real job: the NATS→ClickHouse ingestion gateway in FactoryOps.** A Go service that subscribes to `factory.*`, batches, and writes to ClickHouse. Otherwise drop Go from the narrative; half-used tech reads worse than absent tech.
- NATS (already learning) — transport for the event contract (Twin publishes, gateway consumes)
- ClickHouse (already learning)

**Tier 2 (New, but essential for portfolio):**
- Python (FastAPI for FactoryOps/VisionGuard APIs)
- PostgreSQL + pgvector (knowledge base, corrections)
- React/Next.js (dashboards + UIs)
- PyTorch + YOLO (vision model)
- Claude API (copilot reasoning — direct Anthropic SDK, not LangChain)

**Tier 3 (Nice-to-have, defer):**
- Prometheus/Grafana observability (not yet built — deferred; was Tier 1 in the original 6-month plan)
- Kubernetes (use Docker Compose first)
- dbt (skip data transformation layer for now)
- Airflow (skip orchestration layer for now)
- MES integration (use simulator)

**NOT in this scope:**
- Forecasting
- Advanced optimization
- Multi-agent workflows
- Real-time camera feeds

---

## 12-Month Execution Timeline

### Months 0–6: Foundation + Repositories 1–3 Start
**Your existing 6-month plan remains:**
- Go learning (factory gateway)
- NATS integration
- ClickHouse setup
- Prometheus/Grafana observability

**Sequential (solo dev can't truly parallelize two builds):**
- Week 1–4: Factory Digital Twin — **done first, it's the enabler** ✅ (schema, generators, NATS, ground-truth OEE all working)
- Week 5–16: FactoryOps (consumes Twin's NATS stream end-to-end)
- Week 17–24: VisionGuard (consumes Twin's synthetic defect images)

> Build order is forced by dependency: both consumers need the Twin's contract
> and data before they can do anything. FactoryOps before VisionGuard because the
> NATS→ClickHouse path reuses Twin learnings directly.

### Months 6–9: FactoryOps + VisionGuard MVP
- **FactoryOps:** Dashboard + copilot working
- **VisionGuard:** YOLO trained, inference server running
- **Digital Twin:** Feeding both systems with synthetic data

### Months 9–12: Polish + Production Ready
- **FactoryOps:** RAG optimized, shift summaries working, comprehensive README
- **VisionGuard:** Correction loop functional, retraining automated, dashboard complete
- **All:** Docker Compose working, demo videos recorded

**Deliverable:** Three polished repositories, demo-ready and locally reproducible (`docker-compose up`), fully documented. *Demo-ready* — not multi-node-production; say so honestly.

---

## Why This Works (Execution-Focused)

### 1. Digital Twin Solves Your Biggest Problem
- ❌ Need access to real factory data
- ✅ Generate unlimited synthetic data
- Enables: Repeatable demos, training data for VisionGuard, testing FactoryOps at scale

### 2. Reduced Scope = Faster Shipping
- ❌ Original: 18 features across 2 projects
- ✅ Scoped: 10 essential features
- Result: Ship by month 12, not month 18

### 3. Still Impressive Resume
- ✅ Real-time operational intelligence (FactoryOps)
- ✅ Computer vision + MLOps (VisionGuard)
- ✅ Data engineering (Digital Twin)
- ✅ GenAI integration (copilot)
- No compromises on *what matters*, only on *depth of polish*

### 4. Docker Compose > Kubernetes
- ✅ Works locally, works in production
- ✅ Anyone can run `docker-compose up` and see it
- ✅ Kubernetes is a "nice-to-have", not a differentiator
- Hiring manager cares: "Does it work?" not "Does it scale to 1000 nodes?"

---

## Portfolio Narrative (Cohesive)

**You:** "I build AI systems for factory operations."

**Project 1: FactoryOps AI Command Center**
- Real-time operational intelligence platform
- Combines MES/sensor data with agentic AI copilot
- Plant managers can ask "Why is production down?" and get root cause in seconds
- Tech: NATS → ClickHouse → FastAPI → Claude

**Project 2: VisionGuard AI Quality Inspection**
- Computer vision quality inspection with human-in-the-loop learning
- Inspectors correct misclassifications, which retrain the model weekly
- Automated defect trend analysis by machine/shift/type
- Tech: YOLO v8 → FastAPI → PostgreSQL → React

**Supporting Platform: Factory Digital Twin**
- Synthetic MES event generator + quality simulator
- Enables repeatable demos and training data generation
- Validates FactoryOps calculations against ground truth

**Together:** End-to-end AI system for factory ops, demonstrating data engineering, vision, MLOps, product thinking, manufacturing expertise.

---

## Assessment vs. Scoped Version

| Dimension | Original | Scoped | Target |
|-----------|----------|--------|--------|
| Manufacturing Relevance | 10/10 | 10/10 | ✅ |
| AI Relevance | 9.5/10 | 9.5/10 | ✅ |
| Systems Engineering | 10/10 | 9/10 | ✅ |
| Product Thinking | 10/10 | 9/10 | ✅ |
| Resume Impact | 9.5/10 | 9/10 | ✅ |
| **Realistic Solo Execution** | **6.5/10** | **8.5/10** | ✅ |

**What improved:**
- Reduced features (4 core vs. 11)
- Simplified tech stack (7 vs. 10)
- Added Digital Twin (eliminates data access blocker)
- Clear monthly milestones

---

## How to Pitch This Portfolio

### At Form Energy, Tesla, Anduril
> "I built an AI system for manufacturing operations that combines real-time MES data with an agentic copilot. Plant managers can ask natural language questions and get operational intelligence instantly. I also built a computer vision quality system with continuous learning—inspectors' corrections automatically retrain the model. Everything is runnable with `docker-compose up`."

### At AI Product Management interviews
> "These projects solve real manufacturing problems: OEE improvement, faster decision-making, quality consistency. I speak manufacturing leadership language (cost, downtime, yield) and build products they actually use."

### At Data/AI Engineering interviews
> "I designed a streaming data pipeline (NATS → ClickHouse), built LLM-based reasoning systems (Claude with RAG), implemented computer vision with MLOps, and created a synthetic data platform. I understand production constraints: latency, reliability, cost."

---

## Next Steps

1. ✅ **Digital Twin built** — `factory-digital-twin/`: event contract, deterministic
   generators, NATS publish (~8.9k events/24h), ground-truth OEE ≈ 0.68, synthetic
   defect-image generator (labeled YOLO dataset + MinIO upload, keys match each
   event's `image_ref`). Feeds FactoryOps and VisionGuard.
2. ✅ **FactoryOps built** — Go ingestion gateway (`factory.*` NATS → ClickHouse,
   8904 events, 0 dropped), FastAPI metrics + Copilot (25/25 golden eval, direct
   Anthropic SDK, no LangChain), Next.js dashboard/chat/shift-summary. OEE matches
   Twin ground truth <0.1% after horizon parameterization. `docker compose up`
   runs 7 services.
3. ✅ **VisionGuard built (MVP)** — YOLOv8 detection + EigenCAM, inference server,
   correction UI, full retraining loop (collect → train → compare → conditional
   deploy). Inference is PyTorch/Ultralytics (ONNX deferred); no DVC.
4. **Now: polish + integration glue** — one-command full-stack demo, CI-wired OEE
   validator, committed NEU-DET `metrics.json`, demo videos, and closing the
   VisionGuard upload→retrain path. See [`REVIEW.md`](REVIEW.md) and [`plan.md`](plan.md) for the prioritized roadmap.

You'll have three polished, demo-ready repositories that tell a coherent story.

**This is executable. Build this. 🚀**
