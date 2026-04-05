"""Shared helpers for proposal-scoped promotion replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_synthesis import DeploymentRecord
from redthread.memory.index import MemoryIndex
from redthread.research.models import PhaseThreeProposal
from redthread.research.workspace import ResearchWorkspace


def proposal_fingerprint(proposal: PhaseThreeProposal) -> str:
    payload = f"{proposal.proposal_id}:{proposal.session_tag}:{proposal.session_base_commit}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def promotion_id_for(proposal: PhaseThreeProposal) -> str:
    return f"promotion-{proposal_fingerprint(proposal)}"


def control_limit(kind: str, proposal: PhaseThreeProposal) -> float:
    config_path = Path(proposal.runtime_config_path)
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        return float(payload.get(f"control_max_average_{kind}", 0.0))
    control = next((item for item in proposal.cycle.lane_summaries if item.lane == "control"), None)
    if control is None:
        return 0.0
    return control.average_asr if kind == "asr" else control.average_score


def eligible_records(
    settings: RedThreadSettings,
    workspace: ResearchWorkspace,
    proposal: PhaseThreeProposal,
) -> dict[str, DeploymentRecord]:
    source_index = MemoryIndex(workspace.research_settings(settings))
    eligible = set(proposal.eligible_trace_ids)
    records: dict[str, DeploymentRecord] = {}
    for record in source_index.iter_deployments():
        if eligible and record.trace_id not in eligible:
            continue
        if record.validation.passed:
            records[record.trace_id] = record
    return records
