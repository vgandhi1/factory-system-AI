"""YOLOv8 wrapper: load the deployed model (or fall back to pretrained) and run
detection. Exposes the underlying torch model so explainability can hook it.
"""
from __future__ import annotations

import os
import time

import numpy as np
from PIL import Image

from config import CONF_THRES, FALLBACK_MODEL, IMG_SIZE, MODEL_PATH


class Detector:
    def __init__(self) -> None:
        from ultralytics import YOLO

        path = MODEL_PATH if os.path.exists(MODEL_PATH) else FALLBACK_MODEL
        self.using_custom = os.path.exists(MODEL_PATH)
        self.model_path = path
        self.model = YOLO(path)
        # Class names from the loaded model.
        self.names = self.model.names

    def detect(self, image: Image.Image) -> tuple[list[dict], float]:
        """Return (detections, latency_ms). bbox is [x0,y0,x1,y1] in pixels."""
        arr = np.asarray(image.convert("RGB"))
        t0 = time.perf_counter()
        res = self.model.predict(arr, imgsz=IMG_SIZE, conf=CONF_THRES, verbose=False)
        latency = (time.perf_counter() - t0) * 1000.0

        out: list[dict] = []
        r = res[0]
        for b in r.boxes:
            cls = int(b.cls.item())
            out.append({
                "class_id": cls,
                "class_name": self.names.get(cls, str(cls)),
                "confidence": round(float(b.conf.item()), 4),
                "bbox": [round(v, 1) for v in b.xyxy[0].tolist()],
            })
        return out, round(latency, 2)

    @property
    def torch_model(self):
        # ultralytics keeps the nn.Module at .model.model
        return getattr(self.model, "model", None)


_detector: Detector | None = None


def get_detector() -> Detector:
    global _detector
    if _detector is None:
        _detector = Detector()
    return _detector
