"""CLI commands for weak external evidence import and campaign candidate prep."""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console

from redthread.reporting import (
    ExternalEvidenceBundle,
    ExternalEvidenceSource,
    campaign_candidates_from_external_evidence,
    import_external_evidence_file,
)


def register_evidence_commands(main: click.Group, console: Console) -> None:
    """Register external evidence bridge commands."""

    @main.group()
    def evidence() -> None:
        """Import weak external evidence and prepare candidate campaigns."""

    @evidence.command("import")
    @click.option("--source", type=click.Choice([item.value for item in ExternalEvidenceSource]), required=True)
    @click.option("--input", "input_file", type=click.Path(exists=True, dir_okay=False), required=True)
    @click.option("--output", type=click.Path(dir_okay=False), default="external-evidence.json", show_default=True)
    def import_command(source: str, input_file: str, output: str) -> None:
        """Import external rows as weak RedThread evidence."""
        bundle = import_external_evidence_file(
            Path(input_file),
            source=ExternalEvidenceSource(source),
            output_path=Path(output),
        )
        console.print(
            f"Imported {len(bundle.items)} weak evidence item(s) to {output}. "
            "No findings or regression cases were created."
        )

    @evidence.command("plan")
    @click.option("--input", "input_file", type=click.Path(exists=True, dir_okay=False), required=True)
    @click.option("--output", type=click.Path(dir_okay=False), default="candidate-campaign.json", show_default=True)
    @click.option("--objective", default=None, help="Override candidate campaign objective")
    @click.option("--max-seeds", type=int, default=None, help="Maximum candidate probe seeds to include")
    def plan_command(
        input_file: str,
        output: str,
        objective: str | None,
        max_seeds: int | None,
    ) -> None:
        """Create candidate campaign/probe hints from weak evidence."""
        bundle = ExternalEvidenceBundle.model_validate_json(Path(input_file).read_text(encoding="utf-8"))
        candidates = campaign_candidates_from_external_evidence(
            bundle,
            objective=objective,
            max_seeds=max_seeds,
        )
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(candidates.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(
            f"Wrote {len(candidates.probe_seeds)} candidate probe seed(s) to {output}. "
            "JudgeAgent confirmation is still required."
        )


__all__ = ["register_evidence_commands"]
