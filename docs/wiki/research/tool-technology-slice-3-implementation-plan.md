---
title: Tool Technology Slice 3 Implementation Plan
type: research
status: active
summary: Exact implementation checklist for Slice 3 of RedThread-native tool technology incorporation: one strategy adapter path using static seed replay, trace metadata lineage, scope checks, budget propagation, and fake-target smoke tests without defense or reporting changes.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-2-implementation-plan.md
  - docs/product.md
  - docs/TECH_STACK.md
updated_by: codex
updated_at: 2026-04-26
---

# Tool Technology Slice 3 Implementation Plan

## Goal

Implement Slice 3 from the tool technology incorporation roadmap.

Slice 3 means:

```text
planned campaign → one strategy adapter → AttackTrace with plugin/strategy lineage
```

It does **not** mean all algorithms are migrated.

## Why this slice matters

Slice 1 created RedThread-native contracts.

Slice 2 created deterministic campaign planning.

Slice 3 proves the contracts can affect execution evidence without rewriting the old engine.

The key product move is small but important:

```text
RiskPlugin + AttackStrategySpec + AuthorizedScope
→ strategy adapter
→ existing AttackTrace shape
→ metadata usable by JudgeAgent/report/defense later
```

## Strategy choice

Use `static_seed_replay` first.

Why:

- lowest safety risk
- no attacker LLM needed
- no external runtime dependency
- simple fake-target smoke test
- good proof that planned risk/strategy metadata can reach traces
- does not disturb PAIR/TAP/Crescendo/GS-MCTS direct paths

Do **not** wrap Crescendo yet. Crescendo has more product value, but it crosses more runtime and judge seams. That belongs after the adapter contract is proven.

## Boundaries

### In scope

- Add a narrow `AttackStrategyRunner` protocol.
- Add a minimal `StrategyTarget` protocol.
- Add a small `StrategyRunBudget` model.
- Add `StaticSeedReplayRunner`.
- Accept a `CampaignPlan` from Slice 2.
- Select one planned risk that includes `static_seed_replay`.
- Send deterministic replay prompt(s) to a target.
- Return an existing `AttackTrace` object.
- Attach plugin and strategy metadata to `AttackTrace.metadata`.
- Preserve authorized scope target checks.
- Add fake-target smoke tests.

### Out of scope

- No CLI changes.
- No `RedThreadEngine` wiring.
- No LangGraph supervisor changes.
- No JudgeAgent changes.
- No detector hints.
- No defense synthesis changes.
- No report exporter changes.
- No promptfoo/garak/Strix runtime imports.
- No PAIR/TAP/Crescendo/GS-MCTS rewrite.

## Implemented files

```text
src/redthread/core/strategies/runner.py
src/redthread/core/strategies/static_seed_replay.py
tests/test_static_seed_replay_runner.py
```

Updated exports:

```text
src/redthread/core/strategies/__init__.py
```

## Data flow

```text
build_campaign_plan(config)
→ CampaignPlan
→ StaticSeedReplayRunner.run(plan, target=fake_or_real_target, risk_plugin_id=..., target_id=...)
→ select PlannedRisk
→ validate target_id against AuthorizedScope
→ build deterministic replay seed(s)
→ target.send(prompt, conversation_id=...)
→ AttackTrace(turns=[ConversationTurn(...)], metadata={...})
```

## Metadata contract

The runner attaches these keys to `AttackTrace.metadata`:

```text
trace_source = strategy_adapter
risk_plugin_id
risk_plugin_name
risk_category
risk_plugin_source
strategy_id
strategy_family
source_policy_id
plan_objective
scope_target_ids
target_id
target_system_prompt
budget_max_prompts
budget_max_turns
judge_required
```

Important: `judge_required = true` means this trace is evidence only. It is not a confirmed finding.

JudgeAgent still owns final severity and verdict.

## Exact implementation checklist

### Runner contracts

- [x] Add `StrategyTarget` protocol with async `send(prompt, conversation_id)`.
- [x] Add `AttackStrategyRunner` protocol.
- [x] Add `StrategyRunBudget` with prompt and turn budget.
- [x] Add `StrategyExecutionError` for early adapter failures.

### Static seed replay adapter

- [x] Add `StaticSeedReplayRunner`.
- [x] Require that selected risk actually planned `static_seed_replay`.
- [x] Use plugin examples when present.
- [x] Generate a deterministic seed prompt when examples are absent.
- [x] Respect `budget.max_prompts`.
- [x] Send prompts through the target protocol.
- [x] Return existing `AttackTrace` shape.
- [x] Use a deterministic static replay `Persona`.
- [x] Set `algorithm = static_seed_replay`.
- [x] Attach plugin/strategy/scope/budget metadata.
- [x] Mark `judge_required = true`.
- [x] Leave final outcome unconfirmed pending JudgeAgent.

### Scope safety

- [x] Preserve Slice 1/2 `AuthorizedScope` contract.
- [x] If a `target_id` is supplied and plan scope has target ids, block targets outside scope.
- [x] Do not let runtime/user text expand scope.

### Tests

- [x] Fake target smoke test: planned campaign → runner → trace.
- [x] Trace has plugin id and strategy id.
- [x] Custom policy id becomes `source_policy_id`.
- [x] Budget propagates and limits replay prompts.
- [x] Unplanned strategy/risk combination fails early.
- [x] Out-of-scope target id fails early.

## Acceptance criteria

- Fake target smoke test passes through planned campaign → strategy adapter → trace.
- Trace metadata has risk plugin id and strategy id.
- Trace metadata preserves source policy id for custom policies.
- Static replay respects budget.
- Authorized scope blocks denied target ids.
- Existing direct campaign path is untouched.
- No defense/report changes are included.
- No external runtime dependency is added.

## What this unlocks

Slice 3 creates the first real bridge from planning concepts into execution evidence.

Next systems can now consume trace metadata:

- Slice 4 detector hints can attach weak signals to this trace.
- JudgeAgent can later receive risk/plugin context.
- Reports can show risk/strategy lineage.
- Defense synthesis can later use `risk_plugin_id` and `policy_text` when generating guardrails.
- Regression cases can later preserve strategy lineage.

## Follow-up slice

Next slice should be Slice 4:

```text
Detector hints
```

Build small static hint detectors and attach weak evidence to traces. Keep the rule strict:

```text
Detector hints are signals. JudgeAgent owns verdicts.
```
