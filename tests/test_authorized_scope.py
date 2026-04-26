"""Tests for RedThread Slice 1 planning models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from redthread.orchestration.models import AuthorizedScope, DetectorHint, RegressionCase


def test_authorized_scope_allows_only_explicit_targets() -> None:
    scope = AuthorizedScope(target_ids=["support-agent-dev"])

    assert scope.allows_target("support-agent-dev") is True
    assert scope.allows_target("support-agent-prod") is False


def test_authorized_scope_denies_tools_by_default_and_deny_wins() -> None:
    scope = AuthorizedScope(
        allowed_tools=["target_llm", "sandbox"],
        denied_tools=["sandbox"],
    )

    assert scope.allows_tool("target_llm") is True
    assert scope.allows_tool("shell") is False
    assert scope.allows_tool("sandbox") is False


def test_authorized_scope_domain_requires_network_and_allow_list() -> None:
    no_network = AuthorizedScope(allowed_domains=["dev.example.com"])
    scoped_network = AuthorizedScope(
        can_use_network=True,
        allowed_domains=["dev.example.com"],
        denied_domains=["blocked.dev.example.com"],
    )

    assert no_network.allows_domain("dev.example.com") is False
    assert scoped_network.allows_domain("dev.example.com") is True
    assert scoped_network.allows_domain("api.dev.example.com") is True
    assert scoped_network.allows_domain("blocked.dev.example.com") is False
    assert scoped_network.allows_domain("prod.example.com") is False


def test_user_text_cannot_expand_scope_by_default() -> None:
    scope = AuthorizedScope()

    assert scope.user_text_cannot_expand_scope is True


def test_detector_hint_confidence_is_bounded() -> None:
    hint = DetectorHint(detector_name="secret_pattern", confidence=0.7)

    assert hint.confidence == 0.7
    assert "JudgeAgent" in hint.limitations

    with pytest.raises(ValidationError):
        DetectorHint(detector_name="secret_pattern", confidence=1.2)


def test_regression_case_serializes_replay_metadata() -> None:
    regression = RegressionCase(
        source_finding_id="finding-123",
        risk_plugin_id="sensitive_data_exfiltration",
        strategy_id="crescendo",
        minimized_trace={"turns": ["ask", "leak"]},
        expected_safe_behavior="refuse to reveal customer PII",
        replay_schedule="weekly",
        severity_at_creation="high",
    )

    serialized = regression.model_dump()

    assert serialized["source_finding_id"] == "finding-123"
    assert serialized["risk_plugin_id"] == "sensitive_data_exfiltration"
    assert serialized["minimized_trace"] == {"turns": ["ask", "leak"]}
