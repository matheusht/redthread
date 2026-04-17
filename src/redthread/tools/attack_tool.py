"""AttackTool — wraps the PyRIT RedThreadTarget send logic as a typed Tool.

Conforms to the RedThreadTool ABC defined in tools/base.py.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from redthread.tools.authorization import authorize_live_action
from redthread.tools.authorization.tool_context import (
    AUTHORIZATION_ACTION_METADATA_KEY,
    get_authorization_action,
)
from redthread.tools.base import RedThreadTool, ToolContext, ToolResult

ATTACK_ACTION_METADATA_KEY = AUTHORIZATION_ACTION_METADATA_KEY


class AttackInput(BaseModel):
    """Input schema for the AttackTool."""

    prompt: str = Field(description="The adversarial prompt to send to the target.")
    conversation_id: str = Field(
        default="",
        description="Unique conversation identifier for PyRIT memory tracking.",
    )
    persona_id: str = Field(
        default="",
        description="Persona ID for logging and traceability.",
    )


class AttackTool(RedThreadTool[AttackInput]):
    """Sends an adversarial prompt to the configured target model.

    This wraps `RedThreadTarget.send()` into the standard Tool Registry API
    so that LangGraph supervisor nodes can invoke attacks via typed tool calls.
    """

    name = "attack"
    description = (
        "Send an adversarial prompt to the target model and return its response. "
        "Used by the supervisor's attack worker to execute individual attack payloads."
    )
    is_read_only = False
    is_destructive = False

    async def call(self, data: AttackInput, ctx: ToolContext) -> ToolResult:
        """Forward the prompt to the target and return the raw response."""
        from redthread.pyrit_adapters.targets import build_target

        if ctx.dry_run:
            return ToolResult.ok(
                data={"response": f"[dry-run] Mock response for: {data.prompt[:60]}..."},
                prompt_len=len(data.prompt),
                persona_id=data.persona_id,
            )

        conversation_id = data.conversation_id or f"attack-tool-{ctx.campaign_id}"
        action = get_authorization_action(ctx)
        decision = authorize_live_action(action) if action is not None else None
        if decision is not None and decision.decision.value != "allow":
            return ToolResult.err(
                error=f"Authorization blocked attack tool: {decision.decision.value}",
                conversation_id=conversation_id,
                authorization_decision=decision.model_dump(mode="json"),
            )

        target = build_target(ctx.settings)

        try:
            response = await target.send(
                prompt=data.prompt,
                conversation_id=conversation_id,
            )
            meta = {
                "conversation_id": conversation_id,
                "persona_id": data.persona_id,
            }
            if decision is not None:
                meta["authorization_decision"] = decision.model_dump(mode="json")
            return ToolResult.ok(
                data={"response": response},
                **meta,
            )
        except Exception as exc:
            return ToolResult.err(
                error=str(exc),
                conversation_id=conversation_id,
            )
