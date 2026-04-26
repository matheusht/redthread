---
title: Tool Technology Incorporation Roadmap
type: research
status: active
summary: Detailed next-step roadmap for absorbing selected ideas from promptfoo, garak, Strix, DeepEval, Giskard, and AI-Red-Teaming-Guide into RedThread-native architecture without absorbing whole external runtimes.
source_of_truth:
  - docs/product.md
  - docs/TECH_STACK.md
  - docs/algorithms.md
  - docs/wiki/research/tool-technology-incorporation-assessment.md
  - docs/wiki/research/open-source-redteam-tool-integration-strategy.md
  - docs/wiki/research/ai-red-teaming-guide-redthread-use-case-map.md
  - https://www.promptfoo.dev/docs/red-team/architecture/
  - https://www.promptfoo.dev/docs/red-team/plugins/
  - https://www.promptfoo.dev/docs/red-team/strategies/
  - https://github.com/NVIDIA/garak
  - https://github.com/usestrix/strix
  - https://github.com/requie/AI-Red-Teaming-Guide
updated_by: codex
updated_at: 2026-04-26
---

# Tool Technology Incorporation Roadmap

## Research question

What are the exact next steps for turning the external-tool assessment into RedThread architecture and product work?

## Short answer

Do this in thin, safe layers:

1. Define RedThread-native contracts first.
2. Add registries and static examples second.
3. Route existing PAIR/TAP/Crescendo/GS-MCTS through the strategy contract third.
4. Add garak-style detector hints as weak evidence, not final truth.
5. Add promptfoo-style custom policy input.
6. Add Strix-style scope enforcement before any stronger tool/sandbox execution.
7. Add regression artifacts and report exports after the attack/evidence path is stable.

Do **not** start by importing promptfoo, garak, or Strix runtime code. That creates coupling before RedThread has its own clean abstraction boundary.

## Target end state

RedThread should support a campaign flow like this:

```text
operator declares risks/policies/scope
→ RiskPlugin registry resolves what to test
→ AttackStrategy registry selects how to attack
→ PyRIT-backed target adapter executes attempts
→ detector hints capture cheap signals
→ JudgeAgent gives semantic verdict and severity
→ DefenseSynthesizer proposes fix
→ sandbox validation replays exploit + variants
→ RegressionCase stores durable replay
→ report exporter emits operator artifacts
```

This keeps RedThread's identity clear:

```text
external tools provide ideas, taxonomies, seeds, and interoperability
RedThread owns closed-loop attack → judge → defend → validate → regress
```

## Non-negotiable boundaries

### RedThread must keep

- Python-first implementation.
- LangGraph orchestration boundary.
- PyRIT as target/converter plumbing where it fits.
- JudgeAgent as semantic scoring owner.
- Defense synthesis and sandbox validation as first-class loop stages.
- Deterministic scope and authorization boundaries before stronger execution.
- File/module size discipline: split before files become broad or oversized.

### RedThread must avoid

- Porting promptfoo's TypeScript runtime.
- Forking garak's scanner harness as the campaign engine.
- Importing Strix's broad browser/proxy/terminal runtime into core.
- Letting static detectors create final Critical findings without JudgeAgent review.
- Creating a giant `models.py` or monolithic orchestration file.
- Making `RiskPlugin` responsible for execution, judging, and reporting at once.

## Proposed package layout

Use small files. Keep each piece single-purpose.

```text
src/redthread/models/
  risk_plugin.py              # RiskPlugin, RiskCategory, PluginMetadata
  attack_strategy.py          # AttackStrategySpec, StrategyType, StrategyLayer
  detector_hint.py            # DetectorHint, DetectorEvidence
  authorized_scope.py         # AuthorizedScope, ToolScope, NetworkScope
  regression_case.py          # RegressionCase, ReplayExpectation

src/redthread/core/plugins/
  registry.py                 # RiskPluginRegistry
  builtin.py                  # small built-in plugin list
  custom_policy.py            # policy text → RiskPlugin conversion helpers

src/redthread/core/strategies/
  registry.py                 # AttackStrategyRegistry
  adapters.py                 # wraps PAIR/TAP/Crescendo/GS-MCTS under common interface
  layered.py                  # deterministic strategy layering

src/redthread/evaluation/
  detector_hints.py           # cheap static hints only
  severity_dimensions.py      # guide-style severity model helpers

src/redthread/orchestration/
  campaign_planning.py        # plugin + strategy selection before execution
  scope_enforcement.py        # AuthorizedScope checks before execution/tool use

src/redthread/reporting/
  artifacts.py                # vulnerability report, security card, PR checklist models
  exporters.py                # markdown/json exporters
```

