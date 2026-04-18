---
title: Live Execution Truth Deep Dive
type: research
status: active
summary: Seam map, risk map, evidence map, and exact hardening slices for the live execution truth boundary across targets, judging, orchestration, and operator reporting.
source_of_truth:
  - README.md
  - docs/PHASE_REGISTRY.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - docs/wiki/systems/subsystem-focus-map.md
  - docs/wiki/systems/evaluation-and-anti-hallucination.md
  - docs/wiki/systems/orchestration-and-engine-runtime.md
  - src/redthread/engine.py
  - src/redthread/runtime_modes.py
  - src/redthread/orchestration/supervisor.py
  - src/redthread/orchestration/graphs/judge_graph.py
  - src/redthread/orchestration/runtime_summary.py
  - src/redthread/evaluation/pipeline.py
  - src/redthread/evaluation/judge.py
  - src/redthread/pyrit_adapters/targets.py
  - src/redthread/personas/generator.py
  - src/redthread/core/defense_synthesis.py
  - src/redthread/core/defense_replay_runner.py
  - src/redthread/core/defense_replay_cases.py
  - src/redthread/daemon/monitor.py
  - src/redthread/telemetry/collector.py
  - tests/test_runtime_truth.py
  - tests/test_golden_dataset.py
  - tests/test_evaluation_truth.py
updated_by: codex
updated_at: 2026-04-18
---

# Live Execution Truth Deep Dive

## Research question

What do RedThread's green results actually prove on the real provider/runtime path, where are the true send boundaries, and what exact hardening slices should come next?

## Current synthesis

RedThread is now much stronger on:
- sealed dry-run honesty
- evaluation evidence labeling
- degraded-runtime reporting
- narrow Phase 8 pre-send authorization proof lanes
- defense replay fail-closed behavior

But the repo still does **not** have one broad, shared live-execution truth layer.

Today the strongest truth is split across three different ideas:
1. **sealed consistency evidence**
2. **successful live judge evidence**
3. **narrow live interception proof lanes**

Those are all useful.
They are **not the same thing**.

The next subsystem pass should therefore focus on the real boundary where code calls provider-backed targets and where operators later read those outcomes as trustworthy runtime evidence.

## Implementation status

### Shipped on 2026-04-18

Completed so far:
- extracted the shared PyRIT wrapper into smaller modules under `src/redthread/pyrit_adapters/`
- added `src/redthread/pyrit_adapters/execution_records.py` with normalized `ExecutionMetadata` and `ExecutionRecord`
- extended `RedThreadTarget.send(...)` with optional `execution_metadata` while preserving the old return type and call shape
- added focused regression coverage in `tests/test_target_execution_records.py`
- instrumented `JudgeAgent` so live Auto-CoT and live scoring sends emit seam labels:
  - `judge.autocot`
  - `judge.score`
- added focused judge seam coverage in `tests/test_judge_execution_records.py`

What changed in the recommendation:
- Slice 1 is now complete
- the judge portion of Slice 2 is now complete
- next remaining work is persona, defense, telemetry, runtime aggregation, broader interception, algorithm-path expansion, and the opt-in smoke suite

## Seam map

## A. Primary choke point

### 1. `src/redthread/pyrit_adapters/targets.py`

This is the main execution choke point.

What it does:
- builds live target adapters via `build_target()`, `build_attacker()`, `build_judge_llm()`, and `build_defense_architect()`
- exposes `RedThreadTarget.send()` as the common async boundary
- is the only file importing PyRIT directly

Why it matters:
- almost every real provider-backed execution eventually reaches this wrapper
- but the wrapper currently returns only response text
- it does not emit a shared execution record, seam label, auth decision, or evidence mode

Current status:
- `RedThreadTarget.send(...)` can now emit a normalized execution record when callers pass `execution_metadata`
- this is the first shared execution-truth hook at the common boundary

Remaining gap:
- most caller paths still need to thread seam labels into that boundary

## B. High-trust live seams

### 2. Judge live scoring
Files:
- `src/redthread/evaluation/judge.py`
- `src/redthread/orchestration/graphs/judge_graph.py`
- `src/redthread/evaluation/pipeline.py`

What happens:
- `JudgeAgent` makes 2 live sends on normal path:
  - Auto-CoT step generation
  - final scoring
- `judge_graph.py` labels per-trace runtime status:
  - `sealed_passthrough`
  - `live_re_evaluated`
  - `live_empty_trace_passthrough`
  - `live_judge_error_passthrough`
