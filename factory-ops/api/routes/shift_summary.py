"""Shift handoff summary endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Query

from services import shift_summary

router = APIRouter(prefix="/shift", tags=["shift"])


@router.get("/summary")
def get_summary(start: str | None = Query(None),
                end: str | None = Query(None)):
    return shift_summary.summary(start, end)
