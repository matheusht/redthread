"""Reviewed benchmark material inventory CLI command."""

from __future__ import annotations

import json

import click
from rich.console import Console

from redthread.benchmarks.material_inventory import (
    BenchmarkMaterialInventory,
    list_benchmark_material_manifests,
)
from redthread.benchmarks.material_vault import MaterialVaultError


def register_material_inventory_command(material_group: click.Group, console: Console) -> None:
    """Register the prompt-safe reviewed material inventory command."""

    @material_group.command(name="list")
    @click.option("--material-root", default=None, type=click.Path(exists=False))
    @click.option("--collection-id", default=None, help="Optional vault collection id filter.")
    @click.option("--fixture-id", default=None, help="Optional fixture id filter.")
    @click.option(
        "--material-class",
        type=click.Choice(["redacted", "approved_replay_seed"]),
        default=None,
    )
    @click.option("--allowed-target", "allowed_target_id", default=None)
    @click.option("--verify-hashes", is_flag=True, default=False)
    @click.option("--invalid-hashes-only", is_flag=True, default=False)
    @click.option("--require-valid-hashes", is_flag=True, default=False)
    @click.option("--json", "as_json", is_flag=True, default=False)
    def list_materials(
        material_root: str | None,
        collection_id: str | None,
        fixture_id: str | None,
        material_class: str | None,
        allowed_target_id: str | None,
        verify_hashes: bool,
        invalid_hashes_only: bool,
        require_valid_hashes: bool,
        as_json: bool,
    ) -> None:
        """List reviewed material manifests without returning prompt bodies."""
        try:
            inventory = list_benchmark_material_manifests(
                material_root=material_root,
                collection_id=collection_id,
                fixture_id=fixture_id,
                material_class=material_class,
                allowed_target_id=allowed_target_id,
                verify_hashes=verify_hashes or require_valid_hashes,
                invalid_hashes_only=invalid_hashes_only,
            )
        except MaterialVaultError as exc:
            raise click.ClickException(str(exc)) from exc
        if require_valid_hashes and inventory.invalid_hash_count > 0:
            msg = f"invalid material hashes found: {inventory.invalid_hash_count}"
            raise click.ClickException(msg)
        if as_json:
            click.echo(json.dumps(inventory.model_dump(mode="json"), indent=2))
            return
        _print_inventory(console, inventory, verify_hashes, require_valid_hashes, invalid_hashes_only)


def _print_inventory(
    console: Console,
    inventory: BenchmarkMaterialInventory,
    verify_hashes: bool,
    require_valid_hashes: bool,
    invalid_hashes_only: bool,
) -> None:
    console.print("[bold red]REDTHREAD BENCHMARK MATERIAL INVENTORY[/bold red]")
    console.print(f"Manifest count: {inventory.manifest_count}")
    if inventory.fixture_id is not None:
        console.print(f"Fixture filter: {inventory.fixture_id}")
    if inventory.material_class is not None:
        console.print(f"Material class filter: {inventory.material_class}")
    if inventory.allowed_target_id is not None:
        console.print(f"Allowed target filter: {inventory.allowed_target_id}")
    if invalid_hashes_only:
        console.print("Invalid hashes only: true")
    hash_check = verify_hashes or require_valid_hashes or invalid_hashes_only
    console.print(f"Hash check: {'enabled' if hash_check else 'not checked'}")
    console.print(f"Collections: {inventory.collection_counts}")
    console.print(f"Material classes: {inventory.material_class_counts}")
    console.print(f"Hash statuses: {inventory.hash_status_counts}")
    console.print("Raw prompt bodies: not printed or returned")
    for row in inventory.manifests:
        console.print(
            f"- {row.collection_id} | {row.fixture_id} | {row.material_class} | "
            f"{row.hash_status} | {row.manifest_ref}"
        )
