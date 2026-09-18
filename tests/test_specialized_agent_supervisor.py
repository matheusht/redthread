from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from redthread.config.settings import AlgorithmType, RedThreadSettings, TargetBackend
from redthread.models import CampaignConfig, MitreAtlasTactic, Persona, PsychologicalTrigger
from redthread.orchestration.agents.agent_chain import run_specialized_pipeline
from redthread.orchestration.graphs.attack_graph import run_specialized_attack_worker
from redthread.orchestration.graphs.judge_graph import run_judge_worker
from redthread.orchestration.supervisor_nodes import collect_results_node
from redthread.orchestration.supervisor_routing import fan_out_attack_workers


def _settings() -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OLLAMA,
        target_model="llama3.2:3b",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="test-key",
        algorithm=AlgorithmType.AGENT_CHAIN,
        dry_run=False,
    )


def _persona() -> Persona:
    return Persona(
        name="Chain Persona",
        tactic=MitreAtlasTactic.INITIAL_ACCESS,
        technique="AML.T0051",
        cover_story="Routine audit",
        hidden_objective="Test the chain",
        system_prompt="You are an auditor.",
        psychological_triggers=[PsychologicalTrigger.AUTHORITY],
    )


class _RecordingTarget:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    async def send(
        self,
        prompt: str,
        conversation_id: str = "",
        execution_metadata: object | None = None,
    ) -> str:
        self.calls.append((prompt, conversation_id))
        return self.responses.pop(0)


def test_agent_chain_fans_out_to_specialized_worker() -> None:
    persona = _persona()
    config = CampaignConfig(
        objective="agent chain",
        target_system_prompt="guarded target",
        num_personas=1,
    )
    state = {
        "settings_dict": _settings().model_dump(mode="json"),
        "config_dict": config.model_dump(mode="json"),
        "persona_dicts": [persona.model_dump(mode="json")],
    }

    sends = fan_out_attack_workers(state)  # type: ignore[arg-type]

    assert len(sends) == 1
    assert sends[0].node == "specialized_attack_worker"


@pytest.mark.asyncio
async def test_specialized_worker_converts_pipeline_to_attack_result() -> None:
    from redthread.orchestration.agents.specialized_adapter import run_specialized_attack

    state = {
        "persona_dict": _persona().model_dump(mode="json"),
        "target_system_prompt": "guarded target",
        "metadata": {"settings_dict": _settings().model_dump(mode="json")},
    }
    pipeline = {
        "current_phase": "exploit_completed",
        "turns": [
            {"agent": "recon", "probe": "probe", "response": "refusal"},
            {"agent": "social", "pretext": "hello", "response": "ack"},
            {"agent": "exploit", "payload": "request", "response": "blocked"},
        ],
        "is_jailbreak": True,
    }

    with patch(
        "redthread.orchestration.agents.specialized_adapter.run_specialized_pipeline",
        new=AsyncMock(return_value=pipeline),
    ):
        result = await run_specialized_attack(state)

    assert result.trace.algorithm == "agent_chain"
    assert len(result.trace.turns) == 3
    assert result.verdict.is_jailbreak is False
    assert result.trace.metadata["specialized_is_jailbreak"] is True


@pytest.mark.asyncio
async def test_social_and_exploit_target_turns_share_conversation_history() -> None:
    target = _RecordingTarget(["refusal"] * 3 + ["ack", "blocked safely"])
    attacker = _RecordingTarget(["hello auditor", "request"])
    state = {
        "persona_dict": _persona().model_dump(mode="json"),
        "target_system_prompt": "guarded target",
        "metadata": {
            "settings_dict": _settings().model_dump(mode="json"),
            "trace_id": "agent-chain-test",
        },
    }
    with (
        patch("redthread.pyrit_adapters.targets.build_target", return_value=target),
        patch("redthread.pyrit_adapters.targets.build_attacker", return_value=attacker),
    ):
        await run_specialized_pipeline(state)

    assert len({call[1] for call in target.calls[:3]}) == 3
    assert target.calls[0][1] == "agent-chain-test:recon-probe-1"
    assert target.calls[1][1] == "agent-chain-test:recon-probe-2"
    assert target.calls[2][1] == "agent-chain-test:recon-probe-3"
    assert target.calls[3][1] == "agent-chain-test:target"
    assert target.calls[4][1] == target.calls[3][1]


@pytest.mark.asyncio
async def test_specialized_worker_phase_error_reaches_collection_counter() -> None:
    state = {
        "settings_dict": _settings().model_dump(mode="json"),
        "persona_dict": _persona().model_dump(mode="json"),
        "target_system_prompt": "guarded target",
        "rubric_name": "authorization_bypass",
        "result_dict": None,
        "error": None,
    }
    failed_pipeline = {
        "turns": [],
        "is_jailbreak": False,
        "phase_errors": [{"phase": "exploit", "error": "target unavailable"}],
    }
    with patch(
        "redthread.orchestration.agents.specialized_adapter.run_specialized_pipeline",
        new=AsyncMock(return_value=failed_pipeline),
    ):
        output = await run_specialized_attack_worker(state)  # type: ignore[arg-type]

    assert output["result_dict"]["trace"]["outcome"] == "error"
    assert output["error"] == "target unavailable"
    collected = await collect_results_node({"attack_results": [output]})  # type: ignore[arg-type]
    assert collected["attack_worker_total"] == 1
    assert collected["attack_worker_failures"] == 1
    assert collected["errors"] == ["target unavailable"]

    judged = await run_judge_worker({
        "settings_dict": state["settings_dict"],
        "result_dict": output["result_dict"],
        "rubric_name": "authorization_bypass",
        "judged_result_dict": None,
        "is_jailbreak": False,
        "final_score": 0.0,
        "error": output["error"],
    })
    assert judged["judged_result_dict"]["trace"]["outcome"] == "error"
    assert judged["is_jailbreak"] is False
