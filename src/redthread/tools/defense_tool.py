"""DefenseTool — exposes DefenseSynthesisEngine as a typed destructive Tool.

Marked `is_destructive = True` so that dry-run mode blocks accidental
default-prompt mutations in production.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from redthread.tools.base import RedThreadTool, ToolContext, ToolResult


class DefenseInput(BaseModel):
    """Input schema for the DefenseTool."""

    result_id: str = Field(
        description="ID of the AttackResult to synthesize a defense for."
    )
    attack_result_json: str = Field(
        description="JSON-serialized AttackResult payload (from supervisor state)."
    )


class DefenseTool(RedThreadTool[DefenseInput]):
    """Runs the 5-step Defense Synthesis pipeline for a confirmed jailbreak.

    This is the primary interface between the LangGraph supervisor and the
    DefenseSynthesisEngine. Marked destructive because it can modify the
    effective system prompt via sandbox validation.
    """

    name = "defense_synthesis"
    description = (
        "Run the 5-step Defense Synthesis algorithm (Isolate → Classify → "
        "Generate → Validate → Deploy) for a confirmed jailbreak AttackResult. "
        "Returns a DeploymentRecord with the guardrail clause and validation status."
    )
    is_read_only = False
    is_destructive = True  # sandbox_tool.py injects into target execution path

    async def call(self, data: DefenseInput, ctx: ToolContext) -> ToolResult:
        import json

        from redthread.core.defense_synthesis import DefenseSynthesisEngine
        from redthread.models import AttackResult

        try:
            raw = json.loads(data.attack_result_json)
            result = AttackResult.model_validate(raw)
        except Exception as exc:
            return ToolResult.err(
                error=f"Failed to deserialize AttackResult: {exc}",
                result_id=data.result_id,
            )

        engine = DefenseSynthesisEngine(ctx.settings)
        try:
            record = await engine.run(result)
            return ToolResult.ok(
                data={
                    "trace_id": record.trace_id,
                    "guardrail_clause": record.guardrail_clause,
                    "category": record.classification.category,
                    "severity": record.classification.severity,
                    "validation_passed": record.validation.passed,
                    "exploit_replay_passed": record.validation.exploit_replay_passed,
                    "benign_passed": record.validation.benign_passed,
                    "replay_score": record.validation.judge_score,
                    "benign_checks": [
                        {
                            "case_id": check.case_id,
                            "passed": check.passed,
                            "failure_reason": check.failure_reason,
                        }
                        for check in record.validation.benign_checks
                    ],
                },
                result_id=data.result_id,
            )
        except Exception as exc:
            return ToolResult.err(
                error=f"Defense synthesis failed: {exc}",
                result_id=data.result_id,
            )
