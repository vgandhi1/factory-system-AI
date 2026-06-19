"""Shift handoff intelligence.

Summarizes a shift window: production vs target, OEE, downtime events, quality
issues, and concrete action items for the next shift. Numbers come from the same
ClickHouse queries the dashboard uses; the prose is template-based by default and
optionally rewritten by Claude when an API key is present.
"""
from __future__ import annotations

from db import clickhouse
from config import CLICKHOUSE_DB, COPILOT_ENABLED, ANTHROPIC_API_KEY, COPILOT_MODEL
from services import metrics


def _win(start: str | None, end: str | None) -> tuple[str, dict[str, str]]:
    """Return (SQL predicate, bound params). start/end are bound as ClickHouse
    query parameters, never interpolated."""
    if start and end:
        clause = ("AND ts BETWEEN parseDateTime64BestEffort({start:String}) "
                  "AND parseDateTime64BestEffort({end:String})")
        return clause, {"start": start, "end": end}
    return "", {}


def summary(start: str | None = None, end: str | None = None) -> dict:
    win, win_params = _win(start, end)

    production = clickhouse.query(f"""
        SELECT line_id,
               sumIf(target_qty, event_type = 'production_started')          AS target,
               sumIf(good_qty,   event_type = 'production_completed')        AS good,
               sumIf(scrap_qty,  event_type = 'production_completed')        AS scrap
        FROM {CLICKHOUSE_DB}.production
        WHERE 1 {win}
        GROUP BY line_id
        ORDER BY line_id
    """, win_params)

    oee = metrics.oee(start=start, end=end)
    oee_by_line = {o["line_id"]: o for o in oee}

    downtime = metrics.downtime(start=start, end=end)
    defects = metrics.defects(start=start, end=end)

    action_items = _action_items(production, oee_by_line, downtime, defects)

    result = {
        "window": {"start": start, "end": end},
        "production": production,
        "oee": oee,
        "downtime": downtime,
        "top_defects": defects[:5],
        "action_items": action_items,
        "narrative": _narrative(production, oee_by_line, downtime, defects,
                                action_items),
    }
    if COPILOT_ENABLED:
        try:
            result["narrative"] = _claude_narrative(result)
        except Exception:  # noqa: BLE001 - keep template narrative on failure
            pass
    return result


def _action_items(production, oee_by_line, downtime, defects) -> list[str]:
    items: list[str] = []

    for p in production:
        good = int(p["good"] or 0)
        target = int(p["target"] or 0)
        if target and good < 0.9 * target:
            items.append(
                f"{p['line_id']}: produced {good}/{target} units (below 90% of "
                f"target) — investigate the shift's largest stop.")
    # unplanned downtime
    for c in downtime["by_category"]:
        if not c["planned"] and c["minutes"] >= 15:
            items.append(
                f"{c['line_id']}: {c['minutes']} min unplanned {c['category']} "
                f"downtime — follow the {c['category']} runbook before next shift.")
    # quality
    for d in defects[:2]:
        if int(d["count"]) >= 20:
            items.append(
                f"{d['line_id']}: {d['count']} {d['defect_type']} defects — check "
                f"tool wear / incoming material.")
    # low OEE
    for line, o in oee_by_line.items():
        if o["oee"] < 0.6:
            items.append(f"{line}: OEE {o['oee']:.0%} below 60% target — prioritise.")
    return items or ["No action items: shift ran within targets."]


def _narrative(production, oee_by_line, downtime, defects, action_items) -> str:
    lines_txt = []
    for p in production:
        o = oee_by_line.get(p["line_id"], {})
        lines_txt.append(
            f"{p['line_id']}: {int(p['good'] or 0)}/{int(p['target'] or 0)} good "
            f"units, {int(p['scrap'] or 0)} scrap, OEE {o.get('oee', 0):.0%}.")
    dt = downtime["by_category"]
    dt_txt = ("Top downtime: " +
              ", ".join(f"{c['category']} {c['minutes']}min" for c in dt[:3])
              if dt else "No downtime recorded.")
    def_txt = ("Quality: " +
               ", ".join(f"{d['defect_type']} ×{d['count']}" for d in defects[:3])
               if defects else "No defects recorded.")
    ai_txt = "Action items:\n" + "\n".join(f"  - {a}" for a in action_items)
    return "Shift summary\n" + "\n".join(lines_txt) + f"\n{dt_txt}\n{def_txt}\n{ai_txt}"


def _claude_narrative(result: dict) -> str:
    import json
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=COPILOT_MODEL,
        max_tokens=600,
        system=("You write concise factory shift-handoff summaries for the next "
                "shift lead. Lead with production vs target and OEE per line, then "
                "downtime, then quality, then the action items verbatim. Plain text, "
                "no preamble."),
        messages=[{"role": "user", "content": json.dumps({
            "production": result["production"],
            "oee": result["oee"],
            "downtime": result["downtime"],
            "top_defects": result["top_defects"],
            "action_items": result["action_items"],
        }, default=str)}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()
