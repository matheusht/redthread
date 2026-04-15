from __future__ import annotations

from redthread.core.defense_assets import BENIGN_DEFENSE_PACK
from redthread.core.defense_replay_artifacts import (
    DEFAULT_BENIGN_REPLAY_CASES,
    DEFAULT_DEFENSE_REPLAY_SUITE_ID,
)
from redthread.core.defense_replay_fixtures import build_default_replay_suite


def test_default_runtime_replay_artifacts_expand_starter_benign_pack() -> None:
    assert DEFAULT_DEFENSE_REPLAY_SUITE_ID == "default-defense-replay-v3"
    assert len(DEFAULT_BENIGN_REPLAY_CASES) > len(BENIGN_DEFENSE_PACK)
    assert any(case.case_id == "json_fields" for case in DEFAULT_BENIGN_REPLAY_CASES)
    assert any(case.case_id == "safety_policy_summary" for case in DEFAULT_BENIGN_REPLAY_CASES)


def test_default_replay_suite_uses_runtime_artifacts() -> None:
    suite = build_default_replay_suite("attack")

    assert suite.suite_id == DEFAULT_DEFENSE_REPLAY_SUITE_ID
    assert len(suite.exploit_cases) == 2
    assert len(suite.benign_cases) == len(DEFAULT_BENIGN_REPLAY_CASES)
    assert any(case.case_id == "exploit_override_probe" for case in suite.exploit_cases)
    assert any(case.case_id == "meeting_timezone" for case in suite.benign_cases)
