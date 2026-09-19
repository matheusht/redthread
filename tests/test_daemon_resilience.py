"""Unit tests for SecurityGuardDaemon resilience and task cancellation (Issues #97, #98)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from redthread.config.settings import RedThreadSettings
from redthread.daemon.monitor import SecurityGuardDaemon
from redthread.telemetry.models import ASIReport


def make_settings(tmp_path: Path) -> RedThreadSettings:
    return RedThreadSettings(
        log_dir=tmp_path / "logs",
        memory_dir=tmp_path / "memory",
        target_model="test-target",
        monitor_probe_interval=1,
    )


@pytest.mark.asyncio
async def test_daemon_tolerates_transient_loop_error(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    daemon = SecurityGuardDaemon(settings)

    daemon._warmup = AsyncMock()

    call_count = 0

    async def flaky_inject(target: object) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionResetError("Transient network drop")
        daemon.stop()

    daemon.collector.inject_canary_batch = flaky_inject

    with patch("redthread.daemon.monitor.AgentStabilityIndex") as mock_asi:
        mock_instance = MagicMock()
        mock_instance.compute.return_value = ASIReport(
            target_model="test",
            window_size=10,
            overall_score=95.0,
            response_consistency=100.0,
            semantic_drift=95.0,
            operational_health=100.0,
            behavioral_stability=90.0,
            alert_threshold=70.0,
            recommendation="Normal",
            is_alert=False,
        )
        mock_asi.return_value = mock_instance

        await asyncio.wait_for(daemon.start(), timeout=5.0)

    assert call_count >= 2


@pytest.mark.asyncio
async def test_daemon_cancels_active_tasks_on_shutdown(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    daemon = SecurityGuardDaemon(settings)

    async def slow_campaign() -> None:
        try:
            await asyncio.sleep(100.0)
        except asyncio.CancelledError:
            pass

    task = asyncio.create_task(slow_campaign())
    daemon._active_tasks.add(task)

    daemon._cancel_active_tasks()
    await asyncio.sleep(0.01)

    assert task.done()
    assert len(daemon._active_tasks) == 0
