---
title: Tool Technology Slice 2 Implementation Plan
type: research
status: active
summary: Exact implementation checklist for Slice 2 of RedThread-native tool technology incorporation: campaign planning config parser, custom policies, scope parsing, deterministic plan summaries, and validation tests without execution wiring.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-1-implementation-plan.md
  - docs/product.md
  - docs/TECH_STACK.md
updated_by: codex
updated_at: 2026-04-26
---

# Tool Technology Slice 2 Implementation Plan

## Goal

Implement Slice 2 from the tool technology incorporation roadmap.

Slice 2 means:

```text
campaign config input → deterministic campaign plan
```

It does **not** mean real attack execution yet.

## Why this slice matters

Slice 1 created the vocabulary. Slice 2 makes that vocabulary usable from campaign-like config data.

RedThread should be able to parse:

- old `CampaignConfig` objects
- new risk declarations
- promptfoo-style custom policies
- strategy selection constraints
- Strix-style scope boundaries

Then it should produce an operator-readable plan before any attack runs.

## Boundaries

### In scope

- New planning models.
- Planning function that accepts legacy `CampaignConfig` or a mapping/dict.
- Built-in risk id resolution.
- Custom policy parsing into temporary `RiskPlugin` objects.
- Strategy selection and compatibility validation.
- Scope parsing into `AuthorizedScope`.
- Deterministic plan summary lines.
- Targeted tests.

### Out of scope

- No CLI command changes.
- No attack execution changes.
- No strategy runner adapter.
- No JudgeAgent changes.
- No defense synthesis changes.
- No report exporter changes.
- No external runtime dependency.

## Planned files

```text
src/redthread/core/plugins/custom_policy.py
src/redthread/orchestration/models/campaign_plan.py
src/redthread/orchestration/campaign_planning.py
tests/test_campaign_planning.py
```

Also update exports:

```text
src/redthread/orchestration/models/__init__.py
```

## Exact implementation checklist

### Planning contracts

- [x] Add `CustomPolicyInput` model.
- [x] Add helper to convert custom policy text into a RedThread-native `RiskPlugin`.
- [x] Add `PlannedRisk` model.
- [x] Add `CampaignPlan` model.
- [x] Add deterministic `summary_lines()` helper.

### Planning parser

- [x] Add `build_campaign_plan()`.
- [x] Accept existing `CampaignConfig` with no new fields.
- [x] Accept mapping/dict config with `risks`, `strategies`, and `scope`.
- [x] Parse string risk ids.
- [x] Parse `{id: ...}` risk entries.
- [x] Parse `{custom_policy: {id, text, ...}}` entries.
- [x] Parse `strategies.include`.
- [x] Parse `strategies.max_cost`.
- [x] Parse `scope` into `AuthorizedScope`.
- [x] Validate unknown risk ids early.
- [x] Validate unknown strategy ids early.
- [x] Validate incompatible risk/strategy selections early.

### Tests

- [x] Existing `CampaignConfig` plans successfully.
- [x] New config resolves built-in risks and strategies.
- [x] Custom policy becomes a temporary `RiskPlugin`.
- [x] Scope parses into `AuthorizedScope`.
- [x] Unknown risk fails early.
- [x] Unknown strategy fails early.
- [x] Incompatible strategy fails early.
- [x] Summary lines are deterministic and operator-readable.

## Acceptance criteria

- Existing configs still pass through the planner.
- New risk/strategy/scope fields parse from dict input.
- Custom policy input creates a RedThread-native plugin object.
- Invalid risk or strategy config fails before execution.
- Operator-readable plan summary is available.
- No execution path is changed.
- No external runtime dependency is added.

## Follow-up slice

Next slice should be Slice 3:

```text
One strategy adapter path
```

That should wrap one existing attack engine behind a strategy runner interface and attach plan metadata to traces while keeping old execution paths available.
