from __future__ import annotations

import json
import multiprocessing
from pathlib import Path

import pytest

from redthread.core.defense_synthesis import (
    DeploymentRecord,
    ValidationResult,
    VulnerabilityClassification,
)
from redthread.memory.file_locks import locked_append
from redthread.memory.index import MemoryIndex
from tests.defense_helpers import make_settings


def _record(trace_id: str) -> DeploymentRecord:
    return DeploymentRecord(
        trace_id=trace_id,
        guardrail_clause="Do not disclose protected data.",
        classification=VulnerabilityClassification(
            category="authorization_bypass",
            owasp_ref="LLM01",
            mitre_atlas_ref="AML.T0054",
            severity="HIGH",
            attack_vector="role-play",
        ),
        validation=ValidationResult(passed=True, replay_response="blocked", judge_score=1.0),
        target_model="llama3.2:3b",
        target_system_prompt_hash="prompt-hash",
    )


def _append_worker(memory_dir: str, trace_id: str, queue: object) -> None:
    settings = make_settings().model_copy(update={"memory_dir": Path(memory_dir)})
    queue.put(MemoryIndex(settings).append(_record(trace_id)))


def test_concurrent_duplicate_appends_are_serialized(tmp_path: Path) -> None:
    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    processes = [
        context.Process(target=_append_worker, args=(str(tmp_path), "trace-one", queue))
        for _ in range(6)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0

    assert sum(queue.get() for _ in processes) == 1
    lines = (tmp_path / "deployments.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["trace_id"] for line in lines] == ["trace-one"]


def test_concurrent_distinct_appends_keep_jsonl_and_markdown_intact(tmp_path: Path) -> None:
    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    processes = [
        context.Process(target=_append_worker, args=(str(tmp_path), f"trace-{index}", queue))
        for index in range(6)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0

    assert [queue.get() for _ in processes] == [True] * len(processes)
    records = [
        json.loads(line)
        for line in (tmp_path / "deployments.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert sorted(record["trace_id"] for record in records) == [f"trace-{index}" for index in range(6)]
    memory = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
    assert memory.startswith("# RedThread Threat Knowledge Base")
    assert memory.count("**Trace:**") == 6
    for index in range(6):
        assert f"**Trace:** `trace-{index}`" in memory


def test_legacy_guardrail_parser_accepts_crlf_indentation_and_multiline(tmp_path: Path) -> None:
    settings = make_settings().model_copy(update={"memory_dir": tmp_path})
    index = MemoryIndex(settings)
    index._path.write_text(
        "---\r\n"
        "  **Scope:** model=`llama3.2:3b` | prompt_hash=`prompt-hash`\r\n"
        "> **Guardrail clause:** Do not disclose\r\n"
        "  > protected data or secrets.\r\n"
        "\r\n"
        "**Validated:** ✅ YES (residual score: 1.00)\r\n"
        "---\r\n",
        encoding="utf-8",
    )

    assert index.load_scoped_guardrails("llama3.2:3b", "prompt-hash") == [
        "Do not disclose protected data or secrets."
    ]


def test_legacy_guardrail_parser_isolates_headings_and_validation_status(tmp_path: Path) -> None:
    settings = make_settings().model_copy(update={"memory_dir": tmp_path})
    index = MemoryIndex(settings)
    index._path.write_text(
        "## Failed entry\n"
        "**Scope:** model=`llama3.2:3b` | prompt_hash=`prompt-hash`\n"
        "> **Guardrail clause:** This clause mentions ✅ YES but is not validated.\n"
        "> **Validated:** ✅ YES\n"
        "**Validated:** ❌ NO\n"
        "## Quoted metadata\n"
        "> **Scope:** model=`llama3.2:3b` | prompt_hash=`prompt-hash`\n"
        "**Scope:** model=`other-model` | prompt_hash=`other-hash`\n"
        "> **Guardrail clause:** Quoted scope cannot authorize this clause.\n"
        "**Validated:** ✅ YES (residual score: 1.00)\n"
        "## Valid entry\n"
        "**Scope:** model=`llama3.2:3b` | prompt_hash=`prompt-hash`\n"
        "> **Guardrail clause:** Keep protected data private.\n"
        "**Validated:** ✅ YES (residual score: 1.00)\n",
        encoding="utf-8",
    )

    assert index.load_scoped_guardrails("llama3.2:3b", "prompt-hash") == [
        "Keep protected data private."
    ]


def test_memory_lock_releases_after_write_failure(tmp_path: Path) -> None:
    path = tmp_path / "MEMORY.md"
    with pytest.raises(RuntimeError, match="injected"), locked_append(path) as handle:
        handle.write("partial\n")
        raise RuntimeError("injected")

    with locked_append(path) as handle:
        handle.write("complete\n")

    assert path.read_text(encoding="utf-8") == "partial\ncomplete\n"
