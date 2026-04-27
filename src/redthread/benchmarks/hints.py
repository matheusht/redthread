"""Safe persona and strategy hints derived from benchmark metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field

from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture


class BenchmarkHintProfile(BaseModel):
    """Non-executable hints for planning persona and attack-workflow coverage."""

    fixture_id: str
    recommended_strategy_ids: list[str] = Field(default_factory=list)
    persona_axes: list[str] = Field(default_factory=list)
    judge_focus: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    raw_prompt_required: bool = False

    def summary_lines(self) -> list[str]:
        """Return operator-readable hint summary lines."""
        return [
            f"Fixture: {self.fixture_id}",
            f"Strategies: {', '.join(self.recommended_strategy_ids) or 'none'}",
            f"Persona axes: {', '.join(self.persona_axes) or 'none'}",
            f"Judge focus: {', '.join(self.judge_focus) or 'none'}",
            f"Raw prompt required: {str(self.raw_prompt_required).lower()}",
        ]


def build_fixture_hint_profile(fixture: JailbreakBenchmarkFixture) -> BenchmarkHintProfile:
    """Build safe planning hints from fixture tags without copying prompt bodies."""
    tags = set(fixture.technique_tags)
    personas = set(fixture.persona_tags)
    layers = set(fixture.attack_layers)
    return BenchmarkHintProfile(
        fixture_id=fixture.id,
        recommended_strategy_ids=_strategy_hints(tags, layers),
        persona_axes=_persona_axes(personas, tags),
        judge_focus=_judge_focus(tags, layers),
        source_references=fixture.reference_pages,
        raw_prompt_required=fixture.raw_prompt_required,
    )


def build_fixture_hint_profiles(
    fixtures: list[JailbreakBenchmarkFixture],
) -> list[BenchmarkHintProfile]:
    """Build safe planning hints for a fixture collection."""
    return [build_fixture_hint_profile(fixture) for fixture in fixtures]


def _strategy_hints(tags: set[str], layers: set[str]) -> list[str]:
    strategies = {"static_seed_replay"}
    if "narrative_embedding" in tags or "narrative" in layers:
        strategies.add("crescendo")
    if "strategic_distraction" in tags:
        strategies.add("tap")
    if "agent_instruction_injection" in tags or "tool_orchestration" in layers:
        strategies.add("static_seed_replay")
    return sorted(strategies)


def _persona_axes(personas: set[str], tags: set[str]) -> list[str]:
    axes: set[str] = set()
    if "eni_writer" in personas:
        axes.update(
            {
                "relational_persona_pressure",
                "sycophancy_resistance",
                "guardrail_rebuttal_resilience",
            }
        )
    if "reasoning_hijack_attempt" in tags:
        axes.add("reasoning_channel_boundary")
    if "persona_modulation" in tags:
        axes.add("identity_stability")
    return sorted(axes)


def _judge_focus(tags: set[str], layers: set[str]) -> list[str]:
    focus: set[str] = {"policy_compliance_over_style"}
    if "narrative_embedding" in tags:
        focus.add("fiction_wrapped_policy_bypass")
    if "injection_rebuttal" in tags or "guardrail_rebuttal" in layers:
        focus.add("safety_instruction_rebuttal")
    if "system_prompt_extraction" in tags:
        focus.add("sensitive_instruction_disclosure")
    if "agent_instruction_injection" in tags:
        focus.add("unsafe_tool_authorization")
    return sorted(focus)
