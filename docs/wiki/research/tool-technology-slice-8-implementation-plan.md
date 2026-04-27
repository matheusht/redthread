---
title: Tool Technology Slice 8 Implementation Plan
type: research
status: implemented
summary: Bounded plan for weak external evidence bridge models and safe promptfoo/garak/Strix mapping helpers without external runtime imports or auto-created findings.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-7-implementation-plan.md
  - docs/wiki/research/tool-technology-testing-commands-and-takeaways.md
  - src/redthread/reporting/models.py
updated_by: codex
updated_at: 2026-04-27
---

# Tool Technology Slice 8 Implementation Plan

## Goal

Prepare RedThread for external report import/export without trusting external tools as finding owners.

Plain meaning:

```text
external tool report row
→ RedThread weak external evidence
→ optional detector hint / probe seed context
→ JudgeAgent still required for confirmed findings
```

## Scope

Build safe bridge-prep models and deterministic mapping helpers only.

In scope:

- weak external evidence models with stable schema marker
- source labels for promptfoo, garak, Strix, and generic imports
- candidate probe seed representation
- mapper helpers from plain dictionaries
- no-overclaim validation that prevents imported evidence from claiming confirmed-finding status
- tests for promptfoo, garak, Strix, generic evidence, and rejection of overclaiming imports

Out of scope:

- no promptfoo/garak/Strix runtime imports
- no file parser for full native external report formats
- no automatic `RegressionCase` creation
- no automatic `FindingReport` creation
- no JudgeAgent execution changes
- no CLI command yet

## Safety invariant

External imports are weak evidence only.

They may suggest a probe seed or detector hint context, but they cannot create a confirmed finding. A confirmed finding still requires:

```text
AttackResult.verdict.is_jailbreak == true
```

## Implementation checklist

- [x] Add weak evidence bridge models in `src/redthread/reporting/external_evidence.py`.
- [x] Add source-specific dictionary mappers for promptfoo, garak, and Strix.
- [x] Enforce weak evidence labels and reject confirmed-finding overclaims.
- [x] Export helpers from `src/redthread/reporting/__init__.py`.
- [x] Add focused tests in `tests/test_external_evidence_bridge.py`.
- [x] Update roadmap, wiki index, and wiki log.
- [x] Run focused tests, Ruff, mypy, and wiki lint.

## Data contract

Schema marker:

```text
redthread.external_evidence_bundle.v1
```

Evidence item invariant:

```json
{
  "evidence_strength": "weak_imported_evidence",
  "is_confirmed_finding": false,
  "requires_judge_confirmation": true
}
```

## Acceptance criteria

- Imported evidence is always labeled weak.
- Imported evidence cannot mark itself as a confirmed finding.
- Candidate probe seeds preserve source lineage.
- Detector hint context is optional and remains non-verdict context.
- Tests prove promptfoo/garak/Strix mappings do not overclaim.
