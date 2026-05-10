from __future__ import annotations

import json

import pytest

from redthread.reporting.public_artifacts import (
    PublicArtifactSafetyError,
    assert_public_artifact_safe,
    prompt_safe_json,
    redact_public_artifact_payload,
)


def test_public_artifact_safety_rejects_nested_raw_prompt_fields() -> None:
    with pytest.raises(PublicArtifactSafetyError, match="unsafe field"):
        assert_public_artifact_safe({"safe": {"prompt": "raw attack body"}})


def test_public_artifact_redaction_replaces_unsafe_nested_fields() -> None:
    payload = {
        "prompt": "raw prompt",
        "nested": {"target_system_prompt": "secret system prompt"},
        "items": [{"judge_reasoning": "private reasoning"}],
    }

    redacted = redact_public_artifact_payload(payload)

    assert redacted["prompt"] == "[redacted:prompt]"
    assert redacted["nested"]["target_system_prompt"] == "[redacted:target_system_prompt]"
    assert redacted["items"][0]["judge_reasoning"] == "[redacted:judge_reasoning]"
    assert_public_artifact_safe(redacted)


def test_prompt_safe_json_serializes_redacted_public_payload() -> None:
    rendered = prompt_safe_json({"raw": {"prompt": "raw body"}})
    payload = json.loads(rendered)

    assert payload["raw"] == {}
