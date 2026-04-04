"""SQLite-backed persistent storage for TelemetryCollector."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from typing import Generator

from redthread.config.settings import RedThreadSettings
from redthread.telemetry.models import TelemetryRecord

logger = logging.getLogger(__name__)


class TelemetryStorage:
    """SQLite-backed history for telemetry metrics."""

    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings
        self.db_path = self.settings.log_dir / "telemetry.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    target_model TEXT,
                    prompt_hash TEXT,
                    latency_ms REAL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    error BOOLEAN,
                    error_type TEXT,
                    is_canary BOOLEAN,
                    canary_id TEXT,
                    response_text TEXT,
                    response_embedding JSON
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS drift_baseline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    embedding JSON
                )
                """
            )
            conn.commit()

    def insert(self, record: TelemetryRecord) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO telemetry_records (
                    target_model, prompt_hash, latency_ms, input_tokens, output_tokens,
                    error, error_type, is_canary, canary_id, response_text, response_embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.target_model,
                    record.prompt_hash,
                    record.latency_ms,
                    record.input_tokens,
                    record.output_tokens,
                    record.error,
                    record.error_type,
                    record.is_canary,
                    record.canary_id,
                    record.response_text,
                    json.dumps(record.response_embedding) if record.response_embedding else None,
                ),
            )
            conn.commit()

    def get_metric_series(
        self, metric: str, window: int | None = None, organic_only: bool = True
    ) -> list[float]:
        # Whitelist metric to avoid SQL injection
        allowed_metrics = {"latency_ms", "input_tokens", "output_tokens"}
        if metric not in allowed_metrics:
            raise ValueError(f"Metric {metric} not allowed for series extraction.")

        query = f"SELECT {metric} FROM telemetry_records WHERE "
        query += "is_canary = FALSE " if organic_only else "1=1 "
        query += "ORDER BY id DESC "
        if window is not None:
            query += f"LIMIT {int(window)}"

        with self._connection() as conn:
            rows = conn.execute(query).fetchall()
            # Restore to chronological (id asc)
            return [float(row[0]) for row in reversed(rows) if row[0] is not None]

    def _row_to_record(self, row: sqlite3.Row) -> TelemetryRecord:
        embedding_str = row["response_embedding"]
        return TelemetryRecord(
            target_model=row["target_model"],
            prompt_hash=row["prompt_hash"],
            latency_ms=row["latency_ms"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            error=bool(row["error"]),
            error_type=row["error_type"],
            is_canary=bool(row["is_canary"]),
            canary_id=row["canary_id"],
            response_text=row["response_text"],
            response_embedding=json.loads(embedding_str) if embedding_str else [],
        )

    def get_canary_records(self, canary_id: str | None = None) -> list[TelemetryRecord]:
        query = "SELECT * FROM telemetry_records WHERE is_canary = TRUE"
        params: list[str] = []
        if canary_id:
            query += " AND canary_id = ?"
            params.append(canary_id)
        query += " ORDER BY id ASC"

        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def get_organic_records(self, window: int | None = None) -> list[TelemetryRecord]:
        query = "SELECT * FROM telemetry_records WHERE is_canary = FALSE ORDER BY id DESC"
        if window:
            query += f" LIMIT {int(window)}"

        with self._connection() as conn:
            rows = conn.execute(query).fetchall()
            return [self._row_to_record(r) for r in reversed(rows)]

    def get_total_records(self) -> int:
        with self._connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM telemetry_records").fetchone()[0]

    def get_total_canary_records(self) -> int:
        with self._connection() as conn:
            res = conn.execute("SELECT COUNT(*) FROM telemetry_records WHERE is_canary = TRUE").fetchone()
            return res[0] if res else 0

    def save_baseline(self, embeddings: list[list[float]]) -> None:
        """Clear existing and save a new drift baseline to SQLite."""
        with self._connection() as conn:
            conn.execute("DELETE FROM drift_baseline")
            conn.executemany(
                "INSERT INTO drift_baseline (embedding) VALUES (?)",
                ((json.dumps(e),) for e in embeddings)
            )
            conn.commit()
            
    def load_baseline(self) -> list[list[float]] | None:
        """Load the existing drift baseline, if any."""
        with self._connection() as conn:
            rows = conn.execute("SELECT embedding FROM drift_baseline ORDER BY id ASC").fetchall()
            if not rows:
                return None
            return [json.loads(r[0]) for r in rows if r[0]]
