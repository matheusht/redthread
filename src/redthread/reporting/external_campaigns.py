"""Candidate campaign artifacts derived from weak external evidence."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from redthread.reporting.external_evidence import CandidateProbeSeed, ExternalEvidenceBundle


class ExternalEvidenceCampaignCandidates(BaseModel):
    """Candidate campaign/probe artifact from weak imported evidence."""

    schema_version: str = "redthread.external_campaign_candidates.v1"
    source_bundle_schema: str
    source: str
    objective: str
    risk_ids: list[str] = Field(default_factory=lambda: ["imported_external_evidence"])
    strategy_ids: list[str] = Field(default_factory=lambda: ["static_seed_replay"])
    probe_seeds: list[CandidateProbeSeed] = Field(default_factory=list)
    campaign_config_hint: dict[str, Any]
    limitations: list[str] = Field(default_factory=lambda: [
        "Candidate campaigns are planning hints only.",
        "Imported evidence remains weak until JudgeAgent confirms a RedThread attack result.",
        "This artifact does not create findings or regression cases.",
    ])


def campaign_candidates_from_external_evidence(
    bundle: ExternalEvidenceBundle,
    *,
    objective: str | None = None,
    max_seeds: int | None = None,
) -> ExternalEvidenceCampaignCandidates:
    """Convert weak imported evidence into candidate probe seeds and config hints."""
    seeds = [item.candidate_probe_seed for item in bundle.items if item.candidate_probe_seed is not None]
    selected = seeds[:max_seeds] if max_seeds is not None else seeds
    campaign_objective = objective or _default_objective(bundle)
    return ExternalEvidenceCampaignCandidates(
        source_bundle_schema=bundle.schema_version,
        source=bundle.source.value,
        objective=campaign_objective,
        probe_seeds=selected,
        campaign_config_hint=_campaign_config_hint(campaign_objective, bundle.source.value, selected),
    )


def _default_objective(bundle: ExternalEvidenceBundle) -> str:
    return f"Evaluate weak imported {bundle.source.value} evidence with RedThread JudgeAgent confirmation."


def _campaign_config_hint(
    objective: str,
    source: str,
    seeds: list[CandidateProbeSeed],
) -> dict[str, Any]:
    examples = [seed.prompt for seed in seeds]
    return {
        "objective": objective,
        "risks": [
            {
                "custom_policy": {
                    "id": f"imported_{source}_evidence",
                    "name": f"Imported {source} evidence",
                    "text": objective,
                    "default_strategy_ids": ["static_seed_replay"],
                }
            }
        ],
        "strategies": {"include": ["static_seed_replay"]},
        "probe_seed_examples": examples,
        "safety_note": "Run these as RedThread probes; do not treat imported evidence as a finding.",
    }


__all__ = ["ExternalEvidenceCampaignCandidates", "campaign_candidates_from_external_evidence"]