- `evaluation/pipeline.py` labels evidence mode:
  - `sealed_heuristic`
  - `live_judge`
  - `live_judge_fallback`

Why it matters:
- this is RedThread's main truth layer for score meaning

Current status:
- `JudgeAgent` now labels both live sends at the target boundary using shared execution metadata
- focused tests pin `judge.autocot` and `judge.score`

Remaining gap:
- the same pattern still needs to reach persona generation, defense generation, telemetry, and mainstream attack execution seams

### 3. Defense architect live generation
Files:
- `src/redthread/core/defense_synthesis.py`
- `src/redthread/pyrit_adapters/targets.py`

What happens:
- live defense architect generation calls `build_defense_architect(...).send(...)`
- replay validation later uses patched target replay with separate validation evidence

Why it matters:
- defense generation is a live model step that can affect downstream operator trust

Main gap:
- generation send is live, but not explicitly labeled at the send boundary as live-generated evidence

### 4. Defense replay live validation
Files:
- `src/redthread/core/defense_replay_runner.py`
- `src/redthread/core/defense_replay_cases.py`
- `src/redthread/core/defense_authorization.py`

What happens:
- replay sends are now authorized before execution
- replay cases store `authorization_decision`
- blocked cases fail closed before `target.send(...)`

Why it matters:
- this is currently the cleanest live execution truth seam in the repo

Main gap:
- this proof lane is real but local, not yet the general runtime contract for all live sends

## C. Campaign execution seams

### 5. Persona generation attacker seam
File:
- `src/redthread/personas/generator.py`

What happens:
- dry-run uses sealed persona objects
- live mode uses `build_attacker(...).send(...)`

Why it matters:
- this is the first creative live generation step in a campaign

Main gap:
- no shared execution metadata distinguishes persona-generation live traffic from other attacker traffic

### 6. Attack algorithm seams
Files:
- `src/redthread/core/pair.py`
- `src/redthread/core/tap.py`
- `src/redthread/core/crescendo.py`
- `src/redthread/core/mcts.py`

What happens:
- attack algorithms build attacker and target adapters directly
- they call live `.send(...)` on both offensive and target-facing lanes

Why it matters:
- this is where most real campaign execution traffic happens

Main gap:
- these are still mostly raw send calls from the live-truth perspective
- current narrow Phase 8 interception work does not broadly cover these algorithm paths

### 7. Engine telemetry seam
Files:
- `src/redthread/engine.py`
- `src/redthread/telemetry/collector.py`

What happens:
- post-campaign telemetry can inject live canary probes
- transcript gets telemetry summary and exported telemetry JSONL

Why it matters:
- telemetry is useful operator evidence about continuity and drift

Main gap:
- telemetry probes are real live sends, but they are not modeled in the same execution-truth structure as campaign or judge sends
- docs correctly say this is signal, not proof, but runtime artifacts do not yet unify that story

### 8. Monitoring daemon seam
Files:
- `src/redthread/daemon/monitor.py`
- `src/redthread/telemetry/collector.py`

What happens:
- warmup and recurring canary probes call `target.send(...)`
- telemetry alerts may trigger an isolated follow-up campaign

Why it matters:
- this is background automation touching the live target path

Main gap:
- operator-signal seams and campaign-execution seams still use separate truth vocabularies

## D. Existing narrow interception seams

### 9. Controlled adapter / tools / sandbox / replay
Files:
- `src/redthread/pyrit_adapters/controlled.py`
- `src/redthread/tools/attack_tool.py`
- `src/redthread/tools/sandbox_tool.py`
- `src/redthread/core/defense_replay_runner.py`

What happens:
- optional `ActionEnvelope` authorization can block execution before send
- this is the best current proof-of-control lane

Why it matters:
- it proves the project can fail closed before execution on real seams

Main gap:
- coverage is still narrow and opt-in
- most regular provider calls are still outside this contract

## Risk map

