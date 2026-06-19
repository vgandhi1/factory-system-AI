#!/usr/bin/env python3
"""Prepare a YOLO dataset for VisionGuard.

Two sources, two purposes (see README):

  --source neudet  NEU-DET surface-defect benchmark (6 classes). The *headline
                   metric* (precision/accuracy) is reported here because it's a
                   named public set. NEU-DET ships Pascal-VOC XML; we convert to
                   YOLO txt and write data/neudet.yaml.

  --source twin    The Factory Digital Twin's synthetic images (4 classes:
                   surface/dimension/color/missing_component). Already in YOLO
                   format with data.yaml — we just point at it (or copy it in).
                   This taxonomy matches FactoryOps / EVENT_CONTRACT and is what
                   the correction → retrain → deploy loop runs on.

Usage:
  python prepare_dataset.py --source twin \
      --twin-dir ../../factory-digital-twin/synthetic-images/output
  python prepare_dataset.py --source neudet --neudet-dir data/raw/NEU-DET
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import xml.etree.ElementTree as ET

import yaml

HERE = pathlib.Path(__file__).parent
DATA = HERE / "data"

# NEU-DET's six surface-defect classes (its native taxonomy).
NEU_CLASSES = [
    "crazing", "inclusion", "patches",
    "pitted_surface", "rolled-in_scale", "scratches",
]


def prepare_twin(twin_dir: pathlib.Path) -> pathlib.Path:
    """Point VisionGuard at the Twin's YOLO dataset by rewriting a data.yaml with
    an absolute path. No image copy — the Twin owns the source of truth."""
    src_yaml = twin_dir / "data.yaml"
    if not src_yaml.exists():
        raise SystemExit(
            f"{src_yaml} not found. Generate it first:\n"
            "  cd factory-digital-twin && "
            "python synthetic-images/defect_generator.py")
    cfg = yaml.safe_load(src_yaml.read_text())
    cfg["path"] = str(twin_dir.resolve())
    out = DATA / "twin.yaml"
    DATA.mkdir(exist_ok=True)
    out.write_text(yaml.safe_dump(cfg, sort_keys=False))
    print(f"twin dataset -> {out} ({cfg['names']})")
    return out


def _voc_to_yolo(xml_path: pathlib.Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    size = root.find("size")
    w, h = int(size.find("width").text), int(size.find("height").text)
    rows = []
    for obj in root.findall("object"):
        name = obj.find("name").text.strip()
        if name not in NEU_CLASSES:
            continue
        cls = NEU_CLASSES.index(name)
        b = obj.find("bndbox")
        x0, y0 = float(b.find("xmin").text), float(b.find("ymin").text)
        x1, y1 = float(b.find("xmax").text), float(b.find("ymax").text)
        cx, cy = (x0 + x1) / 2 / w, (y0 + y1) / 2 / h
        bw, bh = (x1 - x0) / w, (y1 - y0) / h
        rows.append(f"{cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    return rows


def prepare_neudet(neudet_dir: pathlib.Path, val_frac: float = 0.2) -> pathlib.Path:
    """Convert NEU-DET (VOC) to a YOLO dataset with a train/val split."""
    images = sorted((neudet_dir / "IMAGES").glob("*.jpg"))
    if not images:
        raise SystemExit(
            f"No images under {neudet_dir}/IMAGES. Download NEU-DET first "
            "(see README) and unzip to data/raw/NEU-DET.")
    ann_dir = neudet_dir / "ANNOTATIONS"
    out = DATA / "neudet"
    for split in ("train", "val"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    n_val = int(len(images) * val_frac)
    for i, img in enumerate(images):
        split = "val" if i < n_val else "train"
        shutil.copy(img, out / "images" / split / img.name)
        rows = _voc_to_yolo(ann_dir / f"{img.stem}.xml")
        (out / "labels" / split / f"{img.stem}.txt").write_text("\n".join(rows))

    cfg = {
        "path": str(out.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: c for i, c in enumerate(NEU_CLASSES)},
    }
    yaml_path = DATA / "neudet.yaml"
    yaml_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    print(f"neudet dataset -> {yaml_path} "
          f"({len(images)} imgs, {n_val} val, {len(NEU_CLASSES)} classes)")
    return yaml_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["twin", "neudet"], required=True)
    ap.add_argument("--twin-dir",
                    default="../../factory-digital-twin/synthetic-images/output")
    ap.add_argument("--neudet-dir", default="data/raw/NEU-DET")
    args = ap.parse_args()

    if args.source == "twin":
        prepare_twin(pathlib.Path(args.twin_dir))
    else:
        prepare_neudet(pathlib.Path(args.neudet_dir))


if __name__ == "__main__":
    main()
