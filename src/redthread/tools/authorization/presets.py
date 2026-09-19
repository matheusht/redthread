"""Least-agency policy presets for Phase 8C."""

from __future__ import annotations

from typing import Final

from redthread.orchestration.models import AuthorizationDecisionType, TrustLevel
from redthread.tools.authorization.capabilities import HIGH_RISK_CAPABILITIES
from redthread.tools.authorization.models import AuthorizationPolicy

_SAFE_FILESYSTEM_ROOTS = ("/workspace/safe", "/tmp/redthread/safe")
_SCRATCH_ROOTS = ("/tmp/redthread/scratch",)
_TARGET_LLM_DOMAINS = ("localhost", "127.0.0.1", "api.openai.com", "api.anthropic.com")

FS_READ_ONLY_PRESET: Final[AuthorizationPolicy] = AuthorizationPolicy(
    policy_id="fs-read-only",
    actor_roles=("filesystem_reader", "retriever", "analyst", "tool_executor"),
    allowed_capabilities=("file.read",),
    denied_capabilities=("file.write", "file.delete", "file.chmod"),
    allowed_path_prefixes=_SAFE_FILESYSTEM_ROOTS,
    reason="filesystem reads are limited to approved safe roots; mutations are denied",
)

SCRATCH_DIR_ONLY_PRESET: Final[AuthorizationPolicy] = AuthorizationPolicy(
    policy_id="scratch-dir-only",
    actor_roles=("filesystem_writer", "executor", "tool_executor"),
    allowed_capabilities=("file.read", "file.write", "file.delete"),
    denied_capabilities=("file.chmod",),
    allowed_path_prefixes=_SCRATCH_ROOTS,
    reason="filesystem reads and writes are confined to the RedThread scratch root",
)

EGRESS_ALLOWLIST_PRESET: Final[AuthorizationPolicy] = AuthorizationPolicy(
    policy_id="egress-allowlist",
    actor_roles=(
        "network_client",
        "executor",
        "tool_executor",
        "retriever",
        "analyst",
    ),
    allowed_capabilities=("network.egress", "http.post", "web.fetch"),
    allowed_domains=_TARGET_LLM_DOMAINS,
    reason="network egress is limited to local or designated target LLM endpoints",
)


def default_least_agency_policies() -> list[AuthorizationPolicy]:
    policies = [
        AuthorizationPolicy(
            policy_id="read-only-retriever",
            actor_roles=("retriever", "analyst", "tool_executor"),
            allowed_capabilities=("lookup_status", "web.fetch", "tool.read"),
            reason="read-only retrieval is allowed",
        ),
        AuthorizationPolicy(
            policy_id="defense-validator-replay",
            actor_roles=("defense_validator",),
            allowed_capabilities=("target.replay",),
            max_target_sensitivity="medium",
            reason="trusted defense replay validation is allowed on controlled target paths",
        ),
        AuthorizationPolicy(
            policy_id="deny-risky-derived-actions",
            actor_roles=("tool_executor", "privileged_executor", "executor"),
            denied_capabilities=tuple(sorted(HIGH_RISK_CAPABILITIES)),
            required_trust_levels=(TrustLevel.TRUSTED,),
            decision=AuthorizationDecisionType.DENY,
            reason="derived or untrusted lineage cannot trigger risky execution",
        ),
        AuthorizationPolicy(
            policy_id="escalate-high-sensitivity-writes",
            actor_roles=("privileged_executor", "executor"),
            allowed_capabilities=("db.write", "memory.write", "file.write"),
            max_target_sensitivity="medium",
            decision=AuthorizationDecisionType.ESCALATE,
            reason="high-sensitivity writes and mutations require explicit approval",
            require_human_approval=True,
        ),
    ]
    return [
        *policies,
        FS_READ_ONLY_PRESET.model_copy(deep=True),
        SCRATCH_DIR_ONLY_PRESET.model_copy(deep=True),
        EGRESS_ALLOWLIST_PRESET.model_copy(deep=True),
    ]
