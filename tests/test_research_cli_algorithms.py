from __future__ import annotations

from types import SimpleNamespace

from click.testing import CliRunner
from pytest import MonkeyPatch

from redthread.cli import main
from redthread.config.settings import AlgorithmType


def test_research_run_accepts_algorithm_override(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class StubHarness:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.results_path = "results.tsv"

        async def run_experiments(
            self,
            cycles: int,
            baseline_first: bool,
            algorithm_override: AlgorithmType | None = None,
        ) -> list[SimpleNamespace]:
            captured["algorithm_override"] = algorithm_override
            return [
                SimpleNamespace(
                    mode="experiment",
                    total_campaigns=1,
                    confirmed_jailbreaks=0,
                    near_misses=0,
                    average_asr=0.0,
                    average_score=1.0,
                    composite_score=1.0,
                )
            ]

    monkeypatch.setattr("redthread.research.runner.PhaseOneResearchHarness", StubHarness)
    result = CliRunner().invoke(main, ["research", "run", "--algorithm", "mcts"])

    assert result.exit_code == 0
    assert getattr(captured["algorithm_override"], "value", None) == "mcts"
    assert "Algorithm override" in result.output


def test_research_supervise_accepts_algorithm_override(monkeypatch: MonkeyPatch) -> None:
    class StubHarness:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.workspace = SimpleNamespace(baseline_registry_path="baseline.json")
            self.results_path = "results.tsv"

        async def run_cycle(
            self,
            baseline_first: bool,
            algorithm_override: AlgorithmType | None = None,
        ) -> SimpleNamespace:
            assert getattr(algorithm_override, "value", None) == "crescendo"
            return SimpleNamespace(accepted=True, winning_lane="offense", rationale="ok")

    monkeypatch.setattr("redthread.research.supervisor.PhaseTwoResearchHarness", StubHarness)
    result = CliRunner().invoke(main, ["research", "supervise", "--algorithm", "crescendo"])

    assert result.exit_code == 0
    assert "crescendo" in result.output


def test_research_phase3_cycle_prints_algorithm_override(monkeypatch: MonkeyPatch) -> None:
    proposal = SimpleNamespace(
        proposal_id="proposal-1",
        algorithm_override="mcts",
        recommended_action="accept",
        rationale="ok",
        cycle=SimpleNamespace(winning_lane="offense"),
    )

    class StubHarness:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.proposals_dir = "proposals"

        async def run_cycle(
            self,
            baseline_first: bool,
            algorithm_override: AlgorithmType | None = None,
        ) -> SimpleNamespace:
            assert getattr(algorithm_override, "value", None) == "mcts"
            return proposal

    monkeypatch.setattr("redthread.research.phase3.PhaseThreeHarness", StubHarness)
    result = CliRunner().invoke(main, ["research", "phase3", "cycle", "--algorithm", "mcts"])

    assert result.exit_code == 0
    assert "Algorithm:" in result.output
    assert "mcts" in result.output


def test_research_mutate_cycle_accepts_algorithm_override(monkeypatch: MonkeyPatch) -> None:
    candidate = SimpleNamespace(candidate_id="c1", mutation_family="family", apply_status="applied")
    proposal = SimpleNamespace(recommended_action="accept", rationale="ok", algorithm_override="tap", cycle=SimpleNamespace(winning_lane="offense"))

    class StubHarness:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        async def run_cycle(
            self,
            baseline_first: bool,
            algorithm_override: AlgorithmType | None = None,
        ) -> tuple[SimpleNamespace, SimpleNamespace]:
            assert getattr(algorithm_override, "value", None) == "tap"
            return candidate, proposal

    monkeypatch.setattr("redthread.research.source_mutation_harness.SourceMutationHarness", StubHarness)
    result = CliRunner().invoke(main, ["research", "mutate", "cycle", "--algorithm", "tap"])

    assert result.exit_code == 0
    assert "tap" in result.output


def test_research_phase4_cycle_accepts_algorithm_override(monkeypatch: MonkeyPatch) -> None:
    candidate = SimpleNamespace(id="m1", kind="runtime", description="desc")
    proposal = SimpleNamespace(recommended_action="accept", rationale="ok", algorithm_override="pair", cycle=SimpleNamespace(winning_lane="offense"))

    class StubHarness:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.workspace = SimpleNamespace(runtime_dir="runtime")

        async def run_cycle(
            self,
            baseline_first: bool,
            algorithm_override: AlgorithmType | None = None,
        ) -> tuple[SimpleNamespace, SimpleNamespace]:
            assert getattr(algorithm_override, "value", None) == "pair"
            return candidate, proposal

    monkeypatch.setattr("redthread.research.phase4.PhaseFourHarness", StubHarness)
    result = CliRunner().invoke(main, ["research", "phase4", "cycle", "--algorithm", "pair"])

    assert result.exit_code == 0
    assert "pair" in result.output


def test_research_algorithm_override_rejects_invalid_value() -> None:
    result = CliRunner().invoke(main, ["research", "run", "--algorithm", "invalid"])

    assert result.exit_code != 0
    assert "Invalid value" in result.output
