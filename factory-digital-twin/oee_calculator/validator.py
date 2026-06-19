"""Validate a consumer's reported OEE against the Twin's ground truth.

FactoryOps (or any consumer) reports OEE per line; this checks it lands within
tolerance of the values computed directly from the event stream. Used in CI to
catch dashboard calculation drift.
"""
from __future__ import annotations

from oee_calculator.oee_engine import compute_oee


def validate(events: list, horizon_s: float, reported: dict[str, dict],
             tol: float = 0.01) -> tuple[bool, list[str]]:
    """reported: {line_id: {availability, performance, quality, oee}}.
    Returns (ok, list_of_mismatch_messages)."""
    truth = {r.line_id: r.as_dict() for r in compute_oee(events, horizon_s)}
    problems: list[str] = []
    for line, t in truth.items():
        r = reported.get(line)
        if r is None:
            problems.append(f"{line}: no reported value")
            continue
        for k in ("availability", "performance", "quality", "oee"):
            if abs(t[k] - r.get(k, -1)) > tol:
                problems.append(
                    f"{line}.{k}: truth={t[k]:.4f} reported={r.get(k)} "
                    f"(>{tol} off)")
    return (not problems), problems
