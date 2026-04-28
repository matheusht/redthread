---
title: Tool Technology Slice 17 Persona Weighting Report Artifacts
type: research
status: implemented
summary: RPI plan and implementation notes for persisting persona outcome telemetry and adaptive persona weighting plans as safe operator report artifacts.
source_of_truth:
  - docs/wiki/research/tool-technology-slice-15-persona-outcome-telemetry.md
  - docs/wiki/research/tool-technology-slice-16-adaptive-persona-weighting.md
  - src/redthread/reporting/persona_artifacts.py
  - src/redthread/reporting/persistence.py
updated_by: pi
updated_at: 2026-04-28
---

# Tool Technology Slice 17 Persona Weighting Report Artifacts

## Goal

Persist weak persona telemetry and the derived adaptive weighting plan in the standard campaign report directory.

Plain flow:

```text
CampaignResult.metadata["persona_outcome_telemetry"]
→ OperatorArtifactBundle
→ persona-outcomes.json
→ adaptive-persona-weighting-plan.json
→ manifest links
```

## Research

Slice 15 attached persona outcome telemetry to campaign metadata.
Slice 16 could derive an adaptive weighting plan from that telemetry.

Current gap:

- Standard report persistence wrote only Markdown, JSON, and manifest files.
- Operators had no durable sidecar artifact for the full telemetry or next-run plan.
- The next slice needs a safe file artifact to feed back into `redthread run`.

Useful seams:

- `build_operator_artifact_bundle()` already receives the full `CampaignResult`.
- `write_campaign_report_artifacts()` owns the standard report directory.
- `OperatorReportManifest` is the durable place to link report sidecars.

## Plan

1. Add a small reporting helper for persona sidecar payloads.
2. Validate campaign metadata as `PersonaOutcomeTelemetry`.
3. Derive `AdaptivePersonaWeightingPlan` from the validated telemetry.
4. Attach both payloads to `OperatorArtifactBundle`.
5. Persist `persona-outcomes.json` when telemetry exists.
6. Persist `adaptive-persona-weighting-plan.json` when telemetry exists.
7. Link both sidecars in `manifest.json`.
8. Add Markdown wording that labels the telemetry as weak metadata.

## Gap check

### Security / red-teaming coverage

No gap. This slice only persists already-derived metadata. It does not execute attacks or change PAIR, TAP, Crescendo, or MCTS.

### Evaluation metrics

No gap. The sidecars copy JudgeAgent-owned verdict fields from existing telemetry. They do not create verdicts.

### Defense pipeline

No gap. The report sidecars do not create findings, defenses, or regression cases. Regression evidence remains gated by JudgeAgent-confirmed `AttackResult` objects.

## Implementation

Added:

```text
src/redthread/reporting/persona_artifacts.py
```

Updated:

```text
src/redthread/reporting/models.py
src/redthread/reporting/artifacts.py
src/redthread/reporting/exporters.py
src/redthread/reporting/persistence.py
```

New sidecar names:

- `persona-outcomes.json`
- `adaptive-persona-weighting-plan.json`

`OperatorReportManifest` now includes optional links to both files.

## Safety invariant

Persona report sidecars are weak operator artifacts.

They cannot:

- create confirmed findings
- create regression cases
- assign severity truth
- prove defense coverage
- bypass JudgeAgent
- load raw jailbreak prompt bodies

## Acceptance criteria

- Report bundles include persona telemetry when campaign metadata has it.
- Report bundles include an adaptive weighting plan derived from telemetry.
- Report persistence writes both sidecars only when telemetry exists.
- Manifest links both sidecars when present.
- Markdown says persona telemetry is weak metadata and JudgeAgent owns findings.
- Existing reports still work when telemetry is absent.

## Verification commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run python -m pytest \
  tests/test_persona_report_artifacts.py \
  tests/test_operator_reporting.py \
  tests/test_adaptive_persona_weighting.py -q

uv run ruff check \
  src/redthread/reporting \
  src/redthread/personas \
  tests/test_persona_report_artifacts.py \
  tests/test_operator_reporting.py \
  tests/test_adaptive_persona_weighting.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run mypy \
  src/redthread/reporting \
  src/redthread/personas \
  tests/test_persona_report_artifacts.py \
  tests/test_operator_reporting.py \
  tests/test_adaptive_persona_weighting.py

python3 scripts/wiki_lint.py
```
