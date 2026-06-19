"""Unit tests for the Digital Twin generator + ground-truth OEE calculator.

Pure logic only (no NATS/MinIO), so it runs in CI without infra.
"""
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oee_calculator.oee_engine import compute_oee  # noqa: E402
from simulator.engine import Engine  # noqa: E402


def _run():
    cfg = yaml.safe_load((ROOT / "simulator" / "config.yaml").read_text())
    events = [e for _, e in Engine(cfg).run()]
    return cfg, events


def test_oee_components_bounded():
    """OEE and each component must stay in [0,1] (guardrail: OEE is 0-100%)."""
    cfg, events = _run()
    results = compute_oee(events, cfg["shift_hours"] * 3600)
    assert results, "no OEE results produced"
    for r in results:
        d = r.as_dict()
        for k in ("availability", "performance", "quality", "oee"):
            assert 0.0 <= d[k] <= 1.0, f"{d['line_id']} {k}={d[k]} out of [0,1]"


def test_no_spurious_setup_before_first_order():
    """Regression: per-line first_order gate. Each line's first event must be a
    production_started, not a phantom 'setup' changeover (engine.py:103)."""
    cfg, events = _run()  # already in chronological (sim-time) order
    first = {}
    for e in events:
        first.setdefault(e.line_id, e.event_type)
    assert first, "no events emitted"
    for line, etype in first.items():
        assert etype == "production_started", f"{line} starts with {etype!r}"
