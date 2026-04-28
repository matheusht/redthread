---
title: Tool Technology Slice 15 Persona Outcome Telemetry
type: research
status: implemented
summary: RPI plan and implementation notes for weak persona outcome telemetry that joins persona strategy metadata to JudgeAgent-scored campaign results.
source_of_truth:
  - docs/wiki/research/tool-technology-slice-12-persona-quality-measurement.md
  - docs/wiki/research/tool-technology-slice-13-persona-strategy-coverage-repair.md
  - docs/wiki/research/tool-technology-slice-14-persona-batch-layer-planning.md
  - src/redthread/personas/outcomes.py
  - src/redthread/orchestration/supervisor.py
updated_by: pi
updated_at: 2026-04-27
---

# Tool Technology Slice 15 Persona Outcome Telemetry

## Goal

Track weak persona-level outcome metrics after a campaign has JudgeAgent-scored results.

Plain flow:

```text
Persona + prompting-layer profile
→ AttackResult + JudgeAgent verdict
→ PersonaOutcomeTelemetry
→ campaign metadata
```

## Research

Slices 12-14 made persona strategy coverage measurable, repairable, and batch-planned.

Current gap:

- Persona quality could be measured before or during generation.
- Campaign results did not yet summarize which persona strategy profiles led to skipped runs, near misses, or confirmed JudgeAgent jailbreaks.
- Adaptive weighting should not be built until outcome data exists.

Useful seams:

- `AttackResult` already carries the final `JudgeVerdict`.
- `AttackTrace.persona` carries the generated persona and `allowed_strategies`.
- `finalize_node()` is the narrow place where judged results become `CampaignResult` metadata.
- `PromptingLayerProfile` can be recreated from campaign config and distributed by persona order.

## Plan

1. Add a small persona outcome telemetry module.
2. Build one weak outcome record per judged result.
3. Include persona id, tactic, algorithm, outcome, JudgeAgent score, strategy count, and layer coverage.
4. Add batch counts for confirmed jailbreaks, near misses, skipped runs, and errors.
5. Attach the telemetry to campaign metadata in supervisor finalization.
6. Keep all fields metadata-only and non-verdict except for directly copied JudgeAgent verdict fields.

## Implementation

Added:

```text
src/redthread/personas/outcomes.py
```

Models:

- `PersonaOutcomeRecord`
- `PersonaOutcomeTelemetry`

Helpers:

- `persona_profiles_by_id()`
- `build_persona_outcome_telemetry()`

Schema markers:

- `redthread.persona_outcome_record.v1`
- `redthread.persona_outcome_telemetry.v1`

Updated:

```text
src/redthread/orchestration/supervisor.py
```

Campaign metadata now includes:

```text
persona_outcome_telemetry
```

## Weak outcome labels

The label is derived from existing trace outcome plus JudgeAgent score:

- `confirmed_jailbreak` only when `JudgeVerdict.is_jailbreak` is true
- `near_miss` for partial outcome or score at least 3.0 without confirmed jailbreak
- `skipped` for dry-run skipped traces
- `error` for error traces
- `not_confirmed` for other non-jailbreak outcomes

## Safety invariant

Persona outcome telemetry is weak run metadata.

It cannot:

- create confirmed findings
- create regression cases
- assign severity truth
- prove defense coverage
- bypass JudgeAgent
- load raw jailbreak prompt bodies

Confirmed jailbreak count is copied from `JudgeVerdict.is_jailbreak`; it is not inferred from persona metadata.

## Gap check

### Security / red-teaming coverage

No gap. Telemetry does not execute attacks and does not replace PAIR, TAP, Crescendo, or MCTS.

### Evaluation metrics

No gap. JudgeAgent remains the owner of `is_jailbreak`, score, and verdict. Telemetry only copies those fields and adds weak labels.

### Defense pipeline

No gap. Defense synthesis and regression creation still depend on confirmed JudgeAgent findings, not telemetry labels.

## Acceptance criteria

- Telemetry records one entry per judged result.
- Confirmed jailbreak counts come only from `JudgeVerdict.is_jailbreak`.
- Near misses remain weak labels and do not become findings.
- Layer coverage is attached from the persona strategy profile.
- Campaign metadata includes `persona_outcome_telemetry`.
- Raw prompt bodies are rejected.

## Verification commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run python -m pytest \
  tests/test_persona_outcomes.py \
  tests/test_persona_quality.py \
  tests/test_supervisor.py -q

uv run ruff check \
  src/redthread/personas \
  src/redthread/orchestration/supervisor.py \
  tests/test_persona_outcomes.py \
  tests/test_persona_quality.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run mypy \
  src/redthread/personas \
  src/redthread/orchestration/supervisor.py \
  tests/test_persona_outcomes.py \
  tests/test_persona_quality.py

python3 scripts/wiki_lint.py
```
