"""AttackTool — wraps the PyRIT RedThreadTarget send logic as a typed Tool.

Conforms to the RedThreadTool ABC defined in tools/base.py.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from redthread.tools.base import RedThreadTool, ToolContext, ToolResult


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

        target = build_target(ctx.settings)
        conversation_id = data.conversation_id or f"attack-tool-{ctx.campaign_id}"

        try:
            response = await target.send(
                prompt=data.prompt,
                conversation_id=conversation_id,
            )
            return ToolResult.ok(
                data={"response": response},
                conversation_id=conversation_id,
                persona_id=data.persona_id,
            )
        except Exception as exc:
            return ToolResult.err(
                error=str(exc),
                conversation_id=conversation_id,
            )
