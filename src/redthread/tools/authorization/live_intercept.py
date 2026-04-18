"""Controlled live interception helper for Phase 8 proof-of-control checks."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TypeVar

from redthread.orchestration.models import ActionEnvelope, AuthorizationDecision
from redthread.pyrit_adapters.interceptors import LiveExecutionInterceptionError
from redthread.pyrit_adapters.targets import ExecutionMetadata
from redthread.tools.authorization.tool_context import AUTHORIZATION_ACTION_METADATA_KEY
from redthread.tools.authorization.engine import AuthorizationEngine
from redthread.tools.authorization.presets import default_least_agency_policies

T = TypeVar("T")
LIVE_SMOKE_ENV = "REDTHREAD_RUN_LIVE_AUTH_SMOKE"


def authorize_live_action(
    action: ActionEnvelope,
    *,
    policies: list | None = None,
) -> AuthorizationDecision:
    engine = AuthorizationEngine(policies or default_least_agency_policies())
    return engine.authorize(action)


def authorize_execution_metadata(
    execution_metadata: ExecutionMetadata,
    *,
    policies: list | None = None,
) -> AuthorizationDecision | None:
    action = execution_metadata.metadata.get(AUTHORIZATION_ACTION_METADATA_KEY)
    if not isinstance(action, ActionEnvelope):
        return None
    return authorize_live_action(action, policies=policies)


def build_execution_authorization_interceptor(
    *,
    policies: list | None = None,
):
    def interceptor(execution_metadata: ExecutionMetadata) -> None:
        decision = authorize_execution_metadata(execution_metadata, policies=policies)
        if decision is None:
            return
        if decision.decision.value != "allow":
            raise LiveExecutionInterceptionError(
                f"Execution blocked at common boundary: {decision.decision.value}"
            )

    return interceptor


def run_live_authorization_smoke(
    action: ActionEnvelope,
    execute: Callable[[], T],
    *,
    policies: list | None = None,
) -> dict[str, object]:
    if os.getenv(LIVE_SMOKE_ENV, "false").lower() != "true":
        return {
            "executed": False,
            "skipped": True,
            "evidence_mode": "live_intercept_opt_in_required",
            "decision": None,
            "result": None,
        }

    decision = authorize_live_action(action, policies=policies)
    if decision.decision.value != "allow":
        return {
            "executed": False,
            "skipped": False,
            "evidence_mode": "live_intercept_smoke",
            "decision": decision.model_dump(mode="json"),
            "result": None,
        }

    return {
        "executed": True,
        "skipped": False,
        "evidence_mode": "live_intercept_smoke",
        "decision": decision.model_dump(mode="json"),
        "result": execute(),
    }
