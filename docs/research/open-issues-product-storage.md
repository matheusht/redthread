---
title: Open issues 19, 76, 77, 88, 89, 90, 91, 92 research
type: research
status: active
summary: Wayfinder research and implementation specifications for the launch-readiness, model/export, telemetry, and memory tickets.
source_of_truth:
  - https://github.com/matheusht/redthread/issues/19
  - https://github.com/matheusht/redthread/issues/74
  - https://github.com/matheusht/redthread/issues/76
  - https://github.com/matheusht/redthread/issues/77
  - https://github.com/matheusht/redthread/issues/88
  - https://github.com/matheusht/redthread/issues/89
  - https://github.com/matheusht/redthread/issues/90
  - https://github.com/matheusht/redthread/issues/91
  - https://github.com/matheusht/redthread/issues/92
updated_by: codex
updated_at: 2026-09-18
---

# Open issue research: product, architecture, telemetry, and memory

Research and implementation specification from this pass. Findings below combine the issue bodies with the current source and test paths; implementation work is limited to #19, #76, #88, #91, and #92. The parent map is Wave 2 production readiness (#74); its operating constraint is minimal diffs, one focused test per change, and a 200-line ceiling ([map](https://github.com/matheusht/redthread/issues/74)).

## Research method and repository constraints

- Decision routing sends architecture and runtime work through `docs/TECH_STACK.md`, `docs/PHASE_REGISTRY.md`, and the relevant subsystem source ([decision tree](../../docs/AGENT_DECISION_TREE.md)).
- The repo's RPI contract requires source-path research before implementation and says research output must contain paths, lines, and objective findings ([RPI](../../docs/RPI_METHODOLOGY.md)).
- The source-of-truth order gives current engineering docs precedence over historical phase notes; the wiki is synthesis, not runtime truth ([decision tree](../../docs/AGENT_DECISION_TREE.md)).
- MemPalace search was attempted for `launch readiness preset` and `telemetry WAL ARIMA ASI memory locking guardrail parser`; the configured CLI returned no results. No prior memory decision was available to resolve the ambiguities below.

## Issue 19 — launch-readiness preset

