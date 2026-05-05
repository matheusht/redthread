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
    @click.option(
        "--review-gate-status",
        type=click.Choice(["not_required", "two_reviewer_gate_met", "two_reviewer_gate_failed"]),
        default=None,
    )
    @click.option("--limit", type=click.IntRange(min=1), default=None)
    @click.option("--verify-hashes", is_flag=True, default=False, help="Deprecated; hashes are checked by default.")
    @click.option("--skip-hash-check", is_flag=True, default=False)
    @click.option("--invalid-hashes-only", is_flag=True, default=False)
    @click.option("--require-valid-hashes", is_flag=True, default=False)
    @click.option("--json", "as_json", is_flag=True, default=False)
    def list_materials(
        material_root: str | None,
        collection_id: str | None,
        fixture_id: str | None,
        material_class: str | None,
        allowed_target_id: str | None,
        review_gate_status: str | None,
        limit: int | None,
        verify_hashes: bool,
        skip_hash_check: bool,
        invalid_hashes_only: bool,
        require_valid_hashes: bool,
        as_json: bool,
    ) -> None:
        """List reviewed material manifests without returning prompt bodies."""
        hash_check_enabled = not skip_hash_check or verify_hashes or require_valid_hashes or invalid_hashes_only
        try:
            inventory = list_benchmark_material_manifests(
                material_root=material_root,
                collection_id=collection_id,
                fixture_id=fixture_id,
                material_class=material_class,
                allowed_target_id=allowed_target_id,
                review_gate_status=review_gate_status,
                limit=limit,
                verify_hashes=hash_check_enabled,
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
        _print_inventory(console, inventory, hash_check_enabled, invalid_hashes_only)


def _print_inventory(
    console: Console,
    inventory: BenchmarkMaterialInventory,
    hash_check_enabled: bool,
    invalid_hashes_only: bool,
) -> None:
    console.print("[bold red]REDTHREAD BENCHMARK MATERIAL INVENTORY[/bold red]")
    console.print(f"Manifest count: {inventory.manifest_count}")
    console.print(f"Engine decision: {inventory.engine_decision}")
    console.print(f"Operator next step: {inventory.operator_next_step}")
    if inventory.fixture_id is not None:
        console.print(f"Fixture filter: {inventory.fixture_id}")
    if inventory.material_class is not None:
        console.print(f"Material class filter: {inventory.material_class}")
    if inventory.allowed_target_id is not None:
        console.print(f"Allowed target filter: {inventory.allowed_target_id}")
    if inventory.review_gate_status is not None:
        console.print(f"Review gate filter: {inventory.review_gate_status}")
    if inventory.limit is not None:
        console.print(f"Limit: {inventory.limit}")
    if invalid_hashes_only:
        console.print("Invalid hashes only: true")
    console.print(f"Hash check: {'enabled' if hash_check_enabled else 'not checked'}")
    console.print(f"Collections: {inventory.collection_counts}")
    console.print(f"Material classes: {inventory.material_class_counts}")
    console.print(f"Hash statuses: {inventory.hash_status_counts}")
    console.print(f"Review gates: {inventory.review_gate_counts}")
    console.print(f"Ready materials: {inventory.material_ready_count}")
    console.print(f"Blocked materials: {inventory.material_blocked_count}")
    console.print("Raw prompt bodies: not printed or returned")
    for row in inventory.manifests:
        console.print(
            f"- {row.collection_id} | {row.fixture_id} | {row.material_class} | "
            f"{row.review_gate_status} | {row.hash_status} | {row.manifest_ref}"
        )
