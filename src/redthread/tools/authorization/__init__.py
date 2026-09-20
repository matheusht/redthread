"""Deterministic authorization helpers for agentic-security phases."""

from redthread.tools.authorization.audit import AuditLogger, AuthorizationAuditRecord
from redthread.tools.authorization.capabilities import CapabilityClass, classify_capability
from redthread.tools.authorization.engine import AuthorizationEngine
from redthread.tools.authorization.live_intercept import (
    authorize_execution_metadata,
    authorize_live_action,
    build_execution_authorization_interceptor,
    run_live_authorization_smoke,
)
from redthread.tools.authorization.models import ArgumentRule, AuthorizationPolicy
from redthread.tools.authorization.presets import (
    EGRESS_ALLOWLIST_PRESET,
    FS_READ_ONLY_PRESET,
    SCRATCH_DIR_ONLY_PRESET,
    default_least_agency_policies,
)
from redthread.tools.authorization.sensitivity import (
    DEFAULT_SENSITIVITY_CATALOG,
    REASON_SENSITIVITY_SPOOFED,
)
from redthread.tools.authorization.validation import REASON_INVALID_ARGUMENTS

__all__ = [
    "AuthorizationEngine",
    "AuthorizationAuditRecord",
    "AuditLogger",
    "ArgumentRule",
    "DEFAULT_SENSITIVITY_CATALOG",
    "REASON_INVALID_ARGUMENTS",
    "REASON_SENSITIVITY_SPOOFED",
    "AuthorizationPolicy",
    "CapabilityClass",
    "classify_capability",
    "default_least_agency_policies",
    "FS_READ_ONLY_PRESET",
    "SCRATCH_DIR_ONLY_PRESET",
    "EGRESS_ALLOWLIST_PRESET",
    "authorize_execution_metadata",
    "authorize_live_action",
    "build_execution_authorization_interceptor",
    "run_live_authorization_smoke",
]
