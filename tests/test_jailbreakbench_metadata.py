"""Tests for the metadata-only JailbreakBench adapter."""

from __future__ import annotations

from redthread.benchmarks.jailbreakbench import load_jailbreakbench_fixtures


def test_jailbreakbench_adapter_loads_metadata_only_fixtures() -> None:
    fixtures = load_jailbreakbench_fixtures()

    assert len(fixtures) == 6
    assert fixtures[0].id == "jailbreakbench-0001"
    assert fixtures[0].source_repo == "https://github.com/JailbreakBench/jailbreakbench"
    assert all(fixture.prompt_material_class == "metadata_only" for fixture in fixtures)
    assert all(fixture.review_status == "pending" for fixture in fixtures)
    assert all(fixture.raw_prompt_required for fixture in fixtures)
    assert not any(fixture.is_executable for fixture in fixtures)


def test_jailbreakbench_adapter_does_not_embed_prompt_bodies() -> None:
    fixtures = load_jailbreakbench_fixtures()

    assert all(fixture.prompt_material_ref == "not-copied" for fixture in fixtures)
    assert all("metadata-only" in fixture.source_path for fixture in fixtures)
    assert all("raw prompts stay outside git" in fixture.notes for fixture in fixtures)
