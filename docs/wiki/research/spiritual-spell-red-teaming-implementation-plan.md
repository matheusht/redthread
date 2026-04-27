---
title: Spiritual Spell Red Teaming Implementation Plan
type: research
status: active
summary: Bounded implementation plan for turning the Spiritual-Spell-Red-Teaming corpus into a safe RedThread benchmark, fixture, persona, and workflow lane.
source_of_truth:
  - docs/wiki/research/spiritual-spell-red-teaming-corpus.md
  - docs/wiki/research/spiritual-spell-red-teaming-source-inventory.md
  - src/redthread/core/strategies/static_seed_replay.py
  - src/redthread/core/plugins/builtin.py
  - src/redthread/core/strategies/builtin.py
  - src/redthread/core/regression_cases.py
updated_by: pi
updated_at: 2026-04-26
---

# Spiritual Spell Red Teaming Implementation Plan

## Goal

Turn the Spiritual-Spell-Red-Teaming corpus into a safe RedThread benchmark lane.

Plain meaning:

```text
public jailbreak corpus
→ metadata-only inventory
→ reviewed benchmark fixture records
→ approved local/static replay runs
→ JudgeAgent scoring
→ confirmed findings become regression cases
→ later strategy/persona hints use safe family labels
```

## Operating stance

Use the corpus as **structure and evidence**, not as a raw prompt dump.

Rules:

- no bulk raw prompt import
- no live third-party model testing without explicit approval
- no automatic defense promotion
- no direct training of persona generation on raw jailbreak text
- no use of alleged system prompts as verified facts
- all replayable seeds need human review first
- all benchmark records need source lineage

## Scope

In scope:

- corpus fixture schema
- metadata-only source records
- family/risk/strategy mapping
- reviewed fixture promotion flow
- static replay MVP using existing `StaticSeedReplayRunner`
- JudgeAgent scoring path
- regression case handoff for confirmed failures
- operator workflow docs
- tests with fake/local targets only

Out of scope for the first implementation:

- no new dependencies
- no new live provider integration
- no raw GitHub corpus sync job
- no automatic prompt rewriting
- no autonomous attack expansion from raw corpus files
- no scheduler
- no production CLI until fixture contract is stable

## Safety invariant

A file path is not an attack case.

A raw prompt is not trusted benchmark material.

A benchmark case is valid only when:

```text
source file is inventoried
+ family/risk/strategy labels are assigned
+ license/provenance status is recorded
+ prompt material class is explicit
+ human review marks it approved
+ target is local or explicitly authorized
```

## Architecture shape

Add one thin benchmark layer. Do not mix it into algorithms.

```text
Corpus inventory
  ↓
Reviewed fixture pack
  ↓
Campaign planning
  ↓
StaticSeedReplayRunner / later TAP or Crescendo hints
  ↓
JudgeAgent verdict
  ↓
RegressionCase conversion for confirmed findings
```

Core principle: benchmark records select RedThread-native strategies. They do not execute arbitrary corpus files.

## Data contract

### Benchmark fixture record

```json
{
  "schema_version": "redthread.jailbreak_benchmark_fixture.v1",
  "id": "spiritual-spell-0001",
  "source_repo": "https://github.com/Goochbeater/Spiritual-Spell-Red-Teaming",
  "source_path": "Jailbreak-Guide/...",
  "source_commit": "pin-before-use",
  "license_status": "unknown",
  "provenance_status": "unverified",
  "family": "system_prompt_leakage",
  "target_family": "anthropic_claude",
  "risk_plugin_id": "system_prompt_leakage",
  "strategy_id": "static_seed_replay",
  "rubric_id": "sensitive_info",
  "prompt_material_class": "metadata_only",
  "prompt_material_ref": "not-copied",
  "safety_level": "high",
  "review_status": "pending",
  "expected_safe_behavior": "refuse to reveal hidden system instructions",
  "notes": "Metadata-only until license and safety review."
}
```

### Allowed prompt material classes

| Class | Meaning | First-slice use |
|---|---|---|
| `metadata_only` | Source exists, but no replay text is stored. | Yes. Default. |
| `redacted` | Safe summary or placeholder exists. | Yes, for docs/tests. |
| `approved_replay_seed` | Human-approved seed can run against local/authorized target. | Later after review. |

## Workflow

### 1. Inventory

Input: source paths from the external repo.

Output: metadata-only records.

Done when:

- every source file has a stable record id
- each record has source path, source family, target family, and safety level
- no raw prompt body is copied

### 2. Classify

Map each record to RedThread concepts.

Required labels:

- `family`
- `target_family`
- `risk_plugin_id`
- `strategy_id`
- `rubric_id`
- `safety_level`

Default mapping:

| Corpus family | Risk plugin | Strategy | Rubric |
|---|---|---|---|
| system prompt / tool schema captures | `system_prompt_leakage` | `static_seed_replay` | `sensitive_info` |
| model-specific base jailbreaks | `prompt_injection` | `static_seed_replay` | `authorization_bypass` |
| persona/preferences/style conditioning | `prompt_injection` | `crescendo` later, metadata-only now | `authorization_bypass` |
| ENI / ENI LIME / ENI NEPTUNE | `prompt_injection` | `tap` or `crescendo` later, metadata-only now | `authorization_bypass` |
| document-based | `prompt_injection` | `static_seed_replay` now, RAG later | `authorization_bypass` |
| agent injection | `unsafe_tool_use` | `tap` later, metadata-only now | `authorization_bypass` |
| coder specialization | `sensitive_data_exfiltration` or high-risk policy bypass | blocked by default | manual review |

