"""Prompt-safe helpers for public RedThread artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

UNSAFE_PUBLIC_KEYS = frozenset({
    "attacker_prompt",
    "judge_reasoning",
    "prompt",
    "probe_seed_examples",
    "prompt_body",
    "raw",
    "raw_prompt",
    "reasoning",
    "target_echo",
    "target_response",
    "target_system_prompt",
})


class PublicArtifactSafetyError(ValueError):
    """Raised when a public artifact contains unsafe raw fields."""


def redact_public_artifact_payload(payload: object) -> object:
    """Return a copy with unsafe public fields replaced by redaction markers."""
    if isinstance(payload, Mapping):
        redacted: dict[str, object] = {}
        for key, value in payload.items():
            key_text = str(key)
            if key_text == "raw" and isinstance(value, Mapping):
                redacted[key_text] = {}
            elif key_text in UNSAFE_PUBLIC_KEYS and _has_public_value(value):
                redacted[key_text] = f"[redacted:{key_text}]"
            else:
                redacted[key_text] = redact_public_artifact_payload(value)
        return redacted
    if isinstance(payload, Sequence) and not isinstance(payload, str):
        return [redact_public_artifact_payload(item) for item in payload]
    return payload


def assert_public_artifact_safe(payload: object, path: str = "$") -> None:
    """Raise if unsafe public fields still contain raw values."""
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_text = str(key)
            if key_text in UNSAFE_PUBLIC_KEYS and _has_public_value(value):
                msg = f"public artifact contains unsafe field: {path}.{key_text}"
                raise PublicArtifactSafetyError(msg)
            assert_public_artifact_safe(value, f"{path}.{key_text}")
        return
    if isinstance(payload, Sequence) and not isinstance(payload, str):
        for index, item in enumerate(payload):
            assert_public_artifact_safe(item, f"{path}[{index}]")


def prompt_safe_json(payload: dict[str, Any]) -> str:
    """Serialize a prompt-safe JSON artifact."""
    safe_payload = redact_public_artifact_payload(payload)
    assert_public_artifact_safe(safe_payload)
    return json.dumps(safe_payload, indent=2, sort_keys=True) + "\n"


def _has_public_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        return bool(stripped) and not stripped.startswith("[redacted:")
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return bool(value)
    return True
