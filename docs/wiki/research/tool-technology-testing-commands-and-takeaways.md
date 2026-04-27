---
title: Tool Technology Testing Commands and Takeaways
type: research
status: active
summary: Durable command set and key takeaways from testing the Tool Technology Incorporation slices.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-6-implementation-plan.md
  - tests/test_operator_reporting.py
  - tests/test_regression_cases.py
  - tests/test_detector_hints.py
updated_by: codex
updated_at: 2026-04-27
---

# Tool Technology Testing Commands and Takeaways

## Purpose

Keep the repeatable test commands and lessons from the Tool Technology Incorporation track in one place.

## Focused Slice 6 command set

Use this after touching operator artifacts, detector hints, or regression links:

```bash
.venv/bin/python -m pytest tests/test_operator_reporting.py tests/test_regression_cases.py tests/test_detector_hints.py -q
.venv/bin/ruff check src/redthread/reporting tests/test_operator_reporting.py src/redthread/cli/run.py
.venv/bin/mypy src/redthread/reporting tests/test_operator_reporting.py
python3 scripts/wiki_lint.py
```

Observed result for the Slice 6 ship pass:

```text
23 passed
ruff: All checks passed
mypy: Success: no issues found
wiki-lint: OK
```

## Broader nearby regression command

Use this before committing a reporting/regression/detector slice:

```bash
.venv/bin/python -m pytest \
  tests/test_agentic_security_models.py \
  tests/test_agentic_security_scenarios.py \
  tests/test_campaign_planning.py \
  tests/test_static_seed_replay_runner.py \
  tests/test_detector_hints.py \
  tests/test_regression_cases.py \
  tests/test_operator_reporting.py \
  tests/test_risk_plugin_registry.py \
  tests/test_attack_strategy_registry.py \
  tests/test_authorized_scope.py \
  tests/test_judge.py \
  tests/test_judge_execution_records.py \
  -q
```

Observed result for the Slice 6 ship pass:

```text
76 passed
```

## Dry-run report persistence smoke test

Campaign checked:

```text
campaign-7175a5a6
```

Artifacts checked:

```text
logs/campaign-7175a5a6.jsonl
reports/campaign-7175a5a6/manifest.json
reports/campaign-7175a5a6/operator-report.md
reports/campaign-7175a5a6/operator-report.json
```

Result: success.

Evidence:

- `runtime_mode` was `sealed_dry_run`.
- `telemetry_mode` was `skipped_in_dry_run`.
- `error_count` was `0`.
- `degraded_runtime` was `false`.
- `operator_report_manifest` appeared in the transcript summary.
- The report directory contained Markdown, JSON, and `manifest.json`.
- The operator report showed `0` confirmed findings and `0.0%` attack success rate.
- All three attack results were skipped dry-run traces with `is_jailbreak: false`.

Takeaway: Slice 7 report persistence works for sealed dry runs. The only expected limitation was missing exact campaign-plan scope, so the report correctly said scope was inferred.

## Key takeaways

- Keep new report/export logic pure and outside attack execution.
- Keep detector hints framed as weak static signals, not proof.
- Keep JudgeAgent as the owner of confirmed findings.
- Only `AttackResult.verdict.is_jailbreak == true` should enter finding-style report rows or regression memory flows.
- Use `CampaignPlan` when exact scope, risk, and strategy data are available; otherwise report inferred scope with a limitation.
- Link regression cases through Slice 5 `finding_regression_link()` output instead of making the reporting layer create regression cases.
- Run `wiki_lint.py` whenever adding or changing durable wiki pages.

## Current file-size watch

Slice 6 left the new reporting files below the 200-line limit:

```text
src/redthread/reporting/__init__.py
src/redthread/reporting/models.py
src/redthread/reporting/artifacts.py
src/redthread/reporting/exporters.py
```

Future slices should split before a reporting file crosses 200 lines.
