---
title: Tool Technology Slice 1 Implementation Plan
type: research
status: active
summary: Exact implementation checklist for Slice 1 of RedThread-native tool technology incorporation: contracts, built-in registries, tests, and no execution wiring.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-assessment.md
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/product.md
  - docs/TECH_STACK.md
  - docs/algorithms.md
updated_by: codex
updated_at: 2026-04-26
---

# Tool Technology Slice 1 Implementation Plan

## Goal

Implement Slice 1 from the incorporation roadmap.

Slice 1 means:

```text
contracts + registries + built-in sample plugin/strategy catalogs
```

It does **not** mean campaign execution changes yet.

## Why this slice matters

RedThread needs native concepts before it can safely absorb ideas from promptfoo, garak, Strix, DeepEval, Giskard, and AI-Red-Teaming-Guide.

This slice creates the vocabulary:

- `RiskPlugin` — what risk/policy to test
- `AttackStrategySpec` — how RedThread can attack it
- `DetectorHint` — weak evidence signal, not final verdict
- `AuthorizedScope` — hard scope boundary
- `RegressionCase` — durable replay target for confirmed failures

## Boundaries

### In scope

- Small Pydantic models.
- Built-in risk plugin registry.
- Built-in attack strategy registry.
- Validation tests.
- Registry lookup/filter tests.
- Scope helper tests.
- No new external runtime dependency.

### Out of scope

- No promptfoo runtime.
- No garak runtime.
- No Strix runtime.
- No campaign execution wiring.
- No CLI commands.
- No JudgeAgent changes.
- No defense synthesis changes.
- No report exporter changes.

## Planned package layout

Because `src/redthread/models.py` already exists as a module and is above the preferred file-size limit, this slice will not add more code there.

Use orchestration-local model modules instead:

```text
src/redthread/orchestration/models/risk_plugin.py
src/redthread/orchestration/models/attack_strategy.py
src/redthread/orchestration/models/authorized_scope.py
src/redthread/orchestration/models/detector_hint.py
src/redthread/orchestration/models/regression_case.py
src/redthread/core/plugins/registry.py
src/redthread/core/plugins/builtin.py
src/redthread/core/strategies/registry.py
src/redthread/core/strategies/builtin.py
```

Reason: these are campaign-planning contracts, not legacy global model additions.

## Exact implementation checklist

### Models

- [x] Add `RiskCategory` enum.
- [x] Add `TargetType` enum.
- [x] Add `RiskPlugin` model.
- [x] Add `StrategyFamily` enum.
- [x] Add `CostLevel` enum.
- [x] Add `AttackStrategySpec` model.
- [x] Add `AuthorizedScope` model.
- [x] Add scope helper methods:
  - [x] `allows_target()`
  - [x] `allows_tool()`
  - [x] `allows_domain()`
- [x] Add `DetectorHint` model.
- [x] Add `RegressionCase` model.
- [x] Export new models from `redthread.orchestration.models`.

### Registries

- [x] Add `RiskPluginRegistry`.
- [x] Add duplicate-id protection.
- [x] Add `get()` lookup.
- [x] Add sorted `list()` output.
- [x] Add filtering by category, target type, and framework tag.
- [x] Add built-in risk plugins:
  - [x] `prompt_injection`
  - [x] `system_prompt_leakage`
  - [x] `sensitive_data_exfiltration`
  - [x] `unsafe_tool_use`
  - [x] `cross_session_data_leak`
  - [x] `unauthorized_action`
- [x] Add `AttackStrategyRegistry`.
- [x] Add duplicate-id protection.
- [x] Add compatibility lookup by plugin id.
- [x] Add built-in strategy specs:
  - [x] `pair`
  - [x] `tap`
  - [x] `crescendo`
  - [x] `gs_mcts`
  - [x] `static_seed_replay`

### Tests

- [x] Add risk plugin registry tests.
- [x] Add attack strategy registry tests.
- [x] Add authorized scope tests.
- [x] Add model validation/serialization tests.
- [x] Confirm no external runtime package was added.

### Verification

- [x] Run targeted tests for Slice 1.
- [x] Run wiki lint.
- [x] Mine wiki changes into MemPalace.
- [x] Keep files small and single-purpose.

## Acceptance criteria

- A developer can list built-in risk plugins.
- A developer can list built-in attack strategy specs.
- A developer can resolve `prompt_injection + crescendo` as a compatible pair.
- `AuthorizedScope` blocks denied targets/tools/domains by helper method.
- `DetectorHint` validates confidence range.
- `RegressionCase` serializes cleanly.
- No campaign execution changed.
- No external runtime dependency added.

## Follow-up slice

Next slice should be Slice 2:

```text
Campaign config planning path
```

That means parsing risk/strategy/scope fields into a deterministic campaign plan, while keeping old campaign configs working.
