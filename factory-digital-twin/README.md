<div align="center">

# Factory Digital Twin

### Deterministic synthetic MES events — the enabler for the whole portfolio

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![NATS](https://img.shields.io/badge/NATS-JetStream-27AAE1?style=for-the-badge)](https://nats.io/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge)](https://docs.pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)

<br />

<img src="https://img.shields.io/badge/OEE_ground_truth-~0.68-emerald?style=flat-square" alt="OEE ~0.68" />
<img src="https://img.shields.io/badge/events_24h-~8900-sky?style=flat-square" alt="~8900 events" />
<img src="https://img.shields.io/badge/role-portfolio_enabler-indigo?style=flat-square" alt="enabler" />

<br />

*Contract:* [`EVENT_CONTRACT.md`](EVENT_CONTRACT.md) · *Portfolio:* [`../README.md`](../README.md) · [`../portfolio/plan.md`](../portfolio/plan.md)

</div>

---

Synthetic factory-event generator. Produces a realistic, **deterministic** stream of MES / downtime / quality events so FactoryOps and VisionGuard can be built and demoed without access to a real plant.

It is the **enabler** repo: it defines the event contract both consumers depend on, and ships a ground-truth OEE calculator that validates their dashboards.

---

## What it generates

- **Production** — orders, completions with good/scrap counts and cycle times
- **Downtime** — planned + unplanned (mechanical, electrical, material, quality) with Poisson failures; **cascading** upstream stops starve downstream lines after a delay
- **Quality** — pass/defect events; defects carry `defect_type` and `image_ref` for VisionGuard
- **Tool wear** — scrap rate rises as tools wear, then resets on service

Numbers land in believable territory: **OEE ≈ 0.68** (A≈0.75, P≈0.95, Q≈0.95), not a suspicious 1.000.

---

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python run.py --out events.jsonl      # batch to JSONL (~9k events / 24h)
python run.py --oee                   # print ground-truth OEE, exit
```

With NATS:

```bash
docker compose up
# or: python run.py --nats nats://localhost:4222 --realtime
```

---

## The contract

[`EVENT_CONTRACT.md`](EVENT_CONTRACT.md) is the stable interface. Pydantic models in [`twin/events.py`](twin/events.py) are the executable form — FactoryOps imports them so producer and consumer validate against one definition.

| Subject | Events |
|---------|--------|
| `factory.production` | `production_started`, `production_completed` |
| `factory.downtime` | `downtime_started`, `downtime_ended` |
| `factory.quality` | `quality_event` |

---

## Ground truth

`oee_calculator/oee_engine.py` computes per-line OEE from the event stream. `oee_calculator/validator.py` checks a consumer's reported OEE within tolerance:

```python
from oee_calculator.validator import validate
ok, problems = validate(events, horizon_s, factoryops_reported)
```

---

## Layout

```
factory-digital-twin/
├── EVENT_CONTRACT.md        # interface spec (read first)
├── twin/events.py           # pydantic models (shared with consumers)
├── simulator/               # config.yaml, engine.py, publisher.py
├── oee_calculator/          # ground-truth OEE + validator
├── synthetic-images/        # YOLO dataset + MinIO upload
├── run.py
└── docker-compose.yml       # NATS + simulator
```

---

## Synthetic defect images

`synthetic-images/defect_generator.py` renders a labeled YOLO dataset matching the event stream — four defect classes plus clean negatives (PIL-only).

```bash
python synthetic-images/defect_generator.py
python synthetic-images/defect_generator.py --limit 300 \
    --minio localhost:9000 --minio-access minioadmin --minio-secret minioadmin
```

Produces `output/{images,labels}/{train,val}/` + `data.yaml`. MinIO keys match `image_ref` exactly for VisionGuard.

---

## Status

| Capability | Status |
|------------|:------:|
| Event contract + pydantic models | ✅ |
| Deterministic MES / downtime / quality | ✅ |
| NATS publish + JSONL batch | ✅ |
| Ground-truth OEE + validator | ✅ |
| Synthetic defect images + MinIO | ✅ |
| Docker Compose | ✅ |
| Cascading cross-line downtime | ✅ |

---

## Portfolio links

Spec: [`SPEC.md`](SPEC.md) · Plan: [`../portfolio/plan.md`](../portfolio/plan.md) · Guardrails: [`../portfolio/GUARDRAILS.md`](../portfolio/GUARDRAILS.md)
