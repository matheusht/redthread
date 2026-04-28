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
updated_by: pi
updated_at: 2026-04-28
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

## Slice 2 implementation status

Slice 2 is shipped as of 2026-04-26.

Implemented:

- Deterministic `build_campaign_plan()` parser.
- Legacy `CampaignConfig` compatibility through a `legacy_objective` temporary risk plugin.
- Dict-style config parsing for `risks`, `strategies`, and `scope`.
- Custom policy parsing into temporary RedThread-native `RiskPlugin` objects.
- Strategy include/max-cost handling.
- Early failures for unknown risks, unknown strategies, and incompatible risk/strategy selections.
- `CampaignPlan` and `PlannedRisk` models with deterministic `summary_lines()`.

See [Tool Technology Slice 2 Implementation Plan](tool-technology-slice-2-implementation-plan.md) for the exact checklist.

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

## Slice 3 implementation status

Slice 3 is shipped as of 2026-04-26.

Implemented:

- Narrow `AttackStrategyRunner` protocol.
- Minimal async `StrategyTarget` boundary.
- `StrategyRunBudget` for prompt and turn budget propagation.
- `StrategyExecutionError` for early adapter failure.
- `StaticSeedReplayRunner` as the first strategy adapter path.
- Planned campaign to `AttackTrace` smoke path using a fake target.
- Trace metadata for risk plugin id, risk category, risk source, strategy id, strategy family, source policy id, scope target ids, target id, target system prompt, budget, and `judge_required`.
- Scope check that blocks a supplied target id outside `AuthorizedScope.target_ids`.
- Targeted tests for adapter execution, metadata lineage, custom policy source id, budget propagation, unplanned strategy rejection, and scope blocking.

See [Tool Technology Slice 3 Implementation Plan](tool-technology-slice-3-implementation-plan.md) for the exact checklist.

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

## Slice 4 implementation status

Slice 4 is shipped as of 2026-04-26.

Implemented:

- Static weak-signal detector library in `redthread.evaluation.detector_hints`.
- Detector coverage for secret-looking tokens, API-key assignment text, system prompt leakage markers, markdown link exfiltration patterns, SQL/stack/error echoes, sensitive data markers, and prompt-injection success strings.
- Target response scanning across normal turns, Crescendo turns, MCTS nodes, and TAP nodes.
- Serialized `DetectorHint` attachment under `AttackTrace.metadata["detector_hints"]`.
- `detector_hint_summary` with count, max confidence, explicit limitations, and `verdict_owner = JudgeAgent`.
- JudgeAgent integration that attaches hints before scoring context construction.
- Judge prompt context that says detector hints are weak static signals, not verdicts, and JudgeAgent must decide final score from full context.
- Tests for detector positives/negatives, trace metadata serialization, judge context inclusion, and the invariant that a high-confidence hint alone does not create a final finding.

See [Tool Technology Slice 4 Implementation Plan](tool-technology-slice-4-implementation-plan.md) for the exact checklist.

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

## Slice 5 implementation status

Slice 5 is shipped as of 2026-04-26.

Implemented:

- `redthread.core.regression_cases` helper module.
- `regression_case_from_attack_result()` for JudgeAgent-confirmed finding to `RegressionCase` conversion.
- `minimize_attack_trace()` for replay-focused trace reduction across normal, Crescendo, MCTS, and TAP traces.
- `replay_payload_from_regression_case()` for extracting the payload defense validation should replay.
- `validate_regression_case_dry()` using the existing sealed defense replay dry-run path.
- `response_satisfies_expected_safe_behavior()` for lightweight expected-safe-response checks.
- `regression_case_artifact()` with stable `redthread.regression_case.v1` schema marker.
- `finding_regression_link()` for report/export slices to connect findings to regression cases.
- Safety invariant: unconfirmed results cannot create regression cases, so detector hints alone cannot create durable regression memory.
- Targeted tests for conversion, rejection, artifact serialization, expected behavior, dry-run replay, and finding links.

See [Tool Technology Slice 5 Implementation Plan](tool-technology-slice-5-implementation-plan.md) for the exact checklist.

## Sixth implementation slice

```text
Slice 6: Guide-style operator artifacts
```

### Build

- guide-style operator artifact models
- pure campaign-result to artifact-bundle builder
- Markdown exporter
- JSON exporter
- detector-hint limitation wording
- regression-link report visibility
- optional one-run CLI report emission

### Definition of done

- A run can emit Markdown and JSON operator summaries.
- Reports include scope, risks, strategies, JudgeAgent verdicts, detector limitations, defense status, and regression links when present.
- Detector hints are presented as weak signals, not proof.
- Report generation remains separate from attack execution.

## Slice 6 implementation status

Slice 6 is shipped as of 2026-04-27.

Implemented:

