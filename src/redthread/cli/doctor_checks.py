"""Individual check implementations for RedThread CLI doctor."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.error import URLError

from redthread.config.settings import RedThreadSettings, TargetBackend

_DEFAULT_TIMEOUT: Final[float] = 1.5


@dataclass(frozen=True)
class DoctorCheck:
    """Single diagnostic check result."""

    name: str
    status: str
    detail: str


def collect_doctor_checks(settings: RedThreadSettings, env_file: str) -> list[DoctorCheck]:
    """Execute all system, environment, and provider health checks."""
    checks = [
        _python_version_check(),
        _venv_check(),
        _console_script_check(),
        _env_file_check(env_file),
        _writable_dir_check("Logs dir", settings.log_dir),
        _writable_dir_check("Memory dir", settings.memory_dir),
        _openai_key_check(settings),
    ]

    ollama_urls = _ollama_urls(settings)
    if not ollama_urls:
        checks.append(DoctorCheck("Ollama reachability", "info", "no Ollama roles configured"))
    else:
        for url in sorted(ollama_urls):
            checks.append(_ollama_check(url, dry_run=settings.dry_run))
    return checks


def _python_version_check() -> DoctorCheck:
    version = sys.version_info
    if (version.major, version.minor) < (3, 12) or (version.major, version.minor) >= (3, 14):
        return DoctorCheck(
            "Python version",
            "fail",
            f"found {version.major}.{version.minor}; need >=3.12,<3.14",
        )
    return DoctorCheck("Python version", "pass", f"found {version.major}.{version.minor}")


def _venv_check() -> DoctorCheck:
    in_venv = sys.prefix != sys.base_prefix or Path(".venv").exists()
    if in_venv:
        return DoctorCheck("Virtual environment", "pass", "active / synchronized (.venv)")
    return DoctorCheck(
        "Virtual environment",
        "warn",
        "no active .venv found; run `uv sync` to set up dependencies",
    )


def _console_script_check() -> DoctorCheck:
    import redthread.cli_doctor as cli_doctor

    command_path = cli_doctor.shutil.which("redthread")
    if command_path:
        return DoctorCheck("redthread command", "pass", command_path)
    return DoctorCheck(
        "redthread command",
        "warn",
        "not on PATH; run `uv sync` or `uv tool install -e .`",
    )


def _env_file_check(env_file: str) -> DoctorCheck:
    path = Path(env_file)
    if path.exists():
        return DoctorCheck("Env file", "pass", str(path))
    example = Path(".env.example")
    if example.exists():
        return DoctorCheck("Env file", "warn", f"missing {path}; run `redthread init` or copy {example}")
    return DoctorCheck("Env file", "warn", f"missing {path}; run `redthread init`")


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
        return DoctorCheck("OpenAI key", "info", "no OpenAI roles configured")
    if settings.openai_api_key and not settings.openai_api_key.startswith("sk-..."):
        return DoctorCheck("OpenAI key", "pass", "configured")
    if os.getenv("OPENAI_API_KEY"):
        return DoctorCheck("OpenAI key", "pass", "configured via OPENAI_API_KEY")
    if settings.dry_run:
        return DoctorCheck("OpenAI key", "info", "missing in .env (offline/dry-run mode active)")
    return DoctorCheck(
        "OpenAI key",
        "warn",
        "missing or placeholder; set OPENAI_API_KEY in .env or run with --dry-run",
    )


def _ollama_urls(settings: RedThreadSettings) -> set[str]:
    urls: set[str] = set()
    if settings.target_backend == TargetBackend.OLLAMA:
        urls.add(settings.target_base_url.rstrip("/"))
    if settings.attacker_backend == TargetBackend.OLLAMA:
        urls.add(settings.attacker_base_url.rstrip("/"))
    return urls


def _ollama_check(base_url: str, *, dry_run: bool = False) -> DoctorCheck:
    import redthread.cli_doctor as cli_doctor

    try:
        with cli_doctor.urlopen(f"{base_url}/api/tags", timeout=_DEFAULT_TIMEOUT):
            return DoctorCheck("Ollama reachability", "pass", base_url)
    except URLError as exc:
        if dry_run:
            return DoctorCheck(
                "Ollama reachability",
                "info",
                f"{base_url} unreachable (offline/dry-run mode active)",
            )
        return DoctorCheck(
            "Ollama reachability",
            "warn",
            f"{base_url} unreachable ({exc.reason}); start with `ollama serve` or use --dry-run",
        )
