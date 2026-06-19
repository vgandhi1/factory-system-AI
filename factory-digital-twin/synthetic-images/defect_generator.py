#!/usr/bin/env python3
"""Generate a labeled YOLO defect dataset that matches the Twin's event stream.

The simulator already stamps each defective part with an `image_ref` of
`minio://defects/{part_id}.png`. This script renders exactly those images (plus
a configurable fraction of clean "negative" parts), writes YOLO labels, splits
train/val, and optionally uploads the images to MinIO under that same key — so
VisionGuard can resolve any quality_event's `image_ref` directly.

Usage:
  python synthetic-images/defect_generator.py                 # local dataset
  python synthetic-images/defect_generator.py --limit 300     # cap defect imgs
  python synthetic-images/defect_generator.py \
      --minio localhost:9000 --minio-access minioadmin \
      --minio-secret minioadmin                               # + upload
"""
from __future__ import annotations

import argparse
import os
import random
import sys

import yaml
from PIL import Image

# allow running from repo root or this dir
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))   # repo root -> simulator package
sys.path.insert(0, _HERE)                    # this dir   -> renderers
from simulator.engine import Engine                       # noqa: E402
from renderers import CLASSES, render_part                # noqa: E402


def _load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _defect_parts(cfg: dict):
    """Run the engine; yield (part_id, defect_type) for defects and 'none' passes."""
    defects, passes = [], []
    for _, ev in Engine(cfg).run():
        if ev.event_type != "quality_event":
            continue
        p = ev.payload
        if p["result"] == "defect":
            defects.append((p["part_id"], p["defect_type"]))
        else:
            passes.append((p["part_id"], "none"))
    return defects, passes


def _write_label(path: str, labels, size: int) -> None:
    lines = []
    for cls, (x0, y0, x1, y1) in labels:
        cx = (x0 + x1) / 2 / size
        cy = (y0 + y1) / 2 / size
        w = (x1 - x0) / size
        h = (y1 - y0) / size
        lines.append(f"{cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    with open(path, "w") as f:
        f.write("".join(line + "\n" for line in lines))


def main() -> int:
    ap = argparse.ArgumentParser(description="Synthetic defect dataset generator")
    ap.add_argument("--config", default="simulator/config.yaml")
    ap.add_argument("--out", default="synthetic-images/output")
    ap.add_argument("--size", type=int, default=640)
    ap.add_argument("--limit", type=int, default=0, help="max defect images (0=all)")
    ap.add_argument("--negatives-ratio", type=float, default=0.3,
                    help="clean images per defect image")
    ap.add_argument("--val-split", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--minio", default=None, help="MinIO endpoint host:port")
    ap.add_argument("--minio-access", default=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"))
    ap.add_argument("--minio-secret", default=os.environ.get("MINIO_SECRET_KEY", "minioadmin"))
    ap.add_argument("--minio-bucket", default="defects")
    args = ap.parse_args()

    cfg = _load_config(args.config)
    seed = args.seed if args.seed is not None else cfg.get("seed", 42)
    rng = random.Random(seed)

    defects, passes = _defect_parts(cfg)
    rng.shuffle(defects)
    if args.limit:
        defects = defects[:args.limit]
    n_neg = int(len(defects) * args.negatives_ratio)
    rng.shuffle(passes)
    negatives = passes[:n_neg]

    samples = [(pid, dt) for pid, dt in defects] + [(pid, "none") for pid, dt in negatives]
    rng.shuffle(samples)

    # dirs
    for split in ("train", "val"):
        os.makedirs(os.path.join(args.out, "images", split), exist_ok=True)
        os.makedirs(os.path.join(args.out, "labels", split), exist_ok=True)

    upload = []
    counts = {c: 0 for c in CLASSES + ["none"]}
    for i, (part_id, dtype) in enumerate(samples):
        split = "val" if rng.random() < args.val_split else "train"
        img, labels = render_part(args.size, dtype, rng)
        img_path = os.path.join(args.out, "images", split, f"{part_id}.png")
        lbl_path = os.path.join(args.out, "labels", split, f"{part_id}.txt")
        img.save(img_path)
        _write_label(lbl_path, labels, args.size)
        counts[dtype if dtype != "none" else "none"] += 1
        upload.append((f"{part_id}.png", img_path))

    # data.yaml for YOLO
    data_yaml = {
        "path": os.path.abspath(args.out),
        "train": "images/train",
        "val": "images/val",
        "names": {i: c for i, c in enumerate(CLASSES)},
    }
    with open(os.path.join(args.out, "data.yaml"), "w") as f:
        yaml.safe_dump(data_yaml, f, sort_keys=False)

    print(f"generated {len(samples)} images -> {args.out}")
    print(f"  by type: {counts}")
    print(f"  data.yaml classes: {CLASSES}")

    if args.minio:
        _upload_minio(args, upload)
    return 0


def _upload_minio(args, upload):
    from minio import Minio
    client = Minio(args.minio, access_key=args.minio_access,
                   secret_key=args.minio_secret, secure=False)
    if not client.bucket_exists(args.minio_bucket):
        client.make_bucket(args.minio_bucket)
    for key, path in upload:
        client.fput_object(args.minio_bucket, key, path, content_type="image/png")
    print(f"uploaded {len(upload)} images to minio://{args.minio_bucket}/ "
          f"(keys match event image_ref)")


if __name__ == "__main__":
    sys.exit(main())
