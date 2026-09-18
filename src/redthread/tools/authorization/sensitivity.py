"""Authoritative sensitivity catalog helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SENSITIVITY_ORDER = {"low": 0, "medium": 1, "high": 2}
REASON_SENSITIVITY_SPOOFED = "sensitivity_spoofed"
DEFAULT_SENSITIVITY_CATALOG = {
    "agent.delegate": "high",
    "db.export": "high",
    "db.write": "high",
    "file.write": "medium",
    "http.post": "high",
    "memory.write": "medium",
    "prompt.update": "high",
    "secrets.read": "high",
    "shell.exec": "high",
    "system.update": "high",
}


def sensitivity_value(level: str) -> int:
    return SENSITIVITY_ORDER.get(level.lower(), 2)


def authoritative_sensitivity(action: Any, catalog: Mapping[str, str]) -> str | None:
    candidates = [action.capability, action.tool_name]
    candidates.extend(
        str(action.arguments[key])
        for key in ("resource", "resource_id", "target", "path", "table", "url", "domain")
        if key in action.arguments
    )
    values = [catalog[key] for key in candidates if key in catalog]
    return max(values, key=sensitivity_value) if values else None
