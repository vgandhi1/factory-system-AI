"""Fine-tune a candidate model on base data + collected corrections.

Builds a merged YOLO data.yaml whose train set is [base_train, corrections_train]
and whose val set is the base holdout (so eval stays comparable across runs), then
trains a candidate into runs/candidate/weights/best.pt.
"""
from __future__ import annotations

import pathlib

import yaml

from config import (
    BASE_DATA_YAML,
    BASE_WEIGHTS,
    CLASS_NAMES,
    DATASET_DIR,
    EPOCHS,
    HERE,
    IMG_SIZE,
)

RUNS = HERE / "runs"
MERGED_YAML = HERE / "merged_data.yaml"


def build_merged_yaml() -> pathlib.Path:
    base = yaml.safe_load(pathlib.Path(BASE_DATA_YAML).read_text())
    base_root = pathlib.Path(base.get("path", ".")).resolve()

    def _abs(p) -> str:
        p = pathlib.Path(p)
        return str(p if p.is_absolute() else base_root / p)

    train_sets = [_abs(base["train"])]
    corr_train = DATASET_DIR / "images" / "train"
    if corr_train.exists() and any(corr_train.iterdir()):
        train_sets.append(str(corr_train.resolve()))

    merged = {
        "train": train_sets,
        "val": _abs(base["val"]),
        "names": {i: c for i, c in enumerate(CLASS_NAMES)},
    }
    MERGED_YAML.write_text(yaml.safe_dump(merged, sort_keys=False))
    print(f"merged dataset -> {MERGED_YAML}: train={train_sets}")
    return MERGED_YAML


def train_candidate() -> pathlib.Path:
    from ultralytics import YOLO

    data = build_merged_yaml()
    RUNS.mkdir(exist_ok=True)
    model = YOLO(BASE_WEIGHTS)
    model.train(data=str(data), epochs=EPOCHS, imgsz=IMG_SIZE,
                project=str(RUNS), name="candidate", exist_ok=True)
    best = RUNS / "candidate" / "weights" / "best.pt"
    print(f"candidate trained -> {best}")
    return best


if __name__ == "__main__":
    train_candidate()
