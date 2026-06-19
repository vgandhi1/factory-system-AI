"""VisionGuard inference API.

Endpoints:
  POST /detect         run detection on an uploaded image or a minio:// image_ref;
                       returns detections + CAM heatmap + similar past defects,
                       and logs everything for the correction/retraining loop.
  GET  /detections     recent detections (correction-UI queue)
  GET  /detections/{id}
  POST /corrections    inspector verdict / corrected boxes
  GET  /trends         defect counts, first-pass yield, scrap rate
  GET  /health
"""
from __future__ import annotations

import io
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

import storage
from config import REVIEW_CONF_THRES
from explainability import get_explainer
from review import review_decision
from yolo_wrapper import get_detector

log = logging.getLogger("visionguard.inference")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        storage.ensure_schema()
    except Exception as exc:  # noqa: BLE001
        log.warning("schema init skipped: %s", exc)
    # Warm the model + explainer so the first request isn't slow.
    get_explainer(get_detector())
    yield


app = FastAPI(title="VisionGuard Inference", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


class DetectRef(BaseModel):
    image_ref: str


class Correction(BaseModel):
    detection_id: int
    verdict: str                       # confirm | correct | reject
    inspector: str = "inspector"
    corrected_boxes: list[dict] = []   # [{class_name, bbox:[x0,y0,x1,y1]}]


def _run(image: Image.Image, image_ref: str, source: str) -> dict:
    det = get_detector()
    exp = get_explainer(det)
    detections, latency = det.detect(image)
    review = review_decision(detections)
    heatmap, embedding = exp.explain(image, detections)
    det_id = storage.log_detection(image_ref, source, det.model_path,
                                   latency, detections, embedding,
                                   review["needs_review"])
    similar = storage.similar_defects(embedding, k=3, exclude_id=det_id)
    return {
        "detection_id": det_id,
        "model": det.model_path,
        "using_custom_model": det.using_custom,
        "latency_ms": latency,
        "meets_latency_target": latency <= 100.0,
        "detections": detections,
        "needs_review": review["needs_review"],
        "review_reason": review["reason"],
        "review_threshold": REVIEW_CONF_THRES,
        "heatmap": heatmap,
        "similar_defects": similar,
    }


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """Detect on an uploaded image (multipart)."""
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    return _run(image, file.filename or "", "upload")


@app.post("/detect/ref")
def detect_ref(body: DetectRef):
    """Detect on a minio:// image_ref (e.g. a quality_event's image_ref)."""
    try:
        image = storage.fetch_image(body.image_ref)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"could not fetch {body.image_ref}: {exc}")
    return _run(image, body.image_ref, "minio")


@app.get("/detections")
def list_detections(limit: int = 50, needs_review: bool | None = None):
    """Correction-UI queue. Pass needs_review=true to show only the items the
    confidence gate routed to a human."""
    return {"detections": storage.recent_detections(limit, needs_review)}


@app.get("/detections/{det_id}")
def get_detection(det_id: int):
    d = storage.get_detection(det_id)
    if not d:
        raise HTTPException(404, "not found")
    return d


@app.post("/corrections")
def submit_correction(c: Correction):
    cid = storage.add_correction(c.detection_id, c.inspector, c.verdict,
                                 c.corrected_boxes)
    return {"correction_id": cid, "status": "logged"}


@app.get("/trends")
def trends():
    return storage.trends()


@app.get("/health")
def health():
    det = get_detector()
    return {
        "status": "ok",
        "model": det.model_path,
        "using_custom_model": det.using_custom,
        "postgres": storage.ping(),
    }
