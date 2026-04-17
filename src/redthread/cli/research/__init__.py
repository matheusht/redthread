"""Research CLI root registration."""

from __future__ import annotations

import click
from rich.console import Console

from redthread.cli.research.core import register_research_core_commands
from redthread.cli.research.daemon import register_research_daemon_commands
from redthread.cli.research.phase3 import register_research_phase3_commands
from redthread.cli.research.phase4 import register_research_phase4_commands
from redthread.cli.research.phase5 import register_research_phase5_commands
from redthread.cli.research.phase6 import register_research_phase6_commands
from redthread.cli.research.promotion import register_research_promotion_commands


def register_research_commands(main: click.Group, console: Console) -> None:
    @main.group()
    def research() -> None:
        """Phase 1 autoresearch harness commands."""

    register_research_core_commands(research, console)
    register_research_phase3_commands(research, console)
    register_research_phase4_commands(research, console)
    register_research_phase5_commands(research, console)
    register_research_phase6_commands(research, console)
    register_research_daemon_commands(research, console)
    register_research_promotion_commands(research, console)
