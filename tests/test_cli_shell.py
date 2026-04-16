from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from redthread.cli import main


class _FakeResponse:
    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


def test_bare_redthread_shows_home_screen() -> None:
    result = CliRunner().invoke(main, [])

    assert result.exit_code == 0
    assert "REDTHREAD" in result.output
    assert "Quick commands" in result.output
    assert "redthread doctor" in result.output


def test_init_command_bootstraps_workspace(tmp_path: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=str(tmp_path)):
        Path(".env.example").write_text("REDTHREAD_DRY_RUN=true\n", encoding="utf-8")

        result = runner.invoke(main, ["init"])

        assert result.exit_code == 0
        assert Path(".env").exists()
        assert Path("logs").exists()
        assert Path("memory").exists()
        assert "REDTHREAD INIT" in result.output


def test_doctor_command_reports_ready_when_local_checks_pass(
    monkeypatch: object,
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "REDTHREAD_OPENAI_API_KEY=sk-real-key",
                "REDTHREAD_LOG_DIR=./logs",
                "REDTHREAD_MEMORY_DIR=./memory",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("redthread.cli_doctor.urlopen", lambda *args, **kwargs: _FakeResponse())
    monkeypatch.setattr("redthread.cli_doctor.shutil.which", lambda _: "/usr/local/bin/redthread")

    result = CliRunner().invoke(main, ["doctor", "--env-file", str(env_file)])

    assert result.exit_code == 0
    assert "REDTHREAD DOCTOR" in result.output
    assert "Doctor Verdict" in result.output
    assert "READY" in result.output
