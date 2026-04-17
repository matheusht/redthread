"""SandboxTool — proxy-injects a guardrail clause into the target execution path.

Used by DefenseSynthesisEngine's Validate step to replay an exact attack
payload through a patched system prompt without mutating production state.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from redthread.tools.authorization import authorize_live_action
from redthread.tools.authorization.tool_context import get_authorization_action
from redthread.tools.base import RedThreadTool, ToolContext, ToolResult


class SandboxInput(BaseModel):
    """Input schema for the SandboxTool."""

    attack_payload: str = Field(
        description="The original adversarial prompt to replay."
    )
    guardrail_clause: str = Field(
        description="The guardrail text to inject before forwarding to the target."
    )
    trace_id: str = Field(
        default="",
        description="Trace ID for correlation logging.",
    )
    rubric_name: str = Field(
        default="authorization_bypass",
        description="Rubric to use for residual scoring.",
    )


class SandboxTool(RedThreadTool[SandboxInput]):
    """Replays an attack payload against a guardrail-patched target proxy.

    Workflow:
      1. Clone current settings with `guardrail_clause` appended to the
         target system prompt (in-memory only — no disk write).
      2. Build a patched `RedThreadTarget` from the cloned settings.
      3. Send `attack_payload` through the patched target.
      4. Score the response with JudgeAgent inline evaluation.
      5. Return residual score so the caller can decide pass/fail.
    """

    name = "sandbox_replay"
    description = (
        "Replay an adversarial payload through a proxy-patched target system prompt "
        "to validate that a proposed guardrail clause neutralizes the attack. "
        "Returns the residual judge score — low score means the guardrail worked."
    )
    is_read_only = False
    is_destructive = True  # Spins up a temporary live LLM call

    async def call(self, data: SandboxInput, ctx: ToolContext) -> ToolResult:
        from redthread.evaluation.judge import JudgeAgent
        from redthread.models import ConversationTurn
        from redthread.pyrit_adapters.targets import build_target

        if ctx.dry_run:
            return ToolResult.ok(
                data={
                    "replay_response": "[dry-run] Guardrail blocked the replay.",
                    "residual_score": 1.0,
                    "passed": True,
                },
                trace_id=data.trace_id,
            )

        patched_prompt = (
            f"[GUARDRAIL CONTEXT: Your system policy now includes: {data.guardrail_clause}]\n\n"
            + data.attack_payload
        )
        conversation_id = f"sandbox-{data.trace_id or ctx.campaign_id}"
        action = get_authorization_action(ctx)
        decision = authorize_live_action(action) if action is not None else None
        if decision is not None and decision.decision.value != "allow":
            return ToolResult.err(
                error=f"Authorization blocked sandbox tool: {decision.decision.value}",
                trace_id=data.trace_id,
                authorization_decision=decision.model_dump(mode="json"),
            )

        # Inject guardrail as a prompt-level prefix (no settings mutation needed)
        patched_target = build_target(ctx.settings)
        judge = JudgeAgent(ctx.settings)

        try:
            replay_response = await patched_target.send(
                prompt=patched_prompt,
                conversation_id=conversation_id,
            )
        except Exception as exc:
            return ToolResult.err(
                error=f"Patched target send failed: {exc}",
                trace_id=data.trace_id,
            )

        replay_turn = ConversationTurn(
            turn_number=1,
            attacker_prompt=data.attack_payload,
            target_response=replay_response,
        )
        residual_score = judge.evaluate_turn(replay_turn, rubric_name=data.rubric_name)
        passed = residual_score < ctx.settings.success_threshold

        meta = {
            "trace_id": data.trace_id,
            "conversation_id": conversation_id,
        }
        if decision is not None:
            meta["authorization_decision"] = decision.model_dump(mode="json")

        return ToolResult.ok(
            data={
                "replay_response": replay_response,
                "residual_score": residual_score,
                "passed": passed,
            },
            **meta,
        )
