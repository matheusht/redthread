"""Fail-closed controlled live adapter wrapper for Phase 8E."""

from __future__ import annotations

from pydantic import BaseModel

from redthread.pyrit_adapters.targets import RedThreadTarget


class LiveAdapterGate(BaseModel):
    enabled: bool = False
    approval_id: str | None = None
    replay_bundle_id: str | None = None


class ControlledLiveAdapter:
    def __init__(self, target: RedThreadTarget, gate: LiveAdapterGate) -> None:
        self._target = target
        self._gate = gate

    async def send(self, prompt: str, conversation_id: str = "") -> str:
        if not self._gate.enabled or not self._gate.approval_id:
            raise RuntimeError("controlled live adapter is locked")
        return await self._target.send(prompt, conversation_id)
