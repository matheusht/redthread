from __future__ import annotations

from types import SimpleNamespace

from click.testing import CliRunner
from pytest import MonkeyPatch

from redthread.cli import main
from redthread.research.source_mutation_models import SourceMutationCandidate
from tests.research_mutation_helpers import make_candidate


def test_research_mutate_inspect_cli(monkeypatch: MonkeyPatch) -> None:
    candidate = make_candidate()

    class StubHarness:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def inspect_latest(self) -> SourceMutationCandidate:
            return candidate

    monkeypatch.setattr("redthread.research.phase5.PhaseFiveHarness", StubHarness)
    result = CliRunner().invoke(main, ["research", "mutate", "inspect"])

    assert result.exit_code == 0
    assert candidate.candidate_id in result.output


def test_research_mutate_revert_cli(monkeypatch: MonkeyPatch) -> None:
    candidate = make_candidate()
    candidate.apply_status = "reverted"

    class StubHarness:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def revert_latest(self) -> SourceMutationCandidate:
            return candidate

    monkeypatch.setattr("redthread.research.phase5.PhaseFiveHarness", StubHarness)
    result = CliRunner().invoke(main, ["research", "mutate", "revert"])

    assert result.exit_code == 0
    assert "reverted" in result.output


def test_research_mutate_cycle_cli(monkeypatch: MonkeyPatch) -> None:
    candidate = make_candidate()
    proposal = SimpleNamespace(
        recommended_action="accept",
        rationale="ok",
        algorithm_override=None,
        promotion_eligibility_status="pending_phase3_accept",
        cycle=SimpleNamespace(winning_lane="offense"),
    )

    class StubHarness:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        async def run_cycle(
            self,
            baseline_first: bool,
            algorithm_override: object | None = None,
        ) -> tuple[SourceMutationCandidate, SimpleNamespace]:
            assert baseline_first is True
            return candidate, proposal

    monkeypatch.setattr("redthread.research.phase5.PhaseFiveHarness", StubHarness)
    result = CliRunner().invoke(main, ["research", "mutate", "cycle", "--baseline-first"])

    assert result.exit_code == 0
    assert candidate.candidate_id in result.output


def test_research_phase5_cycle_cli(monkeypatch: MonkeyPatch) -> None:
    candidate = make_candidate()
    proposal = SimpleNamespace(
        recommended_action="accept",
        rationale="ok",
        algorithm_override="tap",
        promotion_eligibility_status="pending_phase3_accept",
        cycle=SimpleNamespace(winning_lane="offense"),
    )

    class StubHarness:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        async def run_cycle(self, baseline_first: bool, algorithm_override: object | None = None) -> tuple[SourceMutationCandidate, SimpleNamespace]:
            assert baseline_first is True
            return candidate, proposal

    monkeypatch.setattr("redthread.research.phase5.PhaseFiveHarness", StubHarness)
    result = CliRunner().invoke(main, ["research", "phase5", "cycle", "--baseline-first"])

    assert result.exit_code == 0
    assert "Phase 5" in result.output
