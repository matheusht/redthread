"""Weak external evidence bridge models for report import/export prep."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

WEAK_EVIDENCE: Literal["weak_imported_evidence"] = "weak_imported_evidence"


class ExternalEvidenceSource(str, Enum):
    """Supported source labels for imported evidence."""

    PROMPTFOO = "promptfoo"
    GARAK = "garak"
    STRIX = "strix"
    GENERIC = "generic"


class CandidateProbeSeed(BaseModel):
    """Imported prompt candidate that may later seed RedThread testing."""

    source_id: str
    prompt: str
    expected_behavior: str = "JudgeAgent must evaluate before promotion."
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExternalEvidenceItem(BaseModel):
    """One weak imported evidence row from an external tool."""

    source: ExternalEvidenceSource
    source_id: str
    title: str
    description: str = ""
    evidence_strength: Literal["weak_imported_evidence"] = WEAK_EVIDENCE
    is_confirmed_finding: Literal[False] = False
    requires_judge_confirmation: Literal[True] = True
    detector_hint_context: dict[str, Any] = Field(default_factory=dict)
    candidate_probe_seed: CandidateProbeSeed | None = None
    raw: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def reject_confirmed_finding_claims(cls, data: object) -> object:
        """Reject imports that try to claim RedThread finding authority."""
        if isinstance(data, dict):
            if data.get("is_confirmed_finding") is True:
                msg = "external evidence cannot be a confirmed finding"
                raise ValueError(msg)
            if data.get("evidence_strength") not in {None, WEAK_EVIDENCE}:
                msg = "external evidence must remain weak_imported_evidence"
                raise ValueError(msg)
            if data.get("requires_judge_confirmation") is False:
                msg = "external evidence must require JudgeAgent confirmation"
                raise ValueError(msg)
        return data


class ExternalEvidenceBundle(BaseModel):
    """Stable bundle for weak imported evidence."""

    schema_version: str = "redthread.external_evidence_bundle.v1"
    source: ExternalEvidenceSource
    items: list[ExternalEvidenceItem]
    limitations: list[str] = Field(default_factory=lambda: [
        "External evidence is weak imported context, not proof.",
        "JudgeAgent confirmation is required before creating findings or regression cases.",
    ])


def external_evidence_bundle(
    source: ExternalEvidenceSource,
    rows: list[dict[str, Any]],
) -> ExternalEvidenceBundle:
    """Build a weak evidence bundle from normalized dictionaries."""
    return ExternalEvidenceBundle(
        source=source,
        items=[ExternalEvidenceItem(source=source, **row) for row in rows],
    )


def promptfoo_result_to_evidence(row: dict[str, Any]) -> ExternalEvidenceItem:
    """Map a promptfoo-like result row into weak RedThread evidence."""
    prompt = str(row.get("prompt", row.get("vars", {}).get("prompt", "")))
    source_id = str(row.get("id", row.get("testIdx", "promptfoo-result")))
    return ExternalEvidenceItem(
        source=ExternalEvidenceSource.PROMPTFOO,
        source_id=source_id,
        title=str(row.get("description", "promptfoo result")),
        description=str(row.get("error", row.get("reason", ""))),
        detector_hint_context={"pass": row.get("pass"), "score": row.get("score")},
        candidate_probe_seed=_probe_seed(source_id, prompt, row) if prompt else None,
        raw=dict(row),
    )


def garak_result_to_evidence(row: dict[str, Any]) -> ExternalEvidenceItem:
    """Map a garak-like report row into weak RedThread evidence."""
    source_id = str(row.get("entry_id", row.get("probe", "garak-result")))
    prompt = str(row.get("prompt", row.get("attack_prompt", "")))
    return ExternalEvidenceItem(
        source=ExternalEvidenceSource.GARAK,
        source_id=source_id,
        title=str(row.get("probe", "garak probe result")),
        description=str(row.get("detector", row.get("description", ""))),
        detector_hint_context={"detector": row.get("detector"), "score": row.get("score")},
        candidate_probe_seed=_probe_seed(source_id, prompt, row) if prompt else None,
        raw=dict(row),
    )


def strix_finding_to_evidence(row: dict[str, Any]) -> ExternalEvidenceItem:
    """Map a Strix-like appsec finding row into weak RedThread evidence."""
    source_id = str(row.get("finding_id", row.get("id", "strix-finding")))
    objective = str(row.get("objective", row.get("title", "")))
    return ExternalEvidenceItem(
        source=ExternalEvidenceSource.STRIX,
        source_id=source_id,
        title=str(row.get("title", "Strix finding candidate")),
        description=str(row.get("description", row.get("impact", ""))),
        detector_hint_context={"severity": row.get("severity"), "category": row.get("category")},
        candidate_probe_seed=_probe_seed(source_id, objective, row) if objective else None,
        raw=dict(row),
    )


def _probe_seed(source_id: str, prompt: str, row: dict[str, Any]) -> CandidateProbeSeed:
    return CandidateProbeSeed(
        source_id=source_id,
        prompt=prompt,
        metadata={"imported_source_keys": sorted(str(key) for key in row)},
    )


__all__ = [
    "CandidateProbeSeed",
    "ExternalEvidenceBundle",
    "ExternalEvidenceItem",
    "ExternalEvidenceSource",
    "WEAK_EVIDENCE",
    "external_evidence_bundle",
    "garak_result_to_evidence",
    "promptfoo_result_to_evidence",
    "strix_finding_to_evidence",
]
