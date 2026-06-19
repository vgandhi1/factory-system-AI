"""Simulation engine — generates a time-ordered stream of factory events.

Models each line as a sequence of production orders, interrupted by unplanned
downtime (Poisson onsets) and planned setup between orders. Tool wear raises the
scrap rate over time. Defective parts emit quality events with an image_ref so
VisionGuard has a synthetic dataset to consume.

Deterministic given `seed`. Produces (sim_time, Event) tuples merged across all
lines in timestamp order — suitable for both batch seeding and real-time replay.
"""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from twin.events import (
    DowntimeEnded,
    DowntimeStarted,
    Event,
    ProductionCompleted,
    ProductionStarted,
    QualityEvent,
)


@dataclass
class Counters:
    order: int = 0
    downtime: int = 0
    part: int = 0


@dataclass
class LineState:
    cfg: dict
    parts_since_service: int = 0


class Engine:
    def __init__(self, config: dict):
        self.cfg = config
        seed = config.get("seed", 42)
        self.rng = random.Random(seed)
        # dedicated stream: cascade decisions stay stable regardless of how many
        # draws the per-line sim consumes from self.rng.
        self.crng = random.Random(seed + 1337)
        self.counters = Counters()
        self.start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # -- id helpers ------------------------------------------------------------
    def _order_id(self) -> str:
        self.counters.order += 1
        return f"ORD-{self.counters.order:05d}"

    def _downtime_id(self) -> str:
        self.counters.downtime += 1
        return f"DT-{self.counters.downtime:04d}"

    def _part_id(self) -> str:
        self.counters.part += 1
        return f"P-{self.counters.part:06d}"

    def _ts(self, sim_minute: float) -> str:
        return (self.start + timedelta(minutes=sim_minute)).isoformat()

    # -- sampling --------------------------------------------------------------
    def _pick_downtime_category(self) -> tuple[str, float]:
        cats = self.cfg["downtime"]["categories"]
        names = list(cats)
        weights = [cats[n]["weight"] for n in names]
        name = self.rng.choices(names, weights=weights)[0]
        spec = cats[name]
        dur = self.rng.uniform(spec["min"], spec["max"])
        return name, dur

    def _pick_defect_type(self) -> str:
        d = self.cfg["defect_types"]
        names = list(d)
        return self.rng.choices(names, weights=[d[n] for n in names])[0]

    # -- per-line simulation ---------------------------------------------------
    def _simulate_line(self, line_cfg: dict):
        """Return (events, triggers) where triggers are this line's unplanned
        stops as (onset_min, duration_min, category) — used to cascade downtime
        onto downstream lines."""
        out: list[tuple[float, Event]] = []
        triggers: list[tuple[float, float, str]] = []
        line_id = line_cfg["id"]
        prod_station = line_cfg["stations"][0]
        inspect_station = line_cfg["stations"][-1]
        horizon_min = self.cfg["shift_hours"] * 60.0
        mttf = self.cfg["downtime"]["mttf_minutes"]
        setup = self.cfg["downtime"]["setup_minutes"]

        t = 0.0
        parts_since_service = 0
        next_failure = self.rng.expovariate(1.0 / mttf)
        first_order = True

        while t < horizon_min:
            # ---- planned setup / changeover between orders ----
            # Per-line flag, not the global order counter: changeover precedes
            # every order *except this line's first*, so each line behaves the
            # same regardless of simulation order.
            if not first_order:
                setup_dur = self.rng.uniform(setup["min"], setup["max"])
                dt_id = self._downtime_id()
                out.append((t, Event.of("downtime_started", line_id, prod_station,
                    DowntimeStarted(downtime_id=dt_id, category="setup",
                                    planned=True, reason="Order changeover"),
                    ts=self._ts(t))))
                t += setup_dur
                out.append((t, Event.of("downtime_ended", line_id, prod_station,
                    DowntimeEnded(downtime_id=dt_id, duration_s=setup_dur * 60),
                    ts=self._ts(t))))
            first_order = False

            # ---- start order ----
            order_id = self._order_id()
            qty = self.rng.randint(self.cfg["order_qty"]["min"],
                                   self.cfg["order_qty"]["max"])
            out.append((t, Event.of("production_started", line_id, prod_station,
                ProductionStarted(order_id=order_id,
                                  product_sku=line_cfg["product_sku"],
                                  target_qty=qty), ts=self._ts(t))))

            good = scrap = 0
            cycle_sum = 0.0
            for _ in range(qty):
                # unplanned downtime?
                if t >= next_failure and t < horizon_min:
                    cat, dur = self._pick_downtime_category()
                    onset = t
                    dt_id = self._downtime_id()
                    out.append((t, Event.of("downtime_started", line_id, prod_station,
                        DowntimeStarted(downtime_id=dt_id, category=cat,
                                        planned=False,
                                        reason=f"Unplanned {cat} stop"),
                        ts=self._ts(t))))
                    t += dur
                    out.append((t, Event.of("downtime_ended", line_id, prod_station,
                        DowntimeEnded(downtime_id=dt_id, duration_s=dur * 60),
                        ts=self._ts(t))))
                    triggers.append((onset, dur, cat))
                    next_failure = t + self.rng.expovariate(1.0 / mttf)

                # produce one part
                worn = parts_since_service >= line_cfg["tool_wear_after_parts"]
                scrap_rate = (line_cfg["worn_scrap_rate"] if worn
                              else line_cfg["base_scrap_rate"])
                # actual runs slower than ideal (speed loss) -> Performance < 1
                cycle_mean = line_cfg["ideal_cycle_time_s"] * line_cfg.get(
                    "speed_loss", 1.0)
                cycle = max(1.0, self.rng.gauss(cycle_mean,
                                                line_cfg["cycle_jitter_s"]))
                cycle_sum += cycle
                t += cycle / 60.0
                parts_since_service += 1
                part_id = self._part_id()

                if self.rng.random() < scrap_rate:
                    scrap += 1
                    dtype = self._pick_defect_type()
                    out.append((t, Event.of("quality_event", line_id, inspect_station,
                        QualityEvent(part_id=part_id, result="defect",
                                     defect_type=dtype, confidence=1.0,
                                     image_ref=f"minio://defects/{part_id}.png",
                                     equipment_state="tool_worn" if worn else "nominal"),
                        ts=self._ts(t))))
                else:
                    good += 1
                    out.append((t, Event.of("quality_event", line_id, inspect_station,
                        QualityEvent(part_id=part_id, result="pass",
                                     equipment_state="tool_worn" if worn else "nominal"),
                        ts=self._ts(t))))

                if worn and self.rng.random() < 0.02:   # tool service resets wear
                    parts_since_service = 0

            avg_cycle = cycle_sum / qty if qty else line_cfg["ideal_cycle_time_s"]
            out.append((t, Event.of("production_completed", line_id, prod_station,
                ProductionCompleted(order_id=order_id, good_qty=good,
                                    scrap_qty=scrap,
                                    ideal_cycle_time_s=line_cfg["ideal_cycle_time_s"],
                                    actual_cycle_time_s=round(avg_cycle, 2)),
                ts=self._ts(t))))

        return out, triggers

    # -- cascade ---------------------------------------------------------------
    def _cascade_events(self, triggers_by_line: dict, lines_by_id: dict
                        ) -> list[tuple[float, Event]]:
        """Turn source-line stops into delayed downtime on downstream lines.

        Config (per source line): affects, delay_minutes, prob, backup_factor,
        min_source_minutes. Downstream stop = material starvation lasting
        backup_factor * source duration, starting delay_minutes after the source
        onset; only long source stops (>= min_source_minutes) propagate.

        Simplification: the downstream line's production timeline is NOT reflowed,
        so the cascade adds a correlated downtime event (valuable for downtime
        analytics and Copilot root-cause stories) but leaves part counts intact.
        Because A*P = ideal_cycle*count/planned_time is invariant to how planned
        time splits between run and downtime, cascade has ~no net OEE effect here;
        its visible impact is on the Availability/Performance breakdown and the
        downtime stream, not headline OEE. Reflowing production is future work.
        """
        cascade_cfg = self.cfg["downtime"].get("cascade", {})
        horizon_min = self.cfg["shift_hours"] * 60.0
        out: list[tuple[float, Event]] = []

        for src_line, spec in cascade_cfg.items():
            affected = spec["affects"]
            if affected not in lines_by_id:
                continue
            delay = spec["delay_minutes"]
            prob = spec["prob"]
            factor = spec.get("backup_factor", 0.6)
            min_src = spec.get("min_source_minutes", 0)
            station = lines_by_id[affected]["stations"][0]

            for onset, dur, cat in triggers_by_line.get(src_line, []):
                if dur < min_src:           # short stops don't starve downstream
                    continue
                if self.crng.random() >= prob:
                    continue
                start = onset + delay
                if start >= horizon_min:
                    continue
                bdur = dur * factor
                dt_id = self._downtime_id()
                out.append((start, Event.of("downtime_started", affected, station,
                    DowntimeStarted(downtime_id=dt_id, category="material",
                                    planned=False,
                                    reason=f"Backed up by {src_line} {cat} stop"),
                    ts=self._ts(start))))
                end = start + bdur
                out.append((end, Event.of("downtime_ended", affected, station,
                    DowntimeEnded(downtime_id=dt_id, duration_s=bdur * 60),
                    ts=self._ts(end))))
        return out

    # -- public ---------------------------------------------------------------
    def run(self) -> list[tuple[float, Event]]:
        """Return all events across all lines, sorted by sim time."""
        events: list[tuple[float, Event]] = []
        triggers_by_line: dict[str, list] = {}
        lines_by_id = {lc["id"]: lc for lc in self.cfg["lines"]}

        for line_cfg in self.cfg["lines"]:
            evs, triggers = self._simulate_line(line_cfg)
            events.extend(evs)
            triggers_by_line[line_cfg["id"]] = triggers

        events.extend(self._cascade_events(triggers_by_line, lines_by_id))
        events.sort(key=lambda x: x[0])

        # Assign event_ids deterministically from a dedicated seeded stream (in
        # final sorted order) so a given seed yields byte-identical output, while
        # keeping the UUID4 format the contract specifies. Decoupled from the sim
        # rng so it never perturbs simulation behavior.
        idrng = random.Random(self.cfg.get("seed", 42) + 7)
        for _, ev in events:
            ev.event_id = str(uuid.UUID(int=idrng.getrandbits(128), version=4))
        return events
