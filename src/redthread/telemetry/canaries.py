"""Canary helpers for additive agentic-security tracing."""

from __future__ import annotations

from typing import Any


def inject_canary(content: str, tag: str) -> dict[str, Any]:
    return {"content": content, "canary_tags": [tag]}


def merge_canary_tags(*tag_sets: list[str]) -> list[str]:
    merged: list[str] = []
    for tags in tag_sets:
        for tag in tags:
            if tag not in merged:
                merged.append(tag)
    return merged
