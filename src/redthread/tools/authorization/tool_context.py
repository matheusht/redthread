"""Helpers for optional authorization actions carried in tool context metadata."""

from __future__ import annotations

from redthread.orchestration.models import ActionEnvelope
from redthread.tools.base import ToolContext

AUTHORIZATION_ACTION_METADATA_KEY = "authorization_action"


def get_authorization_action(ctx: ToolContext) -> ActionEnvelope | None:
    raw_action = ctx.metadata.get(AUTHORIZATION_ACTION_METADATA_KEY)
    if raw_action is None:
        return None
    return ActionEnvelope.model_validate(raw_action)
