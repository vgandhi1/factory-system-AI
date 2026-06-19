"""Scheduled trigger for the retraining loop.

Runs pipeline.run() immediately, then every INTERVAL_HOURS (default weekly).
Kept dependency-free (plain sleep loop) so it runs as a tiny Compose service or a
cron target. For production, a real scheduler (cron / Airflow) would replace this.

    python scheduler.py --once               # run the loop once and exit
    python scheduler.py --interval-hours 168 # weekly (default)
"""
from __future__ import annotations

import argparse
import time

from pipeline import run


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval-hours", type=float, default=168.0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    while True:
        try:
            print(run(force=args.force))
        except Exception as exc:  # noqa: BLE001 - keep the scheduler alive
            print(f"retrain run failed: {exc}")
        if args.once:
            break
        print(f"sleeping {args.interval_hours}h until next retrain…")
        time.sleep(args.interval_hours * 3600)


if __name__ == "__main__":
    main()
