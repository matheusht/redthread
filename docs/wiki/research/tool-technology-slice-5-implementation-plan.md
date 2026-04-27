---
title: Tool Technology Slice 5 Implementation Plan
type: research
status: implemented
summary: Exact implementation plan for converting JudgeAgent-confirmed findings into durable RegressionCase artifacts with minimized replay payloads, dry-run validation, expected-safe-behavior checks, and finding-to-regression links.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - src/redthread/orchestration/models/regression_case.py
  - src/redthread/models.py
  - src/redthread/core/defense_replay_runner.py
updated_by: codex
updated_at: 2026-04-26
---

# Tool Technology Slice 5 Implementation Plan

## Goal

Turn confirmed RedThread failures into durable replay tests.

Plain meaning:

```text
JudgeAgent confirmed a real bad outcome
→ RedThread keeps the small replay payload
→ RedThread writes a RegressionCase artifact
→ defense validation can dry-run it now
→ future slices can export/report/schedule it
```

## Scope

Build the thin memory seam only.

In scope:

- convert a `JudgeAgent`-confirmed `AttackResult` into `RegressionCase`
- minimize `AttackTrace` into replay-safe fields
- keep risk plugin, strategy, source policy, and detector summary lineage
- serialize the regression artifact with a stable schema marker
- extract replay payload from the minimized trace
- reuse existing sealed defense dry-run validation
- add expected-safe-behavior assertion helper
- add report-friendly finding-to-regression link metadata

Out of scope:

- no persistent artifact directory yet
- no CLI command yet
- no full report exporter yet
- no scheduler runtime yet
- no external promptfoo/garak/Strix import path yet
- no detector-hint-only regression creation

## Safety invariant

A detector hint is not enough.

Regression case creation requires:

```text
AttackResult.verdict.is_jailbreak == true
```

That means `JudgeAgent` owns the finding. Static detector hints can travel inside metadata as supporting context, but cannot create regression cases by themselves.

## Implementation checklist

- [x] Read existing `RegressionCase` model.
- [x] Reuse existing defense replay dry-run path instead of creating another runner.
- [x] Add `redthread.core.regression_cases` helper module.
- [x] Add `RegressionCaseError` for unsafe/malformed conversion.
- [x] Add `RegressionReplaySummary` for replay output.
- [x] Add `regression_case_from_attack_result()`.
- [x] Add `minimize_attack_trace()`.
- [x] Add `replay_payload_from_regression_case()`.
- [x] Add `validate_regression_case_dry()`.
- [x] Add `response_satisfies_expected_safe_behavior()`.
- [x] Add `regression_case_artifact()`.
- [x] Add `finding_regression_link()`.
- [x] Add focused tests.
- [x] Keep files under the 200-line limit.

## Data contract

### Regression artifact

```json
{
  "schema_version": "redthread.regression_case.v1",
  "kind": "regression_case",
  "regression_case": {
    "id": "...",
    "source_finding_id": "...",
    "risk_plugin_id": "sensitive_data_exfiltration",
    "strategy_id": "static_seed_replay",
    "minimized_trace": {
      "trace_id": "...",
      "algorithm": "static_seed_replay",
      "turns": [
        {
          "kind": "turn",
          "turn_number": 1,
          "attacker_prompt": "...",
          "target_response_excerpt": "..."
        }
      ]
    },
    "expected_safe_behavior": "refuse to reveal customer PII",
    "replay_schedule": "weekly",
    "severity_at_creation": "critical"
  }
}
```

### Finding link

```json
{
  "source_finding_id": "result-...",
  "source_trace_id": "trace-...",
  "regression_case_id": "regression-...",
  "risk_plugin_id": "sensitive_data_exfiltration",
  "strategy_id": "static_seed_replay",
  "judge_score": 4.8,
  "status": "regression_case_created"
}
```

## Tests

Implemented in `tests/test_regression_cases.py`:

- confirmed finding creates regression case
- unconfirmed result cannot create regression case
- replay payload extraction works
- artifact serialization includes stable schema and minimized trace
- expected safe behavior detects refusal-style response
- dry-run defense validation consumes regression case
- report link maps finding to regression case

## Validation

Commands run:

```bash
.venv/bin/python -m pytest tests/test_regression_cases.py tests/test_authorized_scope.py tests/test_detector_hints.py tests/test_static_seed_replay_runner.py
.venv/bin/ruff check src/redthread/core/regression_cases.py tests/test_regression_cases.py
.venv/bin/mypy src/redthread/core/regression_cases.py tests/test_regression_cases.py
.venv/bin/python -m pytest tests/test_agentic_security_models.py tests/test_agentic_security_scenarios.py tests/test_campaign_planning.py tests/test_static_seed_replay_runner.py tests/test_detector_hints.py tests/test_regression_cases.py tests/test_risk_plugin_registry.py tests/test_attack_strategy_registry.py tests/test_authorized_scope.py tests/test_judge.py tests/test_judge_execution_records.py
```

Observed result:

- targeted Slice 5 + nearby tests: `30 passed`
- broader nearby suite: `72 passed`
- Ruff: `All checks passed!`
- mypy: `Success: no issues found in 2 source files`

## Next slice guidance

Do not add more regression logic to this helper unless there is a clear artifact/export need.

Next best slice:

```text
Slice 6: Guide-style operator artifacts
```

Build a separate reporting module that can include:

- scope
- risks tested
- strategies used
- JudgeAgent verdicts
- detector hint limitations
- regression case links
- defense validation status
