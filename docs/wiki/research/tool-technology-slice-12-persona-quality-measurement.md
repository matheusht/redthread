---
title: Tool Technology Slice 12 Persona Quality Measurement
type: research
status: implemented
summary: RPI plan and implementation notes for measuring whether metadata-only prompting-layer profiles produce strategy coverage in generated personas.
source_of_truth:
  - docs/wiki/research/tool-technology-slice-11-persona-prompting-layer-profiles.md
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - src/redthread/personas/prompt_layers.py
  - src/redthread/personas/generator.py
  - src/redthread/core/mcts_helpers.py
updated_by: pi
updated_at: 2026-04-27
---

# Tool Technology Slice 12 Persona Quality Measurement

## Goal

Measure whether persona prompting-layer profiles change generated persona strategy coverage.

Plain flow:

```text
PromptingLayerProfile
→ Persona.allowed_strategies
→ PersonaStrategyCoverage
→ weak generation-quality signal only
```

## Research

Slice 11 added metadata-only prompting layers and fed them into `PersonaGenerator`.

Current useful seams:

- `src/redthread/personas/prompt_layers.py` owns safe layer labels and hints.
- `src/redthread/personas/generator.py` creates personas and fills `allowed_strategies`.
- `src/redthread/core/mcts_helpers.py` consumes `allowed_strategies` during MCTS expansion.

Current gap:

- The prompt asks the attacker model to cover enabled layers.
- There was no explicit quality summary proving which layers were covered.
- There was no durable, testable object for operator or future telemetry use.

## Plan

1. Add a small persona quality module.
2. Add a weak strategy-coverage summary model.
3. Compare enabled layers to safe strategy hints.
4. Return covered and missing layers.
5. Add batch coverage summary.
6. Keep all output metadata-only and non-verdict.

## Implementation

Added:

```text
src/redthread/personas/quality.py
```

Models:

- `PersonaStrategyCoverage`
- `PersonaBatchStrategyCoverage`

Helpers:

- `assess_persona_strategy_coverage()`
- `assess_persona_batch_strategy_coverage()`

Schema markers:

- `redthread.persona_strategy_coverage.v1`
- `redthread.persona_batch_strategy_coverage.v1`

## Safety invariant

Persona quality summaries are not findings.

They cannot:

- create confirmed findings
- create regression cases
- assign severity
- prove a target is vulnerable
- bypass JudgeAgent
- load raw jailbreak prompt bodies

## Gap check

### Security / red-teaming coverage

No gap. Slice 12 only measures persona generation quality. It does not replace PAIR, TAP, Crescendo, or MCTS.

### Evaluation metrics

No gap. The metric is a weak generation-quality check, not a security verdict. JudgeAgent still owns campaign outcomes.

### Defense pipeline

No gap. Defense synthesis remains downstream of confirmed JudgeAgent findings only.

## Acceptance criteria

- A persona with enabled layers returns covered and missing layer lists.
- Coverage summaries reject `raw_prompt_loaded = true`.
- Batch summaries expose aggregate covered and missing layers.
- Tests show missing layers are detected.
- No raw jailbreak prompt body enters the model.

## Verification commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run python -m pytest \
  tests/test_persona_quality.py \
  tests/test_persona_prompt_layers.py \
  tests/test_persona_generator.py -q

uv run ruff check src/redthread/personas tests/test_persona_quality.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run mypy \
  src/redthread/personas \
  tests/test_persona_quality.py
```
