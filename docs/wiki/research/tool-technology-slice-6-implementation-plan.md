---
title: Tool Technology Slice 6 Implementation Plan
type: research
status: implemented
summary: Exact implementation plan for guide-style operator artifacts, Markdown/JSON exports, detector-hint limitation wording, and regression-link report visibility.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-5-implementation-plan.md
  - src/redthread/models.py
  - src/redthread/core/regression_cases.py
updated_by: codex
updated_at: 2026-04-27
---

# Tool Technology Slice 6 Implementation Plan

## Goal

Make RedThread campaign output useful to operators without changing attack execution.

Plain meaning:

```text
campaign result
→ guide-style operator artifact bundle
→ markdown report
→ JSON report
→ detector hints shown as weak signals
→ confirmed findings linked to regression cases when links exist
```

## Scope

Build the thin reporting/export seam only.

In scope:

- artifact models for rules of engagement, vulnerability report, system security card, PR checklist, stakeholder readout, and regression pack summary
- pure artifact builder from `CampaignResult`
- optional `CampaignPlan` input for exact scope/risk/strategy summaries
- optional regression link input from Slice 5 `finding_regression_link()` output
- Markdown exporter
- JSON exporter
- optional `redthread run --report-md/--report-json` emission path
- focused tests for shape, required sections, JSON output, detector no-overclaim wording, and regression links

Out of scope:

- no attack execution changes
- no JudgeAgent behavior changes
- no defense synthesis changes
- no persistent report directory convention beyond caller-supplied paths
- no full GRC workflow
- no promptfoo/garak/Strix import/export bridge yet

## Safety invariant

Detector hints remain weak evidence.

Reports may show detector hint context and limitations, but findings still require JudgeAgent verdicts:

```text
AttackResult.verdict.is_jailbreak == true
```

Report text must not treat detector hints as proof.

## Implementation checklist

- [x] Add `src/redthread/reporting/models.py`.
- [x] Add `src/redthread/reporting/artifacts.py`.
- [x] Add `src/redthread/reporting/exporters.py`.
- [x] Add `src/redthread/reporting/__init__.py`.
- [x] Add pure `build_operator_artifact_bundle()` helper.
- [x] Add stable schema marker `redthread.operator_artifacts.v1`.
- [x] Add Markdown exporter.
- [x] Add JSON exporter.
- [x] Add optional CLI output flags for one-run report emission.
- [x] Add focused tests.
- [x] Keep new files under the 200-line limit.

## Data contract

### Operator artifact bundle

```json
{
  "schema_version": "redthread.operator_artifacts.v1",
  "campaign_id": "campaign-...",
  "rules_of_engagement": {
    "objective": "...",
    "scope": {"target_ids": ["support-agent-dev"]},
    "risks_tested": ["sensitive_data_exfiltration"],
    "strategies_used": ["static_seed_replay"],
    "limitations": ["Detector hints are weak static signals only; JudgeAgent verdicts own findings."]
  },
  "vulnerability_report": {
    "finding_count": 1,
    "findings": [],
    "judge_verdicts": [],
    "detector_hint_limitations": "weak static signals only; not proof; JudgeAgent owns verdict"
  },
  "security_card": {},
  "pr_checklist": {},
  "stakeholder_readout": {},
  "regression_pack_summary": {}
}
```

## Tests

Implemented in `tests/test_operator_reporting.py`:

- artifact bundle includes scope, risks, strategies, and JudgeAgent verdicts
- regression links appear in finding and regression pack summaries
- Markdown includes all required operator sections
- Markdown says detector hints are weak signals and does not call them proof
- JSON export has stable schema and expected shape

## Validation

Commands to run:

```bash
.venv/bin/python -m pytest tests/test_operator_reporting.py tests/test_regression_cases.py tests/test_detector_hints.py
.venv/bin/ruff check src/redthread/reporting tests/test_operator_reporting.py src/redthread/cli/run.py
.venv/bin/mypy src/redthread/reporting tests/test_operator_reporting.py
python3 scripts/wiki_lint.py
```

## Next slice guidance

Do not broaden this into a GRC product.

Next useful slice:

```text
Slice 7: Report persistence and import/export bridge prep
```

Possible next work:

- campaign output directory convention for reports and regression packs
- promptfoo-style JSON export/import mapping
- garak report import as weak evidence and probe seeds
- operator report linkage in transcript summary
