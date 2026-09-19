"""Deterministic least-agency authorization preset tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from redthread.orchestration.models import ActionEnvelope, AuthorizationDecisionType
from redthread.tools.authorization import AuthorizationEngine
from redthread.tools.authorization.presets import (
    EGRESS_ALLOWLIST_PRESET,
    FS_READ_ONLY_PRESET,
    SCRATCH_DIR_ONLY_PRESET,
    default_least_agency_policies,
)


def _action(role: str, capability: str, **arguments: str) -> ActionEnvelope:
    return ActionEnvelope(
        actor_id="preset-test",
        actor_role=role,
        capability=capability,
        tool_name=capability,
        arguments=arguments,
        target_sensitivity="low",
        provenance={
            "source_kind": "internal_agent",
            "trust_level": "trusted",
            "origin_id": "preset-test",
        },
        requested_effect="read" if capability.endswith("read") else "write",
    )


def test_presets_are_frozen_and_part_of_default_policy_set() -> None:
    with pytest.raises(ValidationError):
        FS_READ_ONLY_PRESET.reason = "mutated"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        FS_READ_ONLY_PRESET.allowed_capabilities += ("file.write",)  # type: ignore[misc]

    policies = default_least_agency_policies()
    policy_ids = {policy.policy_id for policy in policies}
    assert {
        FS_READ_ONLY_PRESET.policy_id,
        SCRATCH_DIR_ONLY_PRESET.policy_id,
        EGRESS_ALLOWLIST_PRESET.policy_id,
    } <= policy_ids


def test_fs_read_only_preset_allows_safe_reads_and_denies_mutation() -> None:
    engine = AuthorizationEngine([FS_READ_ONLY_PRESET])

    read = engine.authorize(_action("filesystem_reader", "file.read", path="/workspace/safe/readme"))
    write = engine.authorize(_action("filesystem_reader", "file.write", path="/workspace/safe/readme"))
    outside = engine.authorize(_action("filesystem_reader", "file.read", path="/etc/passwd"))
    traversal = engine.authorize(
        _action("filesystem_reader", "file.read", path="/workspace/safe/../etc/passwd")
    )

    assert read.decision == AuthorizationDecisionType.ALLOW
    assert write.decision == AuthorizationDecisionType.DENY
    assert outside.decision == AuthorizationDecisionType.DENY
    assert traversal.decision == AuthorizationDecisionType.DENY


def test_scratch_preset_confines_writes_to_scratch_root() -> None:
    engine = AuthorizationEngine([SCRATCH_DIR_ONLY_PRESET])

    allowed = engine.authorize(
        _action("filesystem_writer", "file.write", path="/tmp/redthread/scratch/job/output")
    )
    outside = engine.authorize(_action("filesystem_writer", "file.write", path="/workspace/output"))
    chmod = engine.authorize(_action("filesystem_writer", "file.chmod", path="/tmp/redthread/scratch/job/output"))

    assert allowed.decision == AuthorizationDecisionType.ALLOW
    assert outside.decision == AuthorizationDecisionType.DENY
    assert chmod.decision == AuthorizationDecisionType.DENY


def test_egress_preset_allows_only_target_llm_domains() -> None:
    engine = AuthorizationEngine([EGRESS_ALLOWLIST_PRESET])

    allowed = engine.authorize(_action("network_client", "network.egress", domain="api.openai.com"))
    allowed_http = engine.authorize(_action("network_client", "http.post", url="https://api.openai.com/v1/responses"))
    allowed_fetch = engine.authorize(_action("retriever", "web.fetch", domain="api.anthropic.com"))
    denied = engine.authorize(_action("network_client", "network.egress", domain="evil.example.com"))
    denied_http = engine.authorize(_action("network_client", "http.post", domain="evil.example.com"))
    denied_fetch = engine.authorize(_action("retriever", "web.fetch", domain="evil.example.com"))

    assert allowed.decision == AuthorizationDecisionType.ALLOW
    assert allowed_http.decision == AuthorizationDecisionType.ALLOW
    assert allowed_fetch.decision == AuthorizationDecisionType.ALLOW
    assert denied.decision == AuthorizationDecisionType.DENY
    assert denied_http.decision == AuthorizationDecisionType.DENY
    assert denied_fetch.decision == AuthorizationDecisionType.DENY


def test_default_policies_apply_egress_boundary_before_generic_fetch_allow() -> None:
    engine = AuthorizationEngine(default_least_agency_policies())

    denied = engine.authorize(_action("retriever", "web.fetch", domain="evil.example.com"))

    assert denied.decision == AuthorizationDecisionType.DENY
    assert denied.policy_id == "scope-boundary"
