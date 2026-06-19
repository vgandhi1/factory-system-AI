"""Run the full retraining loop once:

    collect corrections -> train candidate -> evaluate -> compare -> deploy if better

This is the deliverable: a closed human-in-the-loop MLOps cycle. Accuracy *gain*
on synthetic corrections is not promised; the loop running end-to-end is.

    python pipeline.py            # skip if no new corrections
    python pipeline.py --force    # retrain even with no new corrections
"""
from __future__ import annotations

import argparse

from collect_corrections import collect
from deploy_if_better import deploy_if_better
from train import train_candidate


def run(force: bool = False) -> dict:
    n = collect(dry_run=False)
    if n == 0 and not force:
        print("No new corrections; skipping retrain (use --force to override).")
        return {"status": "skipped", "new_corrections": 0}

    candidate = train_candidate()
    result = deploy_if_better(str(candidate))
    return {"status": "deployed" if result.get("deploy") else "rejected",
            "new_corrections": n, "compare": result}


if __name__ == "__main__":
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    print(json.dumps(run(ap.parse_args().force), indent=2, default=str))
