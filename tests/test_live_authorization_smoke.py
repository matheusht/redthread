from __future__ import annotations

from redthread.orchestration.models import ActionEnvelope
from redthread.tools.authorization import run_live_authorization_smoke


def test_live_smoke_requires_opt_in(monkeypatch: object) -> None:
    monkeypatch.delenv("REDTHREAD_RUN_LIVE_AUTH_SMOKE", raising=False)
    executed = {"value": False}
    action = ActionEnvelope(
        actor_id="analyst-1",
        actor_role="analyst",
        capability="docs.search",
        tool_name="docs.search",
        target_sensitivity="low",
        provenance={
            "source_kind": "internal_agent",
            "trust_level": "trusted",
            "origin_id": "analyst-1",
        },
        requested_effect="read",
    )

    report = run_live_authorization_smoke(action, lambda: executed.__setitem__("value", True))

    assert report["skipped"] is True
    assert report["executed"] is False
    assert executed["value"] is False


def test_live_smoke_blocks_execution_on_denied_action(monkeypatch: object) -> None:
    monkeypatch.setenv("REDTHREAD_RUN_LIVE_AUTH_SMOKE", "true")
    executed = {"value": False}
    action = ActionEnvelope(
        actor_id="exec-1",
        actor_role="executor",
        capability="memory.write",
        tool_name="memory.write",
        target_sensitivity="medium",
        provenance={
            "source_kind": "external_tool",
            "trust_level": "derived",
            "origin_id": "tool-1",
        },
        requested_effect="write",
    )

    report = run_live_authorization_smoke(action, lambda: executed.__setitem__("value", True))

    assert report["evidence_mode"] == "live_intercept_smoke"
    assert report["executed"] is False
    assert report["decision"]["decision"] == "deny"
    assert executed["value"] is False


def test_live_smoke_executes_allowed_action(monkeypatch: object) -> None:
    monkeypatch.setenv("REDTHREAD_RUN_LIVE_AUTH_SMOKE", "true")
    action = ActionEnvelope(
        actor_id="retriever-1",
        actor_role="retriever",
        capability="tool.read",
        tool_name="tool.read",
        target_sensitivity="low",
        provenance={
            "source_kind": "internal_agent",
            "trust_level": "trusted",
            "origin_id": "retriever-1",
        },
        requested_effect="read",
    )

    report = run_live_authorization_smoke(action, lambda: {"status": "ok"})

    assert report["evidence_mode"] == "live_intercept_smoke"
    assert report["executed"] is True
    assert report["decision"]["decision"] == "allow"
    assert report["result"] == {"status": "ok"}
