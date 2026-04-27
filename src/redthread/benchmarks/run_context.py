"""Safe benchmark fixture context for normal `redthread run` campaigns."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, Field

from redthread.benchmarks.hints import BenchmarkHintProfile, build_fixture_hint_profiles
from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures


class BenchmarkRunContextError(ValueError):
    """Raised when a run benchmark context request is invalid."""


class BenchmarkRunContext(BaseModel):
    """Metadata-only benchmark context injected into normal campaign planning."""

    original_objective: str
    objective: str
    fixtures: list[JailbreakBenchmarkFixture] = Field(default_factory=list)
    hint_profiles: list[BenchmarkHintProfile] = Field(default_factory=list)
    summary_lines: list[str] = Field(default_factory=list)

    def metadata(self) -> dict[str, object]:
        """Return prompt-safe metadata for campaign artifacts."""
        return {
            "source": "spiritual-spell",
            "fixture_ids": [fixture.id for fixture in self.fixtures],
            "families": [fixture.family for fixture in self.fixtures],
            "technique_tags": sorted({tag for fixture in self.fixtures for tag in fixture.technique_tags}),
            "persona_tags": sorted({tag for fixture in self.fixtures for tag in fixture.persona_tags}),
            "attack_layers": sorted({layer for fixture in self.fixtures for layer in fixture.attack_layers}),
            "raw_prompt_loaded": False,
            "raw_prompt_policy": "fixture context uses metadata only; raw prompt bodies are not loaded",
        }


def apply_benchmark_fixture_context(
    objective: str,
    fixture_ids: Sequence[str],
) -> BenchmarkRunContext:
    """Append safe fixture metadata hints to a normal run objective."""
    fixtures = _fixtures_by_id(fixture_ids)
    hint_profiles = build_fixture_hint_profiles(fixtures)
    summary_lines = _summary_lines(fixtures, hint_profiles)
    return BenchmarkRunContext(
        original_objective=objective,
        objective=_augmented_objective(objective, fixtures, hint_profiles),
        fixtures=fixtures,
        hint_profiles=hint_profiles,
        summary_lines=summary_lines,
    )


def _fixtures_by_id(fixture_ids: Sequence[str]) -> list[JailbreakBenchmarkFixture]:
    if not fixture_ids:
        msg = "at least one benchmark fixture id is required"
        raise BenchmarkRunContextError(msg)
    fixture_map = {fixture.id: fixture for fixture in load_spiritual_spell_fixtures()}
    fixtures: list[JailbreakBenchmarkFixture] = []
    for fixture_id in fixture_ids:
        fixture = fixture_map.get(fixture_id)
        if fixture is None:
            msg = f"unknown jailbreak benchmark fixture id: {fixture_id}"
            raise BenchmarkRunContextError(msg)
        fixtures.append(fixture)
    return fixtures


def _augmented_objective(
    objective: str,
    fixtures: Sequence[JailbreakBenchmarkFixture],
    hint_profiles: Sequence[BenchmarkHintProfile],
) -> str:
    lines = [
        objective,
        "",
        "Benchmark fixture context (metadata only; do not load or reproduce raw corpus prompts):",
    ]
    for fixture, profile in zip(fixtures, hint_profiles, strict=True):
        lines.extend(
            [
                f"- fixture_id: {fixture.id}",
                f"  family: {fixture.family}",
                f"  expected_safe_behavior: {fixture.expected_safe_behavior}",
                f"  technique_tags: {', '.join(fixture.technique_tags) or '(none)'}",
                f"  persona_axes: {', '.join(profile.persona_axes) or '(none)'}",
                f"  judge_focus: {', '.join(profile.judge_focus) or '(none)'}",
            ]
        )
    return "\n".join(lines)


def _summary_lines(
    fixtures: Sequence[JailbreakBenchmarkFixture],
    hint_profiles: Sequence[BenchmarkHintProfile],
) -> list[str]:
    strategy_ids = sorted(
        {
            strategy_id
            for profile in hint_profiles
            for strategy_id in profile.recommended_strategy_ids
            if strategy_id in {"pair", "tap", "crescendo", "mcts"}
        }
    )
    lines = [
        "Benchmark fixture context: metadata only",
        f"Fixtures: {', '.join(fixture.id for fixture in fixtures)}",
        f"Suggested run algorithms: {', '.join(strategy_ids) if strategy_ids else '(none)'}",
        "Raw prompt bodies: not loaded",
    ]
    return lines
