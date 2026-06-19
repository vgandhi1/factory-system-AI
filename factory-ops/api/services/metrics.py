"""OEE / downtime / bottleneck queries over ClickHouse.

These mirror the Digital Twin's ground-truth `oee_calculator` (EVENT_CONTRACT.md):

    Availability = run_time / planned_time      run_time = planned - downtime
    Performance  = ideal_cycle * total / run_time   (capped at 1)
    Quality      = good / total
    OEE          = A * P * Q

Planned time is parameterized: an explicit [start, end] window uses the window
length; otherwise the default 24h horizon is used, matching the Twin so the
dashboard reconciles within the validator's 1% tolerance.

Shared by the REST routes and the Copilot's tools so both see identical numbers.
"""
from __future__ import annotations

from db import clickhouse
from config import DEFAULT_HORIZON_S


def _window_clause(start: str | None,
                   end: str | None) -> tuple[str, dict[str, str], float | None]:
    """Return (SQL predicate, bound params, window_seconds).

    start/end are bound as ClickHouse query parameters (`{start:String}` /
    `{end:String}`), never interpolated. window_seconds is None when no explicit
    window was given (caller falls back to the default horizon)."""
    if start and end:
        clause = ("AND ts BETWEEN parseDateTime64BestEffort({start:String}) "
                  "AND parseDateTime64BestEffort({end:String})")
        params = {"start": start, "end": end}
        # planned-time seconds for the window
        rows = clickhouse.query(
            "SELECT dateDiff('second', "
            "parseDateTime64BestEffort({start:String}), "
            "parseDateTime64BestEffort({end:String})) AS w",
            params,
        )
        return clause, params, float(rows[0]["w"]) if rows else None
    return "", {}, None


def oee(line_id: str | None = None,
        start: str | None = None,
        end: str | None = None,
        horizon_s: float | None = None) -> list[dict]:
    """Per-line OEE breakdown. Filters by line_id / time window when given."""
    win, win_params, win_s = _window_clause(start, end)
    planned_s = win_s if win_s is not None else float(horizon_s or DEFAULT_HORIZON_S)

    line_filter = ""
    if line_id:
        line_filter = f"AND line_id = '{clickhouse.safe_line_id(line_id)}'"

    sql = f"""
    WITH
      prod AS (
        SELECT line_id,
               sum(good_qty)                AS good,
               sum(good_qty + scrap_qty)    AS total,
               avg(ideal_cycle_time_s)      AS ideal_cycle
        FROM {_db()}.production
        WHERE event_type = 'production_completed' {line_filter} {win}
        GROUP BY line_id
      ),
      down AS (
        SELECT line_id, sum(duration_s) AS downtime_s
        FROM {_db()}.downtime
        WHERE event_type = 'downtime_ended' {line_filter} {win}
        GROUP BY line_id
      )
    SELECT
      p.line_id AS line_id,
      {planned_s}                                                   AS planned_s,
      ifNull(d.downtime_s, 0)                                        AS downtime_s,
      greatest(0, {planned_s} - ifNull(d.downtime_s, 0))            AS run_time_s,
      round(least(1, greatest(0, {planned_s} - ifNull(d.downtime_s, 0)) / {planned_s}), 4) AS availability,
      round(greatest(0, least(1.0, (p.ideal_cycle * p.total) /
            nullIf(greatest(0, {planned_s} - ifNull(d.downtime_s, 0)), 0))), 4)  AS performance,
      round(greatest(0, least(1, p.good / nullIf(p.total, 0))), 4)   AS quality,
      p.good AS good_qty, p.total AS total_qty
    FROM prod p
    LEFT JOIN down d ON p.line_id = d.line_id
    ORDER BY line_id
    """
    rows = clickhouse.query(sql, win_params)
    for r in rows:
        # Components are clamped to [0,1] in SQL; clamp again defensively and
        # bound the product so OEE never leaves [0,1] (guardrail: OEE is 0-100%).
        a = min(1.0, max(0.0, float(r["availability"] or 0)))
        p = min(1.0, max(0.0, float(r["performance"] or 0)))
        q = min(1.0, max(0.0, float(r["quality"] or 0)))
        r["availability"], r["performance"], r["quality"] = a, p, q
        r["oee"] = round(a * p * q, 4)
    return rows


def downtime(line_id: str | None = None,
             start: str | None = None,
             end: str | None = None) -> dict:
    """Downtime totals: by category and planned vs unplanned."""
    win, win_params, _ = _window_clause(start, end)
    # category / planned live on downtime_started; duration_s on downtime_ended.
    # Join them on downtime_id to attribute each stop's duration to its category.
    line_filter = ""
    if line_id:
        line_filter = f"AND s.line_id = '{clickhouse.safe_line_id(line_id)}'"
    started = (f"(SELECT downtime_id, line_id, category, planned FROM {_db()}.downtime "
               f"WHERE event_type = 'downtime_started')")
    ended = (f"(SELECT downtime_id, duration_s FROM {_db()}.downtime "
             f"WHERE event_type = 'downtime_ended' {win})")

    by_cat = clickhouse.query(f"""
        SELECT s.line_id AS line_id, s.category AS category,
               max(s.planned) AS planned,
               count()        AS events,
               round(sum(e.duration_s) / 60, 1) AS minutes
        FROM {started} s
        INNER JOIN {ended} e ON s.downtime_id = e.downtime_id
        WHERE 1 {line_filter}
        GROUP BY s.line_id, s.category
        ORDER BY minutes DESC
    """, win_params)
    planned_split = clickhouse.query(f"""
        SELECT if(s.planned = 1, 'planned', 'unplanned') AS kind,
               round(sum(e.duration_s) / 60, 1) AS minutes,
               count() AS events
        FROM {started} s
        INNER JOIN {ended} e ON s.downtime_id = e.downtime_id
        WHERE 1 {line_filter}
        GROUP BY kind
        ORDER BY kind
    """, win_params)
    return {"by_category": by_cat, "by_kind": planned_split}


def bottleneck(start: str | None = None, end: str | None = None) -> dict:
    """The line with the lowest OEE limits throughput. Also surface the station
    with the most downtime as the within-line constraint."""
    lines = oee(start=start, end=end)
    bottleneck_line = min(lines, key=lambda r: r["oee"]) if lines else None

    win, win_params, _ = _window_clause(start, end)
    stations = clickhouse.query(f"""
        SELECT line_id, station_id,
               round(sum(duration_s) / 60, 1) AS downtime_min,
               count() AS stops
        FROM {_db()}.downtime
        WHERE event_type = 'downtime_ended' {win}
        GROUP BY line_id, station_id
        ORDER BY downtime_min DESC
        LIMIT 5
    """, win_params)
    return {
        "bottleneck_line": bottleneck_line,
        "all_lines": lines,
        "worst_stations": stations,
    }


def defects(line_id: str | None = None,
            start: str | None = None,
            end: str | None = None) -> list[dict]:
    """Quality breakdown by defect type, for the Copilot's quality questions."""
    win, win_params, _ = _window_clause(start, end)
    line_filter = ""
    if line_id:
        line_filter = f"AND line_id = '{clickhouse.safe_line_id(line_id)}'"
    return clickhouse.query(f"""
        SELECT line_id, defect_type,
               count()                                  AS count,
               round(100 * countIf(result = 'defect') / count(), 2) AS pct_of_inspected
        FROM {_db()}.quality
        WHERE result = 'defect' {line_filter} {win}
        GROUP BY line_id, defect_type
        ORDER BY count DESC
    """, win_params)


def _db() -> str:
    from config import CLICKHOUSE_DB
    return CLICKHOUSE_DB
