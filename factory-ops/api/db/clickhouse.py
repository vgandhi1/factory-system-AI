"""Thin ClickHouse client over the HTTP interface.

The gateway already lands events in ClickHouse; here we only read. Queries go
through the HTTP endpoint with `FORMAT JSON` and come back as dict rows. SQL is
built by the metrics layer. User-supplied time-window values are passed as bound
ClickHouse query parameters (see `query(..., params=...)`), never interpolated;
`line_id` is validated against a strict allowlist pattern before interpolation.
"""
from __future__ import annotations

import re

import httpx

from config import (
    CLICKHOUSE_DB,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_URL,
    CLICKHOUSE_USER,
)

_LINE_RE = re.compile(r"^[a-zA-Z0-9_-]{1,40}$")


class BadLineID(ValueError):
    pass


def safe_line_id(line_id: str) -> str:
    """Validate a line_id before it is interpolated into SQL."""
    if not _LINE_RE.match(line_id):
        raise BadLineID(f"invalid line_id: {line_id!r}")
    return line_id


def query(sql: str, params: dict[str, str] | None = None) -> list[dict]:
    """Run read-only SQL, return rows as dicts.

    `params` are bound as ClickHouse query parameters (referenced as
    ``{name:Type}`` placeholders in `sql`). ClickHouse substitutes them with
    proper escaping, so user-supplied values are never string-interpolated into
    the query text. Use this for any value that originates from a request or an
    LLM tool call.
    """
    request = {
        "database": CLICKHOUSE_DB,
        "default_format": "JSON",
        "query": sql,
    }
    for name, value in (params or {}).items():
        request[f"param_{name}"] = value
    auth = (CLICKHOUSE_USER, CLICKHOUSE_PASSWORD) if CLICKHOUSE_PASSWORD else None
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(CLICKHOUSE_URL, params=request, auth=auth)
        resp.raise_for_status()
        return resp.json().get("data", [])


def ping() -> bool:
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{CLICKHOUSE_URL}/ping")
            return r.status_code == 200
    except httpx.HTTPError:
        return False
