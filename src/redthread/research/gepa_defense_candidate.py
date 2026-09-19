"""Defense prompt candidate helpers for the Phase 3 GEPA lane."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from redthread.core import defense_assets
from redthread.research.defense_source_mutation_validator import validate_defense_prompt_candidate

DEFENSE_COMPONENT_FIELDS: frozenset[str] = frozenset(
    {"DEFENSE_ARCHITECT_SYSTEM_PROMPT", "DEFENSE_ARCHITECT_USER_TEMPLATE"}
)
DEFENSE_ASSETS_PATH = Path("src/redthread/core/defense_assets.py")


class DefenseAllowlistViolation(ValueError):
    """Raised when a GEPA defense candidate touches a forbidden component."""


def assert_defense_allowlisted(candidate: Mapping[str, object]) -> None:
    """Raise if a defense candidate edits anything outside architect prompts."""
    unknown = set(candidate) - DEFENSE_COMPONENT_FIELDS
    if unknown:
        allowed = ", ".join(sorted(DEFENSE_COMPONENT_FIELDS))
        raise DefenseAllowlistViolation(
            f"GEPA defense candidate references non-allowlisted field(s): {sorted(unknown)}. "
            f"Allowed fields: {allowed}."
        )


def seed_defense_candidate() -> dict[str, str]:
    """Return the current defense architect prompts as GEPA components."""
    return {
        "DEFENSE_ARCHITECT_SYSTEM_PROMPT": defense_assets.DEFENSE_ARCHITECT_SYSTEM_PROMPT,
        "DEFENSE_ARCHITECT_USER_TEMPLATE": defense_assets.DEFENSE_ARCHITECT_USER_TEMPLATE,
    }


def render_defense_assets_candidate(before_content: str, candidate: dict[str, str]) -> str:
    """Render a candidate into ``defense_assets.py`` content without applying it."""
    assert_defense_allowlisted(candidate)
    tree = ast.parse(before_content)
    replacements: list[tuple[int, int, str]] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id not in candidate:
                continue
            end = node.end_lineno or node.lineno
            replacements.append((node.lineno, end, _assignment(target.id, candidate[target.id])))
    if not replacements:
        return before_content
    lines = before_content.splitlines()
    for start, end, text in sorted(replacements, reverse=True):
        lines[start - 1 : end] = text.splitlines()
    return "\n".join(lines) + "\n"


def validate_defense_candidate_file(
    root: Path,
    candidate: dict[str, str],
) -> tuple[bool, list[dict[str, Any]], str]:
    """Run the existing Phase 6 sealed validator against a virtual candidate."""
    target_path = root / DEFENSE_ASSETS_PATH
    before = target_path.read_text(encoding="utf-8")
    after = render_defense_assets_candidate(before, candidate)
    outcome = validate_defense_prompt_candidate(target_path, before, after, root)
    return outcome.passed, [check.model_dump() for check in outcome.checks], after


def _assignment(name: str, value: str) -> str:
    escaped = value.replace('"""', r"\"\"\"")
    body = escaped if escaped.endswith("\n") else f"{escaped}\n"
    candidate_code = f'{name} = """\\\n{body}"""'
    try:
        ast.parse(candidate_code)
        return candidate_code
    except SyntaxError:
        return f"{name} = {repr(value)}"
