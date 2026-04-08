"""LangGraph Supervisor — central coordinator for RedThread Phase 4.

Implements a StateGraph with the following macro-workflow:
  generate_personas → fan_out → [attack_worker × N] → collect → judge_worker → route → defense_worker?

Workflow:
  1. `generate_personas`   — Creates adversarial personas from the campaign objective.
  2. Fan-out via Send API  — Spawns one `attack_worker` per persona in parallel.
  3. `collect_results`     — Aggregates attack_worker outputs into the supervisor state.
  4. `judge_workers`       — Runs G-Eval re-evaluation on each result sequentially
                             (can be parallelized in a future iteration).
  5. `route_to_defense`    — Conditional: if any jailbreaks confirmed, route to defense.
  6. `defense_worker`      — Optional: runs Defense Synthesis for confirmed jailbreaks.
  7. `finalize`            — Builds final CampaignResult.

The StateGraph schema is `SupervisorState`. The supervisor exposes a single
`invoke(config)` method that engine.py calls as a facade.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Literal

from langgraph.graph import END, StateGraph
from langgraph.types import Send
from typing_extensions import TypedDict

from redthread.config.settings import RedThreadSettings
from redthread.models import CampaignConfig, CampaignResult

logger = logging.getLogger(__name__)


# ── Supervisor state schema ───────────────────────────────────────────────────

def _merge_lists(a: list, b: list) -> list:
    return a + b


class SupervisorState(TypedDict):
    """Global state flowing through the LangGraph supervisor."""

    settings_dict: dict[str, Any]
    config_dict: dict[str, Any]
    persona_dicts: list[dict[str, Any]]

    # Attack worker outputs — collected via Send fan-out
    attack_results: Annotated[list[dict[str, Any]], _merge_lists]

    # Post-judge results
    judged_results: Annotated[list[dict[str, Any]], _merge_lists]

    # Defense outputs
    defense_records: Annotated[list[dict[str, Any]], _merge_lists]

    # Final
    campaign_result_dict: dict[str, Any] | None
    errors: Annotated[list[str], _merge_lists]


# ── Node functions ────────────────────────────────────────────────────────────

async def generate_personas_node(state: SupervisorState) -> dict[str, Any]:
    """Generate adversarial personas for the campaign objective."""
    from redthread.config.settings import RedThreadSettings
    from redthread.models import CampaignConfig
    from redthread.personas.generator import PersonaGenerator

    settings = RedThreadSettings.model_validate(state["settings_dict"])
    config = CampaignConfig.model_validate(state["config_dict"])

    logger.info("👤 Supervisor: generating %d personas...", config.num_personas)

    gen = PersonaGenerator(settings)
    personas = await gen.generate_batch(
        objective=config.objective,
        count=config.num_personas,
    )

    return {"persona_dicts": [p.model_dump(mode="json") for p in personas]}


def fan_out_attack_workers(state: SupervisorState) -> list[Send]:
    """Fan out one attack_worker per persona using LangGraph Send API."""
    from redthread.orchestration.graphs.attack_graph import AttackWorkerState

    config = state["config_dict"]
    sends = []
    for persona_dict in state["persona_dicts"]:
        worker_state: AttackWorkerState = {
            "settings_dict": state["settings_dict"],
            "persona_dict": persona_dict,
            "target_system_prompt": config.get("target_system_prompt", ""),
            "rubric_name": config.get("rubric_name", "authorization_bypass"),
            "result_dict": None,
            "error": None,
        }
        sends.append(Send("attack_worker", worker_state))

    logger.info("⚡ Supervisor: fanning out %d attack workers...", len(sends))
    return sends


async def collect_results_node(state: SupervisorState) -> dict[str, Any]:
    """Collect all attack_worker outputs — consolidates fan-out results."""
    logger.info(
        "📦 Supervisor: collecting %d attack results...",
        len(state["attack_results"]),
    )
    errors = [
        r.get("error")
        for r in state["attack_results"]
        if r.get("error")
    ]
    return {"errors": errors}


async def judge_all_results_node(state: SupervisorState) -> dict[str, Any]:
    """Run JudgeAgent re-evaluation on all collected attack results."""
    from redthread.orchestration.graphs.judge_graph import run_judge_worker

    judged: list[dict[str, Any]] = []
    errors: list[str] = []

    config = state["config_dict"]

    for raw_result in state["attack_results"]:
        if not raw_result.get("result_dict"):
            continue  # Skip failed workers

        worker_output = await run_judge_worker({
            "settings_dict": state["settings_dict"],
            "result_dict": raw_result["result_dict"],
            "rubric_name": config.get("rubric_name", "authorization_bypass"),
            "judged_result_dict": None,
            "is_jailbreak": False,
            "final_score": 0.0,
            "error": None,
        })

        if worker_output.get("judged_result_dict"):
            judged.append(worker_output["judged_result_dict"])
        if worker_output.get("error"):
            errors.append(worker_output["error"])

    logger.info(
        "🔬 Supervisor: %d results judged | jailbreaks=%d",
        len(judged),
        sum(1 for r in judged if r.get("verdict", {}).get("is_jailbreak")),
    )
    return {"judged_results": judged, "errors": errors}


def route_to_defense(state: SupervisorState) -> Literal["defense_synthesis", "finalize"]:
    """Conditional routing — skip defense synthesis if no jailbreaks confirmed."""
    jailbreaks = [
        r for r in state["judged_results"]
        if r.get("verdict", {}).get("is_jailbreak")
    ]
    if jailbreaks:
        logger.info(
            "🛡️  Supervisor: routing to defense synthesis (%d jailbreaks).",
            len(jailbreaks),
        )
        return "defense_synthesis"
    logger.info("✅ Supervisor: no jailbreaks — routing directly to finalize.")
    return "finalize"


async def defense_synthesis_node(state: SupervisorState) -> dict[str, Any]:
    """Run DefenseWorker for all confirmed jailbreaks."""
    from redthread.orchestration.graphs.defense_graph import run_defense_worker

    records: list[dict[str, Any]] = []
    errors: list[str] = []

    for result_dict in state["judged_results"]:
        if not result_dict.get("verdict", {}).get("is_jailbreak"):
            continue

        worker_output = await run_defense_worker({
            "settings_dict": state["settings_dict"],
            "result_dict": result_dict,
            "defense_deployed": False,
            "guardrail_clause": None,
            "error": None,
        })

        records.append({
            "defense_deployed": worker_output["defense_deployed"],
            "guardrail_clause": worker_output.get("guardrail_clause"),
        })
        if worker_output.get("error"):
            errors.append(worker_output["error"])

    return {"defense_records": records, "errors": errors}


async def finalize_node(state: SupervisorState) -> dict[str, Any]:
    """Assemble the final CampaignResult from all judged results."""
    from datetime import datetime, timezone

    from redthread.models import AttackResult, CampaignConfig, CampaignResult

    config = CampaignConfig.model_validate(state["config_dict"])
    results: list[AttackResult] = []

    for r_dict in state["judged_results"]:
        try:
            results.append(AttackResult.model_validate(r_dict))
        except Exception as exc:
            logger.warning("Failed to deserialize judged result: %s", exc)

    campaign = CampaignResult(
        config=config,
        results=results,
        ended_at=datetime.now(timezone.utc),
    )

    logger.info(
        "✅ Supervisor finalized | ASR=%.1f%% | avg_score=%.2f | runs=%d",
        campaign.attack_success_rate * 100,
        campaign.average_score,
        len(campaign.results),
    )

    return {"campaign_result_dict": campaign.model_dump(mode="json")}


# ── Attack worker adapter (required for fan-out target node) ──────────────────

async def attack_worker_node(state: dict[str, Any]) -> dict[str, Any]:
    """Adapter wrapping run_attack_worker for LangGraph node registration."""
    from redthread.orchestration.graphs.attack_graph import run_attack_worker
    result = await run_attack_worker(state)  # type: ignore[arg-type]
    # The supervisor's attack_results field collects via _merge_lists reducer
    return {"attack_results": [result]}


# ── Graph construction ────────────────────────────────────────────────────────

def build_supervisor_graph() -> StateGraph:
    """Construct and compile the LangGraph supervisor StateGraph."""

    graph = StateGraph(SupervisorState)

    # Register nodes
    graph.add_node("generate_personas", generate_personas_node)
    graph.add_node("attack_worker", attack_worker_node)
    graph.add_node("collect_results", collect_results_node)
    graph.add_node("judge_all", judge_all_results_node)
    graph.add_node("defense_synthesis", defense_synthesis_node)
    graph.add_node("finalize", finalize_node)

    # Entry point
    graph.set_entry_point("generate_personas")

    # Sequential edges
    graph.add_conditional_edges(
        "generate_personas",
        fan_out_attack_workers,  # Returns list[Send] — fan-out
        ["attack_worker"],
    )
    graph.add_edge("attack_worker", "collect_results")
    graph.add_edge("collect_results", "judge_all")

    # Conditional routing after judge
    graph.add_conditional_edges(
        "judge_all",
        route_to_defense,
        {
            "defense_synthesis": "defense_synthesis",
            "finalize": "finalize",
        },
    )
    graph.add_edge("defense_synthesis", "finalize")
    graph.add_edge("finalize", END)

    return graph


class RedThreadSupervisor:
    """Facade over the compiled LangGraph supervisor graph.

    Usage (from engine.py)::

        supervisor = RedThreadSupervisor(settings)
        campaign_result = await supervisor.invoke(config)
    """

    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings
        self._graph = build_supervisor_graph().compile()

    async def invoke(self, config: CampaignConfig) -> CampaignResult:
        """Execute the full campaign via the LangGraph supervisor."""
        from datetime import datetime, timezone

        from redthread.core.guardrail_loader import GuardrailLoader

        loader = GuardrailLoader(self.settings)
        injected_config = loader.inject_guardrails(config)

        initial_state: SupervisorState = {
            "settings_dict": self.settings.model_dump(mode="json"),
            "config_dict": injected_config.model_dump(mode="json"),
            "persona_dicts": [],
            "attack_results": [],
            "judged_results": [],
            "defense_records": [],
            "campaign_result_dict": None,
            "errors": [],
        }

        logger.info(
            "🚀 Supervisor.invoke | objective=%s | algorithm=%s | personas=%d",
            config.objective,
            self.settings.algorithm.value,
            config.num_personas,
        )

        final_state = await self._graph.ainvoke(initial_state)

        if final_state.get("errors"):
            logger.warning(
                "Supervisor completed with %d error(s): %s",
                len(final_state["errors"]),
                final_state["errors"][:3],
            )

        # Deserialize final CampaignResult
        if final_state.get("campaign_result_dict"):
            return CampaignResult.model_validate(final_state["campaign_result_dict"])

        # Fallback empty result
        return CampaignResult(
            config=injected_config,
            ended_at=datetime.now(timezone.utc),
        )