| Priority | Risk | Why it matters | Evidence |
|---|---|---|---|
| Critical | No shared live send contract | Real provider calls happen in many places, but most do not emit common execution evidence or interception metadata | `src/redthread/pyrit_adapters/targets.py`, direct callers in `core/`, `personas/`, `daemon/`, `telemetry/` |
| Critical | Green can overstate live proof | Sealed regression, live judge success, fallback scoring, telemetry, and narrow auth proof are all different evidence classes | `src/redthread/evaluation/pipeline.py`, `docs/wiki/systems/evaluation-and-anti-hallucination.md` |
| High | Algorithm send paths bypass current proof lane | PAIR/TAP/Crescendo/MCTS build targets directly and call `.send(...)` without shared auth/evidence plumbing | `src/redthread/core/pair.py`, `tap.py`, `crescendo.py`, `mcts.py` |
| High | Live defense generation is under-labeled | Defense architect output is live model generation, but runtime artifacts do not clearly classify it as such | `src/redthread/core/defense_synthesis.py` |
| High | Telemetry traffic is not normalized against campaign traffic | Real live probes exist, but their evidence meaning is different and not carried through one execution schema | `src/redthread/engine.py`, `src/redthread/telemetry/collector.py`, `src/redthread/daemon/monitor.py` |
| Medium | Judge success is stronger than fallback, but the repo still lacks send-level proof for the judge path | Current labels are honest, but still one layer above the actual provider boundary | `src/redthread/evaluation/judge.py`, `src/redthread/orchestration/graphs/judge_graph.py` |
| Medium | Runtime summaries are aggregate, not seam-specific | Operators can see degraded runtime and judge status, but not a normalized map of which live boundaries actually executed | `src/redthread/orchestration/runtime_summary.py`, `src/redthread/engine.py` |

## Evidence map

## What we already prove well

### 1. Dry-run stays offline
Strong evidence:
- `tests/test_runtime_truth.py`
- dry-run persona generation refuses live provider construction
- dry-run engine path labels `sealed_dry_run`
- dry-run telemetry labels `skipped_in_dry_run`

Meaning:
- sealed mode is honestly sealed for the tested paths

### 2. Evaluation distinguishes sealed, live, and fallback
Strong evidence:
- `src/redthread/evaluation/pipeline.py`
- `src/redthread/evaluation/results.py`
- `tests/test_evaluation_truth.py`
- `tests/test_golden_dataset.py`

Meaning:
- a score is not presented as if every run came from the same truth strength

### 3. Judge passthrough and runtime degradation are surfaced
Strong evidence:
- `src/redthread/orchestration/graphs/judge_graph.py`
- `src/redthread/orchestration/runtime_summary.py`
- `tests/test_runtime_truth.py`
- `tests/test_supervisor.py`

Meaning:
- operators can see when judging was sealed, live, or degraded by error

### 4. Narrow live fail-closed seams exist now
Strong evidence:
- `src/redthread/tools/authorization/live_intercept.py`
- `src/redthread/pyrit_adapters/controlled.py`
- `src/redthread/tools/attack_tool.py`
- `src/redthread/tools/sandbox_tool.py`
- `src/redthread/core/defense_replay_runner.py`
- tests for each seam

Meaning:
- RedThread can already block execution before send on some real paths

## What we do not yet prove well

### 5. Repo-wide live send coverage
Weak / missing evidence:
- no single artifact says which provider-backed sends happened, from which seam, under which execution role, with which controls

Meaning:
- a green full run is still partly a composition of separate local truths, not one unified live-execution truth story

### 6. Full campaign live execution provenance
Weak / missing evidence:
- persona generation, algorithm sends, telemetry probes, defense architect generation, and judge sends do not all report into one normalized execution record

Meaning:
- operators still need code knowledge to understand what was truly exercised live

### 7. Shared proof that target traffic passed through the intended control boundary
Weak / missing evidence:
- `RedThreadTarget.send()` is common, but not instrumented as a universal proof boundary

Meaning:
- the repo has partial fail-closed lanes, not a general enforcement spine

## Contradictions and uncertainty

- The docs are now mostly honest about sealed vs live vs fallback evidence.
- The runtime is healthier than the older status audit implied.
- But the code still spreads real sends across many local call sites.
- So the repo is **not lying**, but it is still **under-instrumented** at the most important live boundary.

## Exact implementation slices

## Slice 1 — Add a shared live execution record at the target boundary

Goal:
- make `RedThreadTarget.send()` emit a normalized execution event for every live provider call

Primary files:
- `src/redthread/pyrit_adapters/targets.py`
- new `src/redthread/pyrit_adapters/execution_records.py`
- possibly new `src/redthread/pyrit_adapters/interceptors.py`
- tests: new `tests/test_target_execution_records.py`

