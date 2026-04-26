"""Registry for RedThread risk plugins."""

from __future__ import annotations

import builtins
from collections.abc import Iterable

from redthread.orchestration.models import RiskCategory, RiskPlugin, TargetType


class RiskPluginRegistry:
    """In-memory registry for RedThread-native risk plugins."""

    def __init__(self, plugins: Iterable[RiskPlugin] = ()) -> None:
        self._plugins: dict[str, RiskPlugin] = {}
        for plugin in plugins:
            self.register(plugin)

    def register(self, plugin: RiskPlugin, *, replace: bool = False) -> None:
        """Register a plugin, protecting against accidental duplicate ids."""
        if plugin.id in self._plugins and not replace:
            msg = f"risk plugin already registered: {plugin.id}"
            raise ValueError(msg)
        self._plugins[plugin.id] = plugin

    def get(self, plugin_id: str) -> RiskPlugin:
        """Return a plugin by id, or raise a clear KeyError."""
        try:
            return self._plugins[plugin_id]
        except KeyError as exc:
            msg = f"unknown risk plugin: {plugin_id}"
            raise KeyError(msg) from exc

    def list(self) -> builtins.list[RiskPlugin]:
        """Return plugins sorted by stable id."""
        return [self._plugins[key] for key in sorted(self._plugins)]

    def ids(self) -> builtins.list[str]:
        """Return sorted plugin ids."""
        return [plugin.id for plugin in self.list()]

    def filter(
        self,
        *,
        category: RiskCategory | None = None,
        target_type: TargetType | None = None,
        framework_tag: str | None = None,
    ) -> builtins.list[RiskPlugin]:
        """Return plugins matching all supplied filters."""
        plugins = self.list()
        if category is not None:
            plugins = [plugin for plugin in plugins if plugin.category == category]
        if target_type is not None:
            plugins = [plugin for plugin in plugins if plugin.applies_to(target_type)]
        if framework_tag is not None:
            plugins = [plugin for plugin in plugins if plugin.has_framework_tag(framework_tag)]
        return plugins