- `redthread.reporting.models` for rules of engagement, vulnerability report, security card, PR checklist, stakeholder readout, and regression pack summaries.
- `redthread.reporting.artifacts.build_operator_artifact_bundle()` for pure artifact construction from `CampaignResult` with optional `CampaignPlan`, regression links, and defense status inputs.
- `redthread.reporting.exporters` for stable JSON and Markdown output.
- Optional `redthread run --report-md/--report-json` flags for caller-chosen artifact paths.
- Tests proving report shape, required Markdown sections, stable JSON schema, detector no-overclaim wording, and regression-link visibility.

See [Tool Technology Slice 6 Implementation Plan](tool-technology-slice-6-implementation-plan.md) for the exact checklist.

## Seventh implementation slice

```text
Slice 7: Report persistence and import/export bridge prep
```

### Build

- standard campaign report directory writer
- operator report manifest with stable schema marker
- transcript summary link to the manifest when report persistence is used
- optional `redthread run --report-dir` flag
- durable testing commands and key takeaways page

### Definition of done

- A caller can persist report artifacts under `<report-dir>/<campaign-id>/`.
- The persisted directory contains Markdown, JSON, and `manifest.json`.
- The manifest includes bridge-prep notes that preserve the weak-evidence boundary for future external imports.
- Transcript summaries can point at the manifest without changing attack execution.

## Slice 7 implementation status

Slice 7 is shipped as of 2026-04-27.

Implemented:

- `redthread.reporting.models.OperatorReportManifest` with schema marker `redthread.operator_report_manifest.v1`.
- `redthread.reporting.persistence.write_campaign_report_artifacts()` for standard campaign report directories.
- Optional `redthread run --report-dir` output path.
- `operator_report_manifest` field in transcript summaries when campaign metadata provides it.
- Tests proving manifest persistence and transcript linkage.
- Durable testing commands and takeaways in [Tool Technology Testing Commands and Takeaways](tool-technology-testing-commands-and-takeaways.md).

See [Tool Technology Slice 7 Implementation Plan](tool-technology-slice-7-implementation-plan.md) for the exact checklist.

## Eighth implementation slice

```text
Slice 8: Weak external evidence bridge prep
```

### Build

- weak external evidence models
- source labels for promptfoo, garak, Strix, and generic imports
- candidate probe seed model
- deterministic dictionary mappers
- no-overclaim validation for imported evidence

### Definition of done

- External tool rows can be represented as RedThread-native weak evidence.
- Imported evidence can carry detector hint context and candidate probe seeds.
- Imported evidence cannot claim confirmed-finding status.
- No external tool runtime is imported.

## Slice 8 implementation status

Slice 8 is shipped as of 2026-04-27.

Implemented:

- `redthread.reporting.external_evidence` for weak imported evidence bridge models.
- `ExternalEvidenceBundle` with schema marker `redthread.external_evidence_bundle.v1`.
- `promptfoo_result_to_evidence()`, `garak_result_to_evidence()`, and `strix_finding_to_evidence()` mapping helpers.
- Validation that rejects imported evidence claiming confirmed-finding status or non-weak evidence strength.
- Tests proving promptfoo, garak, Strix, generic bundle, and overclaim rejection behavior.

See [Tool Technology Slice 8 Implementation Plan](tool-technology-slice-8-implementation-plan.md) for the exact checklist.

## Ninth implementation slice

```text
Slice 9: External evidence import CLI
```

### Build

- JSON import helper for common external payload shapes
- `redthread evidence import` command
- output file using `redthread.external_evidence_bundle.v1`
- overclaim rejection for rows that claim confirmed-finding authority

### Definition of done

- promptfoo/garak/Strix/generic JSON rows can become weak evidence bundles.
- Imported evidence remains weak and JudgeAgent-gated.
- No findings, regression cases, or attacks are created by import.

## Slice 9 implementation status

Slice 9 is shipped as of 2026-04-27.

Implemented:

- `redthread.reporting.external_import` for JSON payload import.
- `redthread evidence import` CLI command.
- Tests for promptfoo-style import and bad generic overclaim rejection.

See [Tool Technology Slice 9 Implementation Plan](tool-technology-slice-9-implementation-plan.md) for the exact checklist.

## Tenth implementation slice

```text
Slice 10: External evidence to candidate campaign/probe seeds
```

### Build

- candidate campaign artifact model
- weak evidence bundle to probe-seed conversion
- campaign config hint with static seed replay strategy
- `redthread evidence plan` command

### Definition of done

- Weak evidence bundles can produce candidate probe seeds and campaign hints.
- The artifact is explicitly planning-only and not a finding.
- Operators still run RedThread campaigns for JudgeAgent confirmation.

## Slice 10 implementation status

Slice 10 is shipped as of 2026-04-27.

Implemented:

- `redthread.reporting.external_campaigns` for candidate campaign/probe artifacts.
- Schema marker `redthread.external_campaign_candidates.v1`.
- `redthread evidence plan` CLI command.
- Tests for probe seed extraction, safety notes, and CLI output.

See [Tool Technology Slice 10 Implementation Plan](tool-technology-slice-10-implementation-plan.md) for the exact checklist.

## Eleventh implementation slice

```text
Slice 11: Persona prompting layer profiles
```

### Build