Change:
- add a small `ExecutionRecord` model carrying fields like:
  - `seam`
  - `role`
  - `model_name`
  - `conversation_id`
  - `runtime_mode`
  - `success`
  - `error`
  - `authorization_decision` if present
  - `evidence_class`
- let `RedThreadTarget.send()` optionally accept execution metadata or a tiny envelope
- keep old call sites compatible by making metadata optional

Acceptance:
- one live send can produce a structured record without changing existing return type
- dry-run paths remain offline
- no public API break for current callers

## Slice 2 — Thread seam labels through the highest-value live callers first

Goal:
- instrument the truth-critical seams before the broad attack surface

Primary files:
- `src/redthread/evaluation/judge.py`
- `src/redthread/core/defense_synthesis.py`
- `src/redthread/core/defense_replay_cases.py`
- `src/redthread/personas/generator.py`
- `src/redthread/engine.py`
- `src/redthread/telemetry/collector.py`
- `src/redthread/daemon/monitor.py`

Change:
- pass explicit seam labels like:
  - `judge.autocot`
  - `judge.score`
  - `defense.architect`
  - `defense.replay`
  - `persona.generate`
  - `telemetry.canary`
  - `telemetry.warmup`
- mark evidence class on each seam:
  - live judge evidence
  - live generation evidence
  - live replay evidence
  - telemetry signal

Acceptance:
- one transcript or report path can distinguish judge sends from telemetry probes from defense replay sends
- telemetry remains labeled as signal, not proof

## Slice 3 — Add shared runtime aggregation for execution-truth artifacts

Goal:
- expose seam-level truth to operators without opening raw code

Primary files:
- `src/redthread/orchestration/runtime_summary.py`
- `src/redthread/engine.py`
- `src/redthread/models.py` or local report models
- CLI surface if needed
- tests: new `tests/test_execution_truth_summary.py`

Change:
- aggregate execution records into campaign metadata and transcript summary
- include counts by seam and evidence class
- include explicit degraded markers when expected live seams were skipped or failed

Acceptance:
- operators can answer: which live seams really ran, which degraded, and which were only telemetry signal

## Slice 4 — Expand from narrow auth proof lanes to the main target factory seam

Goal:
- stop treating live interception as only a side lane

Primary files:
- `src/redthread/pyrit_adapters/targets.py`
- `src/redthread/tools/authorization/live_intercept.py`
- `src/redthread/pyrit_adapters/controlled.py`
- selected callers in `src/redthread/core/`
- tests: new `tests/test_live_execution_interceptor.py`

Change:
- add an optional pre-send interception hook at the common target boundary
- reuse current authorization decision path where possible
- begin with opt-in mode so existing behavior is preserved

Acceptance:
- at least one normal campaign send path outside tool/replay seams is intercepted before provider execution
- deny path proves no underlying send happened

## Slice 5 — Add a tiny opt-in live execution truth smoke suite

Goal:
- prove one honest end-to-end live path instead of only local mocks

Primary files:
- new `tests/test_live_execution_truth_smoke.py`
- maybe CLI or docs for env gating
- docs/wiki follow-up pages

Change:
- add an env-gated smoke suite that proves at least:
  - one persona live generation send
  - one attack or target live send
  - one judge live send
  - one blocked pre-send intercept case
  - one telemetry probe labeled as signal

Acceptance:
- suite is explicit, opt-in, small, and honest
- output shows different evidence classes instead of flattening them into one green result

## Recommended order of attack

1. **Slice 1 — shared execution record**
   - first because everything else becomes cleaner once the common boundary can emit structured truth

2. **Slice 2 — instrument judge, defense, persona, telemetry seams**
   - second because these seams define operator trust most directly

3. **Slice 3 — aggregate and surface execution truth**
   - third because instrumentation without operator visibility is half-finished

4. **Slice 4 — widen interception from side lanes into the main target boundary**
   - fourth because it is more powerful and riskier, so it should land after shared records and reporting exist

5. **Slice 5 — opt-in live smoke proof**
   - last because it is the final honesty check after the runtime can already explain what happened

## Bottom line

RedThread is now in a good place to stop adding isolated truth patches and start building one shared live-execution truth spine.

The real next move is:
- instrument the common target boundary
- label live seams consistently
- surface those records to operators
- then prove one tiny real end-to-end live path

That is the cleanest way to answer the repo's current hardest question:

**What does a green result actually mean on the real runtime path?**
