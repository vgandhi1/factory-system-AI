"""Inference server configuration."""
from __future__ import annotations

import os


def _env(k: str, d: str = "") -> str:
    v = os.getenv(k)
    return v if v not in (None, "") else d


# Model. Prefers a promoted custom model; falls back to pretrained yolov8n so the
# server boots out-of-the-box (it just won't recognise factory defects until a
# real model is trained + deployed).
MODEL_PATH = _env("MODEL_PATH", "models/best.pt")
FALLBACK_MODEL = _env("FALLBACK_MODEL", "yolov8n.pt")
IMG_SIZE = int(_env("IMG_SIZE", "640"))
# Box filter: minimum confidence for YOLO to emit a detection at all.
CONF_THRES = float(_env("CONF_THRES", "0.25"))
# Human-review gate: any emitted defect call below this confidence must be routed
# to an inspector and is never auto-accepted (portfolio guardrail). Distinct from
# CONF_THRES — a box can clear the box filter yet still require human review.
REVIEW_CONF_THRES = float(_env("REVIEW_CONF_THRES", "0.70"))

# Embedding dimension for the pgvector similarity search. The backbone activation
# channel vector is resized to this fixed length so the column type is stable.
EMBED_DIM = int(_env("EMBED_DIM", "256"))

# Storage.
POSTGRES_DSN = _env("POSTGRES_DSN",
                    "postgresql://visionguard:visionguard@localhost:5432/visionguard")
MINIO_ENDPOINT = _env("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = _env("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = _env("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = _env("MINIO_SECURE", "false").lower() == "true"
