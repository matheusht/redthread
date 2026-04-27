"""Reviewed prompt material loading for jailbreak benchmark fixtures."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture


class PromptMaterialError(ValueError):
    """Raised when prompt material is unavailable or unsafe to load."""


class PromptMaterial(BaseModel):
    """Reviewed prompt text plus safety metadata."""

    fixture_id: str
    material_class: str
    material_ref: str
    text: str
    may_execute: bool


def load_prompt_material(
    fixture: JailbreakBenchmarkFixture,
    *,
    material_root: str | Path,
) -> PromptMaterial:
    """Load reviewed prompt material for a fixture.

    Metadata-only fixtures intentionally fail here. Redacted material can be
    loaded for review/reference. Only approved replay seeds may execute.
    """
    if fixture.prompt_material_class == "metadata_only":
        msg = "metadata-only fixtures do not include prompt material"
        raise PromptMaterialError(msg)
    path = _safe_material_path(material_root, fixture.prompt_material_ref)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"could not read prompt material: {fixture.prompt_material_ref}"
        raise PromptMaterialError(msg) from exc
    return PromptMaterial(
        fixture_id=fixture.id,
        material_class=fixture.prompt_material_class,
        material_ref=fixture.prompt_material_ref,
        text=text,
        may_execute=fixture.is_executable,
    )


def load_replay_seed_prompts(
    fixture: JailbreakBenchmarkFixture,
    *,
    material_root: str | Path,
) -> list[str]:
    """Load executable replay prompts from an approved fixture."""
    if not fixture.is_executable:
        msg = "only approved replay seed fixtures may execute"
        raise PromptMaterialError(msg)
    material = load_prompt_material(fixture, material_root=material_root)
    return [material.text]


def _safe_material_path(material_root: str | Path, material_ref: str) -> Path:
    if material_ref == "not-copied":
        msg = "fixture has no prompt material reference"
        raise PromptMaterialError(msg)
    root = Path(material_root).resolve()
    path = (root / material_ref).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        msg = "prompt material reference escapes material root"
        raise PromptMaterialError(msg) from exc
    return path
