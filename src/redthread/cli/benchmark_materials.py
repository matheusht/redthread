"""Reviewed benchmark material CLI commands."""

from __future__ import annotations

import json
from typing import cast

import click
from rich.console import Console

from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.jailbreakbench import load_jailbreakbench_fixtures
from redthread.benchmarks.material_inventory import list_benchmark_material_manifests
from redthread.benchmarks.material_review import (
    MaterialReviewError,
    ReviewableMaterialClass,
    import_reviewed_material,
)
from redthread.benchmarks.material_vault import MaterialVaultError
from redthread.benchmarks.material_verify import verify_benchmark_material_manifest
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures


def register_benchmark_material_commands(eval_group: click.Group, console: Console) -> None:
    """Register reviewed material import commands under `redthread eval`."""

    @eval_group.group(name="jailbreak-material")
    def material_group() -> None:
        """Reviewed jailbreak benchmark material tools."""

    @material_group.command(name="import")
    @click.option(
        "--source",
        type=click.Choice(["spiritual-spell", "jailbreakbench"]),
        default="spiritual-spell",
        show_default=True,
    )
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
    @click.option("--collection-id", default=None, help="Vault collection id; defaults to --source.")
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
        collection_id: str | None,
        allow_nonlocal_targets: bool,
        as_json: bool,
    ) -> None:
        """Copy one human-reviewed material file into the private vault."""
        fixture = _fixture_by_id(source, fixture_id)
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
                collection_id=collection_id or source,
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

    @material_group.command(name="verify")
    @click.option("--manifest-ref", required=True)
    @click.option("--material-root", default=None, type=click.Path(exists=False))
    @click.option("--json", "as_json", is_flag=True, default=False)
    def verify_material(manifest_ref: str, material_root: str | None, as_json: bool) -> None:
        """Verify one reviewed material manifest without printing prompt bodies."""
        try:
            verification = verify_benchmark_material_manifest(manifest_ref, material_root=material_root)
        except MaterialVaultError as exc:
            raise click.ClickException(str(exc)) from exc
        if as_json:
            click.echo(json.dumps(verification.model_dump(mode="json"), indent=2))
            return
        console.print("[bold red]REDTHREAD BENCHMARK MATERIAL VERIFY[/bold red]")
        console.print(f"Fixture: {verification.fixture_id}")
        console.print(f"Material class: {verification.material_class}")
        console.print(f"Manifest ref: {verification.manifest_ref}")
        console.print(f"Material ref: {verification.material_ref}")
        console.print(f"Hash verified: {verification.hash_verified}")
        console.print("Raw prompt body: not printed")

    @material_group.command(name="list")
    @click.option("--material-root", default=None, type=click.Path(exists=False))
    @click.option("--collection-id", default=None, help="Optional vault collection id filter.")
    @click.option(
        "--material-class",
        type=click.Choice(["redacted", "approved_replay_seed"]),
        default=None,
    )
    @click.option("--allowed-target", "allowed_target_id", default=None)
    @click.option("--verify-hashes", is_flag=True, default=False)
    @click.option("--require-valid-hashes", is_flag=True, default=False)
    @click.option("--json", "as_json", is_flag=True, default=False)
    def list_materials(
        material_root: str | None,
        collection_id: str | None,
        material_class: str | None,
        allowed_target_id: str | None,
        verify_hashes: bool,
        require_valid_hashes: bool,
        as_json: bool,
    ) -> None:
        """List reviewed material manifests without reading prompt bodies."""
        try:
            inventory = list_benchmark_material_manifests(
                material_root=material_root,
                collection_id=collection_id,
                material_class=material_class,
                allowed_target_id=allowed_target_id,
                verify_hashes=verify_hashes or require_valid_hashes,
            )
        except MaterialVaultError as exc:
            raise click.ClickException(str(exc)) from exc
        if require_valid_hashes and inventory.invalid_hash_count > 0:
            msg = f"invalid material hashes found: {inventory.invalid_hash_count}"
            raise click.ClickException(msg)
        if as_json:
            click.echo(json.dumps(inventory.model_dump(mode="json"), indent=2))
            return
        console.print("[bold red]REDTHREAD BENCHMARK MATERIAL INVENTORY[/bold red]")
        console.print(f"Manifest count: {inventory.manifest_count}")
        if material_class is not None:
            console.print(f"Material class filter: {material_class}")
        if allowed_target_id is not None:
            console.print(f"Allowed target filter: {allowed_target_id}")
        console.print(f"Hash check: {'enabled' if verify_hashes or require_valid_hashes else 'not checked'}")
        console.print("Raw prompt bodies: not read")
        for row in inventory.manifests:
            console.print(
                f"- {row.fixture_id} | {row.material_class} | "
                f"{row.hash_status} | {row.manifest_ref}"
            )


def _fixture_by_id(source: str, fixture_id: str) -> JailbreakBenchmarkFixture:
    for fixture in _fixtures_for_source(source):
        if fixture.id == fixture_id:
            return fixture
    raise click.ClickException(f"unknown jailbreak benchmark fixture id: {fixture_id}")


def _fixtures_for_source(source: str) -> list[JailbreakBenchmarkFixture]:
    if source == "jailbreakbench":
        return load_jailbreakbench_fixtures()
    return load_spiritual_spell_fixtures()
