"""Promote a candidate model to production iff it beats the current one.

Copies the winning .pt to inference-server/models/best.pt and exports best.onnx.
The inference server picks up best.pt on its next restart. Conservative by design:
a candidate must clear the improvement margin (compare_models) to deploy.
"""
from __future__ import annotations

import shutil

from compare_models import compare
from config import DEPLOY_DIR


def deploy_if_better(candidate_path: str, data_yaml: str | None = None) -> dict:
    result = compare(candidate_path, data_yaml)
    if not result["deploy"]:
        print(f"NOT deploying: {result['reason']}")
        return result

    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    dst = DEPLOY_DIR / "best.pt"
    shutil.copy(candidate_path, dst)

    # Export ONNX alongside for the ONNX-Runtime deployment path.
    try:
        from ultralytics import YOLO
        onnx = YOLO(str(dst)).export(format="onnx", dynamic=True)
        shutil.copy(onnx, DEPLOY_DIR / "best.onnx")
    except Exception as exc:  # noqa: BLE001
        print(f"(onnx export skipped: {exc})")

    print(f"DEPLOYED candidate -> {dst}. {result['reason']}")
    result["deployed_to"] = str(dst)
    return result


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--data", default=None)
    args = ap.parse_args()
    print(json.dumps(deploy_if_better(args.candidate, args.data), indent=2, default=str))
