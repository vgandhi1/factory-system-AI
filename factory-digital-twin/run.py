#!/usr/bin/env python3
"""Digital Twin entrypoint.

Usage:
  python run.py --out events.jsonl          # batch to file (default)
  python run.py --nats nats://localhost:4222  # publish to NATS
  python run.py --nats $NATS_URL --realtime   # paced real-time replay
  python run.py --oee                        # print ground-truth OEE and exit

Config from simulator/config.yaml (override with --config).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import yaml

from oee_calculator.oee_engine import compute_oee
from simulator.engine import Engine
from simulator.publisher import publish_nats, write_file


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main() -> int:
    ap = argparse.ArgumentParser(description="Factory Digital Twin")
    ap.add_argument("--config", default="simulator/config.yaml")
    ap.add_argument("--out", default="events.jsonl",
                    help="JSONL output file (file mode)")
    ap.add_argument("--nats", default=os.environ.get("NATS_URL"),
                    help="NATS server URL; if set, publishes instead of file")
    ap.add_argument("--realtime", action="store_true",
                    help="pace publishing by simulated time")
    ap.add_argument("--oee", action="store_true",
                    help="print ground-truth OEE and exit")
    args = ap.parse_args()

    cfg = load_config(args.config)
    engine = Engine(cfg)
    events = engine.run()
    horizon_s = cfg["shift_hours"] * 3600.0

    if args.oee:
        results = [r.as_dict() for r in compute_oee([e for _, e in events], horizon_s)]
        print(json.dumps(results, indent=2))
        return 0

    if args.nats:
        rf = cfg.get("realtime_factor", 0.0) if args.realtime else 0.0
        sent = asyncio.run(publish_nats(events, args.nats, rf))
        print(f"published {sent} events to {args.nats}")
    else:
        n = write_file(events, args.out)
        print(f"wrote {n} events to {args.out}")

    # ground-truth OEE summary alongside the run
    for r in compute_oee([e for _, e in events], horizon_s):
        d = r.as_dict()
        print(f"  {d['line_id']}: OEE={d['oee']:.3f} "
              f"(A={d['availability']:.3f} P={d['performance']:.3f} "
              f"Q={d['quality']:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
