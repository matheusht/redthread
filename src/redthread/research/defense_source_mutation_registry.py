"""Template registry for bounded defense prompt mutation work."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from redthread.research.source_mutation_registry import SourceMutationTemplate


@dataclass(frozen=True)
class DefenseSourceMutationTemplate(SourceMutationTemplate):
    """A bounded source-mutation template scoped to defense prompt assets."""


DEFENSE_TEMPLATES = (
    DefenseSourceMutationTemplate(
        mutation_family="defense_clause_scope_tightening",
        rationale="Strengthen the architect prompt so proposed clauses stay narrow to the confirmed exploit pattern.",
        metric_goal="Improve exploit blocking without widening benign regressions in defense-generated guardrails.",
        target_file="src/redthread/core/defense_assets.py",
        old="- **Precise over Polite**: Prioritize blocking the threat over conversational politeness.",
        new=(
            "- **Precise over Polite**: Prioritize blocking the threat over conversational politeness.\n"
            "- **Scope Discipline**: Keep the clause narrowly tied to the confirmed exploit pattern and avoid broad restrictions on unrelated benign help."
        ),
        selected_tests=("tests/test_defense.py", "tests/test_guardrail_loader.py", "tests/test_research_phase6.py"),
    ),
    DefenseSourceMutationTemplate(
        mutation_family="defense_user_template_narrowing",
        rationale="Ask the architect for an exploit-scoped clause that preserves benign utility.",
        metric_goal="Improve defense prompt specificity without mutating runtime deployment logic.",
        target_file="src/redthread/core/defense_assets.py",
        old="Please classify and propose a narrowly scoped, evidence-aware guardrail clause that blocks the exploit without degrading ordinary benign assistance.",
        new=(
            "Please classify and propose a narrowly scoped, evidence-aware guardrail clause that blocks the exploit without degrading ordinary benign assistance. "
            "Anchor the clause to the exact exploit evidence in the trace instead of broad refusal language."
        ),
        selected_tests=("tests/test_defense.py", "tests/test_guardrail_loader.py", "tests/test_research_phase6.py"),
    ),
)


def select_defense_template(
    ranked_slugs: list[str],
    templates: Sequence[SourceMutationTemplate] = DEFENSE_TEMPLATES,
) -> SourceMutationTemplate:
    """Select the next defense prompt mutation template."""
    focus = ranked_slugs[0] if ranked_slugs else "authorization_bypass"
    if focus in {"prompt_injection", "system_prompt_exfiltration"}:
        return templates[0]
    return templates[min(1, len(templates) - 1)]
