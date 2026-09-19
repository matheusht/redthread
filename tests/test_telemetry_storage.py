"""Tests for SQLite telemetry storage indexes."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.telemetry.storage import TelemetryStorage


def make_settings(tmp_path: Path) -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OPENAI,
        target_model="gpt-4o",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="sk-test",
        dry_run=True,
    ).model_copy(update={"data_dir": tmp_path})


def test_telemetry_indexes_are_idempotent_and_used_for_model_time_queries(
    tmp_path: Path,
) -> None:
    settings = make_settings(tmp_path)
    storage = TelemetryStorage(settings)
    TelemetryStorage(settings)

    with sqlite3.connect(storage.db_path) as connection:
        indexes = {
            row[1]
            for row in connection.execute("PRAGMA index_list('telemetry_records')")
        }
        query_plan = connection.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT * FROM telemetry_records
            WHERE target_model = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            ("gpt-4o", 50),
        ).fetchall()

    assert indexes >= {"idx_telemetry_model_time", "idx_telemetry_canary"}
    assert any("idx_telemetry_model_time" in row[3] for row in query_plan)


def test_telemetry_storage_creates_composite_indexes(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    storage = TelemetryStorage(settings)

    with storage._connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE 'idx_telemetry_%'"
        )
        indexes = {row[0] for row in cursor.fetchall()}

        assert "idx_telemetry_model_time" in indexes
        assert "idx_telemetry_canary" in indexes

        plan_cursor = conn.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM telemetry_records WHERE target_model = 'gpt-4o' ORDER BY timestamp DESC"
        )
        plan_details = " ".join(row[3] for row in plan_cursor.fetchall())
        assert "idx_telemetry_model_time" in plan_details

        canary_plan = conn.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM telemetry_records WHERE is_canary = 1 AND canary_id = 'test-canary'"
        )
        canary_details = " ".join(row[3] for row in canary_plan.fetchall())
        assert "idx_telemetry_canary" in canary_details


def test_telemetry_storage_configures_concurrent_connections(tmp_path: Path) -> None:
    storage = TelemetryStorage(make_settings(tmp_path))

    with storage._connection() as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
