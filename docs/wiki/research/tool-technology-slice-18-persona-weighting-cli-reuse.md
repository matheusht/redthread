---
title: Tool Technology Slice 18 Persona Weighting CLI Reuse
type: research
status: implemented
summary: RPI plan and implementation notes for reusing safe adaptive persona weighting plan artifacts in later redthread run campaigns.
source_of_truth:
  - docs/wiki/research/tool-technology-slice-16-adaptive-persona-weighting.md
  - docs/wiki/research/tool-technology-slice-17-persona-weighting-report-artifacts.md
  - src/redthread/cli/persona_weighting.py
  - src/redthread/cli/run.py
updated_by: pi
updated_at: 2026-04-28
---

# Tool Technology Slice 18 Persona Weighting CLI Reuse

## Goal

Let an operator feed a safe `adaptive-persona-weighting-plan.json` artifact into a later `redthread run` campaign.

Plain flow:

```text
previous report/adaptive-persona-weighting-plan.json
→ redthread run --persona-weighting-plan ...
→ CampaignConfig.persona_weighting_plan
→ supervisor validation
→ weighted persona batch planning
```

## Research

Slice 16 already added optional `CampaignConfig.persona_weighting_plan` transport and supervisor validation.
Slice 17 persisted the derived plan as a report sidecar.

Current gap:

- There was no operator-facing CLI path from the sidecar file back into a later run.
- Operators would need custom Python to reuse the plan.
- Raw prompt body safeguards needed to hold at the file boundary too.

Useful seams:

- `redthread run` already builds `CampaignConfig`.
- `AdaptivePersonaWeightingPlan` already validates the schema and rejects `raw_prompt_loaded=True`.
- The existing supervisor path already treats the plan as optional.

## Plan

1. Add a small CLI helper to load weighting plan files.
2. Parse JSON and validate it as `AdaptivePersonaWeightingPlan`.
3. Reject unsafe raw-prompt keys before model validation.
4. Add `redthread run --persona-weighting-plan PATH`.
5. Pass the validated payload into `CampaignConfig.persona_weighting_plan`.
6. Add focused CLI tests for accepted, rejected, and raw-prompt-key plans.

## Gap check

### Security / red-teaming coverage

No gap. This slice only changes plan reuse. It does not create new attack strategies.

### Evaluation metrics

No gap. The CLI flag does not create evaluation truth. JudgeAgent still owns verdicts.

### Defense pipeline

No gap. The reused plan can bias next-run persona layer exploration, but it cannot create findings, regression cases, or defense validation evidence.

## Implementation

Added:

```text
src/redthread/cli/persona_weighting.py
```

Updated:

```text
src/redthread/cli/run.py
```

New CLI flag:

```bash
redthread run \
  --objective "Retest trusted instruction handling" \
  --system-prompt "Do not reveal secrets." \
  --persona-weighting-plan reports/<campaign-id>/adaptive-persona-weighting-plan.json
```

## Safety invariant

The weighting plan is a planning hint only.

The CLI loader rejects:

- malformed JSON
- malformed adaptive weighting schema
- `raw_prompt_loaded=true`
- raw prompt body keys such as `raw_prompt_body`

The loaded plan cannot:

- create confirmed findings
- create regression cases
- set severity truth
- bypass JudgeAgent

## Acceptance criteria

- CLI accepts a valid adaptive persona weighting plan artifact.
- CLI passes the validated JSON into `CampaignConfig.persona_weighting_plan`.
- CLI rejects unsafe plans before campaign execution.
- Raw prompt body keys are rejected.
- Existing benchmark fixture CLI behavior still works.

## Verification commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run python -m pytest \
  tests/test_persona_weighting_cli.py \
  tests/test_run_benchmark_fixture_cli.py \
  tests/test_adaptive_persona_weighting.py -q

uv run ruff check \
  src/redthread/cli \
  src/redthread/personas \
  src/redthread/models.py \
  tests/test_persona_weighting_cli.py \
  tests/test_run_benchmark_fixture_cli.py \
  tests/test_adaptive_persona_weighting.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src uv run mypy \
  src/redthread/cli \
  src/redthread/personas \
  src/redthread/models.py \
  tests/test_persona_weighting_cli.py \
  tests/test_run_benchmark_fixture_cli.py \
  tests/test_adaptive_persona_weighting.py

python3 scripts/wiki_lint.py
```