If current repo structure differs, adapt names, but keep the separation:

```text
models = typed contracts
core = algorithms and registries
evaluation = judging/scoring/hints
orchestration = campaign flow
reporting = operator artifacts
```

## Phase 0 — Architecture decision and contracts only

### Goal

Create the stable internal language before wiring behavior.

### Why first

This prevents RedThread from copying external tools too literally. The goal is native RedThread concepts, not a wrapper over someone else's runtime.

### Work items

1. Create typed contracts:
   - `RiskPlugin`
   - `AttackStrategySpec`
   - `DetectorHint`
   - `AuthorizedScope`
   - `RegressionCase`
2. Add enums and metadata fields:
   - risk category
   - target type
   - modality
   - language
   - framework tags: OWASP, MITRE ATLAS, NIST AI RMF
   - cost level
   - destructive/semi-destructive flag
3. Create one small registry interface:
   - register plugin
   - list plugins
   - get plugin by id
   - filter by target/risk/framework tag
4. Add docs for contract meaning.

### Suggested first models

```text
RiskPlugin
  id
  name
  category
  description
  policy_text
  examples
  expected_failure_modes
  applicable_target_types
  default_strategy_ids
  judge_rubric_id
  tags

AttackStrategySpec
  id
  name
  family
  description
  compatible_plugin_ids
  cost_level
  max_turns
  uses_llm_attacker
  supports_layering
  safety_requirements

DetectorHint
  id
  source
  confidence
  evidence_text
  detector_name
  limitations
  trace_ref

AuthorizedScope
  target_ids
  allowed_tools
  denied_tools
  allowed_domains
  denied_domains
  workspace_roots
  can_use_network
  can_execute_code
  user_text_cannot_expand_scope

RegressionCase
  id
  source_finding_id
  minimized_trace
  expected_safe_behavior
  replay_schedule
  severity_at_creation
```

### Acceptance criteria

- Contracts exist and import cleanly.
- No runtime behavior changes yet.
- Tests cover validation and defaults.
- Contracts do not depend on promptfoo, garak, or Strix packages.
- No file crosses the repo line-count limit.

### Tests

- unit tests for model construction
- invalid field validation
- registry add/get/list/filter behavior
- serialization round-trip

## Phase 1 — Built-in plugin and strategy registries

### Goal

Make RedThread campaign planning plugin-driven without changing core algorithms yet.

### Work items

1. Add a built-in `RiskPluginRegistry`.
2. Seed it with a small list only:
   - prompt injection
   - system prompt leakage
   - sensitive data exfiltration
   - unsafe tool use
   - cross-session data leak
   - unauthorized action
3. Add an `AttackStrategyRegistry` with specs for existing RedThread algorithms:
   - PAIR
   - TAP
   - Crescendo
   - GS-MCTS
   - static seed replay
4. Add compatibility mapping:
   - which strategies are sane defaults for which plugins
   - which strategies need multi-turn target support
   - which strategies need stronger scope review

### Why this matters

This imports promptfoo/garak's best taxonomy idea while preserving RedThread's algorithms.

### Acceptance criteria

- A campaign can resolve `risk ids → plugin specs → strategy specs`.
- Existing attack engines are not rewritten.
- Strategy registry can explain why a strategy was selected.
- Unknown risk ids fail clearly.

### Tests

- plugin lookup
- strategy lookup
- compatibility filter
- error for unsupported plugin/strategy pair
- snapshot-style test for default registry contents

## Phase 2 — Campaign config support

### Goal

Let operators declare risks, policies, strategies, and scope in campaign config.

### Example config target

```yaml
campaign:
  name: support-agent-security-pass

scope:
  targets:
    - support-agent-dev
  allowed_domains:
    - dev.example.com
  allowed_tools:
    - target_llm
  denied_tools:
    - shell
  user_text_cannot_expand_scope: true

risks:
  - id: prompt_injection
  - id: sensitive_data_exfiltration
  - custom_policy:
      id: no-contractual-commitments
      text: "The assistant must not make binding contractual commitments."

strategies:
  include:
    - crescendo
    - tap
    - static_seed_replay
  max_cost: medium

judge:
  severity_dimensions:
    - exploitability
    - user_impact
    - autonomy
    - blast_radius
    - recoverability
```

### Work items

1. Extend `CampaignConfig` carefully or add a nested config model.
2. Parse `risks` into `RiskPlugin` instances.
3. Parse custom policy entries.
4. Parse `scope` into `AuthorizedScope`.
5. Produce a campaign plan object before execution.
6. Add operator-readable planning summary.

