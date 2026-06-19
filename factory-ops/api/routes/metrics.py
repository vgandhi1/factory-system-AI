"""REST endpoints for the dashboard: OEE, downtime, bottlenecks, defects."""
from __future__ import annotations

from fastapi import APIRouter, Query

from services import metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/oee")
def get_oee(line_id: str | None = Query(None),
            start: str | None = Query(None),
            end: str | None = Query(None)):
    return {"lines": metrics.oee(line_id, start, end)}


@router.get("/downtime")
def get_downtime(line_id: str | None = Query(None),
                 start: str | None = Query(None),
                 end: str | None = Query(None)):
    return metrics.downtime(line_id, start, end)


@router.get("/bottleneck")
def get_bottleneck(start: str | None = Query(None),
                   end: str | None = Query(None)):
    return metrics.bottleneck(start, end)


@router.get("/defects")
def get_defects(line_id: str | None = Query(None),
                start: str | None = Query(None),
                end: str | None = Query(None)):
    return {"defects": metrics.defects(line_id, start, end)}
