"""Tool base class — modeled after Claude Code's Tool.ts.

Every operation in RedThread is a typed, schema-validated tool with:
  - Pydantic input schema (≈ Zod schema in TypeScript)
  - Permission check hook
  - Input validation
  - is_read_only / is_destructive flags
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from redthread.config.settings import RedThreadSettings

InputT = TypeVar("InputT", bound=BaseModel)


@dataclass
class ToolContext:
    """Runtime context passed into every tool call."""

    settings: RedThreadSettings
    campaign_id: str
    dry_run: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    is_valid: bool
    error: str | None = None


@dataclass
class PermissionResult:
    allowed: bool
    reason: str | None = None


@dataclass
class ToolResult:
    success: bool
    data: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any = None, **meta: Any) -> "ToolResult":
        return cls(success=True, data=data, metadata=meta)

    @classmethod
    def err(cls, error: str, **meta: Any) -> "ToolResult":
        return cls(success=False, error=error, metadata=meta)


class RedThreadTool(ABC, Generic[InputT]):
    """Base class for all RedThread tools.

    Subclasses must implement:
      - input_schema: Type[InputT]  — Pydantic model for input
      - call()                      — the actual tool logic

    Optionally override:
      - validate_input()    — extra validation beyond Pydantic
      - check_permissions() — permission gates
    """

    name: str
    description: str
    is_read_only: bool = False
    is_destructive: bool = False
    max_result_size_chars: int = 50_000

    async def validate_input(self, data: InputT) -> ValidationResult:
        """Override for additional validation beyond Pydantic schema."""
        return ValidationResult(is_valid=True)

    async def check_permissions(
        self, data: InputT, ctx: ToolContext
    ) -> PermissionResult:
        """Override to add permission gates. Default: always allowed."""
        if self.is_destructive and ctx.dry_run:
            return PermissionResult(
                allowed=False,
                reason=f"Tool '{self.name}' is destructive and dry_run=True",
            )
        return PermissionResult(allowed=True)

    @abstractmethod
    async def call(self, data: InputT, ctx: ToolContext) -> ToolResult:
        """Execute the tool. Always implement this."""
        ...

    async def run(self, data: InputT, ctx: ToolContext) -> ToolResult:
        """Full pipeline: validate → check permissions → call."""
        validation = await self.validate_input(data)
        if not validation.is_valid:
            return ToolResult.err(f"Validation failed: {validation.error}")

        permission = await self.check_permissions(data, ctx)
        if not permission.allowed:
            return ToolResult.err(f"Permission denied: {permission.reason}")

        return await self.call(data, ctx)
