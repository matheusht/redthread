"""Campaign planning parser for Slice 2 tool-technology incorporation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from redthread.core.plugins import (
    CustomPolicyInput,
    RiskPluginRegistry,
    default_risk_plugin_registry,
    plugin_from_custom_policy,
)
from redthread.core.strategies import AttackStrategyRegistry, default_attack_strategy_registry
from redthread.orchestration.models import (
    AttackStrategySpec,
    AuthorizedScope,
    CampaignPlan,
    CostLevel,
    PlannedRisk,
    RiskCategory,
    RiskPlugin,
    TargetType,
)


class CampaignPlanningError(ValueError):
    """Raised when campaign planning input cannot produce a safe plan."""


def build_campaign_plan(
    config: BaseModel | Mapping[str, Any],
    *,
    plugin_registry: RiskPluginRegistry | None = None,
    strategy_registry: AttackStrategyRegistry | None = None,
) -> CampaignPlan:
    """Build a deterministic campaign plan without executing attacks."""
    data = _config_to_mapping(config)
    plugins = plugin_registry or default_risk_plugin_registry()
    strategies = strategy_registry or default_attack_strategy_registry()

    objective = str(data.get("objective", "")).strip()
    if not objective:
        msg = "campaign objective is required"
        raise CampaignPlanningError(msg)

    risk_plugins = _resolve_risk_plugins(data.get("risks"), objective, plugins)
    include_ids, max_cost = _parse_strategy_selection(data.get("strategies"))
    planned_risks = _select_strategies(risk_plugins, include_ids, max_cost, strategies)
    selected_strategy_specs = _unique_strategy_specs(planned_risks, strategies)

    return CampaignPlan(
        objective=objective,
        target_system_prompt=str(data.get("target_system_prompt", "")),
        rubric_name=str(data.get("rubric_name", "authorization_bypass")),
        num_personas=int(data.get("num_personas", 3)),
        risks=planned_risks,
        strategies=selected_strategy_specs,
        scope=AuthorizedScope.model_validate(data.get("scope") or {}),
    )


def _config_to_mapping(config: BaseModel | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(config, BaseModel):
        return config.model_dump()
    return config


def _resolve_risk_plugins(
    raw_risks: Any,
    objective: str,
    registry: RiskPluginRegistry,
) -> list[RiskPlugin]:
    if not raw_risks:
        return [_legacy_objective_plugin(objective)]
    if not isinstance(raw_risks, list):
        msg = "risks must be a list"
        raise CampaignPlanningError(msg)

    plugins: list[RiskPlugin] = []
    for raw_risk in raw_risks:
        plugins.append(_resolve_one_risk(raw_risk, registry))
    return plugins


def _resolve_one_risk(raw_risk: Any, registry: RiskPluginRegistry) -> RiskPlugin:
    if isinstance(raw_risk, str):
        return _get_plugin(raw_risk, registry)
    if not isinstance(raw_risk, Mapping):
        msg = "risk entries must be strings or mappings"
        raise CampaignPlanningError(msg)
    if "id" in raw_risk:
        return _get_plugin(str(raw_risk["id"]), registry)
    if "custom_policy" in raw_risk:
        policy = CustomPolicyInput.model_validate(raw_risk["custom_policy"])
        return plugin_from_custom_policy(policy)
    msg = "risk mapping must contain 'id' or 'custom_policy'"
    raise CampaignPlanningError(msg)


def _get_plugin(plugin_id: str, registry: RiskPluginRegistry) -> RiskPlugin:
    try:
        return registry.get(plugin_id)
    except KeyError as exc:
        msg = f"unknown risk plugin: {plugin_id}"
        raise CampaignPlanningError(msg) from exc


def _legacy_objective_plugin(objective: str) -> RiskPlugin:
    return RiskPlugin(
        id="legacy_objective",
        name="Legacy objective",
        category=RiskCategory.CUSTOM_POLICY,
        policy_text=objective,
        applicable_target_types=[TargetType.CHAT_AGENT],
        default_strategy_ids=["static_seed_replay"],
        source="redthread_legacy_campaign_config",
    )


def _parse_strategy_selection(raw_strategies: Any) -> tuple[list[str] | None, CostLevel | None]:
    if raw_strategies is None:
        return None, None
    if isinstance(raw_strategies, list):
        return [str(strategy_id) for strategy_id in raw_strategies], None
    if not isinstance(raw_strategies, Mapping):
        msg = "strategies must be a list or mapping"
        raise CampaignPlanningError(msg)

    include = raw_strategies.get("include")
    include_ids = [str(strategy_id) for strategy_id in include] if include is not None else None
    max_cost_raw = raw_strategies.get("max_cost")
    max_cost = CostLevel(max_cost_raw) if max_cost_raw is not None else None
    return include_ids, max_cost


def _select_strategies(
    risk_plugins: list[RiskPlugin],
    include_ids: list[str] | None,
    max_cost: CostLevel | None,
    registry: AttackStrategyRegistry,
) -> list[PlannedRisk]:
    planned: list[PlannedRisk] = []
    for plugin in risk_plugins:
        candidate_ids = include_ids or plugin.default_strategy_ids or ["static_seed_replay"]
        specs = [_get_strategy(strategy_id, registry) for strategy_id in candidate_ids]
        if max_cost is not None:
            specs = [spec for spec in specs if _cost_rank(spec.cost_level) <= _cost_rank(max_cost)]
        compatible = [spec for spec in specs if spec.is_compatible_with(plugin.id)]
        if not compatible:
            msg = f"no compatible strategies selected for risk plugin: {plugin.id}"
            raise CampaignPlanningError(msg)
        planned.append(PlannedRisk(plugin=plugin, strategy_ids=[spec.id for spec in compatible]))
    return planned


def _get_strategy(strategy_id: str, registry: AttackStrategyRegistry) -> AttackStrategySpec:
    try:
        return registry.get(strategy_id)
    except KeyError as exc:
        msg = f"unknown attack strategy: {strategy_id}"
        raise CampaignPlanningError(msg) from exc


def _unique_strategy_specs(
    planned_risks: list[PlannedRisk],
    registry: AttackStrategyRegistry,
) -> list[AttackStrategySpec]:
    selected_ids = sorted({strategy_id for risk in planned_risks for strategy_id in risk.strategy_ids})
    return [registry.get(strategy_id) for strategy_id in selected_ids]


def _cost_rank(cost_level: CostLevel) -> int:
    return {
        CostLevel.LOW: 1,
        CostLevel.MEDIUM: 2,
        CostLevel.HIGH: 3,
    }[cost_level]
