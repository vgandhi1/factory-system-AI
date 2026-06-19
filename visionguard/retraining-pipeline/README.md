# Retraining pipeline (the MLOps loop)

The headline deliverable: a closed human-in-the-loop cycle.

```
inspector corrections (Postgres)
        │  collect_corrections.py   (+ images from MinIO → YOLO labels)
        ▼
   merged dataset (base + corrections)
        │  train.py                 (fine-tune candidate)
        ▼
   candidate model
        │  compare_models.py        (A/B vs deployed, same holdout)
        ▼
   deploy_if_better.py  ── better? ──► inference-server/models/best.pt (+ .onnx)
        ▲                  no ──► keep current
        │
   scheduler.py  (weekly / on-demand)  →  pipeline.py  (orchestrates all of the above)
```

> Honest framing: the loop running end-to-end is the deliverable. An accuracy
> *gain* from synthetic corrections is not promised — promotion is gated on a
> real holdout improvement (`IMPROVE_MARGIN`), so a non-improving candidate is
> correctly rejected.

## Run

```bash
pip install -r requirements.txt
python pipeline.py            # one full cycle (skips if no new corrections)
python pipeline.py --force    # retrain even without new corrections
python scheduler.py --once    # same as pipeline, via the scheduler entrypoint
python scheduler.py           # weekly loop (default 168h)
```

Individual stages are runnable too:

```bash
python collect_corrections.py --dry-run
python train.py
python compare_models.py  --candidate runs/candidate/weights/best.pt
python deploy_if_better.py --candidate runs/candidate/weights/best.pt
```

## Config (env)

| Var | Default | Meaning |
|-----|---------|---------|
| `POSTGRES_DSN` | `…@localhost:5432/visionguard` | corrections source |
| `MINIO_*` | `localhost:9000` / `minioadmin` | image store |
| `BASE_DATA_YAML` | `../model-training/data/twin.yaml` | base train + holdout |
| `DEPLOY_DIR` | `../inference-server/models` | where `best.pt` is promoted |
| `IMPROVE_MARGIN` | `0.005` | min mAP50 gain to deploy |
| `RETRAIN_EPOCHS` | `30` | fine-tune epochs |
