# **Project 1: FactoryOps AI Command Center (Flagship)**

**Timeline:** 3–4 months

**Scope:** Core operational intelligence

## **Core Features**

* **Data ingestion layer:** Consumes synthetic MES events from the Factory Digital Twin, processes them in real-time using Kafka or NATS, and stores the data in ClickHouse.  
* **OEE \+ Downtime dashboard:** A React dashboard with sub-second query latency that provides a real-time OEE breakdown (Availability, Performance, Quality), tracks downtime events, and identifies bottlenecks.  
* **Factory Copilot (RAG-based):** A chat interface that uses Claude with structured prompts to query ClickHouse for live data and PostgreSQL for historical context, returning root cause hypotheses along with supporting data.  
* **Shift handoff intelligence:** Utilizes NLP (Claude) or templates to summarize shifts, highlighting production versus target metrics, downtime events, quality issues, and action items.

## **Tech Stack**

* **Data ingestion:** NATS  
* **Analytics DB:** ClickHouse  
* **Knowledge base:** PostgreSQL \+ pgvector  
* **API:** FastAPI (Python)  
* **Copilot:** Claude API (direct Anthropic SDK)  
* **Frontend:** React/Next.js  
* **Local dev:** Docker Compose

## **Deliverables Structure**

* data-layer/: Contains the NATS consumer, ClickHouse schema, and Dockerfile.  
* api/: Contains the FastAPI app, routing for metrics and copilot, LLM tools, and Dockerfile.  
* frontend/: Contains the dashboard, chat, and shift-summary pages.  
* knowledge-base/: Contains the SQL schema and seed data from the simulator.  
* docker-compose.yml and README.md.

## **Success Criteria**

* Successfully ingest synthetic MES data from the Digital Twin.  
* The dashboard accurately shows OEE, downtime breakdowns, and bottlenecks with sub-second latency.  
* The Copilot correctly answers 80%+ of operational questions.  
* The shift summary successfully captures key events and action items.  
* The entire system can be launched with docker-compose up.

---

## **As-Built (June 2026)**

Status: **shipped, demo-ready** (~85–90% spec).

* **Copilot uses the direct Anthropic SDK, not LangChain.** Tool-use over 5 tools; less abstraction, easier debug.
* **Copilot eval: 25/25 golden set (100%)**, exceeds the 80% bar. Caveat: eval scores keywords, not numeric values.
* **OEE reconciliation fixed** — API matches Twin ground truth <0.1% after horizon parameterization.
* Go gateway, ClickHouse, FastAPI metrics/copilot/shift-summary, Next.js dashboard/chat/shift pages all built. `docker compose up` runs 7 services (includes sibling Twin).
* **Known gaps:** no time-window/live-refresh in UI; procedures seeded but not wired into Copilot tools; NATS at-most-once (no JetStream/dedup); no auth, CORS `*`. See [`portfolio/REVIEW.md`](../portfolio/REVIEW.md) for full list.