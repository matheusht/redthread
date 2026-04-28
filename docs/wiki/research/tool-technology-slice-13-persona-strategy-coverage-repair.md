---
title: Tool Technology Slice 13 Persona Strategy Coverage Repair
type: research
status: implemented
summary: RPI plan and implementation notes for safely repairing generated personas that miss required prompting-layer strategy coverage.
source_of_truth:
  - docs/wiki/research/tool-technology-slice-11-persona-prompting-layer-profiles.md
  - docs/wiki/research/tool-technology-slice-12-persona-quality-measurement.md
  - src/redthread/personas/prompt_layers.py
  - src/redthread/personas/quality.py
  - src/redthread/personas/generator.py
updated_by: pi
updated_at: 2026-04-27
---

# Tool Technology Slice 13 Persona Strategy Coverage Repair

## Goal

Make persona generation robust when the attacker model returns incomplete `allowed_strategies`.

Plain flow:

```text
generated persona
→ measure missing layer coverage
→ append safe deterministic fallback hints
→ MCTS receives complete strategy set
```

## Research

Slice 11 made the prompt ask for one strategy per enabled layer.

But live models can ignore part of the instruction.

Current gap:

- Missing layer coverage could silently weaken MCTS exploration.
- Retrying the model would cost more and may produce unstable output.
- A deterministic fallback is safer and easier to test.

The safe hints already live in `profile_strategy_hints()`.

## Plan

1. Reuse Slice 12 coverage measurement.
2. Add a repair helper that appends missing safe hints.
3. Do not remove or rewrite model-generated strategies.
4. Avoid duplicates.
5. Wire repair into live persona generation after JSON parsing and fallback trigger strategies.
6. Keep dry-run deterministic behavior intact.

## Implementation

Added to:

```text
src/redthread/personas/quality.py
```

Helper:

```text
repair_persona_strategy_coverage(persona, profile)
```

Updated:

```text
src/redthread/personas/generator.py
```

Behavior:

- If no prompting profile exists, return persona unchanged.
- If strategies already cover all enabled layers, return persona unchanged.
- If coverage is missing, append safe hints from `profile_strategy_hints()`.

## Safety invariant

Repair uses only metadata-derived safe hints.

It does not:

- call a model again
- import raw prompt bodies
- synthesize jailbreak text
- ask for hidden chain-of-thought
- create findings or regression cases

## Gap check

### Security / red-teaming coverage

No gap. This improves strategy inputs for existing attack algorithms. It does not create a new attack verdict path.

### Evaluation metrics

No gap. Repair output is still pre-attack planning data. JudgeAgent still scores attack traces.

### Defense pipeline

No gap. Defense synthesis remains downstream of confirmed JudgeAgent findings only.

## Acceptance criteria

- Missing layer hints are appended deterministically.
- Existing model strategies are preserved.
- Duplicate hints are not appended.
- Live-generation path repairs incomplete `allowed_strategies`.
- Tests prove repair behavior with a fake attacker target.

## Verification commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run python -m pytest \
  tests/test_persona_quality.py \
  tests/test_persona_generator.py -q

uv run ruff check src/redthread/personas tests/test_persona_quality.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run mypy \
  src/redthread/personas \
  tests/test_persona_quality.py
```
