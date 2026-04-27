"""Tests for metadata-only jailbreak benchmark dry-run reports."""

from __future__ import annotations

import pytest

from redthread.benchmarks.dry_run import (
    BenchmarkDryRunError,
    build_jailbreak_corpus_dry_run_report,
)


def test_builds_spiritual_spell_dry_run_without_prompt_material() -> None:
    report = build_jailbreak_corpus_dry_run_report(limit=3)

    assert report.source == "spiritual-spell"
    assert report.total_fixture_count == 210
    assert report.selected_fixture_ids == [
        "spiritual-spell-0001",
        "spiritual-spell-0002",
        "spiritual-spell-0003",
    ]
    assert report.executable_fixture_ids == []
    assert report.blocked_fixture_ids == report.selected_fixture_ids
    assert "Raw prompt bodies: not loaded" in report.summary_lines
    assert report.raw_prompt_policy == "raw prompt bodies are not loaded during dry-run"


def test_filters_dry_run_by_fixture_id_and_family() -> None:
    report = build_jailbreak_corpus_dry_run_report(
        fixture_ids=["spiritual-spell-0032"],
        families=["eni_variants"],
    )

    assert report.selected_fixture_ids == ["spiritual-spell-0032"]
    assert any("eni_variants" in line for line in report.summary_lines)


def test_dry_run_can_include_safe_hint_profiles() -> None:
    report = build_jailbreak_corpus_dry_run_report(
        fixture_ids=["spiritual-spell-0032"],
        include_hints=True,
    )

    assert len(report.hint_profiles) == 1
    assert "relational_persona_pressure" in report.hint_profiles[0].persona_axes
    assert "crescendo" in report.hint_profiles[0].recommended_strategy_ids


def test_dry_run_blocks_live_target_without_authorization() -> None:
    with pytest.raises(BenchmarkDryRunError, match="local-dev"):
        build_jailbreak_corpus_dry_run_report(target_id="prod-model")


def test_dry_run_rejects_empty_filter_result() -> None:
    with pytest.raises(BenchmarkDryRunError, match="no benchmark fixtures matched"):
        build_jailbreak_corpus_dry_run_report(fixture_ids=["missing-fixture"])