- metadata-only `PromptingLayerProfile` contract
- deterministic tag-to-profile mapping for benchmark fixtures
- safe prompt-layer constraints for `PersonaGenerator`
- transport from `redthread run --benchmark-fixture` into supervisor persona generation
- tests proving raw prompt bodies are not loaded and strategies reflect enabled layers

### Definition of done

- Fixture tags like `plain_language`, `strategic_distraction`, `narrative_embedding`, `eni_writer`, and `reasoning_hijack_attempt` become safe profile fields.
- The persona generation prompt receives profile constraints, not raw jailbreak prompt bodies.
- `allowed_strategies` include concrete tactics for enabled layers.
- JudgeAgent remains the only verdict owner.

## Slice 11 implementation status

Slice 11 is shipped as of 2026-04-27.

Implemented:

- `redthread.personas.prompt_layers` with schema marker `redthread.prompting_layer_profile.v1`.
- `PromptingLayerProfile` builders from fixture tags and fixture records.
- Safe strategy hints for enabled prompting layers.
- Persona-generation prompt constraints that forbid raw prompt body reproduction and hidden chain-of-thought requests.
- Transport through `BenchmarkRunContext`, `CampaignConfig`, `redthread run`, and supervisor persona generation.
- Tests for tag mapping, prompt rendering, CLI transport, supervisor transport, and dry-run allowed strategies.

See [Tool Technology Slice 11 Persona Prompting Layer Profiles](tool-technology-slice-11-persona-prompting-layer-profiles.md) for the exact checklist.

## Twelfth implementation slice

```text
Slice 12: Persona quality measurement
```

Build:

- weak `PersonaStrategyCoverage` summaries
- batch coverage summaries
- explicit covered/missing layer lists
- tests proving missing layer detection

Status: shipped as of 2026-04-27.

See [Tool Technology Slice 12 Persona Quality Measurement](tool-technology-slice-12-persona-quality-measurement.md).

## Thirteenth implementation slice

```text
Slice 13: Persona strategy coverage repair
```

Build:

- deterministic repair of missing safe layer hints
- no live retry required
- no rewriting of model-generated strategies
- integration in live persona generation after parsing

Status: shipped as of 2026-04-27.

See [Tool Technology Slice 13 Persona Strategy Coverage Repair](tool-technology-slice-13-persona-strategy-coverage-repair.md).

## Fourteenth implementation slice

```text
Slice 14: Persona batch layer planning
```

Build:

- per-persona prompting-layer profile distribution
- non-empty layer allocation for multi-persona batches
- aggregate batch coverage tests
- no new CLI flags

Status: shipped as of 2026-04-27.

See [Tool Technology Slice 14 Persona Batch Layer Planning](tool-technology-slice-14-persona-batch-layer-planning.md).

## Fifteenth implementation slice

```text
Slice 15: Persona outcome telemetry
```

Build:

- weak persona-level outcome records
- aggregate persona outcome telemetry in campaign metadata
- near-miss/skipped/error labels that are not findings
- confirmed jailbreak count copied only from `JudgeVerdict.is_jailbreak`

Status: shipped as of 2026-04-27.

See [Tool Technology Slice 15 Persona Outcome Telemetry](tool-technology-slice-15-persona-outcome-telemetry.md).

## Sixteenth implementation slice

```text
Slice 16: Adaptive persona weighting
```

Build:

- planning-only `AdaptivePersonaWeightingPlan`
- one deterministic weight per enabled prompting layer
- stronger weighting for JudgeAgent-confirmed jailbreak layers
- weaker exploration weighting for near-miss layers
- optional weighted prompting-layer batch distribution
- optional `PersonaGenerator.generate_batch()` plan support
- optional `CampaignConfig.persona_weighting_plan` supervisor transport
- regression evidence gate tests proving near misses do not create regression cases

Status: shipped as of 2026-04-28.

See [Tool Technology Slice 16 Adaptive Persona Weighting](tool-technology-slice-16-adaptive-persona-weighting.md).

## Seventeenth implementation slice

```text
Slice 17: Persona weighting report artifacts
```

Build:

- report bundle fields for weak persona telemetry and adaptive weighting plans
- standard report sidecars: `persona-outcomes.json` and `adaptive-persona-weighting-plan.json`
- manifest links to the sidecars when telemetry exists
- Markdown wording that labels persona telemetry as weak metadata

Status: shipped as of 2026-04-28.

See [Tool Technology Slice 17 Persona Weighting Report Artifacts](tool-technology-slice-17-persona-weighting-report-artifacts.md).

## Eighteenth implementation slice

```text
Slice 18: Persona weighting CLI reuse
```

Build:

- validated `adaptive-persona-weighting-plan.json` loader
- `redthread run --persona-weighting-plan PATH`
- `CampaignConfig.persona_weighting_plan` CLI transport
- raw prompt body key rejection at the file boundary

Status: shipped as of 2026-04-28.

See [Tool Technology Slice 18 Persona Weighting CLI Reuse](tool-technology-slice-18-persona-weighting-cli-reuse.md).

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
