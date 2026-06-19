"""Ground-truth OEE from the raw event stream.

This is the reference FactoryOps' dashboard must match. Computes per-line
Availability / Performance / Quality / OEE from production + downtime + quality
events using the standard definitions in EVENT_CONTRACT.md.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class LineAgg:
    planned_time_s: float = 0.0     # total horizon for the line
    downtime_s: float = 0.0         # all stops (planned + unplanned)
    total_count: int = 0            # good + scrap
    good_count: int = 0
    ideal_cycle_time_s: float = 0.0  # representative ideal cycle
    _orders: int = 0


@dataclass
class OEEResult:
    line_id: str
    availability: float
    performance: float
    quality: float
    oee: float

    def as_dict(self) -> dict:
        return {
            "line_id": self.line_id,
            "availability": round(self.availability, 4),
            "performance": round(self.performance, 4),
            "quality": round(self.quality, 4),
            "oee": round(self.oee, 4),
        }


def compute_oee(events: list, horizon_s: float) -> list[OEEResult]:
    """events: list of twin.events.Event (or dicts). horizon_s: planned time."""
    agg: dict[str, LineAgg] = defaultdict(LineAgg)

    for ev in events:
        d = ev.model_dump() if hasattr(ev, "model_dump") else ev
        line = d["line_id"]
        p = d["payload"]
        a = agg[line]
        a.planned_time_s = horizon_s
        et = d["event_type"]
        if et == "downtime_ended":
            a.downtime_s += float(p["duration_s"])
        elif et == "production_completed":
            a.total_count += p["good_qty"] + p["scrap_qty"]
            a.good_count += p["good_qty"]
            a.ideal_cycle_time_s = float(p["ideal_cycle_time_s"])
            a._orders += 1

    results = []
    for line, a in agg.items():
        run_time = max(0.0, a.planned_time_s - a.downtime_s)
        availability = run_time / a.planned_time_s if a.planned_time_s else 0.0
        performance = ((a.ideal_cycle_time_s * a.total_count) / run_time
                       if run_time > 0 else 0.0)
        performance = min(performance, 1.0)   # cap (cycle estimate noise)
        quality = a.good_count / a.total_count if a.total_count else 0.0
        results.append(OEEResult(line, availability, performance, quality,
                                 availability * performance * quality))
    return sorted(results, key=lambda r: r.line_id)
