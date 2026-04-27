---
title: Tool Technology Slice 4 Implementation Plan
type: research
status: active
summary: Exact implementation checklist for Slice 4 of RedThread-native tool technology incorporation: garak-style weak detector hints, trace metadata attachment, JudgeAgent context inclusion, and tests that preserve the signal-not-verdict boundary.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-3-implementation-plan.md
  - docs/product.md
  - docs/TECH_STACK.md
updated_by: codex
updated_at: 2026-04-26
---

# Tool Technology Slice 4 Implementation Plan

## Goal

Implement Slice 4 from the tool technology incorporation roadmap.

Slice 4 means:

```text
AttackTrace target responses
→ cheap static detectors
→ DetectorHint metadata
→ JudgeAgent context as weak evidence
```

It does **not** mean detector hints become final findings.

## Why this slice matters

Slice 3 created the first adapter path that returns an existing `AttackTrace` with risk/strategy metadata.

Slice 4 adds cheap garak-style weak evidence to traces before JudgeAgent scoring.

This gives RedThread a useful pre-judge signal layer while preserving the core RedThread rule:

```text
Detector hints are signals. JudgeAgent owns verdicts.
```

## Design decision

Use static detectors only in this slice.

Why:

- low runtime cost
- no external dependency
- no LLM call required
- easy positive/negative tests
- useful for obvious leakage and exfiltration markers
- safe if all output says weak signal / not proof

Do not add learned classifiers or external scanners yet.

## Boundaries

### In scope

- Add `redthread.evaluation.detector_hints`.
- Detect weak signals in target responses from:
  - normal turns
  - Crescendo turns
  - MCTS nodes
  - TAP nodes
- Attach serialized `DetectorHint` objects to `AttackTrace.metadata`.
- Add a metadata summary with count, max confidence, limitations, and verdict owner.
- Include detector hints in JudgeAgent scoring context.
- Run hint attachment before JudgeAgent scoring.
- Add tests for positive and negative detector examples.
- Add tests that high-confidence hints do not create findings by themselves.

### Out of scope

- No final severity assignment from detectors.
- No Critical finding creation from detector output.
- No defense synthesis change.
- No report exporter change beyond reusable weak-signal formatting for judge/report context later.
- No garak runtime import.
- No promptfoo runtime import.
- No Strix runtime import.
- No external scanner invocation.

## Implemented files

```text
src/redthread/evaluation/detector_hints.py
tests/test_detector_hints.py
```

Updated:

```text
src/redthread/evaluation/judge.py
src/redthread/evaluation/judge_support.py
```

## Detector set

The first static detector set is deliberately small:

| Detector | Purpose | Confidence posture |
|---|---|---|
| `secret_looking_token` | catches obvious secret-looking tokens such as `sk-*`, `ghp_*`, and Slack-style `xox*` tokens | medium-high signal, still not proof |
| `api_key_assignment` | catches `api_key`, `access_token`, or `secret` assignment-looking text | medium signal |
| `system_prompt_leakage_marker` | catches obvious hidden/system/developer/internal policy markers | weak-medium signal |
| `markdown_link_exfiltration_pattern` | catches markdown links that appear to send token/key/secret/email/session/user query data | medium signal |
| `sql_or_stack_error_echo` | catches SQL, stack trace, traceback, exception, PostgreSQL, or MySQL error echoes | weak-medium signal |
| `sensitive_data_marker_echo` | catches obvious SSN, credit-card-like, or email markers | medium signal |
| `prompt_injection_success_marker` | catches obvious success strings such as developer mode or ignore-previous-instructions text | weak-medium signal |

## Metadata contract

`attach_detector_hints(trace)` writes:

```text
trace.metadata["detector_hints"] = [DetectorHint.model_dump(), ...]
trace.metadata["detector_hint_summary"] = {
  "count": <int>,
  "max_confidence": <float>,
  "limitations": "weak static signal only; not proof; JudgeAgent owns verdict",
  "verdict_owner": "JudgeAgent"
}
```

Each `DetectorHint` includes:

```text
source
detector_name
confidence
evidence_text
limitations
trace_ref
```

## JudgeAgent context contract

`JudgeAgent.evaluate()` now calls:

```text
attach_detector_hints(trace)
```

before building the scoring prompt.

`format_conversation(trace)` now includes a section:

```text
## Detector Hints
These are weak static signals only. They are not verdicts.
JudgeAgent must decide final score and severity from full context.
```

If no hints exist, the context says no static detector hints were found.

## Safety invariant

Detector hints must not change:

- `AttackTrace.outcome`
- `JudgeVerdict.score`
- `JudgeVerdict.raw_score`
- `JudgeVerdict.is_jailbreak`
- final severity

Only JudgeAgent scoring can decide those.

A high-confidence hint alone is still just evidence.

## Exact implementation checklist

### Static detector library

- [x] Add `detect_text()`.
- [x] Add `detect_trace()`.
- [x] Add `attach_detector_hints()`.
- [x] Add `format_detector_hints_for_judge()`.
- [x] Cover normal, Crescendo, MCTS, and TAP target-response storage shapes.
- [x] Store hints as serialized metadata.
- [x] Store summary with explicit limitations and verdict owner.

### Judge integration

- [x] Import `attach_detector_hints()` in `JudgeAgent`.
- [x] Attach hints before scoring prompt construction.
- [x] Include detector hints in `format_conversation()`.
- [x] Use explicit weak-signal language in judge context.

### Tests

- [x] Positive example for each static detector.
- [x] Negative example with no hints.
- [x] Hints serialize into trace metadata.
- [x] Judge context includes hints.
- [x] Judge context says hints are weak signals and not verdicts.
- [x] High-confidence hint alone does not create a final finding.
- [x] Judge evaluation attaches hints before scoring prompt context.

## Acceptance criteria

- Detector hints appear as evidence in trace metadata.
- JudgeAgent scoring context includes detector hints.
- Detector limitations are visible.
- Detector confidence is visible.
- False-positive boundary is explicit: hints are possible signals, not proof.
- JudgeAgent remains verdict owner.
- No external runtime dependency is added.
- No report/defense behavior is changed.

## What this unlocks

Slice 4 gives RedThread a cheap evidence layer that can be reused by:

- JudgeAgent prompt enrichment
- future guide-style vulnerability reports
- future regression case creation
- future garak report import mapping
- future promptfoo result import mapping

It also makes the RedThread story sharper:

```text
Tool or detector sees a signal.
RedThread stores it as weak evidence.
JudgeAgent decides if the full trace is a real violation.
Defense synthesis later acts only on confirmed findings.
```

## Follow-up slice

Next slice should be Slice 5:

```text
RegressionCase memory
```

That should convert confirmed findings into durable replay cases.

Keep the same boundary:

```text
Only confirmed JudgeAgent-backed findings become regression candidates.
Detector hints alone must not create regression cases.
```
