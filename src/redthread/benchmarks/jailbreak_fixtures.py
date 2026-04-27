"""Reviewed jailbreak benchmark fixture contracts."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, ValidationError, model_validator

JAILBREAK_FIXTURE_SCHEMA_VERSION = "redthread.jailbreak_benchmark_fixture.v1"
PromptMaterialClass = Literal["metadata_only", "redacted", "approved_replay_seed"]
ReviewStatus = Literal["pending", "rejected", "metadata_only", "redacted", "approved_replay_seed"]


class JailbreakFixtureError(ValueError):
    """Raised when a benchmark fixture pack is unsafe or malformed."""


class JailbreakBenchmarkFixture(BaseModel):
    """Operator-reviewed jailbreak benchmark fixture metadata.

    Raw prompt bodies are intentionally not part of this contract. A fixture
    points to reviewed material and records whether it may execute.
    """

    schema_version: Literal["redthread.jailbreak_benchmark_fixture.v1"] = (
        "redthread.jailbreak_benchmark_fixture.v1"
    )
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$", min_length=1)
    source_repo: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    source_commit: str = Field(min_length=1)
    license_status: str = Field(min_length=1)
    provenance_status: str = Field(min_length=1)
    family: str = Field(min_length=1)
    target_family: str = Field(min_length=1)
    risk_plugin_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$", min_length=1)
    strategy_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$", min_length=1)
    rubric_id: str = Field(min_length=1)
    prompt_material_class: PromptMaterialClass = "metadata_only"
    prompt_material_ref: str = "not-copied"
    safety_level: str = Field(min_length=1)
    review_status: ReviewStatus = "pending"
    expected_safe_behavior: str = Field(min_length=1)
    technique_tags: list[str] = Field(default_factory=list)
    persona_tags: list[str] = Field(default_factory=list)
    attack_layers: list[str] = Field(default_factory=list)
    reference_pages: list[str] = Field(default_factory=list)
    raw_prompt_required: bool = False
    notes: str = ""

    @model_validator(mode="after")
    def validate_safety_gate(self) -> JailbreakBenchmarkFixture:
        """Reject executable-looking records that skip human review."""
        if self.prompt_material_class == "approved_replay_seed":
            if self.review_status != "approved_replay_seed":
                msg = "approved replay seeds require approved_replay_seed review status"
                raise ValueError(msg)
            if self.prompt_material_ref == "not-copied":
                msg = "approved replay seeds require an explicit prompt material reference"
                raise ValueError(msg)
        if self.review_status == "approved_replay_seed" and self.prompt_material_class != "approved_replay_seed":
            msg = "approved_replay_seed review status requires approved replay material"
            raise ValueError(msg)
        return self

    @property
    def is_executable(self) -> bool:
        """Return whether this fixture may be used for replay execution."""
        return (
            self.prompt_material_class == "approved_replay_seed"
            and self.review_status == "approved_replay_seed"
        )

    def lineage_metadata(self) -> dict[str, str]:
        """Return trace-safe source metadata for benchmark runs."""
        return {
            "benchmark_fixture_id": self.id,
            "benchmark_schema_version": self.schema_version,
            "benchmark_source_repo": self.source_repo,
            "benchmark_source_path": self.source_path,
            "benchmark_source_commit": self.source_commit,
            "benchmark_family": self.family,
            "benchmark_prompt_material_class": self.prompt_material_class,
            "benchmark_review_status": self.review_status,
            "benchmark_technique_tags": ",".join(self.technique_tags),
            "benchmark_persona_tags": ",".join(self.persona_tags),
            "benchmark_attack_layers": ",".join(self.attack_layers),
            "benchmark_reference_pages": ",".join(self.reference_pages),
            "benchmark_raw_prompt_required": str(self.raw_prompt_required).lower(),
        }


def load_jailbreak_fixture_file(path: str | Path) -> list[JailbreakBenchmarkFixture]:
    """Load a jailbreak fixture pack from a JSON file."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
    except OSError as exc:
        msg = f"could not read jailbreak fixture file: {path}"
        raise JailbreakFixtureError(msg) from exc
    except json.JSONDecodeError as exc:
        msg = f"invalid jailbreak fixture JSON: {path}"
        raise JailbreakFixtureError(msg) from exc
    if not isinstance(data, Mapping):
        msg = "jailbreak fixture file must contain a JSON object"
        raise JailbreakFixtureError(msg)
    return load_jailbreak_fixture_pack(data)


def load_jailbreak_fixture_pack(data: Mapping[str, Any]) -> list[JailbreakBenchmarkFixture]:
    """Load fixtures from a schema-marked in-memory fixture pack."""
    if data.get("schema_version") != JAILBREAK_FIXTURE_SCHEMA_VERSION:
        msg = "unknown jailbreak fixture schema version"
        raise JailbreakFixtureError(msg)
    raw_fixtures = data.get("fixtures")
    if not _is_fixture_sequence(raw_fixtures):
        msg = "jailbreak fixture pack requires a fixtures list"
        raise JailbreakFixtureError(msg)
    fixture_items = cast(Sequence[object], raw_fixtures)
    fixtures: list[JailbreakBenchmarkFixture] = []
    seen_ids: set[str] = set()
    for raw_fixture in fixture_items:
        fixture = _parse_fixture(raw_fixture)
        if fixture.id in seen_ids:
            msg = f"duplicate jailbreak fixture id: {fixture.id}"
            raise JailbreakFixtureError(msg)
        seen_ids.add(fixture.id)
        fixtures.append(fixture)
    return fixtures


def _is_fixture_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def _parse_fixture(raw_fixture: object) -> JailbreakBenchmarkFixture:
    if not isinstance(raw_fixture, Mapping):
        msg = "each jailbreak fixture must be a JSON object"
        raise JailbreakFixtureError(msg)
    try:
        return JailbreakBenchmarkFixture.model_validate(raw_fixture)
    except ValidationError as exc:
        msg = "invalid jailbreak benchmark fixture"
        raise JailbreakFixtureError(msg) from exc
