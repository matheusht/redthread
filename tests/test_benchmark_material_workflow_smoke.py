"""End-to-end prompt-safe benchmark material workflow smoke test."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from click.testing import CliRunner

from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def test_material_inventory_to_local_replay_workflow_is_prompt_safe(tmp_path: Path) -> None:
    raw_seed = "workflow smoke private reviewed seed"
    fixture = next(item for item in load_spiritual_spell_fixtures() if item.id == "spiritual-spell-0032")
    source = tmp_path / "reviewed-seed.txt"
    source.write_text(raw_seed, encoding="utf-8")
    import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-review-owner",
        reviewed_at="2026-04-26T00:00:00Z",
        reviewer_ids=["security-review-owner", "benchmark-owner"],
        material_class="approved_replay_seed",
    )

    command_result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--ready-only",
            "--replay-commands-only",
        ],
    )

    assert command_result.exit_code == 0
    assert command_result.output.startswith("redthread eval jailbreak-corpus --replay")
    assert raw_seed not in command_result.output

    report_path = tmp_path / "workflow-replay-report.json"
    replay_args = shlex.split(command_result.output.strip())
    replay_result = CliRunner().invoke(
        main,
        [*replay_args[1:], "--report-out", str(report_path)],
    )

    assert replay_result.exit_code == 0, replay_result.output
    assert "Evidence mode: sealed_local_replay" in replay_result.output
    assert "Scorecard: not scored (sealed_local_smoke_only)" in replay_result.output
    assert raw_seed not in replay_result.output
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["tested_fixture_ids"] == ["spiritual-spell-0032"]
    assert payload["evidence_mode"] == "sealed_local_replay"
    assert payload["not_scored_reason"] == "sealed_local_smoke_only"
    assert raw_seed not in report_path.read_text(encoding="utf-8")