### Acceptance criteria

- Old campaign configs still work.
- New risk/strategy config produces deterministic plan.
- Invalid scope blocks early.
- Custom policy becomes a plugin-like object.

### Tests

- backwards compatibility config test
- custom policy parse test
- invalid scope test
- campaign plan summary test

## Phase 3 — Strategy adapter layer

### Goal

Route existing attack algorithms through a shared strategy interface.

### Important rule

Do not rewrite PAIR/TAP/Crescendo/GS-MCTS. Wrap them.

### Work items

1. Add a narrow `AttackStrategyRunner` protocol.
2. Create adapters:
   - `PairStrategyRunner`
   - `TapStrategyRunner`
   - `CrescendoStrategyRunner`
   - `MctsStrategyRunner`
   - `StaticSeedReplayRunner`
3. Each adapter receives:
   - plugin objective
   - target adapter
   - judge config
   - scope
   - run budget
4. Each adapter returns existing RedThread trace/outcome shapes plus metadata.
5. Add planning metadata to traces:
   - selected plugin id
   - selected strategy id
   - strategy family
   - source policy id

### Acceptance criteria

- At least one existing algorithm runs through the adapter path.
- Old direct path still works during transition.
- Trace metadata shows plugin and strategy ids.
- Strategy adapter has no reporting or defense synthesis responsibility.

### Tests

- fake target adapter run
- adapter metadata test
- budget propagation test
- no-scope-expansion invariant

## Phase 4 — Garak-style detector hints

### Goal

Add cheap weak evidence before JudgeAgent scoring.

### Key rule

Detector hints are not final verdicts.

They are input features for JudgeAgent and report context.

### First detector hints

Start with low-risk static detectors:

- secret-looking tokens
- API key patterns
- obvious system prompt leakage markers
- markdown link exfiltration pattern
- SQL/error stack echo
- sensitive data marker echo
- known prompt injection success strings

### Work items

1. Create `DetectorHint` model.
2. Create `detector_hints.py` with small detector functions.
3. Attach hints to attack traces.
4. Pass hints into JudgeAgent prompt/context as evidence.
5. Show hints in reports as supporting signals.

### Acceptance criteria

- Detector hints can be present with no final finding.
- JudgeAgent remains final severity owner.
- Detector confidence and limitations are visible.
- False positives are labeled as possible hints, not proof.

### Tests

- each detector has positive/negative examples
- hints serialize into trace metadata
- judge context includes hints
- high-confidence hint alone does not create final Critical finding

## Phase 5 — Custom policy plugins

### Goal

Let user business rules become attack objectives, judge rubrics, defense constraints, and regression tests.

### Flow

```text
custom policy text
→ custom RiskPlugin
→ adversarial objectives
→ strategy selection
→ JudgeRubric
→ failed trace
→ defense synthesis constraint
→ regression case
```

### Work items

1. Add custom policy parser.
2. Require id, text, and optional severity tags.
3. Generate default objective templates:
   - direct violation
   - indirect violation
   - multi-turn violation
   - tool-mediated violation
4. Add judge rubric binding.
5. Add report section for custom policies.

### Acceptance criteria

- User can define one custom policy in config.
- RedThread can attack it with at least one strategy.
- JudgeAgent receives the policy text as rubric context.
- Result includes policy id.
- Defense synthesis receives policy text as a constraint.

### Tests

- custom policy parse
- objective generation
- judge rubric context includes policy
- result maps back to policy id

## Phase 6 — Strix-style AuthorizedScope enforcement

### Goal

Make scope structured and enforceable before RedThread gains stronger agentic execution powers.

### Work items

1. Add `AuthorizedScope` to campaign context.
2. Validate target ids and domains before execution.
3. Validate tool usage before tool calls.
4. Make user-provided prompts unable to expand scope.
5. Emit clear blocked-scope evidence.
6. Add scope summary to reports.

### Required invariant

```text
User prompt text can narrow scope, but cannot expand scope.
```

### Acceptance criteria

- Out-of-scope target is blocked before execution.
- Denied tool is blocked before execution.
- Scope block creates operator-readable evidence.
- Scope is included in final report.

### Tests

- allowed target passes
- denied target blocks
- denied tool blocks
- user text cannot add new target
- scope block appears in transcript/report metadata

## Phase 7 — RegressionCase memory

### Goal

Turn confirmed failures into durable replay tests.

### Flow

```text
confirmed finding
→ minimize trace
→ create RegressionCase
→ replay against defended target
→ store result
→ schedule future replay
```

### Work items

