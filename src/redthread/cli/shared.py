"""Shared CLI helpers for RedThread."""

from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from click import Choice, option
from rich.console import Console
from rich.logging import RichHandler

T = TypeVar("T")


def setup_logging(console: Console, verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )


def run_async_command(
    console: Console,
    task_factory: Callable[[], Awaitable[T]],
    *,
    error_label: str,
    verbose: bool = False,
) -> T:
    try:
        return asyncio.run(task_factory())
    except KeyboardInterrupt:
        console.print(f"\n[yellow]{error_label} interrupted.[/yellow]")
        sys.exit(1)
    except Exception as exc:
        console.print(f"\n[bold red]{error_label} failed:[/bold red] {exc}")
        if verbose:
            console.print_exception()
        sys.exit(1)


def research_algorithm_override_option(func: Callable[..., Any]) -> Callable[..., Any]:
    return option(
        "--algorithm",
        type=Choice(["pair", "tap", "crescendo", "mcts"], case_sensitive=False),
        default=None,
        help="Override all selected research objectives for this invocation only.",
    )(func)
