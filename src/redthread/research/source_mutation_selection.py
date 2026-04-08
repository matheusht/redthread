"""Template selection helpers for bounded source mutation phases."""

from __future__ import annotations

from collections.abc import Sequence

from redthread.research.source_mutation_registry import SourceMutationTemplate


def select_phase5_template(
    ranked_slugs: list[str],
    templates: Sequence[SourceMutationTemplate],
) -> SourceMutationTemplate:
    """Select the next offense-focused mutation template."""
    if len(templates) == 1:
        return templates[0]
    focus = ranked_slugs[0] if ranked_slugs else "authorization_bypass"
    if focus == "prompt_injection":
        return templates[min(3, len(templates) - 1)]
    if focus == "sensitive_info_exfiltration":
        return templates[min(5, len(templates) - 1)]
    if focus == "system_prompt_exfiltration":
        return templates[min(4, len(templates) - 1)]
    if focus == "authorization_bypass":
        return templates[min(2, len(templates) - 1)]
    return templates[min(6, len(templates) - 1)]
