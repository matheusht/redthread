---
title: Tool Technology Slice 14 Persona Batch Layer Planning
type: research
status: implemented
summary: RPI plan and implementation notes for distributing prompting layers across generated persona batches for better strategy diversity.
source_of_truth:
  - docs/wiki/research/tool-technology-slice-11-persona-prompting-layer-profiles.md
  - docs/wiki/research/tool-technology-slice-12-persona-quality-measurement.md
  - src/redthread/personas/prompt_layers.py
  - src/redthread/personas/batch_planning.py
  - src/redthread/personas/generator.py
updated_by: pi
updated_at: 2026-04-27
---

# Tool Technology Slice 14 Persona Batch Layer Planning

## Goal

Spread enabled prompting layers across a persona batch instead of forcing every persona to carry every layer.

Plain flow:

```text
full PromptingLayerProfile
→ per-persona layer profiles
→ diverse generated personas
→ batch coverage summary
```

## Research

Before this slice, `PersonaGenerator.generate_batch()` passed the same full profile to every persona.

That was safe, but blunt:

- every persona saw the same layer constraints
- batch diversity came mostly from tactics and psychological triggers
- layer coverage existed, but was not intentionally distributed

Current useful seams:

- `generate_batch()` already controls per-persona tactic and trigger choice.
- `PromptingLayerProfile.enabled_layers` gives stable layer ordering.
- Slice 12 can measure batch coverage after generation.

## Plan

1. Add a small batch-planning helper.
2. Keep full profile when only one persona is requested.
3. For multi-persona batches, distribute enabled layers round-robin.
4. Never create an empty per-persona profile when a full profile exists.
5. Preserve fixture lineage and raw prompt policy.
6. Pass the per-persona profile into each generation call.

## Implementation

Added:

```text
src/redthread/personas/batch_planning.py
```

Helper:

```text
prompting_layer_profiles_for_batch(profile, count)
```

Updated:

```text
src/redthread/personas/generator.py
```

Behavior:

- `count <= 0` returns no profiles.
- no profile or empty profile stays unchanged.
- one persona receives the full profile.
- multiple personas receive distributed non-empty profiles.
- aggregate batch coverage still covers all enabled layers.

## Safety invariant

Batch planning only rearranges safe metadata labels.

It does not:

- add CLI flags
- load raw prompt bodies
- copy jailbreak text
- alter JudgeAgent verdict ownership
- create findings or regression cases

## Gap check

### Security / red-teaming coverage

No gap. The slice improves diversity of persona strategy inputs but still uses the normal attack algorithms.

### Evaluation metrics

No gap. Batch coverage is weak generation metadata. JudgeAgent remains the only verdict owner.

### Defense pipeline

No gap. Defense synthesis is unchanged and still requires confirmed jailbreaks.

## Acceptance criteria

- A full profile can be split into per-persona profiles.
- Per-persona profiles preserve source fixture ids and raw prompt policy.
- Generated dry-run batches cover all enabled layers.
- Tests prove distribution and aggregate coverage.
- No raw prompt body is loaded.

## Verification commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run python -m pytest \
  tests/test_persona_quality.py \
  tests/test_persona_prompt_layers.py \
  tests/test_run_benchmark_fixture_cli.py -q

uv run ruff check src/redthread/personas tests/test_persona_quality.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run mypy \
  src/redthread/personas \
  tests/test_persona_quality.py
```
