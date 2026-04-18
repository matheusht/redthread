from __future__ import annotations

import json

from redthread.config.settings import RedThreadSettings
from redthread.models import CampaignResult
from redthread.runtime_modes import campaign_runtime_mode, telemetry_runtime_mode


def write_transcript(settings: RedThreadSettings, campaign: CampaignResult) -> None:
    transcript_path = settings.log_dir / f"{campaign.id}.jsonl"
    with transcript_path.open("w", encoding="utf-8") as handle:
        _write_summary_line(settings, campaign, handle)
        for result in campaign.results:
            handle.write(json.dumps(_build_attack_result_line(result)) + "\n")
        if campaign.metadata.get("asi_report"):
            handle.write(json.dumps(_build_asi_line(campaign)) + "\n")


def _write_summary_line(settings: RedThreadSettings, campaign: CampaignResult, handle: object) -> None:
    runtime_summary = campaign.metadata.get("runtime_summary", {})
    summary = {
        "type": "campaign_result",
        "id": campaign.id,
        "objective": campaign.config.objective,
        "algorithm": settings.algorithm.value,
        "target_model": settings.target_model,
        "attacker_model": settings.attacker_model,
        "judge_model": settings.judge_model,
        "runtime_mode": campaign.metadata.get("runtime_mode", campaign_runtime_mode(settings)),
        "telemetry_mode": campaign.metadata.get("telemetry_mode", telemetry_runtime_mode(settings)),
        "degraded_runtime": campaign.metadata.get("degraded_runtime", False),
        "error_count": campaign.metadata.get("error_count", 0),
        "runtime_summary": runtime_summary,
        "execution_truth_summary": campaign.metadata.get("execution_truth_summary", {}),
        "execution_records_sample": campaign.metadata.get("execution_records_sample", []),
        "agentic_security_report": campaign.metadata.get("agentic_security_report", {}),
        "num_runs": len(campaign.results),
        "attack_success_rate": campaign.attack_success_rate,
        "average_score": campaign.average_score,
        "started_at": campaign.started_at.isoformat(),
        "ended_at": campaign.ended_at.isoformat() if campaign.ended_at else None,
    }
    handle.write(json.dumps(summary) + "\n")


def _build_attack_result_line(result: object) -> dict[str, object]:
    line = {
        "type": "attack_result",
        "result_id": result.id,
        "persona_name": result.trace.persona.name,
        "tactic": result.trace.persona.tactic.value,
        "outcome": result.trace.outcome.value,
        "score": result.verdict.score,
        "is_jailbreak": result.verdict.is_jailbreak,
        "iterations": result.iterations_used,
        "duration_seconds": result.duration_seconds,
        "reasoning": result.verdict.reasoning,
        "feedback": result.verdict.feedback,
        "judge_runtime_status": result.trace.metadata.get("judge_runtime_status"),
        "judge_error": result.trace.metadata.get("judge_error"),
        "turns": [
            {
                "turn": turn.turn_number,
                "attacker": turn.attacker_prompt[:200],
                "target": turn.target_response[:200],
                "improvement": turn.improvement_rationale,
            }
            for turn in result.trace.turns
        ],
    }
    if result.trace.nodes:
        line["tree_stats"] = {
            "total_nodes": len(result.trace.nodes),
            "pruned_nodes": sum(1 for node in result.trace.nodes if node.is_pruned),
            "max_depth_reached": max((node.depth for node in result.trace.nodes), default=0),
        }
        line["winning_path"] = [
            {"depth": node.depth, "prompt": node.attacker_prompt[:150], "score": node.score}
            for node in result.trace.nodes
            if not node.is_pruned
        ]
    if result.trace.mcts_nodes:
        line.update(_build_mcts_line(result))
    return line


def _build_mcts_line(result: object) -> dict[str, object]:
    visited = [node for node in result.trace.mcts_nodes if node.depth > 0 and node.visit_count > 0]
    best = max(visited, key=lambda node: node.total_reward / node.visit_count) if visited else None
    node_map = {node.id: node for node in result.trace.mcts_nodes}
    winning_path = []
    if best:
        current = best
        while current and current.depth > 0:
            winning_path.append(current)
            current = node_map.get(current.parent_id or "")
        winning_path.reverse()
    return {
        "mcts_stats": {
            "total_nodes": len(result.trace.mcts_nodes),
            "tokens_consumed": result.trace.metadata.get("tokens_consumed", 0),
            "max_depth_reached": max((node.depth for node in result.trace.mcts_nodes), default=0),
        },
        "mcts_winning_path": [
            {"depth": node.depth, "strategy": node.strategy, "score": node.score}
            for node in winning_path
        ],
    }


def _build_asi_line(campaign: CampaignResult) -> dict[str, object]:
    report = campaign.metadata["asi_report"]
    return {
        "type": "asi_report",
        "campaign_id": campaign.id,
        "asi_score": report["overall_score"],
        "health_tier": report["health_tier"],
        "is_alert": report["is_alert"],
        "response_consistency": report["response_consistency"],
        "semantic_drift": report["semantic_drift"],
        "operational_health": report["operational_health"],
        "behavioral_stability": report["behavioral_stability"],
        "anomaly_count": sum(1 for anomaly in report["anomalies"] if anomaly["is_anomaly"]),
        "organic_records": report["metadata"].get("organic_records", 0),
        "canary_records": report["metadata"].get("canary_records", 0),
        "baseline_fitted": report["metadata"].get("baseline_fitted", False),
        "semantic_drift_mode": report["metadata"].get("semantic_drift_mode", "unknown"),
        "response_consistency_mode": report["metadata"].get("response_consistency_mode", "unknown"),
        "evidence_warnings": report["metadata"].get("evidence_warnings", []),
        "recommendation": report["recommendation"],
    }
