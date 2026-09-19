"""Launch replay provenance checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from redthread.core.defense_evidence import LIVE_BASELINE_REPLAY

from .models import LaunchReplayEvidence


def replay_status(metadata: Mapping[str, Any], finding_trace_ids: set[str], clean_trace_ids: set[str], scope_hash: str) -> tuple[bool, bool]:
    """Read baseline plus applicable candidate facts; scores cannot imply replay."""
    baseline = (
        baseline_replay_status(metadata.get("launch_readiness_replay"), clean_trace_ids, scope_hash)
        if clean_trace_ids else (True, True)
    )
    if not finding_trace_ids:
        return baseline
    replay_checks: list[bool] = []
    benign_checks: list[bool] = []
    records = metadata.get("defense_records", [])
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        return False, False
    matching_ids: set[str] = set()
    for record in records:
        if not isinstance(record, Mapping) or str(record.get("trace_id", "")) not in finding_trace_ids:
            continue
        matching_ids.add(str(record.get("trace_id", "")))
        validation = record.get("validation")
        cases = validation.get("replay_cases", []) if isinstance(validation, Mapping) else []
        if not isinstance(validation, Mapping) or not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)):
            replay_checks.append(False)
            benign_checks.append(False)
            continue
        rows = [case for case in cases if isinstance(case, Mapping)]
        exploit = [case for case in rows if case.get("kind") == "exploit"]
        benign = [case for case in rows if case.get("kind") == "benign"]
        live_validation = validation.get("evidence_mode") == "live_replay"
        replay_checks.append(live_validation and bool(exploit) and validation.get("exploit_replay_passed") is True and all(case.get("passed") is True for case in exploit))
        benign_checks.append(live_validation and bool(benign) and validation.get("benign_passed") is True and all(case.get("passed") is True for case in benign))
    if matching_ids != finding_trace_ids:
        return False, False
    return baseline[0] and all(replay_checks), baseline[1] and all(benign_checks)


def baseline_replay_status(value: Any, trace_ids: set[str], scope_hash: str) -> tuple[bool, bool]:
    if not isinstance(value, Mapping):
        return False, False
    try:
        evidence = LaunchReplayEvidence.model_validate(value)
    except ValueError:
        return False, False
    if evidence.evidence_mode != LIVE_BASELINE_REPLAY:
        return False, False
    if trace_ids and not trace_ids.issubset(set(evidence.trace_ids)):
        return False, False
    if evidence.scope_hash != scope_hash:
        return False, False
    exploit = [case for case in evidence.replay_cases if case.get("kind") == "exploit"]
    benign = [case for case in evidence.replay_cases if case.get("kind") == "benign"]
    return evidence.exploit_replay_passed and bool(exploit) and all(case.get("passed") is True for case in exploit), evidence.benign_passed and bool(benign) and all(case.get("passed") is True for case in benign)


__all__ = ["baseline_replay_status", "replay_status"]
