"""Custom policy conversion helpers for campaign planning."""

from __future__ import annotations

from pydantic import BaseModel, Field

from redthread.orchestration.models import RiskCategory, RiskPlugin, TargetType


class CustomPolicyInput(BaseModel):
    """User-supplied business rule that should become a temporary risk plugin."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$", min_length=1)
    text: str = Field(min_length=1)
    name: str = ""
    target_types: list[TargetType] = Field(default_factory=lambda: [TargetType.CHAT_AGENT])
    default_strategy_ids: list[str] = Field(default_factory=lambda: ["static_seed_replay"])
    judge_rubric_id: str = "authorization_bypass"
    owasp_tags: list[str] = Field(default_factory=list)
    nist_tags: list[str] = Field(default_factory=list)


def plugin_from_custom_policy(policy: CustomPolicyInput) -> RiskPlugin:
    """Convert a custom policy into a RedThread-native temporary RiskPlugin."""
    return RiskPlugin(
        id=policy.id,
        name=policy.name or policy.id.replace("_", " ").replace("-", " ").title(),
        category=RiskCategory.CUSTOM_POLICY,
        policy_text=policy.text,
        applicable_target_types=policy.target_types,
        default_strategy_ids=policy.default_strategy_ids,
        judge_rubric_id=policy.judge_rubric_id,
        owasp_tags=policy.owasp_tags,
        nist_tags=policy.nist_tags,
        source="redthread_custom_policy",
    )