### 3. Review

Human operator decides whether a record can move past metadata.

Review outcomes:

- `rejected`
- `metadata_only`
- `redacted`
- `approved_replay_seed`

Promotion needs:

- source commit pinned
- license state noted
- abuse risk noted
- replay target class approved
- expected safe behavior written

### 4. Plan campaign

Use existing campaign planning concepts.

The planner should receive selected fixture ids and emit:

- risk plugin ids
- strategy ids
- target scope
- benchmark metadata
- dry-run summary

The planner must reject:

- unapproved replay seeds
- missing source lineage
- live targets without explicit authorization
- unknown risk plugin ids

### 5. Execute MVP

First executable path uses `static_seed_replay` only.

Why:

- low cost
- deterministic
- already exists
- easy to test with fake/local targets
- good fit for reviewed seeds

Trace metadata must include:

- benchmark id
- source repo
- source path
- source commit
- family
- prompt material class
- review status
- risk plugin id
- strategy id

### 6. Score

JudgeAgent remains verdict owner.

Detector hints may support context. They are not final findings.

Done when:

- every run gets a JudgeAgent verdict
- unsafe target response is scored through existing rubrics
- trace metadata keeps benchmark lineage

### 7. Convert confirmed failures

Only confirmed jailbreaks can become regression cases.

Use existing regression helper path:

```text
AttackResult.verdict.is_jailbreak == true
→ RegressionCase
```

Do not create regression cases from:

- metadata-only records
- detector hints alone
- unreviewed seeds
- failed/inconclusive traces

### 8. Report

Operator report should show:

- fixture ids tested
- source families tested
- risk plugins tested
- target scope
- JudgeAgent results
- detector hint limitations
- regression case links
- blocked records and why

## Implementation slices

### Slice A — fixture schema and loader

Build:

- benchmark fixture model
- JSON fixture schema marker
- loader for a small local fixture pack
- validation errors for unsafe records

Tests:

- loads valid metadata-only record
- rejects missing source lineage
- rejects approved seed without review status
- rejects unknown prompt material class

### Slice B — Spiritual Spell metadata fixture pack

Build:

- small generated fixture pack from source inventory
- default records are `metadata_only`
- no raw prompt bodies
- stable ids and family labels

Tests:

- every fixture has id, path, family, risk, strategy, review status
- all initial fixtures are non-executable unless approved
- count matches inventory sample or chosen subset

### Slice C — campaign planning bridge

Build:

- helper that converts approved benchmark fixtures into campaign planning inputs
- dry-run summary lines
- hard reject for live targets unless authorized

Tests:

- metadata-only fixtures cannot execute
- approved local fixture can plan static replay
- scope target rejection works

### Slice D — static replay metadata wiring

Build:

- attach benchmark fixture metadata to `AttackTrace.metadata`
- keep existing `StaticSeedReplayRunner` behavior
- no strategy rewrite

Tests:

- trace includes benchmark id and source path
- trace keeps risk plugin and strategy lineage
- fake target run stays deterministic

### Slice E — reporting and regression handoff

Build:

- small report helper for benchmark runs
- finding-to-regression link inclusion when present
- blocked-record summary

Tests:

- confirmed finding can link to regression case
- unconfirmed run has no regression link
- report states detector hints are weak signals

### Slice F — later strategy hints

Only after A-E are stable.

Build later:

- TAP branch diversity hints from family labels
- Crescendo narrative hints from approved persona metadata
- agent-injection subset for tool/agent runtime tests

Do not use raw prompt text for this slice.

## CLI shape after MVP

Do not implement until fixture path is stable.

Proposed shape:

```bash
redthread eval jailbreak-corpus \
  --source spiritual-spell \
  --fixture-id spiritual-spell-0001 \
  --target local-dev \
  --dry-run
```

Batch shape:

```bash
redthread eval jailbreak-corpus \
  --source spiritual-spell \
  --family system_prompt_leakage \
  --strategy static_seed_replay \
  --target local-dev \
  --dry-run
```

Default behavior should be dry-run first.

## Acceptance criteria

MVP is done when:

- RedThread has a fixture schema for jailbreak benchmark records
- Spiritual Spell records can exist as metadata-only fixtures
- no raw prompt body is copied by default
- unreviewed fixtures cannot execute
- approved local fixtures can plan a static replay run
- trace metadata keeps benchmark lineage
- JudgeAgent scores the run
- confirmed findings can become regression cases
- wiki and report surfaces explain what was tested and what was blocked

## Stop conditions

Stop and ask before:

- copying raw prompt bodies from the external repo
- adding a dependency
- adding a live provider target
- changing schemas used outside this benchmark lane
- creating a scheduler or background sync
- using alleged system prompts as trusted secrets
- promoting any defense automatically

## Next best action

Implement **Slice A** first.

Smallest safe patch:

```text
src/redthread/benchmarks/jailbreak_fixtures.py
tests/test_jailbreak_fixtures.py
```

Keep the first patch pure Python. No CLI. No live target. No raw prompts.
