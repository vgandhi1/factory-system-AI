#!/usr/bin/env python3
"""Evaluate a trained model on a dataset's val split and print the headline metrics.

    python evaluate.py --model models/neudet_v1/weights/best.pt --data data/neudet.yaml

Reports per-class and overall precision / recall / mAP plus mean inference latency.
The success criteria (precision >90%, classify accuracy >80%, <100ms/image) are
checked against the printed numbers.
"""
from __future__ import annotations

import argparse
import json
import pathlib


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--json", action="store_true", help="emit metrics as JSON")
    args = ap.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.model)
    m = model.val(data=args.data, imgsz=args.imgsz)

    speed = getattr(m, "speed", {})  # ms per image, by stage
    latency = sum(float(v) for v in speed.values())
    metrics = {
        "precision": round(float(m.box.mp), 4),
        "recall": round(float(m.box.mr), 4),
        "map50": round(float(m.box.map50), 4),
        "map50_95": round(float(m.box.map), 4),
        "latency_ms": round(latency, 2),
        "meets_precision_90": float(m.box.mp) >= 0.90,
        "meets_latency_100ms": latency <= 100.0,
    }
    if args.json:
        print(json.dumps(metrics))
    else:
        for k, v in metrics.items():
            print(f"{k:22s} {v}")

    out = pathlib.Path(args.model).parent / "metrics.json"
    out.write_text(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
