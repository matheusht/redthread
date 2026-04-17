"""CLI doctor checks for local RedThread operator setup."""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.error import URLError
from urllib.request import urlopen

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from redthread.config.settings import RedThreadSettings, TargetBackend

_DEFAULT_TIMEOUT: Final[float] = 1.5


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str


STATUS_STYLE: dict[str, str] = {
    "pass": "green",
    "warn": "yellow",
    "fail": "red",
}
STATUS_LABEL: dict[str, str] = {
    "pass": "PASS",
    "warn": "WARN",
    "fail": "FAIL",
}


def run_doctor(console: Console, settings: RedThreadSettings, env_file: str) -> int:
    checks = collect_doctor_checks(settings, env_file)
    render_doctor_report(console, settings, env_file, checks)
    return 1 if any(check.status == "fail" for check in checks) else 0


def collect_doctor_checks(settings: RedThreadSettings, env_file: str) -> list[DoctorCheck]:
    checks = [
        _python_version_check(),
        _console_script_check(),
        _env_file_check(env_file),
        _logs_dir_check(settings.log_dir),
        _memory_dir_check(settings.memory_dir),
        _openai_key_check(settings),
    ]

    ollama_urls = _ollama_urls(settings)
    if not ollama_urls:
        checks.append(DoctorCheck("Ollama reachability", "warn", "no Ollama roles configured"))
    else:
        for url in sorted(ollama_urls):
            checks.append(_ollama_check(url))
    return checks


def render_doctor_report(
    console: Console,
    settings: RedThreadSettings,
    env_file: str,
    checks: list[DoctorCheck],
) -> None:
    console.print(
        Panel.fit(
            "[bold red]REDTHREAD DOCTOR[/bold red]\n[dim]Local CLI health check[/dim]",
            border_style="red",
        )
    )

    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_row("[dim]Env file[/dim]", env_file)
    summary.add_row("[dim]Algorithm[/dim]", settings.algorithm.value)
    summary.add_row("[dim]Target[/dim]", settings.target_model)
    summary.add_row("[dim]Attacker[/dim]", settings.attacker_model)
    summary.add_row("[dim]Judge[/dim]", settings.judge_model)
    console.print(summary)
    console.print()

    table = Table(title="Checks")
    table.add_column("Status", justify="center")
    table.add_column("Check", style="cyan")
    table.add_column("Detail")

    for check in checks:
        style = STATUS_STYLE[check.status]
        label = STATUS_LABEL[check.status]
        table.add_row(f"[{style}]{label}[/{style}]", check.name, check.detail)

    console.print(table)

    failures = sum(1 for check in checks if check.status == "fail")
    warnings = sum(1 for check in checks if check.status == "warn")
    border = "red" if failures else "yellow" if warnings else "green"
    verdict = "NOT READY" if failures else "READY WITH WARNINGS" if warnings else "READY"
    console.print(
        Panel(
            f"[bold]{verdict}[/bold]\n\nFailures: {failures}\nWarnings: {warnings}",
            border_style=border,
            title="Doctor Verdict",
        )
    )


def _python_version_check() -> DoctorCheck:
    version = sys.version_info
    if (version.major, version.minor) < (3, 12) or (version.major, version.minor) >= (3, 14):
        return DoctorCheck(
            "Python version",
            "fail",
            f"found {version.major}.{version.minor}; need >=3.12,<3.14",
        )
    return DoctorCheck("Python version", "pass", f"found {version.major}.{version.minor}")


def _console_script_check() -> DoctorCheck:
    command_path = shutil.which("redthread")
    if command_path:
        return DoctorCheck("redthread command", "pass", command_path)
    return DoctorCheck(
        "redthread command",
        "warn",
        "not on PATH yet; install with `uv tool install -e .` or `pip install -e .`",
    )


def _env_file_check(env_file: str) -> DoctorCheck:
    path = Path(env_file)
    if path.exists():
        return DoctorCheck("Env file", "pass", str(path))
    example = Path(".env.example")
    if example.exists():
        return DoctorCheck("Env file", "warn", f"missing {path}; copy from {example}")
    return DoctorCheck("Env file", "warn", f"missing {path}")


def _logs_dir_check(path: Path) -> DoctorCheck:
    return _writable_dir_check("Logs dir", path)


def _memory_dir_check(path: Path) -> DoctorCheck:
    return _writable_dir_check("Memory dir", path)


def _writable_dir_check(name: str, path: Path) -> DoctorCheck:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".doctor-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return DoctorCheck(name, "fail", f"{path} not writable: {exc}")
    return DoctorCheck(name, "pass", str(path))


def _openai_key_check(settings: RedThreadSettings) -> DoctorCheck:
    needs_openai = any(
        backend == TargetBackend.OPENAI
        for backend in (
            settings.judge_backend,
            settings.defense_architect_backend,
            settings.target_backend,
            settings.attacker_backend,
        )
    )
    if not needs_openai:
        return DoctorCheck("OpenAI key", "warn", "no OpenAI roles configured")
    if settings.openai_api_key and not settings.openai_api_key.startswith("sk-..."):
        return DoctorCheck("OpenAI key", "pass", "configured")
    if os.getenv("OPENAI_API_KEY"):
        return DoctorCheck("OpenAI key", "pass", "configured via OPENAI_API_KEY")
    return DoctorCheck("OpenAI key", "warn", "missing or placeholder value")


def _ollama_urls(settings: RedThreadSettings) -> set[str]:
    urls: set[str] = set()
    if settings.target_backend == TargetBackend.OLLAMA:
        urls.add(settings.target_base_url.rstrip("/"))
    if settings.attacker_backend == TargetBackend.OLLAMA:
        urls.add(settings.attacker_base_url.rstrip("/"))
    return urls


def _ollama_check(base_url: str) -> DoctorCheck:
    try:
        with urlopen(f"{base_url}/api/tags", timeout=_DEFAULT_TIMEOUT):
            return DoctorCheck("Ollama reachability", "pass", base_url)
    except URLError as exc:
        return DoctorCheck("Ollama reachability", "warn", f"{base_url} unreachable: {exc.reason}")
