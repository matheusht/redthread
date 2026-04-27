---
title: Tool Technology Slice 9 Implementation Plan
type: research
status: implemented
summary: Bounded plan for importing external JSON rows into RedThread weak evidence bundles without creating findings or regression cases.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-8-implementation-plan.md
  - src/redthread/reporting/external_evidence.py
updated_by: codex
updated_at: 2026-04-27
---

# Tool Technology Slice 9 Implementation Plan

## Goal

Give operators a small CLI seam for importing external tool JSON as weak RedThread evidence.

Plain meaning:

```text
promptfoo/garak/Strix/generic JSON
→ redthread evidence import
→ redthread.external_evidence_bundle.v1
```

## Scope

In scope:

- JSON import helper for common payload shapes: list, `results`, `findings`, `items`, or `rows`
- source selection: `promptfoo`, `garak`, `strix`, `generic`
- output bundle file
- CLI command under `redthread evidence import`
- rejection of imported rows that claim confirmed-finding authority
- tests for helper and CLI behavior

Out of scope:

- no external runtime imports
- no full native promptfoo/garak/Strix parser
- no confirmed findings
- no regression cases
- no campaign execution

## Safety invariant

Imported rows are weak evidence only.

The import path must not create:

- `FindingReport`
- `RegressionCase`
- JudgeAgent verdicts
- severity truth

## Implementation checklist

- [x] Add `src/redthread/reporting/external_import.py`.
- [x] Add `redthread evidence import` CLI command.
- [x] Export import helpers from `redthread.reporting`.
- [x] Add tests for promptfoo-style import and overclaim rejection.
- [x] Keep new files below 200 lines.

## Command shape

```bash
redthread evidence import \
  --source promptfoo \
  --input promptfoo-results.json \
  --output artifacts/external-evidence.json
```

## Acceptance criteria

- The output schema is `redthread.external_evidence_bundle.v1`.
- Every item has `evidence_strength: weak_imported_evidence`.
- Every item has `is_confirmed_finding: false`.
- Every item has `requires_judge_confirmation: true`.
- Bad imports that claim confirmed-finding status fail validation.