Issue: [#19](https://github.com/matheusht/redthread/issues/19).

### Current execution path

`redthread run` currently accepts one objective, one system prompt, one rubric, one algorithm override, persona count, optional report destinations, and optional benchmark/persona metadata. The command creates `CampaignConfig`, invokes `RedThreadEngine`, then calls `write_run_reports` ([run command](../../src/redthread/cli/run.py#L63-L188)). `CampaignConfig` has no preset, risk profile, release stage, gate policy, baseline, or target-config file ([models](../../src/redthread/models.py#L161-L204)).

`RedThreadEngine.run()` delegates one campaign to `RedThreadSupervisor`; it records runtime truth and telemetry, then writes a transcript ([engine](../../src/redthread/engine.py#L20-L68)). The supervisor injects active guardrails, runs the LangGraph campaign, and returns `CampaignResult` ([supervisor](../../src/redthread/orchestration/supervisor.py#L31-L60)). Confirmed jailbreaks route to defense synthesis, where the defense worker validates exploit and benign replay cases and indexes only a `validated_candidate`; it does not promote an active guardrail ([defense worker](../../src/redthread/orchestration/graphs/defense_graph.py#L35-L84)).

The existing operator bundle already exposes confirmed findings, strategy IDs, attack success rate, evidence mode counts, evidence uncertainty, defense status, and regression links ([artifact builder](../../src/redthread/reporting/artifacts.py#L28-L88); [models](../../src/redthread/reporting/models.py#L33-L138)). Markdown already prints evidence/uncertainty, findings, defense and regression status, stakeholder readout, and limitations ([exporter](../../src/redthread/reporting/exporters.py#L18-L47), [exporter sections](../../src/redthread/reporting/exporters.py#L69-L179)). Evidence collection distinguishes runtime mode, judge runtime status, evidence class, defense status, and fallback reasons ([evidence summary](../../src/redthread/reporting/evidence_summary.py#L12-L45)).

### Spec decision

Implement the first release as a bounded readiness preset that executes the existing campaign path for every required strategy, then renders an aggregate report. Do not add a second attack executor or claim universal model safety.

1. Add a typed `LaunchReadinessConfig` (or equivalent policy model) with defaults matching the issue: required live judge, required replay, required benign replay, fallback diagnostic-only, required strategy IDs, and maximum unresolved high findings.
2. Add a `launch-readiness` preset resolver and an explicit bounded multi-strategy campaign plan. The current CLI's `--algorithm` is a single `AlgorithmType` setting ([settings and run override](../../src/redthread/cli/run.py#L28-L61)), while the existing strategy registry already describes `pair`, `tap`, and `crescendo` ([built-ins](../../src/redthread/core/strategies/builtin.py#L1-L90)). Launch readiness must execute the required strategies through the normal supervisor/attack/judge/defense path and aggregate their results; a metadata-only report over one algorithm is insufficient. The smallest coherent implementation is an explicit coordinator that runs one normal campaign per selected strategy, preserves per-run evidence and defense records, then builds one aggregate readiness packet. Do not hide fan-out in a report renderer or silently change the default single-algorithm path.
3. Add a readiness report artifact before detailed operator findings. Reuse `OperatorArtifactBundle` and existing prompt-safe exporters; add a separate typed launch gate summary rather than overloading `StakeholderReadout`.
4. Derive gate status only from observed evidence. Suggested states: `blocked` if unresolved high findings exceed the limit, required live judge evidence is absent, or required replay/benign evidence is absent; `conditional` if findings are absent but evidence is mixed, fallback-only, or required human review remains; `ready` only when all configured gates pass. This is a derived launch decision, not a safety certification.
5. Emit a sanitized external-review packet containing finding IDs, trace IDs, strategy, scope, evidence labels, hashes/reproduction references, replay/utility status, and defense promotion state. Do not include raw prompts or target system prompts; the benchmark handoff already establishes this redaction boundary ([handoff](../../src/redthread/benchmarks/regression_handoff.py#L180-L201)).

### Dependencies and open requirements

- A target-config YAML shape and adapter loading contract do not exist in the current CLI. Adding them is a separate input/config feature; the launch preset should initially accept existing CLI inputs and write a clear limitation when no target config is present. Strategy coverage remains mandatory when the preset is selected.
- “Capability uplift,” “universal/broad/narrow/context-specific scope,” and “replay-confirmed failure” are not currently typed in `CampaignResult` or `OperatorArtifactBundle`. They need explicit source fields or must be marked `unknown`; do not infer them from judge score or detector hints.
- Existing live evidence labels are available, but sealed dry-run and heuristic fallback are distinct evidence classes and fallback is not equivalent to live judge proof ([anti-hallucination SOP](../../docs/ANTI_HALLUCINATION_SOP.md#41-post-processing--evaluation)).
- Defense validation already runs replay and benign cases, but the campaign report does not currently promote those per-finding results into a launch-gate model. The bridge must read `defense_records` and `ValidationResult` data, preserving candidate/validated/promotable/active status.
- Issue #19 has no `wayfinder:task` label and no accepted target-config schema. Treat target-config ingestion and capability-uplift measurement as unresolved follow-on work.

### Minimal implementation acceptance tests

- `redthread run --preset launch-readiness ...` executes every required preset strategy through the normal campaign pipeline, produces the standard report directory plus one aggregate launch-readiness Markdown/JSON artifact, and preserves per-strategy results.
- A missing strategy implementation, failed strategy run, or incomplete strategy set is a readiness failure; the coordinator must not silently downgrade to one strategy.
- A dry-run or fallback-only campaign is visibly `blocked`/`conditional` under a policy requiring live judge evidence; no fallback result can satisfy promotion/readiness.
- A confirmed finding with missing replay or failed benign utility gate blocks readiness.
- A clean campaign with required evidence and no unresolved high findings yields `ready`; the report says this is evidence-scoped and not a safety certification.
- The external packet contains no raw attacker prompt, target response, or target system prompt.
- Existing `tests/test_run_cli_reports.py`, reporting tests, and evidence-summary tests remain green; add focused tests for gate evaluation and prompt-safe export.

## Issue 76 — decompose core data models

Issue: [#76](https://github.com/matheusht/redthread/issues/76).

### Current execution path

`src/redthread/models.py` is 204 lines. It defines taxonomy/persona models, attack-tree/search models, conversation/trace models, judge/result models, and campaign config/result in one module ([models](../../src/redthread/models.py#L1-L204)). The issue's stated split is persona/taxonomy into `personas/models.py`, tree-search structures into `core/models.py`, and compatibility re-exports ([issue](https://github.com/matheusht/redthread/issues/76)).

Imports are broad: persona enums/classes are used by persona generators and taxonomy modules; `AttackNode` is used by TAP; `MCTSNode` is used by MCTS; `CrescendoTurn` is used by Crescendo; all higher-level trace/result/config types are imported by engine, supervisor, core strategies, reporting, and tests. Representative paths include [`personas/generator.py`](../../src/redthread/personas/generator.py#L1-L15), [`core/tap.py`](../../src/redthread/core/tap.py#L1-L32), [`core/mcts.py`](../../src/redthread/core/mcts.py#L1-L30), and [`core/crescendo.py`](../../src/redthread/core/crescendo.py#L1-L27).

### Spec decision

- Create `src/redthread/personas/models.py` containing `MitreAtlasTactic`, `PsychologicalTrigger`, and `Persona`.
- Create `src/redthread/core/models.py` containing `AttackNode`, `MCTSNode`, and `CrescendoTurn` as search/strategy state.
- Keep execution/result models (`AttackOutcome`, `ConversationTurn`, `AttackTrace`, `JudgeVerdict`, `AttackResult`, `CampaignConfig`, `CampaignResult`) in `models.py`.
- Re-export every moved symbol from `redthread.models`; this is required for source compatibility because current imports use that module throughout runtime and tests.
- Avoid importing `redthread.models` from the new modules. New modules should depend only on Pydantic/stdlib; root `models.py` imports the leaf modules first, then defines trace models.

### Acceptance tests

- Existing imports from `redthread.models` construct and compare the same classes and enum values.
- Direct imports from the new leaf modules work.
- TAP, MCTS, Crescendo, persona generation, engine, reporting, and all model tests pass.
- Every model file is below 200 lines; `models.py` should remain comfortably below the issue's 150-line target.
- `ruff check src/` and `mypy src/redthread/` pass.

## Issue 77 — benchmark exports and regression handoff serialization (external owner)

Issue: [#77](https://github.com/matheusht/redthread/issues/77).

### Current execution path

`benchmarks/__init__.py` is 202 lines: it imports a broad set of names from nearly every benchmark submodule and repeats them in a large `__all__`. No runtime or test code currently uses `from redthread.benchmarks import ...`; current imports target concrete submodules. This makes the package root mostly a convenience API, but external callers may still rely on it.

`regression_handoff.py` is 201 lines and mixes Pydantic handoff schemas, replay-result filtering, redaction, and JSON file writing. The main path is `run_approved_jailbreak_replay_with_regression_handoff` → `build_benchmark_regression_handoff` → `write_benchmark_regression_handoff_artifact`; only confirmed jailbreaks become redacted regression cases, while safe/non-replayable results become skip rows ([builder](../../src/redthread/benchmarks/regression_handoff.py#L85-L138)). The writer validates prompt safety before creating parent directories and writing JSON ([writer](../../src/redthread/benchmarks/regression_handoff.py#L141-L161)).

### External-owner boundary

Issue #77 is excluded from this implementation pass because another contributor owns it. Its research remains here for provenance only: current code mixes handoff schemas, redaction, and JSON writing in [`regression_handoff.py`](../../src/redthread/benchmarks/regression_handoff.py#L85-L161), and the package root is 202 lines. Do not refactor or indirectly duplicate its changes while implementing the remaining scope.

## Issue 88 — SQLite WAL and busy timeout

Issue: [#88](https://github.com/matheusht/redthread/issues/88).

### Current execution path

`TelemetryStorage.__init__()` creates the database and calls `_init_db()`. Every read/write obtains a fresh connection from `_connection()`, which currently uses `sqlite3.connect(..., timeout=10.0)` and only sets `row_factory`; no SQLite PRAGMA is applied ([storage](../../src/redthread/telemetry/storage.py#L17-L33)). Inserts and baseline writes commit through those connections ([storage](../../src/redthread/telemetry/storage.py#L73-L96), [baseline](../../src/redthread/telemetry/storage.py#L161-L177)). `TelemetryCollector` delegates all storage reads and writes to this class ([collector](../../src/redthread/telemetry/collector.py#L29-L75)).

### Spec decision

Apply `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000` immediately after connection creation, before yielding the connection. WAL is persistent at database level; busy timeout is connection-scoped, so both belong in the factory. Keep the existing 10-second sqlite connect timeout unless evidence shows it conflicts; the requested 5-second busy timeout controls SQLite lock waits after connection creation.

Do not issue a second connection just to initialize PRAGMAs. `_init_db()` already flows through `_connection()`, so initialization and all later operations receive the same policy.

### Acceptance tests

- A storage connection reports `journal_mode == "wal"` and `busy_timeout == 5000`.
- Two storage instances can read/write the same database without immediate `database is locked` errors in a focused contention test.
- Existing index/query-plan tests stay green ([storage tests](../../tests/test_telemetry_storage.py#L25-L75)).
- File remains below 200 lines.

## Issue 89 — zero-variance ARIMA series (external owner)

Issue: [#89](https://github.com/matheusht/redthread/issues/89).

### Current execution path

`ArimaDetector.detect()` rejects fewer than three observations, limits to `window_size`, uses a z-score fallback below `min_observations`, and otherwise invokes `pmdarima.auto_arima` on `window[:-1]` ([ARIMA detector](../../src/redthread/telemetry/arima.py#L83-L121)). A broad exception handler falls back to z-score, which does not express a stationary/constant result ([fallback](../../src/redthread/telemetry/arima.py#L129-L164)). `analyze_collector()` runs this path for latency, output tokens, and derived response length ([collector analysis](../../src/redthread/telemetry/arima.py#L166-L195)).

### External-owner boundary

Issue #89 is excluded from this implementation pass because another contributor owns it. Research finding: [`ArimaDetector.detect`](../../src/redthread/telemetry/arima.py#L83-L164) sends flat series into `auto_arima` or z-score fallback. Do not modify ARIMA code or tests here.

## Issue 90 — insufficient ASI telemetry (external owner)

Issue: [#90](https://github.com/matheusht/redthread/issues/90).

### Current execution path and mismatch

The issue names `AgentStabilityIndex.calculate()` and an `ASIReport.status`/nullable `asi_score`, but the repository exposes `compute()` and `ASIReport.overall_score: float`; there is no `status` field ([ASI](../../src/redthread/telemetry/asi.py#L27-L74), [report model](../../src/redthread/telemetry/models.py#L61-L102)). `compute()` currently runs ARIMA, response consistency, semantic drift, operational health, and behavioral stability regardless of record count, then computes a weighted score and alert ([compute](../../src/redthread/telemetry/asi.py#L73-L137)). Assessment helpers intentionally use defaults when evidence is absent, and reporting calls `health_tier`, formats `overall_score`, and emits caveats ([reporting](../../src/redthread/telemetry/reporting.py#L44-L72)). Transcript serialization also expects a numeric `overall_score` ([transcript](../../src/redthread/engine_transcript.py#L120-L160)).

### External-owner boundary

Issue #90 is excluded from this implementation pass because another contributor owns it. Research finding: current [`AgentStabilityIndex.compute`](../../src/redthread/telemetry/asi.py#L73-L137) computes on empty/short data and `ASIReport` has no status field ([model](../../src/redthread/telemetry/models.py#L61-L102)). Do not modify ASI code or tests here.

## Issue 91 — atomic cross-process memory writes

Issue: [#91](https://github.com/matheusht/redthread/issues/91).

### Current execution path

`MemoryIndex.append()` evaluates canary containment, checks duplicate trace IDs, mutates metadata, then independently opens `MEMORY.md` and `deployments.jsonl` in append mode ([memory index](../../src/redthread/memory/index.py#L37-L69)). Duplicate detection reads the JSONL file without synchronization ([memory index](../../src/redthread/memory/index.py#L89-L102), [duplicate helper](../../src/redthread/memory/index.py#L176-L177)). Multiple processes can therefore both pass `_is_duplicate()` and append, and line writes can interleave.

### Spec decision

Use stdlib `fcntl.flock` on a deterministic lock handle/context manager. Serialize duplicate check and both writes under one deployments lock so two processes cannot both accept the same trace ID. Acquire locks in a fixed order (deployments first, memory second) to avoid lock-order deadlocks; release in `finally`/context-manager exit. Flush and `fsync` each file before releasing its lock if durability is part of the atomicity contract.

The lock can be on the data file itself or a stable sidecar; a sidecar avoids changing file offsets and keeps lock identity stable across open modes. Ensure parent files exist before locking. The append operation should not write one file and silently report success if the second write fails; raise/return failure according to existing error semantics after releasing locks.

### Acceptance tests

- Spawn multiple processes against one `MemoryIndex`, append unique records, and assert every JSONL line parses and every Markdown entry is intact.
- Spawn multiple processes with the same trace ID and assert exactly one append succeeds.
- Assert lock release after an injected write failure so a later append is not blocked.
- Preserve canary containment, validation status, and existing deduplication behavior ([memory tests](../../tests/test_defense_memory.py#L17-L106)).
- File remains below 200 lines; a small lock helper module is preferable if needed.

## Issue 92 — structured legacy Markdown guardrail parser

Issue: [#92](https://github.com/matheusht/redthread/issues/92).

### Current execution path

`load_scoped_guardrails()` treats structured `deployments.jsonl` as authoritative when present. It only parses legacy Markdown when JSONL is empty, splitting on the exact LF delimiter `---\n\n`, matching exact scope text, and accepting only a line beginning exactly `> **Guardrail clause:**`; it captures one line only ([memory index](../../src/redthread/memory/index.py#L121-L138)). Current writers use that exact single-line format ([formatting](../../src/redthread/memory/formatting.py#L16-L53)), while the fallback must support hand-edited/legacy files. Existing loader tests cover structured records and whitespace-normalized prompt scope ([tests](../../tests/test_guardrail_loader.py#L64-L172)).

### Spec decision

Normalize CRLF to LF, locate candidate entry blocks by Markdown separator or heading boundaries, and extract a scoped guardrail clause with a compiled multiline regex. Accept optional leading whitespace before `>`, optional whitespace after `>`, and continuation quote lines. Normalize continuation lines by removing quote prefixes and joining trimmed lines with spaces/newlines according to the intended clause contract. Preserve the existing “validated YES + exact target model/prompt hash” scope gate.

The issue's suggested lookahead regex is a useful starting point, but a parser should avoid terminating on every blank line inside a multiline quoted clause. Recommended contract: collect consecutive `>` lines after the clause marker, normalize them, then stop at the first non-quote line or entry separator. Do not parse Markdown when structured deployments exist; this maintains the current authoritative-source boundary.

### Acceptance tests

- Legacy Markdown with LF and CRLF parses the same scoped clause.
- Single-line clauses with exact and indented blockquote markers parse.
- Multiline quoted clauses preserve all content after normalization.
- Nonmatching model, prompt hash, or failed validation is ignored.
- Structured JSONL remains authoritative even if Markdown has a matching clause.
- Add focused tests to `tests/test_guardrail_loader.py` or a memory parser test; keep `index.py` below 200 lines.

## Implementation and test evidence

- #76 moved persona/taxonomy models to `src/redthread/personas/models.py` and search-state models to `src/redthread/core/models.py`; `src/redthread/models.py` keeps compatibility imports. All three model files remain below 150 lines.
- #88 configures WAL and a 5000 ms busy timeout in the shared SQLite connection factory. The focused telemetry test verifies both PRAGMAs.
- #91 uses deterministic sidecar `fcntl.flock` locks. Duplicate detection and both append writes run under one deployment lock; readers use the same lock family. The multiprocessing test accepts six concurrent duplicate writers exactly once, and the lock-release test writes successfully after an injected exception.
- #92 uses a dedicated legacy parser with newline normalization, whitespace-tolerant scope/marker matching, quoted continuation support, and anchored unquoted scope/validation metadata. Conflicting or quoted metadata cannot authorize a clause. Focused parser coverage includes CRLF, indentation, multiline clauses, heading boundaries, and spoof rejection.
- Validation: `COLUMNS=240 REDTHREAD_DRY_RUN=true .venv/bin/pytest -q tests/test_memory_index_locking.py tests/test_guardrail_loader.py tests/test_defense_memory.py tests/test_telemetry_storage.py` → 17 passed; the combined model/strategy/telemetry focused set → 56 passed. Ruff and mypy pass for all changed source modules. #19 launch-readiness runtime work is owned by the evaluation agent and remains outside this implementation evidence.

## Dependency order and launch-readiness recommendation

Recommended implementation order for the parent map:

1. #88, #89, and #90: isolated telemetry correctness seams and focused tests.
2. #91, then #92: locking must make JSONL authoritative and parser fallback deterministic under concurrent writes.
3. #76 and #77: mechanical module/API decomposition; run import, benchmark, Ruff, and mypy checks after each split.
4. #19: build the launch packet on top of the now-stable evidence/report surfaces. Do not make launch readiness depend on undocumented target-config or capability-uplift inference.

The smallest complete #19 launch slice is: typed policy + preset resolver, explicit coordinator over the existing campaign executor for every required strategy, typed fail-closed gate evaluator, executive Markdown/JSON section, and prompt-safe external packet. It should fail closed for missing required live/replay/benign evidence and state `conditional`/`blocked` when evidence is sealed or fallback-only. Capability uplift and scope classification remain explicit follow-on requirements until their input and measurement contracts exist; multi-strategy coverage is part of the launch preset itself.
