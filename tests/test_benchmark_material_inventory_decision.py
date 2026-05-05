"""Tests for engine-calculated material inventory decisions."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from click.testing import CliRunner

from redthread.benchmarks.material_inventory import list_benchmark_material_manifests
from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _manifest(tmp_path: Path, text: str = "toy decision prompt body") -> None:
    fixture = next(
        item for item in load_spiritual_spell_fixtures()
        if item.id == "spiritual-spell-0032"
    )
    source = tmp_path / "reviewed-seed.txt"
    source.write_text(text, encoding="utf-8")
    import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-review-owner",
        reviewed_at="2026-04-26T00:00:00Z",
        reviewer_ids=["security-review-owner", "benchmark-owner"],
        material_class="approved_replay_seed",
    )


def test_material_inventory_decision_needs_hash_check(tmp_path: Path) -> None:
    _manifest(tmp_path, "decision unchecked body")

    inventory = list_benchmark_material_manifests(material_root=tmp_path)

    assert inventory.material_ready_count == 0
    assert inventory.material_blocked_count == 0
    assert inventory.blocked_reason_counts == {}
    assert inventory.engine_decision == "needs_hash_check"
    assert inventory.operator_next_step == "verify hashes before replay"
    assert inventory.operator_summary == "ready=0; blocked=0; hash check needed"
    assert inventory.suggested_replay_commands == []
    assert "decision unchecked body" not in inventory.model_dump_json()


def test_material_inventory_decision_ready_for_replay(tmp_path: Path) -> None:
    _manifest(tmp_path, "decision ready body")

    inventory = list_benchmark_material_manifests(material_root=tmp_path, verify_hashes=True)

    assert inventory.material_ready_count == 1
    assert inventory.material_blocked_count == 0
    assert inventory.blocked_reason_counts == {}
    assert inventory.engine_decision == "ready_for_replay"
    assert inventory.operator_next_step == "ready for approved local replay"
    assert inventory.operator_summary == "ready=1; blocked=0; no operator action needed"
    assert inventory.suggested_replay_commands == [
        "redthread eval jailbreak-corpus --replay --fixture-id spiritual-spell-0032 "
        "--manifest-ref spiritual-spell/manifests/spiritual-spell-0032.json "
        f"--material-root {shlex.quote(str(tmp_path.resolve()))}"
    ]
    assert "decision ready body" not in inventory.model_dump_json()


def test_material_inventory_decision_blocked(tmp_path: Path) -> None:
    _manifest(tmp_path, "decision blocked body")
    material_path = tmp_path / "spiritual-spell" / "reviewed" / "spiritual-spell-0032.txt"
    material_path.write_text("tampered decision body", encoding="utf-8")

    inventory = list_benchmark_material_manifests(material_root=tmp_path, verify_hashes=True)

    assert inventory.material_ready_count == 0
    assert inventory.material_blocked_count == 1
    assert inventory.blocked_reason_counts == {"hash_mismatch": 1}
    assert inventory.engine_decision == "blocked"
    assert inventory.operator_next_step == "fix invalid hashes or review gates before replay"
    assert inventory.operator_summary == "ready=0; blocked=1; fix blockers before replay"
    assert inventory.suggested_replay_commands == []
    assert "tampered decision body" not in inventory.model_dump_json()


def test_material_inventory_cli_prints_engine_decision_without_extra_flags(tmp_path: Path) -> None:
    _manifest(tmp_path, "decision cli body")

    result = CliRunner().invoke(
        main,
        ["eval", "jailbreak-material", "list", "--material-root", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "Engine decision: ready_for_replay" in result.output
    assert "Operator next step: ready for approved local replay" in result.output
    assert "Operator summary: ready=1; blocked=0; no operator action needed" in result.output
    assert "Ready materials: 1" in result.output
    assert "Blocked materials: 0" in result.output
    assert "Suggested replay: redthread eval jailbreak-corpus --replay" in result.output
    assert "Blocked reasons:" not in result.output
    assert "decision cli body" not in result.output


def test_material_inventory_cli_json_includes_engine_decision(tmp_path: Path) -> None:
    _manifest(tmp_path, "decision json body")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["engine_decision"] == "ready_for_replay"
    assert payload["operator_next_step"] == "ready for approved local replay"
    assert payload["operator_summary"] == "ready=1; blocked=0; no operator action needed"
    assert payload["material_ready_count"] == 1
    assert payload["material_blocked_count"] == 0
    assert payload["suggested_replay_commands"] == [
        "redthread eval jailbreak-corpus --replay --fixture-id spiritual-spell-0032 "
        "--manifest-ref spiritual-spell/manifests/spiritual-spell-0032.json "
        f"--material-root {shlex.quote(str(tmp_path.resolve()))}"
    ]
    assert payload["blocked_reason_counts"] == {}
    assert "decision json body" not in result.output
