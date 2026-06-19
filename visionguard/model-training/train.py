#!/usr/bin/env python3
"""Fine-tune YOLOv8 on a prepared dataset and export ONNX for the inference server.

    python train.py --data data/neudet.yaml --epochs 50 --name neudet_v1
    python train.py --data data/twin.yaml   --epochs 30 --name twin_v1

Outputs:
  models/<name>/weights/best.pt    – PyTorch weights
  models/<name>.onnx               – ONNX export (used by inference-server)

The inference server loads models/best.onnx by convention; promote a run with
retraining-pipeline/deploy_if_better.py rather than overwriting by hand.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil

HERE = pathlib.Path(__file__).parent
MODELS = HERE / "models"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="dataset yaml from prepare_dataset.py")
    ap.add_argument("--base", default="yolov8n.pt", help="pretrained starting weights")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--name", default="vg_run")
    args = ap.parse_args()

    from ultralytics import YOLO

    MODELS.mkdir(exist_ok=True)
    model = YOLO(args.base)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(MODELS),
        name=args.name,
        exist_ok=True,
    )

    best = MODELS / args.name / "weights" / "best.pt"
    onnx = YOLO(str(best)).export(format="onnx", imgsz=args.imgsz, dynamic=True)
    dst = MODELS / f"{args.name}.onnx"
    shutil.copy(onnx, dst)
    print(f"\nTrained: {best}\nExported ONNX: {dst}")
    print("Promote with: python ../retraining-pipeline/deploy_if_better.py")


if __name__ == "__main__":
    main()
