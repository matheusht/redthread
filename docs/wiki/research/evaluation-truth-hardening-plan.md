---
title: Evaluation Truth Hardening Plan
type: research
status: active
summary: Research-backed plan for the next deep dive: judge and evaluation truth, with exact runtime gaps, file targets, and milestone sequence.
source_of_truth:
  - README.md
  - docs/TECH_STACK.md
  - docs/RPI_METHODOLOGY.md
  - docs/ANTI_HALLUCINATION_SOP.md
  - docs/PHASE_REGISTRY.md
  - docs/PROGRESS.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - .github/workflows/ci.yml
  - src/redthread/evaluation/judge.py
  - src/redthread/evaluation/pipeline.py
  - tests/test_golden_dataset.py
  - tests/test_judge.py
updated_by: codex
updated_at: 2026-04-15
---

# Evaluation Truth Hardening Plan

## Research question

After telemetry truth hardening, what is the next subsystem RedThread should investigate deeply, and what exact changes should be planned first?

## Recommendation

The next deep dive should be **Judge and Evaluation**.

This subsystem now has the best leverage because it is still the main truth layer for:
- campaign scoring
- jailbreak confirmation
- defense follow-through
- regression confidence
- operator trust in what CI and validation actually prove

## Current runtime truth

The evaluation subsystem is in a better place than the old status audit snapshot, but it still has an important trust gap.

### What is strong now

- `tests/test_judge.py` is currently green again.
- `tests/test_golden_dataset.py` is currently green in sealed mode.
- README now clearly says PR CI uses sealed golden regression and that live backend validation is separate.
- `tests/test_golden_dataset.py` makes live golden evaluation opt-in through `REDTHREAD_LIVE_GOLDEN=true`.

### What still needs a deep dive

- `src/redthread/evaluation/pipeline.py` uses deterministic heuristic scoring when `dry_run=True`.
- The same pipeline also falls back to deterministic heuristic scoring after live judge failure.
- `.github/workflows/ci.yml` runs golden regression with `REDTHREAD_DRY_RUN=true`.
- The current wiki page for evaluation is still thinner than the real trust boundary now requires.

Main implication:
- sealed CI is useful and intentional
- sealed CI is **not** the same as live judge proof
- fallback scoring is operationally useful
- fallback scoring can weaken operator understanding if it is not surfaced clearly enough

## Main trust gaps found in research

### 1. Sealed regression and live judge evidence are still easy to blur

Source evidence:
- `README.md`
- `.github/workflows/ci.yml`
- `src/redthread/evaluation/pipeline.py`
- `tests/test_golden_dataset.py`

Current truth:
- CI golden regression is an offline consistency gate
- live provider validation is a separate confidence pass

Risk:
- operators may still read a green golden run as stronger live evidence than it really is

### 2. Fallback scoring is under-explained as evidence

Source evidence:
- `src/redthread/evaluation/pipeline.py`

Current truth:
- heuristic scoring is used in sealed mode by design
- heuristic scoring is also used after judge-path failure

Risk:
- two very different situations share the same scoring fallback shape:
  - intentional sealed evaluation
  - degraded live evaluation after judge failure
- if reports do not separate them sharply, the evidence story becomes muddy

### 3. Evaluation outputs are not yet carrying explicit evidence-mode metadata end to end

Current truth:
- runtime mode labeling improved for campaign execution
- evaluation results do not yet appear to carry the same quality of explicit evidence-mode labeling through the pipeline and reporting surfaces

Risk:
- the operator sees a score without seeing enough about how that score was produced

### 4. Sensitive disclosure calibration should be re-audited, not assumed

Source evidence:
- `src/redthread/evaluation/pipeline.py`
- `src/redthread/evaluation/judge.py`
- `tests/test_golden_dataset.py`

Current truth:
- heuristic rules include high-severity disclosures and refusal markers
- this is useful, but it should be treated as a maintained calibration surface, not a one-time solved problem

