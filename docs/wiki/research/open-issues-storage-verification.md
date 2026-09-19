---
title: Open Issues Storage Verification
type: research
status: implemented
summary: Verification record for SQLite concurrency and append-only memory storage changes in issues 88, 91, and 92.
source_of_truth:
  - src/redthread/telemetry/storage.py
  - src/redthread/memory/file_locks.py
  - src/redthread/memory/index.py
  - src/redthread/memory/legacy_parser.py
  - tests/test_memory_index_locking.py
  - tests/test_telemetry_storage.py
updated_by: codex
updated_at: 2026-09-18
---

# Open Issues Storage Verification

## Verified changes

- SQLite connections enable WAL mode and a 5000 ms busy timeout in [`TelemetryStorage`](../../../src/redthread/telemetry/storage.py).
- [`MemoryIndex`](../../../src/redthread/memory/index.py) serializes duplicate detection and both append files with deterministic sidecar `fcntl.flock` locks. Readers use the same lock family.
- [`legacy_parser`](../../../src/redthread/memory/legacy_parser.py) normalizes line endings, isolates entries at `---` separators or `##` headings, requires a dedicated `**Validated:** ✅ YES` line, and supports indented multiline quoted clauses.

## Evidence

Focused verification ran with `COLUMNS=240 REDTHREAD_DRY_RUN=true`:

```text
tests/test_memory_index_locking.py
tests/test_guardrail_loader.py
tests/test_defense_memory.py
tests/test_telemetry_storage.py
17 passed
```

Coverage includes six concurrent duplicate writers (one accepted), six concurrent distinct writers (all JSONL records parse and all Markdown entries remain intact), lock release after an injected exception, WAL/busy-timeout PRAGMAs, CRLF/indentation/multiline parsing, heading-delimited entries, and rejection of failed or quoted scope/validation metadata even when clause text contains `✅ YES`.

Ruff passes for changed storage modules and focused tests. Mypy passes for the changed memory and telemetry source modules.
