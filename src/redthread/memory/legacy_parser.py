"""Parser for legacy Markdown guardrail entries."""

from __future__ import annotations

import re

_SCOPE = re.compile(
    r"^\s*\*\*Scope:\*\*\s*model\s*=\s*`([^`]+)`\s*\|\s*prompt_hash\s*=\s*`([^`]+)`\s*$"
)
_CLAUSE = re.compile(r"^\s*>\s*\*\*Guardrail clause:\*\*\s*(.*)$")
_QUOTE = re.compile(r"^\s*>\s?(.*)$")
_HEADING = re.compile(r"^\s*##\s+")
_SEPARATOR = re.compile(r"^\s*---\s*$")
_VALIDATED = re.compile(r"^\s*\*\*Validated:\*\*\s*(✅\s*YES|❌\s*NO)(?:\s|$)")


def _entry_blocks(content: str) -> list[list[str]]:
    """Split legacy Markdown at separators or entry headings."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in content.splitlines():
        boundary = _SEPARATOR.match(line) or _HEADING.match(line)
        if boundary and current:
            blocks.append(current)
            current = []
        if not _SEPARATOR.match(line):
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


def load_legacy_guardrails(content: str, target_model: str, prompt_hash: str) -> list[str]:
    """Return validated scoped clauses from a legacy Markdown memory file."""
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    clauses: list[str] = []
    for lines in _entry_blocks(normalized):
        block = "\n".join(lines)
        validation_matches = [match for line in lines if (match := _VALIDATED.match(line))]
        if len(validation_matches) != 1 or validation_matches[0] is None:
            continue
        if validation_matches[0].group(1) != "✅ YES":
            continue
        scope_matches = [match for line in lines if (match := _SCOPE.match(line))]
        if len(scope_matches) != 1 or scope_matches[0] is None:
            continue
        scope = scope_matches[0]
        if scope.group(1) != target_model or scope.group(2) != prompt_hash:
            continue
        lines = block.splitlines()
        for index, line in enumerate(lines):
            marker = _CLAUSE.match(line)
            if not marker:
                continue
            parts = [marker.group(1).strip()]
            for continuation in lines[index + 1 :]:
                quoted = _QUOTE.match(continuation)
                if not quoted:
                    break
                value = quoted.group(1).strip()
                if value:
                    parts.append(value)
            clause = " ".join(part for part in parts if part).strip()
            if clause:
                clauses.append(clause)
            break
    return clauses


__all__ = ["load_legacy_guardrails"]
