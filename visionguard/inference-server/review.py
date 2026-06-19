"""Confidence-gate decision (portfolio guardrail), isolated from the FastAPI /
model / DB stack so it is unit-testable without those heavy imports.

Pure function: any defect call below the threshold is routed to a human and is
never auto-accepted; a clean image (no detections) is a pass.
"""
from __future__ import annotations

from config import REVIEW_CONF_THRES


def review_decision(detections: list[dict],
                    threshold: float = REVIEW_CONF_THRES) -> dict:
    if not detections:
        return {"needs_review": False, "reason": "no defects detected (pass)"}
    low = [d for d in detections if d.get("confidence", 0.0) < threshold]
    if low:
        worst = min(d.get("confidence", 0.0) for d in low)
        return {
            "needs_review": True,
            "reason": (f"{len(low)} detection(s) below {threshold:.2f} "
                       f"confidence (min {worst:.2f}) — routed to human review"),
        }
    return {
        "needs_review": False,
        "reason": f"all detections >= {threshold:.2f} confidence",
    }
