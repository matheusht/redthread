"""CLI init flow for first-run RedThread setup."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@dataclass(frozen=True)
class InitResult:
    env_path: Path
    log_dir: Path
    memory_dir: Path
    env_created: bool


def run_init(console: Console, env_file: str, *, force: bool = False) -> int:
    result = initialize_workspace(env_file, force=force)
    render_init_report(console, result)
    return 0


def initialize_workspace(env_file: str, *, force: bool = False) -> InitResult:
    env_path = Path(env_file)
    example_path = Path(".env.example")

    env_created = False
    if force or not env_path.exists():
        if example_path.exists():
            shutil.copyfile(example_path, env_path)
        else:
            env_path.write_text("", encoding="utf-8")
        env_created = True

    log_dir = Path("logs")
    memory_dir = Path("memory")
    log_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)

    return InitResult(
        env_path=env_path,
        log_dir=log_dir,
        memory_dir=memory_dir,
        env_created=env_created,
    )


def render_init_report(console: Console, result: InitResult) -> None:
    console.print(
        Panel.fit(
            "[bold red]REDTHREAD INIT[/bold red]\n[dim]Local workspace bootstrap[/dim]",
            border_style="red",
        )
    )

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]Env file[/dim]", str(result.env_path))
    table.add_row(
        "[dim]Env action[/dim]",
        "created from .env.example" if result.env_created else "kept existing file",
    )
    table.add_row("[dim]Logs dir[/dim]", str(result.log_dir))
    table.add_row("[dim]Memory dir[/dim]", str(result.memory_dir))
    console.print(table)
    console.print()
    console.print(
        Panel(
            "[bold]Next steps[/bold]\n\n"
            "1. Fill in your API keys in `.env` if needed\n"
            "2. Run `redthread doctor`\n"
            "3. Run `redthread` to see the home screen\n"
            "4. Run `redthread run --dry-run ...` for a safe smoke test",
            border_style="cyan",
            title="Ready",
        )
    )
