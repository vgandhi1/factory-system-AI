"""Evaluate a model on a dataset's val split. Returns comparable metrics."""
from __future__ import annotations

from config import IMG_SIZE


def evaluate(model_path: str, data_yaml: str, imgsz: int = IMG_SIZE) -> dict:
    from ultralytics import YOLO

    m = YOLO(model_path).val(data=data_yaml, imgsz=imgsz, verbose=False)
    speed = getattr(m, "speed", {})
    return {
        "model": model_path,
        "precision": round(float(m.box.mp), 4),
        "recall": round(float(m.box.mr), 4),
        "map50": round(float(m.box.map50), 4),
        "map50_95": round(float(m.box.map), 4),
        "latency_ms": round(sum(float(v) for v in speed.values()), 2),
    }


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True)
    args = ap.parse_args()
    print(json.dumps(evaluate(args.model, args.data), indent=2))
