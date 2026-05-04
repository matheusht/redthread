"""Reviewed benchmark material CLI commands."""

from __future__ import annotations

import json
from typing import cast

import click
from rich.console import Console

from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.material_review import (
    MaterialReviewError,
    ReviewableMaterialClass,
    import_reviewed_material,
)
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures


def register_benchmark_material_commands(eval_group: click.Group, console: Console) -> None:
    """Register reviewed material import commands under `redthread eval`."""

    @eval_group.group(name="jailbreak-material")
    def material_group() -> None:
        """Reviewed jailbreak benchmark material tools."""

    @material_group.command(name="import")
    @click.option("--source", default="spiritual-spell", show_default=True)
    @click.option("--fixture-id", required=True)
    @click.option("--source-material", required=True, type=click.Path(exists=True, dir_okay=False))
    @click.option("--material-root", required=True, type=click.Path(exists=True, file_okay=False))
    @click.option("--reviewed-by", required=True)
    @click.option("--reviewed-at", required=True)
    @click.option("--reviewer", "reviewers", multiple=True, help="Reviewer id; repeat for approved replay seeds.")
    @click.option(
        "--material-class",
        type=click.Choice(["redacted", "approved_replay_seed"]),
        default="redacted",
        show_default=True,
    )
    @click.option("--allowed-target", "allowed_targets", multiple=True)
    @click.option("--collection-id", default="spiritual-spell", show_default=True)
    @click.option("--allow-nonlocal-targets", is_flag=True, default=False)
    @click.option("--json", "as_json", is_flag=True, default=False)
    def import_material(
        source: str,
        fixture_id: str,
        source_material: str,
        material_root: str,
        reviewed_by: str,
        reviewed_at: str,
        material_class: str,
        reviewers: tuple[str, ...],
        allowed_targets: tuple[str, ...],
        collection_id: str,
        allow_nonlocal_targets: bool,
        as_json: bool,
    ) -> None:
        """Copy one human-reviewed material file into the private vault."""
        if source != "spiritual-spell":
            raise click.ClickException(f"unsupported jailbreak corpus source: {source}")
        fixture = _fixture_by_id(fixture_id)
        try:
            result = import_reviewed_material(
                fixture,
                source_material_path=source_material,
                material_root=material_root,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                reviewer_ids=list(reviewers) or None,
                material_class=cast(ReviewableMaterialClass, material_class),
                allowed_target_ids=list(allowed_targets) or None,
                collection_id=collection_id,
                allow_nonlocal_targets=allow_nonlocal_targets,
            )
        except MaterialReviewError as exc:
            raise click.ClickException(str(exc)) from exc
        payload = result.model_dump()
        if as_json:
            click.echo(json.dumps(payload, indent=2))
            return
        console.print("[bold red]REDTHREAD BENCHMARK MATERIAL IMPORT[/bold red]")
        console.print(f"Fixture: {fixture.id}")
        console.print(f"Material class: {result.manifest.material_class}")
        console.print(f"Material ref: {result.material_ref}")
        console.print(f"Manifest ref: {result.manifest_ref}")
        console.print(f"Reviewers: {', '.join(result.manifest.reviewers)}")
        console.print("Raw prompt body: copied to private vault; not printed")


def _fixture_by_id(fixture_id: str) -> JailbreakBenchmarkFixture:
    for fixture in load_spiritual_spell_fixtures():
        if fixture.id == fixture_id:
            return fixture
    raise click.ClickException(f"unknown jailbreak benchmark fixture id: {fixture_id}")
