"""Publish events to NATS, or to stdout/file when NATS is unavailable.

Keeps the engine transport-agnostic. Real-time mode paces publishing to match
simulated timestamps scaled by `realtime_factor`.
"""
from __future__ import annotations

import asyncio
import json
from typing import Iterable

from twin.events import Event


async def publish_nats(events: list[tuple[float, Event]], servers: str,
                       realtime_factor: float = 0.0) -> int:
    import nats  # imported lazily so file-only mode needs no dependency

    nc = await nats.connect(servers)
    sent = 0
    prev_min = events[0][0] if events else 0.0
    try:
        for sim_min, ev in events:
            if realtime_factor > 0:
                delay = (sim_min - prev_min) * 60.0 * realtime_factor
                if delay > 0:
                    await asyncio.sleep(delay)
                prev_min = sim_min
            await nc.publish(ev.subject(), ev.model_dump_json().encode())
            sent += 1
        await nc.flush()
    finally:
        await nc.drain()
    return sent


def write_file(events: list[tuple[float, Event]], path: str) -> int:
    with open(path, "w") as f:
        for _, ev in events:
            f.write(ev.model_dump_json() + "\n")
    return len(events)
