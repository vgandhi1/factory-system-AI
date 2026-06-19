"""A/B compare a candidate model against the currently deployed model.

Both are evaluated on the same val split (the merged data.yaml's val), so the
comparison is apples-to-apples. Returns the metrics for each and whether the
candidate beats current by the configured margin. If there is no deployed model
yet, the candidate wins by default.
"""
from __future__ import annotations

import pathlib

from config import DEPLOY_DIR, IMPROVE_MARGIN
from evaluate import evaluate
from train import MERGED_YAML


def compare(candidate_path: str, data_yaml: str | None = None) -> dict:
    data_yaml = data_yaml or str(MERGED_YAML)
    current_path = DEPLOY_DIR / "best.pt"

    cand = evaluate(candidate_path, data_yaml)
    if not current_path.exists():
        return {"candidate": cand, "current": None, "deploy": True,
                "reason": "no deployed model yet"}

    cur = evaluate(str(current_path), data_yaml)
    delta = cand["map50"] - cur["map50"]
    deploy = delta >= IMPROVE_MARGIN
    return {
        "candidate": cand,
        "current": cur,
        "map50_delta": round(delta, 4),
        "margin": IMPROVE_MARGIN,
        "deploy": deploy,
        "reason": (f"candidate mAP50 {cand['map50']} vs current {cur['map50']} "
                   f"(Δ{delta:+.4f}, need ≥{IMPROVE_MARGIN})"),
    }


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--data", default=None)
    args = ap.parse_args()
    print(json.dumps(compare(args.candidate, args.data), indent=2))
