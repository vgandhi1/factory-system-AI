# **Project 2: VisionGuard AI Quality Inspection**

**Timeline:** 3–4 months

**Scope:** Core vision \+ continuous learning

## **Core Features**

* **Defect detection \+ classification:** Uses YOLO v8 fine-tuned on synthetic or public datasets for multi-class classification (surface, dimension, color, missing component) with inference under 100ms per image.  
* **Explainability:** Utilizes EigenCAM heatmaps, confidence scores, and embedding similarity search for past defects.  
* **Inspector correction UI:** A web interface where an inspector verifies or corrects detections, logging the feedback into PostgreSQL for future model retraining.  
* **Automated retraining loop:** A scheduled (weekly or on-demand) trigger that collects corrections, fine-tunes YOLO, validates on a holdout test set, and updates the inference service if A/B testing proves it is better.  
* **Trend dashboard:** Tracks defect counts, calculates first-pass yield, and monitors scrap rate trends.

## **Tech Stack**

* **Model:** YOLO v8 (PyTorch)  
* **Inference server:** FastAPI \+ PyTorch/Ultralytics (loads `.pt`; ONNX export deferred)  
* **Storage:** PostgreSQL \+ MinIO  
* **Frontend:** React  
* **Retraining:** PyTorch (DVC deferred — manual gitignored models + promotion gate)  
* **Local dev:** Docker Compose

## **Deliverables Structure**

* model-training/: Contains notebooks for dataset preparation, training, and evaluation, along with data and saved models.  
* inference-server/: Contains the FastAPI endpoint, YOLO wrapper, and explainability scripts.  
* correction-ui/: Contains pages for viewing images and submitting bounding box/label corrections.  
* retraining-pipeline/: Scripts to collect corrections, train, evaluate, compare models, and deploy.  
* dashboard/, postgres/, minio/, docker-compose.yml, and README.md.

## **Success Criteria**

* Detect defects with \>90% precision on the test set.  
* Classify defect types with \>80% accuracy.  
* Achieve inference of \<100ms per image.  
* Have a functional Inspector UI for viewing, correcting, and submitting feedback.  
* Demonstrate the weekly retraining loop end-to-end (collect → retrain → validate on holdout → conditional deploy if better). The loop completion is the deliverable; accuracy gain on synthetic corrections is not promised.  
* EigenCAM heatmaps must align with inspector intuition.  
* The entire system can be launched with docker-compose up.

---

## **As-Built (June 2026)**

Status: **MVP, demo-ready with caveats** (~70–75% spec).

* **Explainability is EigenCAM, not Grad-CAM** (`inference-server/explainability.py`).
* **Inference loads PyTorch `.pt` via Ultralytics, not ONNX Runtime.** `onnxruntime` is in requirements but never imported; ONNX export path deferred.
* **DVC not implemented.** Models are gitignored; promotion gated by an `IMPROVE_MARGIN` check instead.
* **UI is consolidated into one `webui/` app** (Next.js 14), not separate `correction-ui/` + `dashboard/`. Correction is label-only via dropdown — no bbox editing, no detection overlay yet.
* **Retraining loop complete** (collect → train → compare → conditional deploy), behind `--profile retrain`. Headline precision/accuracy gates use the named public set (NEU-DET); synthetic Twin corrections exercise the loop only.
* **Known gaps:** file-upload corrections don't persist to MinIO so they don't yet feed retrain; trends are lifetime aggregates (not time-series); no committed `metrics.json`. See [`portfolio/REVIEW.md`](../portfolio/REVIEW.md) for full list.