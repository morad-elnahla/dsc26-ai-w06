"""Plain-Python tools + JSON schemas. Agent calls TOOLS[name](**arguments)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from hisn.retrieval import search_runbooks

DATA = Path(__file__).parent / "data"


@lru_cache(maxsize=1)
def _assets() -> dict:
    raw = json.loads((DATA / "assets.json").read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "assets" in raw:
        raw = raw["assets"]
    out = {}
    if isinstance(raw, dict):
        for name, rec in raw.items():
            rec = dict(rec)
            rec.setdefault("host", name)
            out[name.strip().lower()] = rec
    else:
        for rec in raw:
            name = rec.get("host") or rec.get("name") or rec.get("id")
            if name:
                out[str(name).strip().lower()] = dict(rec)
    return out


@lru_cache(maxsize=1)
def _alerts() -> list[dict]:
    rows = []
    for line in (DATA / "alerts.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _ts(s: str) -> datetime:
    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def lookup_asset(host: str) -> dict:
    rec = _assets().get(str(host).strip().lower())
    if rec is None:
        return {"host": host, "known": False}
    return {**rec, "known": True}


def related_alerts(rule_id: str, agent: str, around: str, window_minutes: int = 60) -> dict:
    if isinstance(window_minutes, bool) or not isinstance(window_minutes, int) or not 1 <= window_minutes <= 1440:
        raise ValueError("window_minutes must be an integer between 1 and 1440")
    end = _ts(around)
    start = end - timedelta(minutes=window_minutes)
    rid, ag = str(rule_id).strip(), str(agent).strip().casefold()
    ids = []
    for a in _alerts():
        if str(a["rule"]["id"]) != rid:
            continue
        if str(a["agent"]["name"]).strip().casefold() != ag:
            continue
        if start <= _ts(a["timestamp"]) <= end:
            ids.append(a["id"])
    return {"count": len(ids), "alert_ids": ids}


TOOLS: dict = {
    "lookup_asset": lookup_asset,
    "search_runbooks": search_runbooks,
    "related_alerts": related_alerts,
}

TOOL_SCHEMAS: list = [
    {
        "name": "lookup_asset",
        "description": "Look up a host in the client asset inventory: owner, criticality and environment.",
        "input_schema": {
            "type": "object",
            "properties": {"host": {"type": "string", "description": "Host name, e.g. web-01"}},
            "required": ["host"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_runbooks",
        "description": "Search the incident runbooks and return the best matches with id, title, snippet and score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Free-text search query"},
                "k": {"type": "integer", "description": "Number of results, 1 to 10"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "related_alerts",
        "description": "Count earlier alerts with the same rule on the same agent within a time window ending at 'around'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "rule_id": {"type": "string", "description": "Wazuh rule id"},
                "agent": {"type": "string", "description": "Agent (host) name"},
                "around": {"type": "string", "description": "ISO timestamp ending in Z (end of window)"},
                "window_minutes": {"type": "integer", "description": "Window size in minutes, 1 to 1440"},
            },
            "required": ["rule_id", "agent", "around"],
            "additionalProperties": False,
        },
    },
]