1. Create `RegressionCase` model.
2. Add conversion from confirmed attack outcome.
3. Add minimized replay trace format.
4. Add expected safe behavior.
5. Add CLI/report export for regression cases.
6. Optionally store under a stable artifact path.

### Example artifact

```json
{
  "id": "regression-2026-04-26-001",
  "source_finding_id": "finding-123",
  "risk_plugin_id": "sensitive_data_exfiltration",
  "strategy_id": "crescendo",
  "expected_safe_behavior": "refuse to reveal customer PII",
  "replay_schedule": "weekly",
  "severity_at_creation": "high"
}
```

### Acceptance criteria

- Confirmed finding can create a regression case.
- Regression case can replay in dry-run/fake-target mode.
- Report links finding to regression case.
- Defense validation can use the regression case.

### Tests

- finding → regression conversion
- replay artifact serialization
- expected-safe-behavior assertion
- report link test

## Phase 8 — Guide-style operator artifacts

### Goal

Make RedThread outputs enterprise-useful without changing the attack engine.

### Artifacts to add

1. Rules of engagement summary.
2. Vulnerability report.
3. Model/system security card.
4. PR checklist.
5. Stakeholder readout.
6. Regression pack summary.

### Work items

1. Add artifact models.
2. Add markdown exporter.
3. Add JSON exporter.
4. Add report sections for:
   - scope
   - risks tested
   - strategies used
   - evidence
   - judge verdict
   - defense status
   - regression status
   - framework mapping
5. Keep report generation separate from attack execution.

### Acceptance criteria

- One command/run can emit markdown and JSON summaries.
- Reports include scope and limitations.
- Reports do not overclaim detector hints as proof.
- Reports link findings to regression cases.

### Tests

- artifact model tests
- markdown snapshot test
- JSON schema/shape test
- no-overclaim detector wording test

## Phase 9 — Optional external import/export

### Goal

After native concepts exist, use external tools more cleanly.

### Imports

- garak report → RedThread evidence + DetectorHint + possible ProbeSeed
- promptfoo result → RedThread evidence + RegressionCase candidate
- Strix finding → RedThread appsec objective + AuthorizedScope context

### Exports

- RedThread campaign plan → promptfoo-style eval config where useful
- RedThread confirmed findings → guide-style vulnerability report
- RedThread regression cases → pytest/developer-friendly test pack later

### Acceptance criteria

- Imports never bypass JudgeAgent for final severity.
- External provenance is preserved.
- Imported artifacts can feed defense synthesis only after RedThread confirmation.

## First implementation slice

If implementing tomorrow, do this exact slice:

```text
Slice 1: Contracts + registries + one fake planned campaign
```

### Files likely touched

```text
src/redthread/models/risk_plugin.py
src/redthread/models/attack_strategy.py
src/redthread/models/authorized_scope.py
src/redthread/models/detector_hint.py
src/redthread/models/regression_case.py
src/redthread/core/plugins/registry.py
src/redthread/core/plugins/builtin.py
src/redthread/core/strategies/registry.py
tests/test_risk_plugin_registry.py
tests/test_attack_strategy_registry.py
tests/test_authorized_scope.py
```

### Build only

- models
- registries
- built-in sample plugins
- built-in strategy specs
- validation tests

### Do not build yet

- no real attack execution changes
- no garak import
- no promptfoo export
- no sandbox runtime
- no report exporter

### Definition of done

- Tests pass.
- A developer can list built-in risk plugins.
- A developer can list built-in strategy specs.
- A developer can resolve `prompt_injection + crescendo` into a valid plan object.
- No external runtime dependency was added.

## Slice 1 implementation status

Slice 1 is shipped as of 2026-04-26.

Implemented:

- RedThread-native `RiskPlugin`, `AttackStrategySpec`, `AuthorizedScope`, `DetectorHint`, and `RegressionCase` contracts.
- Built-in risk plugin registry.
- Built-in attack strategy registry.
- Compatibility lookup for `prompt_injection + crescendo`.
- Scope helper methods for target, tool, and domain checks.
- Targeted tests for registries, model validation, detector confidence bounds, and regression serialization.

See [Tool Technology Slice 1 Implementation Plan](tool-technology-slice-1-implementation-plan.md) for the exact checklist.

## Second implementation slice

```text
Slice 2: Campaign config planning path
```

### Build

- campaign config parsing for `risks`, `strategies`, and `scope`
- custom policy parse into a temporary plugin object
- deterministic campaign plan summary

### Definition of done

- Existing configs still pass.
- New config fields parse.
- Invalid risk/strategy fails early.
- Operator sees a plan summary before execution.

## Third implementation slice

```text
Slice 3: One strategy adapter path
```

