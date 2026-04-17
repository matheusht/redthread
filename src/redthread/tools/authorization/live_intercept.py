"""Controlled live interception helper for Phase 8 proof-of-control checks."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TypeVar

from redthread.orchestration.models import ActionEnvelope
from redthread.tools.authorization.engine import AuthorizationEngine
from redthread.tools.authorization.presets import default_least_agency_policies

T = TypeVar("T")
LIVE_SMOKE_ENV = "REDTHREAD_RUN_LIVE_AUTH_SMOKE"


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

    engine = AuthorizationEngine(policies or default_least_agency_policies())
    decision = engine.authorize(action)
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
