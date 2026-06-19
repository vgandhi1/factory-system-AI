<div align="center">

# VisionGuard AI Quality Inspection

### YOLO defect inspection with a human-in-the-loop retrain loop

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-111827?style=for-the-badge)](https://ultralytics.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-inference-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-webui-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)

<br />

<img src="https://img.shields.io/badge/MLOps_loop-complete-emerald?style=flat-square" alt="retrain loop" />
<img src="https://img.shields.io/badge/defect_classes-4-sky?style=flat-square" alt="4 classes" />
<img src="https://img.shields.io/badge/role-quality_inspection-violet?style=flat-square" alt="vision" />

<br />

*Portfolio:* [`../portfolio/Scoped_Executable_Portfolio.md`](../portfolio/Scoped_Executable_Portfolio.md) · [`../portfolio/plan.md`](../portfolio/plan.md)

</div>

---

Computer-vision defect inspection with a human-in-the-loop learning loop. Inspectors verify or correct detections; corrections feed a retrain pipeline that auto-deploys only when the new model is genuinely better.

Consumes the [Factory Digital Twin](../factory-digital-twin)'s synthetic defect images (same 4-class taxonomy as the [event contract](../factory-digital-twin/EVENT_CONTRACT.md)).

> **Honest framing.** Headline precision is measured on the public **NEU-DET** set. Twin synthetic images exercise the *MLOps loop*, not the headline metric. Promotion is gated on holdout improvement — loop completion is the deliverable.

---

## Status

| Component | Status |
|-----------|:------:|
| YOLOv8 training (NEU-DET + Twin synthetic) | ✅ |
| Inference server (FastAPI, <100ms target) | ✅ |
| Explainability — EigenCAM + similar-defect search | ✅ |
| Inspector correction UI + trend dashboard | ✅ |
| Retrain loop — collect → train → compare → deploy | ✅ |
| PostgreSQL + pgvector, MinIO, docker-compose | ✅ |

---

## Architecture

```
            uploads / minio:// image_ref
                      │
              inference-server (YOLOv8)
        detect • CAM heatmap • feature embedding
                      │
   ┌──────────────────┼─────────────────────┐
   ▼                  ▼                      ▼
PostgreSQL        webui (Next.js)        MinIO (images)
detections +   inspect → correct →      defect parts from
corrections +   trends dashboard         the Digital Twin
pgvector              │
   └── retraining-pipeline: collect → train → A/B compare → deploy if better
```

---

## Run

```bash
docker compose up --build
```

| Surface | URL |
|---------|-----|
| Web UI | http://localhost:3001 |
| Inference API | http://localhost:8001/docs |
| MinIO console | http://localhost:9101 (API on **9100**) |

### Train and deploy a real model

```bash
cd ../factory-digital-twin && python synthetic-images/defect_generator.py \
    --minio localhost:9100 --minio-access minioadmin --minio-secret minioadmin
cd ../visionguard/model-training && pip install -r requirements.txt
python prepare_dataset.py --source twin
python train.py --data data/neudet.yaml --epochs 50 --name neudet_v1
cp model-training/models/twin_v1/weights/best.pt inference-server/models/best.pt
docker compose restart inference-server
```

### Score a Twin image

```bash
curl -XPOST localhost:8001/detect/ref -H 'content-type: application/json' \
     -d '{"image_ref":"minio://defects/P-000931.png"}'
```

### Retraining loop

```bash
docker compose --profile retrain up retrainer
```

---

## Directory map

| Path | What |
|------|------|
| [`model-training/`](model-training) | Dataset prep, YOLOv8 train, evaluate |
| [`inference-server/`](inference-server) | FastAPI detect + CAM + similarity |
| [`webui/`](webui) | Inspector UI + trends (Next.js) |
| [`retraining-pipeline/`](retraining-pipeline) | Collect → train → compare → deploy |
| [`postgres/`](postgres) | Schema + pgvector |

---

## Success criteria

| Criterion | Where |
|-----------|-------|
| >90% precision (public set) | `model-training/evaluate.py` on NEU-DET |
| >80% defect classification | same eval report |
| <100ms/image inference | `latency_ms` in API response |
| Inspector UI: view → correct → submit | `webui` → `/corrections` |
| MLOps loop end-to-end | `retraining-pipeline/pipeline.py` |
| EigenCAM heatmaps | `inference-server/explainability.py` |

---

## Portfolio links

Spec: [`SPEC.md`](SPEC.md) · Plan: [`../portfolio/plan.md`](../portfolio/plan.md) · Guardrails: [`../portfolio/GUARDRAILS.md`](../portfolio/GUARDRAILS.md)
