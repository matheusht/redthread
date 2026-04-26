"""Tests for RedThread risk plugin contracts and registry."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from redthread.core.plugins import RiskPluginRegistry, default_risk_plugin_registry
from redthread.orchestration.models import RiskCategory, RiskPlugin, TargetType


def test_default_registry_lists_builtin_plugins_sorted() -> None:
    registry = default_risk_plugin_registry()

    assert registry.ids() == sorted(registry.ids())
    assert registry.ids() == [
        "cross_session_data_leak",
        "prompt_injection",
        "sensitive_data_exfiltration",
        "system_prompt_leakage",
        "unauthorized_action",
        "unsafe_tool_use",
    ]


def test_registry_get_and_filter_by_category_target_and_framework() -> None:
    registry = default_risk_plugin_registry()

    prompt_injection = registry.get("prompt_injection")
    assert prompt_injection.category == RiskCategory.PROMPT_INJECTION
    assert prompt_injection.applies_to(TargetType.RAG)

    assert [p.id for p in registry.filter(category=RiskCategory.UNSAFE_TOOL_USE)] == [
        "unsafe_tool_use"
    ]
    rag_plugins = registry.filter(target_type=TargetType.RAG)
    assert {plugin.id for plugin in rag_plugins} == {
        "prompt_injection",
        "sensitive_data_exfiltration",
    }
    assert {plugin.id for plugin in registry.filter(framework_tag="LLM06")} == {
        "cross_session_data_leak",
        "sensitive_data_exfiltration",
        "unauthorized_action",
    }


def test_registry_rejects_duplicate_plugin_ids() -> None:
    plugin = RiskPlugin(
        id="custom_policy_check",
        name="Custom policy check",
        category=RiskCategory.CUSTOM_POLICY,
    )
    registry = RiskPluginRegistry([plugin])

    with pytest.raises(ValueError, match="already registered"):
        registry.register(plugin)


def test_registry_can_replace_plugin_explicitly() -> None:
    original = RiskPlugin(id="policy", name="Policy", category=RiskCategory.CUSTOM_POLICY)
    replacement = RiskPlugin(
        id="policy",
        name="Replacement policy",
        category=RiskCategory.CUSTOM_POLICY,
    )
    registry = RiskPluginRegistry([original])

    registry.register(replacement, replace=True)

    assert registry.get("policy").name == "Replacement policy"


def test_unknown_plugin_get_raises_clear_key_error() -> None:
    registry = default_risk_plugin_registry()

    with pytest.raises(KeyError, match="unknown risk plugin"):
        registry.get("missing")


def test_risk_plugin_validates_id_shape() -> None:
    with pytest.raises(ValidationError):
        RiskPlugin(id="Bad Id", name="Bad", category=RiskCategory.CUSTOM_POLICY)
