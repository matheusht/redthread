"""Deterministic simulated registry for sealed tool-hijack scenarios."""

from __future__ import annotations

from typing import Any

from redthread.tools.fixtures.agentic_security import ToolFixture


class SimulatedToolRegistry:
    def __init__(self) -> None:
        self._fixtures: dict[str, ToolFixture] = {}

    def register(self, fixture: ToolFixture) -> None:
        self._fixtures[fixture["name"]] = fixture

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": fixture["name"],
                "description": fixture["description"],
                "input_schema": fixture["input_schema"],
            }
            for fixture in self._fixtures.values()
        ]

    def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        fixture = self._fixtures[name]
        return {
            "tool_name": name,
            "arguments": arguments,
            "content": fixture.get("return_text", ""),
            "return_sequence": fixture.get("return_sequence", []),
            "suggested_capability": fixture.get("suggested_capability"),
            "canary_tags": fixture.get("canary_tags", []),
        }
