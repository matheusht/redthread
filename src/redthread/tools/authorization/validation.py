"""Scalar argument validation for authorization policy grants."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from redthread.tools.authorization.models import ArgumentRule, AuthorizationPolicy

REASON_INVALID_ARGUMENTS = "invalid_arguments"
MAX_ARGUMENT_STRING_LENGTH = 16_384
DEFAULT_ARGUMENT_SCHEMAS = {
    "docs.search": {"query": ArgumentRule()},
    "lookup_status": {"tenant": ArgumentRule(max_length=256)},
    "secrets.read": {"path": ArgumentRule(max_length=4096, kind="path")},
    "tool.read": {"resource": ArgumentRule(max_length=1024)},
    "web.fetch": {"url": ArgumentRule(max_length=2048)},
}
_TRAVERSAL = re.compile(r"(?:^|[/\\])\.\.(?:[/\\]|$)")
_ABSOLUTE_PATH = re.compile(r"^(?:[/\\]|[A-Za-z]:[/\\])")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_SHELL_META = re.compile(r"[;&|$`()<>`]")


def validate_arguments(
    arguments: dict[str, Any],
    actor_role: str,
    capability: str,
    policies: Sequence[AuthorizationPolicy],
    default_schemas: dict[str, dict[str, ArgumentRule]] | None = None,
) -> str | None:
    for key, value in arguments.items():
        if not isinstance(key, str) or not key.strip():
            return "argument keys must be non-empty strings"
        if isinstance(value, str):
            if len(value) > MAX_ARGUMENT_STRING_LENGTH:
                return f"argument '{key}' exceeds maximum length"
            if _CONTROL.search(value):
                return f"argument '{key}' contains control characters"

    matched_policy = False
    for policy in policies:
        if actor_role not in policy.actor_roles or capability not in policy.allowed_capabilities:
            continue
        matched_policy = True
        keys = set(arguments)
        if not keys.issubset(policy.argument_schema):
            return "argument keys are not allowed by policy"
        if not set(policy.required_argument_keys).issubset(keys):
            return "required argument is missing"
        if arguments and not policy.argument_schema:
            return "policy has no scalar argument schema"
        for key, rule in policy.argument_schema.items():
            if key in arguments:
                reason = _validate_rule(key, arguments[key], rule)
                if reason:
                    return reason
    if matched_policy or not arguments:
        return None
    schema = (default_schemas or DEFAULT_ARGUMENT_SCHEMAS).get(capability)
    if schema is None:
        return "non-empty arguments require a declared scalar schema"
    if not set(arguments).issubset(schema):
        return "argument keys are not declared for capability"
    for key, rule in schema.items():
        if key in arguments:
            reason = _validate_rule(key, arguments[key], rule)
            if reason:
                return reason
    return None


def _validate_rule(key: str, value: object, rule: ArgumentRule) -> str | None:
    valid_types = {
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }
    if not valid_types[rule.value_type]:
        return f"argument '{key}' has invalid scalar type"
    if not isinstance(value, str):
        return None
    if len(value) > rule.max_length:
        return f"argument '{key}' exceeds maximum length"
    if rule.kind == "path" and (_TRAVERSAL.search(value) or (
        _ABSOLUTE_PATH.search(value) and not rule.allow_absolute
    )):
        return f"argument '{key}' contains an unsafe path"
    if rule.kind == "command" and _SHELL_META.search(value):
        return f"argument '{key}' contains shell metacharacters"
    return None
