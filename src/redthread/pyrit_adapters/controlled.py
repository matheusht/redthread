"""Fail-closed controlled live adapter wrapper for Phase 8E."""

from __future__ import annotations

from pydantic import BaseModel

from redthread.orchestration.models import ActionEnvelope, AuthorizationDecision
from redthread.pyrit_adapters.targets import RedThreadTarget
from redthread.tools.authorization import authorize_live_action
from redthread.tools.authorization.models import AuthorizationPolicy


class LiveAdapterGate(BaseModel):
    enabled: bool = False
    approval_id: str | None = None
    replay_bundle_id: str | None = None


class LiveAuthorizationInterceptionError(RuntimeError):
    def __init__(self, decision: AuthorizationDecision) -> None:
        self.decision = decision
        super().__init__(f"controlled live adapter blocked action: {decision.decision.value}")


class ControlledLiveAdapter:
    def __init__(
        self,
        target: RedThreadTarget,
        gate: LiveAdapterGate,
        *,
        policies: list[AuthorizationPolicy] | None = None,
    ) -> None:
        self._target = target
        self._gate = gate
        self._policies = policies

    async def send(
        self,
        prompt: str,
        conversation_id: str = "",
        *,
        action: ActionEnvelope | None = None,
    ) -> str:
        if not self._gate.enabled or not self._gate.approval_id:
            raise RuntimeError("controlled live adapter is locked")
        if action is not None:
            decision = authorize_live_action(action, policies=self._policies)
            if decision.decision.value != "allow":
                raise LiveAuthorizationInterceptionError(decision)
        return await self._target.send(prompt, conversation_id)
