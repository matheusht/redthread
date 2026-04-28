---
title: Tool Technology Slice 16 Adaptive Persona Weighting
type: research
status: implemented
summary: RPI plan and implementation notes for next-run persona prompting-layer weighting from weak outcome telemetry while preserving JudgeAgent-only regression evidence gates.
source_of_truth:
  - docs/wiki/research/tool-technology-slice-15-persona-outcome-telemetry.md
  - src/redthread/personas/adaptive_weighting.py
  - src/redthread/personas/batch_planning.py
  - src/redthread/personas/generator.py
updated_by: pi
updated_at: 2026-04-28
---

# Tool Technology Slice 16 Adaptive Persona Weighting

## Goal

Use Slice 15 weak persona outcome telemetry to create a deterministic next-run persona weighting plan.

Plain flow:

```text
PersonaOutcomeTelemetry
→ AdaptivePersonaWeightingPlan
→ weighted prompting-layer batch profiles
→ next persona generation batch
```

## Research

Slice 15 created safe telemetry after JudgeAgent-scored campaign results.

Current gap:

- Persona telemetry can show which prompting layers produced confirmed jailbreaks, near misses, skipped runs, or errors.
- Persona batch planning still distributes layers evenly.
- There was no planning-only way to emphasize layers that deserve more exploration in a later batch.

Useful seams:

- `PersonaOutcomeTelemetry.records[*].covered_layers` gives metadata-only layer coverage.
- `JudgeVerdict.is_jailbreak` remains the only confirmed jailbreak source.
- `prompting_layer_profiles_for_batch()` is the narrow place to weight next-run layer distribution.
- `PersonaGenerator.generate_batch()` can accept an optional plan without changing default campaign behavior.

## Plan

1. Add a small adaptive weighting module.
2. Convert telemetry into one layer weight per enabled prompting layer.
3. Let JudgeAgent-confirmed jailbreaks raise weight most.
4. Let weak near misses raise exploration weight less.
5. Keep skipped/error/not-confirmed telemetry as context only.
6. Add optional weighted layer distribution to batch planning.
7. Add optional plan support to `PersonaGenerator.generate_batch()`.
8. Prove near misses do not create regression cases.

## Gap check

### Security / red-teaming coverage

No gap. The slice changes next-run persona planning only. It does not replace PAIR, TAP, Crescendo, MCTS, or attack execution.

### Evaluation metrics

No gap. JudgeAgent remains the source for confirmed jailbreak status. The adaptive plan copies no verdict authority into persona metadata.

### Defense pipeline

No gap. The adaptive plan does not synthesize defenses, create findings, or create regression cases. Durable regression evidence still requires a JudgeAgent-confirmed `AttackResult`.

## Implementation

Added:

```text
src/redthread/personas/adaptive_weighting.py
```

Models:

- `AdaptivePersonaLayerWeight`
- `AdaptivePersonaWeightingPlan`

Helper:

- `build_adaptive_persona_weighting_plan()`

Schema markers:

- `redthread.adaptive_persona_layer_weight.v1`
- `redthread.adaptive_persona_weighting_plan.v1`

Updated:

```text
src/redthread/personas/batch_planning.py
src/redthread/personas/generator.py
```

`prompting_layer_profiles_for_batch()` now accepts optional `layer_weights`.

`PersonaGenerator.generate_batch()` now accepts optional `persona_weighting_plan`.

`CampaignConfig` now accepts optional `persona_weighting_plan`, and the supervisor passes it into persona generation.

Default behavior stays unchanged when no plan is supplied.

## Weighting rule

For each enabled layer:

```text
weight = 1.0 + (JudgeAgent-confirmed jailbreaks * 2.0) + (weak near misses * 0.75)
```

The minimum weight is `0.25`.

This is deterministic and metadata-only.

## Safety invariant

Adaptive persona weighting is planning metadata.

It cannot:

- create confirmed findings
- create regression cases
- assign severity truth
- prove defense coverage
- bypass JudgeAgent
- load raw jailbreak prompt bodies

Only `AttackResult.verdict.is_jailbreak == true` can become durable regression evidence.

## Acceptance criteria

- Telemetry can produce an adaptive weighting plan.
- Confirmed JudgeAgent layers receive stronger weight than near-miss layers.
- Near-miss layers can increase exploration weight but stay weak.
- Weighted batch planning emphasizes higher-weight layers deterministically.
- Default persona generation remains unchanged without a plan.
- Raw prompt bodies are rejected.
- Near-miss attack results still cannot create regression cases.

## Verification commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run python -m pytest \
  tests/test_adaptive_persona_weighting.py \
  tests/test_persona_quality.py \
  tests/test_persona_outcomes.py -q

uv run ruff check \
  src/redthread/personas \
  src/redthread/models.py \
  src/redthread/orchestration/supervisor.py \
  tests/test_adaptive_persona_weighting.py \
  tests/test_persona_quality.py \
  tests/test_persona_outcomes.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run mypy \
  src/redthread/personas \
  src/redthread/models.py \
  src/redthread/orchestration/supervisor.py \
  tests/test_adaptive_persona_weighting.py \
  tests/test_persona_quality.py \
  tests/test_persona_outcomes.py

python3 scripts/wiki_lint.py
```
