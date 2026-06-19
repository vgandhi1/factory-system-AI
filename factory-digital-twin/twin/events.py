"""Event schema — the contract between Twin and consumers.

Pydantic models mirror EVENT_CONTRACT.md. Importable by FactoryOps so both
sides validate against the same definitions. Bump SCHEMA_VERSION on breaking
changes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1

# NATS subjects (single source of truth)
SUBJECT_PRODUCTION = "factory.production"
SUBJECT_DOWNTIME = "factory.downtime"
SUBJECT_QUALITY = "factory.quality"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


class DowntimeCategory(str, Enum):
    mechanical = "mechanical"
    electrical = "electrical"
    setup = "setup"
    quality = "quality"
    material = "material"
    break_ = "break"


class DefectType(str, Enum):
    surface = "surface"
    dimension = "dimension"
    color = "color"
    missing_component = "missing_component"
    none = "none"


# ---- payloads ----------------------------------------------------------------

class ProductionStarted(BaseModel):
    order_id: str
    product_sku: str
    target_qty: int


class ProductionCompleted(BaseModel):
    order_id: str
    good_qty: int
    scrap_qty: int
    ideal_cycle_time_s: float
    actual_cycle_time_s: float


class DowntimeStarted(BaseModel):
    downtime_id: str
    category: DowntimeCategory
    planned: bool
    reason: str


class DowntimeEnded(BaseModel):
    downtime_id: str
    duration_s: float


class QualityEvent(BaseModel):
    part_id: str
    result: Literal["pass", "defect"]
    defect_type: DefectType = DefectType.none
    confidence: float = 1.0
    image_ref: str | None = None
    equipment_state: str = "nominal"


Payload = Union[
    ProductionStarted,
    ProductionCompleted,
    DowntimeStarted,
    DowntimeEnded,
    QualityEvent,
]


# ---- envelope ----------------------------------------------------------------

class Event(BaseModel):
    schema_version: int = SCHEMA_VERSION
    event_id: str = Field(default_factory=_new_id)
    event_type: str
    ts: str = Field(default_factory=_now_iso)
    line_id: str
    station_id: str
    payload: dict

    @classmethod
    def of(cls, event_type: str, line_id: str, station_id: str,
           payload: BaseModel, ts: str | None = None) -> "Event":
        return cls(
            event_type=event_type,
            line_id=line_id,
            station_id=station_id,
            payload=payload.model_dump(mode="json"),
            **({"ts": ts} if ts else {}),
        )

    def subject(self) -> str:
        if self.event_type.startswith("production"):
            return SUBJECT_PRODUCTION
        if self.event_type.startswith("downtime"):
            return SUBJECT_DOWNTIME
        return SUBJECT_QUALITY