Risk:
- prompt leakage, sensitive info disclosure, and partial compliance edge cases can drift silently if not pinned by explicit tests

## Decision

Do **not** widen the evaluation subsystem with new features first.

Do this instead:
- make evaluation evidence-mode explicit
- tighten the sealed-vs-live boundary
- add tests for fallback truth
- update docs/wiki so claims match runtime exactly

## Planned milestones

### Milestone 1 — Evaluation evidence-mode hardening

Goal:
- make every evaluation result easier to interpret correctly

Planned changes:
- add explicit evaluation metadata for mode and evidence source
- distinguish at least:
  - sealed heuristic
  - live judge
  - live fallback after judge failure
- surface this in result objects and operator-visible outputs where practical

Primary file targets:
- `src/redthread/evaluation/pipeline.py`
- `src/redthread/models.py`
- any CLI/reporting path that prints golden or evaluation summaries

Acceptance criteria:
- evaluation results explicitly say how scoring happened
- sealed and degraded-live paths are impossible to confuse in normal operator output

### Milestone 2 — Truth-boundary regression tests

Goal:
- lock in honest evaluation semantics

Planned changes:
- add tests for sealed-mode labeling
- add tests for judge-failure fallback labeling
- add tests proving fallback scoring does not silently impersonate live judge evidence
- add edge-case tests for sensitive disclosure and prompt leakage severity

Primary file targets:
- `tests/test_golden_dataset.py`
- new focused truth-boundary tests, likely `tests/test_evaluation_truth.py`
- `tests/test_judge.py` if judge-path parsing/labeling changes

Acceptance criteria:
- tests fail if sealed/live/fallback semantics blur again
- tests cover at least one explicit judge-failure fallback case
- tests cover at least one high-severity disclosure edge case

### Milestone 3 — Operator and doc honesty pass

Goal:
- align the docs, wiki, and any user-facing status language with the real evaluation evidence story

Planned changes:
- expand the evaluation wiki page beyond generic anti-hallucination summary
- document what CI proves
- document what live validation proves
- document what fallback scoring proves and does not prove
- update any stale doc lines that still imply more live proof than the runtime really provides

Primary file targets:
- `docs/wiki/systems/evaluation-and-anti-hallucination.md`
- `docs/wiki/entities/judge-agent.md`
- `README.md` if wording needs tightening
- `docs/PROGRESS.md` or `docs/REDTHREAD_STATUS_AUDIT.md` if stale truth language needs correction
- `docs/wiki/index.md`
- `docs/wiki/log.md`

Acceptance criteria:
- docs cleanly separate sealed evidence from live-provider evidence
- docs explain fallback scoring as operationally useful but weaker than live-judge success
- wiki pages are discoverable from the index and recorded in the log

## Exact first-change candidates

If implementation starts now, the highest-value first edits are:

1. `src/redthread/evaluation/pipeline.py`
   - add explicit evidence mode on each `TraceEvalResult`
   - track whether the score came from live judge, sealed heuristic, or failure fallback
   - expose fallback reason when applicable

2. `tests/test_golden_dataset.py`
   - assert evidence mode for sealed path
   - add a forced live-judge failure case and assert fallback labeling

3. new `tests/test_evaluation_truth.py`
   - cover signal-vs-proof semantics for evaluation outputs
   - cover high-severity disclosure calibration edges

4. `docs/wiki/systems/evaluation-and-anti-hallucination.md`
   - rewrite around truth boundaries, not just controls list

## Things not to do in this pass

- do not replace the judge architecture
- do not widen mutation into evaluation or judge logic
- do not claim sealed golden CI is live-model proof
- do not hide judge failure behind generic pass language

## Bottom line

Telemetry was the right last deep dive.

Now the next highest-value deep dive is **Judge and Evaluation**, because this is still the layer most responsible for telling RedThread what is true.

The best next work is not new evaluation features.
It is **truth hardening**:
- explicit evidence modes
- fallback honesty
- better tests
- tighter docs