### Build

- wrap one existing attack engine first, preferably static seed replay or Crescendo
- attach plugin/strategy metadata to traces
- keep old path available

### Definition of done

- Fake target smoke test passes through planned campaign → strategy adapter → trace.
- Trace has plugin id and strategy id.
- No defense/report changes yet.

## Fourth implementation slice

```text
Slice 4: Detector hints
```

### Build

- small static detector hint library
- hint attachment to traces
- judge-context inclusion

### Definition of done

- Detector hints appear as evidence.
- JudgeAgent remains verdict owner.
- Report/test language says hints are weak signals.

## Fifth implementation slice

```text
Slice 5: RegressionCase
```

### Build

- confirmed finding → regression case
- replay artifact serialization
- link to defense validation

### Definition of done

- A confirmed finding can generate a replayable regression artifact.
- Defense validation can consume it in fake/dry-run mode.

## Risk register

| Risk | Why it matters | Mitigation |
|---|---|---|
| Abstraction bloat | Too many models before value | Ship thin contracts only, then one end-to-end slice |
| Runtime coupling | External tool internals leak into RedThread | No direct promptfoo/garak/Strix dependency in P0/P1 |
| Detector overclaim | Static matches become false Critical findings | DetectorHint is weak evidence; JudgeAgent owns severity |
| Scope bypass | User prompt expands allowed target/tool area | `user_text_cannot_expand_scope = true` invariant |
| Monolith growth | Models/orchestration become huge | Split modules before adding behavior |
| Product confusion | RedThread looks like a wrapper | Keep closed-loop defense validation as core story |
| CI burden | New config breaks existing campaigns | Backward-compatible parsing and migration tests |

## Open questions before coding

1. Should `RiskPlugin` live under `models/` as Pydantic models or under `core/plugins/` with dataclasses?
2. Should custom policies generate attack objectives deterministically first, or use an LLM planner later?
3. Should detector hints be run before JudgeAgent, after target response, or both?
4. What is the minimum severity dimension set for v1?
5. Where should regression artifacts live on disk?
6. Should the CLI expose `redthread plugins list` and `redthread strategies list` immediately?
7. How much of the guide-style reporting should be markdown-only at first?

## Recommended answers to open questions

1. Use Pydantic models for serialization and validation.
2. Start deterministic. Add LLM planning later only with tests.
3. Run detector hints after target response and before JudgeAgent.
4. Start with: exploitability, user impact, autonomy, blast radius, recoverability.
5. Store regression artifacts under campaign output directories first; add shared library later.
6. Yes, add list commands once registries exist.
7. Start markdown + JSON. Avoid UI work.

## Milestone map

### Milestone A — Native concepts exist

- contracts
- registries
- built-in plugins
- built-in strategies
- tests

Expected value: RedThread has a native language for external-tool ideas.

### Milestone B — Campaign planning uses concepts

- config parse
- custom policy parse
- plan summary
- scope validation

Expected value: operators can declare what to test and how.

### Milestone C — Execution path carries concepts

- one or more strategy adapters
- trace metadata
- detector hints
- JudgeAgent context enrichment

Expected value: concepts affect real campaign evidence.

### Milestone D — Closed loop uses concepts

- defense synthesis receives plugin/policy context
- validation uses regression case
- reports show risk/plugin/strategy lineage

Expected value: RedThread's core differentiator gets stronger.

### Milestone E — Interop becomes clean

- garak import maps to RedThread evidence
- promptfoo export/import maps to RedThread risk/regression concepts
- Strix findings map to scoped appsec objectives

Expected value: integrations become durable because native concepts already exist.

## What success looks like

A strong future RedThread result should read like this:

```text
Risk: sensitive_data_exfiltration
Source: custom policy + OWASP LLM06
Strategy: crescendo layered with authority impersonation
Target: support-agent-dev
Scope: dev.example.com only, no shell, no external network
Detector hints: possible PII marker echo, confidence 0.62
Judge verdict: High, policy violated
Defense: add retrieval filter + response policy guard
Validation: original exploit blocked, two variants blocked
Regression: weekly replay case created
Report: vulnerability report + PR checklist emitted
```

That is better than simple integration.

It shows RedThread absorbed the good ideas and still owns the closed loop.

## Immediate next command for an implementer

Start with Mini-RPI if only adding contracts and registries. Escalate to full RPI once campaign execution changes.

Recommended first task:

```text
Implement Slice 1: RedThread-native RiskPlugin, AttackStrategySpec, AuthorizedScope, DetectorHint, RegressionCase models plus plugin/strategy registries and tests. Do not wire campaign execution yet.
```
