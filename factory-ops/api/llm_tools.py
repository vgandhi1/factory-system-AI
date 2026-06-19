"""Tool definitions the Copilot exposes to Claude, plus their dispatcher.

Each tool is a thin wrapper over the metrics (ClickHouse) and knowledge-base
(pgvector) services, so Claude and the deterministic fallback both reason over
the exact same numbers the dashboard shows. Tool results are JSON-serializable.
"""
from __future__ import annotations

from services import kb, metrics

# Anthropic tool-use schema. Kept small and orthogonal: live metrics from
# ClickHouse, historical context from the knowledge base.
TOOLS = [
    {
        "name": "get_oee",
        "description": "Live OEE breakdown (Availability, Performance, Quality, "
                       "OEE) per line from the event stream. Use for any question "
                       "about OEE or how a line is performing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "line_id": {"type": "string",
                            "description": "e.g. 'line-1'. Omit for all lines."},
                "start": {"type": "string", "description": "ISO-8601 window start."},
                "end": {"type": "string", "description": "ISO-8601 window end."},
            },
        },
    },
    {
        "name": "get_downtime",
        "description": "Downtime totals by category and planned vs unplanned. Use "
                       "for downtime / stoppage questions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "line_id": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
        },
    },
    {
        "name": "get_bottleneck",
        "description": "Identify the throughput-limiting line (lowest OEE) and the "
                       "stations with the most downtime.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
        },
    },
    {
        "name": "get_defects",
        "description": "Quality defect counts by type (surface, dimension, color, "
                       "missing_component) per line.",
        "input_schema": {
            "type": "object",
            "properties": {
                "line_id": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
        },
    },
    {
        "name": "search_incidents",
        "description": "Search the historical incident knowledge base for similar "
                       "past events, their diagnosed root cause and resolution. Use "
                       "to ground root-cause hypotheses in prior incidents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "Natural-language description of the issue."},
                "line_id": {"type": "string"},
            },
            "required": ["query"],
        },
    },
]


def dispatch(name: str, args: dict) -> dict:
    """Execute a tool call and return a JSON-serializable result."""
    if name == "get_oee":
        return {"lines": metrics.oee(args.get("line_id"),
                                     args.get("start"), args.get("end"))}
    if name == "get_downtime":
        return metrics.downtime(args.get("line_id"),
                                args.get("start"), args.get("end"))
    if name == "get_bottleneck":
        return metrics.bottleneck(args.get("start"), args.get("end"))
    if name == "get_defects":
        return {"defects": metrics.defects(args.get("line_id"),
                                           args.get("start"), args.get("end"))}
    if name == "search_incidents":
        return {"incidents": kb.search_incidents(args["query"],
                                                 line_id=args.get("line_id"))}
    return {"error": f"unknown tool {name}"}
