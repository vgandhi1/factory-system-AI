"""Shared configuration for the retraining pipeline."""
from __future__ import annotations

import os
import pathlib

HERE = pathlib.Path(__file__).parent
REPO = HERE.parent


def _env(k: str, d: str = "") -> str:
    v = os.getenv(k)
    return v if v not in (None, "") else d


POSTGRES_DSN = _env("POSTGRES_DSN",
                    "postgresql://visionguard:visionguard@localhost:5432/visionguard")
MINIO_ENDPOINT = _env("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = _env("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = _env("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = _env("MINIO_SECURE", "false").lower() == "true"

# Operational taxonomy (matches the Twin / EVENT_CONTRACT). The retraining loop
# runs on these classes; "none" means a negative (no-defect) example.
CLASS_NAMES = ["surface", "dimension", "color", "missing_component"]

# Paths.
DATASET_DIR = pathlib.Path(_env("DATASET_DIR", str(HERE / "dataset")))
# Base dataset to fine-tune on alongside corrections (the Twin's synthetic set).
BASE_DATA_YAML = _env("BASE_DATA_YAML",
                      str(REPO / "model-training" / "data" / "twin.yaml"))
# Where a promoted model lands (the inference server reads models/best.pt).
DEPLOY_DIR = pathlib.Path(_env("DEPLOY_DIR",
                               str(REPO / "inference-server" / "models")))

# Promotion gate: a candidate must beat the current model's mAP50 by this margin.
IMPROVE_MARGIN = float(_env("IMPROVE_MARGIN", "0.005"))
EPOCHS = int(_env("RETRAIN_EPOCHS", "30"))
IMG_SIZE = int(_env("IMG_SIZE", "640"))
BASE_WEIGHTS = _env("BASE_WEIGHTS", "yolov8n.pt")
