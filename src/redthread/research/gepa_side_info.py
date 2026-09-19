"""Redaction and shaping of GEPA reflective side information (``gepa_side_info``).

This is the ONLY channel between RedThread execution and a (future) reflection LM.
It must never leak raw jailbreak payloads, target transcripts, canary strings, or
secrets. The strategy is allowlist-by-construction: we build the side-info record
from a small set of safe, structured fields and never copy free-form transcript
text. Any short diagnostic string we do include is run through ``redact_text``.

Naming note: GEPA's "ASI" (Actionable Side Information) collides with RedThread's
telemetry "ASI" score. We deliberately call this payload ``gepa_side_info``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from redthread.research.models import ResearchBatchSummary

BANNED_KEYS: frozenset[str] = frozenset(
    {
        "attacker_prompt",
        "target_response",
        "transcript",
        "conversation",
        "turns",
        "raw",
        "system_prompt",
        "messages",
    }
)

_REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?<!\[REDACTED_)CANARY[\w-]*", re.IGNORECASE), "[REDACTED_CANARY]"),
    (re.compile(r"sk-[A-Za-z0-9]{16,}"), "[REDACTED_SECRET]"),
    (re.compile(r"(?:api[_-]?key|token|secret)\s*[:=]\s*\S+", re.IGNORECASE), "[REDACTED_SECRET]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
)


class RedactionLeak(AssertionError):
    """Raised when a banned key or pattern survives into the side-info payload."""


def redact_text(text: str) -> str:
    """Scrub canary markers, secrets, and emails from a short free-text string."""
    cleaned = text
    for pattern, replacement in _REDACTIONS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


def _safe_objective_record(result: Any) -> dict[str, Any]:
    """Build a structured, transcript-free record for one objective result."""
    return {
        "slug": redact_text(result.slug),
        "campaign_id": redact_text(result.campaign_id),
        "attack_success_rate": round(result.attack_success_rate, 4),
        "average_score": round(result.average_score, 4),
        "confirmed_jailbreaks": result.confirmed_jailbreaks,
        "near_misses": result.near_misses,
    }


def _safe_summary_record(
    summary: ResearchBatchSummary,
    *,
    include_objectives: bool,
) -> dict[str, Any]:
    """Build a transcript-free aggregate record for one evaluation split."""
    record: dict[str, Any] = {
        "average_asr": round(summary.average_asr, 4),
        "average_score": round(summary.average_score, 4),
        "confirmed_jailbreaks": summary.confirmed_jailbreaks,
        "near_misses": summary.near_misses,
    }
    if include_objectives:
        record["objectives"] = [_safe_objective_record(r) for r in summary.objective_results]
    return record


def build_side_info(
    candidate_id: str,
    *,
    train: ResearchBatchSummary,
    val: ResearchBatchSummary | None = None,
    control: ResearchBatchSummary | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Assemble a redacted ``gepa_side_info`` payload from batch summaries.

    Only structured metrics are included. No transcript or prompt text is copied.
    """
    payload: dict[str, Any] = {
        "candidate_id": redact_text(candidate_id),
        "train": _safe_summary_record(train, include_objectives=True),
    }
    if val is not None:
        payload["val"] = _safe_summary_record(val, include_objectives=True)
    if control is not None:
        payload["control"] = _safe_summary_record(control, include_objectives=False)
    if notes:
        payload["notes"] = redact_text(notes)
    assert_clean(payload)
    return payload


def assert_clean(payload: Mapping[str, Any]) -> None:
    """Fail closed if any banned key appears anywhere in the payload tree."""

    def check_text(text: str, *, context: str) -> None:
        lowered = text.lower()
        if any(banned in lowered for banned in BANNED_KEYS):
            raise RedactionLeak(f"banned text in {context}")
        if redact_text(text) != text:
            raise RedactionLeak(f"unredacted sensitive value in {context}")

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                key_text = str(key)
                if any(banned in key_text.lower() for banned in BANNED_KEYS):
                    raise RedactionLeak(f"banned key '{key}' present in gepa_side_info")
                check_text(key_text, context=f"key '{key}'")
                walk(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            check_text(node, context="value")

    walk(payload)
