"""Least-agency policy presets for Phase 8C."""

from __future__ import annotations

from redthread.orchestration.models import AuthorizationDecisionType, TrustLevel
from redthread.tools.authorization.capabilities import HIGH_RISK_CAPABILITIES
from redthread.tools.authorization.models import ArgumentRule, AuthorizationPolicy


def default_least_agency_policies() -> list[AuthorizationPolicy]:
    return [
        AuthorizationPolicy(
            policy_id="read-only-retriever",
            actor_roles=["retriever", "analyst", "tool_executor"],
            allowed_capabilities=["lookup_status", "web.fetch", "tool.read"],
            argument_schema={
                "tenant": ArgumentRule(max_length=256),
                "url": ArgumentRule(max_length=2048),
                "resource": ArgumentRule(max_length=1024),
            },
            reason="read-only retrieval is allowed",
        ),
        AuthorizationPolicy(
            policy_id="defense-validator-replay",
            actor_roles=["defense_validator"],
            allowed_capabilities=["target.replay"],
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
            actor_roles=["tool_executor", "privileged_executor", "executor"],
            denied_capabilities=sorted(HIGH_RISK_CAPABILITIES),
            required_trust_levels=[TrustLevel.TRUSTED],
            decision=AuthorizationDecisionType.DENY,
            reason="derived or untrusted lineage cannot trigger risky execution",
        ),
        AuthorizationPolicy(
            policy_id="escalate-high-sensitivity-writes",
            actor_roles=["privileged_executor", "executor"],
            allowed_capabilities=["db.write", "memory.write", "file.write"],
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
