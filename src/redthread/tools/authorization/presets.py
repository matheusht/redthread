"""Least-agency policy presets for Phase 8C."""

from __future__ import annotations

from typing import Final

from redthread.orchestration.models import AuthorizationDecisionType, TrustLevel
from redthread.tools.authorization.capabilities import HIGH_RISK_CAPABILITIES
from redthread.tools.authorization.models import ArgumentRule, AuthorizationPolicy

_SAFE_FILESYSTEM_ROOTS = ("/workspace/safe", "/tmp/redthread/safe")
_SCRATCH_ROOTS = ("/tmp/redthread/scratch",)
_TARGET_LLM_DOMAINS = ("localhost", "127.0.0.1", "api.openai.com", "api.anthropic.com")

FS_READ_ONLY_PRESET: Final[AuthorizationPolicy] = AuthorizationPolicy(
    policy_id="fs-read-only",
    actor_roles=("filesystem_reader", "retriever", "analyst", "tool_executor"),
    allowed_capabilities=("file.read",),
    denied_capabilities=("file.write", "file.delete", "file.chmod"),
    argument_schema={"path": ArgumentRule(allow_absolute=True, max_length=4096)},
    allowed_path_prefixes=_SAFE_FILESYSTEM_ROOTS,
    reason="filesystem reads are limited to approved safe roots; mutations are denied",
)

SCRATCH_DIR_ONLY_PRESET: Final[AuthorizationPolicy] = AuthorizationPolicy(
    policy_id="scratch-dir-only",
    actor_roles=("filesystem_writer", "executor", "tool_executor"),
    allowed_capabilities=("file.read", "file.write", "file.delete"),
    denied_capabilities=("file.chmod",),
    argument_schema={"path": ArgumentRule(allow_absolute=True, max_length=4096)},
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
    argument_schema={
        "domain": ArgumentRule(max_length=1024),
        "url": ArgumentRule(max_length=2048),
        "host": ArgumentRule(max_length=1024),
    },
    allowed_domains=_TARGET_LLM_DOMAINS,
    reason="network egress is limited to local or designated target LLM endpoints",
)


def default_least_agency_policies() -> list[AuthorizationPolicy]:
    policies = [
        AuthorizationPolicy(
            policy_id="read-only-retriever",
            actor_roles=("retriever", "analyst", "tool_executor"),
            allowed_capabilities=("lookup_status", "web.fetch", "tool.read"),
            argument_schema={
                "tenant": ArgumentRule(max_length=256),
                "url": ArgumentRule(max_length=2048),
                "domain": ArgumentRule(max_length=1024),
                "resource": ArgumentRule(max_length=1024),
            },
            reason="read-only retrieval is allowed",
        ),
        AuthorizationPolicy(
            policy_id="defense-validator-replay",
            actor_roles=("defense_validator",),
            allowed_capabilities=("target.replay",),
            argument_schema={
                "trace_id": ArgumentRule(max_length=256),
                "case_id": ArgumentRule(max_length=256),
                "kind": ArgumentRule(max_length=32),
                "prompt_sha256": ArgumentRule(max_length=64),
            },
            required_argument_keys=["trace_id", "case_id", "kind", "prompt_sha256"],
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
            argument_schema={
                "table": ArgumentRule(max_length=256),
                "entry": ArgumentRule(max_length=4096),
                "path": ArgumentRule(max_length=4096, kind="path"),
            },
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
