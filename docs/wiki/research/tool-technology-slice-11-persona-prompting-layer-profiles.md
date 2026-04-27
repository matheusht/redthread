---
title: Tool Technology Slice 11 Persona Prompting Layer Profiles
type: research
status: implemented
summary: Bounded plan and RPI findings for adding metadata-only onion/ENI prompting-layer profiles to PersonaGenerator without copying raw jailbreak prompts or changing JudgeAgent ownership.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/concepts/peeling-onions.md
  - docs/wiki/entities/eni-writer-persona.md
  - docs/wiki/decisions/jailbreak-benchmark-material-vault.md
  - src/redthread/benchmarks/run_context.py
  - src/redthread/personas/generator.py
  - src/redthread/personas/generation_support.py
updated_by: pi
updated_at: 2026-04-27
---

# Tool Technology Slice 11 Persona Prompting Layer Profiles

## Goal

Add a safe persona prompting layer between benchmark fixture metadata and `PersonaGenerator`.

Plain flow:

```text
benchmark fixture tags
→ PromptingLayerProfile
→ safe persona-generation constraints
→ allowed_strategies diversity
→ normal RedThread campaign
→ JudgeAgent still owns verdicts
```

## Research findings

### Current fixture path

`redthread run --benchmark-fixture spiritual-spell-0032` already loads fixture metadata through `src/redthread/benchmarks/run_context.py`.

It appends safe context to the campaign objective and records metadata such as:

- fixture ids
- families
- technique tags
- persona tags
- attack layers
- `raw_prompt_loaded = false`

It does not load raw corpus prompts.

### Current persona path

`src/redthread/orchestration/supervisor.py` calls:

```python
PersonaGenerator.generate_batch(objective=config.objective, count=config.num_personas)
```

`PersonaGenerator.generate()` currently builds one attacker prompt from:

- objective
- ATLAS tactic and technique
- psychological triggers

It does not receive a typed onion/ENI layer profile.

### Current safe metadata

The Spiritual Spell fixture builder already emits safe tags:

- `plain_language`
- `strategic_distraction`
- `narrative_embedding`
- `persona_modulation`
- `reasoning_hijack_attempt`
- `injection_rebuttal`
- `eni_writer`
- attack layers like `reasoning`, `persona`, and `guardrail_rebuttal`

These tags are enough for strategy shaping. Raw prompt bodies are not needed.

### Wiki research boundary

The wiki pages for Peeling Onions and ENI Writer Persona describe method families. They are research synthesis, not prompt source material.

Implementation must use labels and constraints only.

## Planning approach

Build a small typed profile in the persona package.

Do not add CLI flags like:

```text
--plain-language
--strategic-distraction
--narrative-embedding
```

Use existing fixture metadata from:

```text
--benchmark-fixture spiritual-spell-0032
```

## Data contract

Add a small profile:

```text
redthread.prompting_layer_profile.v1
```

Fields:

- `plain_language`
- `strategic_distraction`
- `narrative_embedding`
- `persona_modulation`
- `guardrail_rebuttal_resilience`
- `reasoning_boundary_pressure`
- `source_fixture_ids`
- `raw_prompt_loaded = false`
- `raw_prompt_policy`

Safe tag mapping:

| Source tag | Profile field |
|---|---|
| `plain_language` | `plain_language` |
| `strategic_distraction` | `strategic_distraction` |
| `narrative_embedding` or layer `narrative` | `narrative_embedding` |
| `persona_modulation`, `eni_writer`, or layer `persona` | `persona_modulation` |
| `injection_rebuttal`, `guardrail_rebuttal`, or `eni_writer` | `guardrail_rebuttal_resilience` |
| `reasoning_hijack_attempt` or layer `reasoning` | `reasoning_boundary_pressure` |

Use the safe name `reasoning_boundary_pressure`. Do not ask for hidden chain-of-thought.

## Implementation checklist

- [x] Add `src/redthread/personas/prompt_layers.py`.
- [x] Add `PromptingLayerProfile` with schema marker `redthread.prompting_layer_profile.v1`.
- [x] Add deterministic builders from fixture tags and fixture records.
- [x] Add safe strategy hints for enabled layers.
- [x] Add prompt rendering helper in `generation_support.py`.
- [x] Update `PERSONA_GENERATION_PROMPT` with metadata-only constraints.
- [x] Update `PersonaGenerator.generate()` and `generate_batch()` to accept an optional profile.
- [x] Transport the profile through `BenchmarkRunContext`, `CampaignConfig`, CLI run config, and supervisor persona generation.
- [x] Keep raw prompt bodies out of source, tests, docs, and generated prompts.
- [x] Add focused tests for tag mapping, prompt rendering, CLI transport, supervisor transport, and dry-run allowed strategies.

## Safety invariant

Prompting-layer profiles are not findings.

They only shape persona diversity. They cannot:

- create confirmed findings
- create regression cases
- assign severity
- prove defenses work
- bypass JudgeAgent
- load raw jailbreak prompt bodies

Only `AttackResult.verdict.is_jailbreak == true` can become durable regression memory.

## Gap check

### Security / red-teaming coverage

No gap. This slice does not replace PAIR, TAP, Crescendo, MCTS, or static replay. It only gives persona generation better metadata-derived strategy constraints.

### Evaluation metrics

No gap. The plan leaves `JudgeAgent` as verdict owner. Prompting profiles are weak planning context only.

### Defense pipeline

No gap. Defense synthesis and regression promotion remain downstream of confirmed JudgeAgent findings. This slice does not promote detector hints, fixture tags, or generated personas into defenses.

## Acceptance criteria

- Fixture metadata tags create a deterministic profile.
- The profile reaches `PersonaGenerator` during normal `redthread run --benchmark-fixture` campaigns.
- Persona prompt text says raw prompt bodies are not loaded.
- Persona prompt text forbids hidden chain-of-thought requests.
- Dry-run persona `allowed_strategies` reflect enabled layers.
- No raw Spiritual Spell prompt body is copied into source, tests, docs, or wiki.

## Verification commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run python -m pytest \
  tests/test_persona_prompt_layers.py \
  tests/test_persona_generator.py \
  tests/test_run_benchmark_fixture_cli.py -q

uv run ruff check \
  src/redthread/personas \
  src/redthread/benchmarks/run_context.py \
  src/redthread/cli/run.py \
  src/redthread/orchestration/supervisor.py \
  tests/test_persona_prompt_layers.py \
  tests/test_persona_generator.py \
  tests/test_run_benchmark_fixture_cli.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run mypy \
  src/redthread/personas \
  src/redthread/benchmarks/run_context.py \
  src/redthread/cli/run.py \
  src/redthread/orchestration/supervisor.py \
  tests/test_persona_prompt_layers.py \
  tests/test_persona_generator.py \
  tests/test_run_benchmark_fixture_cli.py

python3 scripts/wiki_lint.py
```

## Next slice candidate

Slice 12 should measure whether prompting-layer profiles change run quality.

Keep it bounded:

- compare dry-run prompt shape first
- then compare local approved targets only
- record near-miss and refusal patterns as weak evidence
- do not promote anything without JudgeAgent confirmation
