"""Metadata-only JailbreakBench fixture adapter."""

from __future__ import annotations

from typing import Any

from redthread.benchmarks.jailbreak_fixtures import (
    JAILBREAK_FIXTURE_SCHEMA_VERSION,
    JailbreakBenchmarkFixture,
    load_jailbreak_fixture_pack,
)

JAILBREAKBENCH_SOURCE_REPO = "https://github.com/JailbreakBench/jailbreakbench"
JAILBREAKBENCH_SOURCE_COMMIT = "pin-before-use"

_METADATA_ROWS: tuple[dict[str, str], ...] = (
    {
        "family": "harmful_request_refusal",
        "target_family": "general_policy",
        "risk_plugin_id": "prompt_injection",
        "rubric_id": "insecure_output",
        "safety_level": "high",
    },
    {
        "family": "privacy_secret_extraction",
        "target_family": "privacy_policy",
        "risk_plugin_id": "sensitive_info_disclosure",
        "rubric_id": "sensitive_info",
        "safety_level": "high",
    },
    {
        "family": "cyber_abuse_request",
        "target_family": "cyber_safety",
        "risk_plugin_id": "unsafe_cyber_assistance",
        "rubric_id": "cyber_safety",
        "safety_level": "high",
    },
    {
        "family": "deception_and_fraud_request",
        "target_family": "fraud_safety",
        "risk_plugin_id": "unsafe_persuasion",
        "rubric_id": "fraud_safety",
        "safety_level": "high",
    },
    {
        "family": "violence_or_physical_harm_request",
        "target_family": "physical_safety",
        "risk_plugin_id": "unsafe_physical_harm",
        "rubric_id": "physical_safety",
        "safety_level": "high",
    },
    {
        "family": "controlled_substance_request",
        "target_family": "regulated_goods",
        "risk_plugin_id": "unsafe_regulated_goods",
        "rubric_id": "regulated_goods",
        "safety_level": "high",
    },
)


def jailbreakbench_fixture_pack_data() -> dict[str, Any]:
    """Return a metadata-only JailbreakBench fixture pack."""
    return {
        "schema_version": JAILBREAK_FIXTURE_SCHEMA_VERSION,
        "fixtures": [_record(index, row) for index, row in enumerate(_METADATA_ROWS, start=1)],
    }


def load_jailbreakbench_fixtures() -> list[JailbreakBenchmarkFixture]:
    """Load metadata-only JailbreakBench fixture models."""
    return load_jailbreak_fixture_pack(jailbreakbench_fixture_pack_data())


def _record(index: int, row: dict[str, str]) -> dict[str, Any]:
    fixture_id = f"jailbreakbench-{index:04d}"
    return {
        "schema_version": JAILBREAK_FIXTURE_SCHEMA_VERSION,
        "id": fixture_id,
        "source_repo": JAILBREAKBENCH_SOURCE_REPO,
        "source_path": f"metadata-only/jailbreakbench-policy-category#{row['family']}",
        "source_commit": JAILBREAKBENCH_SOURCE_COMMIT,
        "license_status": "unknown",
        "provenance_status": "unverified_metadata_only",
        "family": row["family"],
        "target_family": row["target_family"],
        "risk_plugin_id": row["risk_plugin_id"],
        "strategy_id": "static_seed_replay",
        "rubric_id": row["rubric_id"],
        "prompt_material_class": "metadata_only",
        "prompt_material_ref": "not-copied",
        "safety_level": row["safety_level"],
        "review_status": "pending",
        "expected_safe_behavior": _expected_safe_behavior(row["target_family"]),
        "technique_tags": ["benchmark_metadata_only"],
        "persona_tags": [],
        "attack_layers": ["policy_boundary"],
        "reference_pages": ["docs/wiki/decisions/jailbreak-benchmark-material-vault.md"],
        "raw_prompt_required": True,
        "notes": "Metadata-only JailbreakBench adapter; raw prompts stay outside git.",
    }


def _expected_safe_behavior(target_family: str) -> str:
    return f"refuse unsafe {target_family} requests while preserving benign assistance"
