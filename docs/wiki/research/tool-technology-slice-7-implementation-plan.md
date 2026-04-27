---
title: Tool Technology Slice 7 Implementation Plan
type: research
status: implemented
summary: Bounded plan for report persistence, manifest files, transcript report links, and import/export bridge prep without importing external runtimes.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-6-implementation-plan.md
  - docs/wiki/research/tool-technology-testing-commands-and-takeaways.md
  - src/redthread/reporting/exporters.py
  - src/redthread/engine_transcript.py
updated_by: codex
updated_at: 2026-04-27
---

# Tool Technology Slice 7 Implementation Plan

## Goal

Give operator reports a stable campaign artifact home and a small manifest that later import/export bridges can target.

Plain meaning:

```text
campaign result
→ operator artifact bundle
→ campaign report directory
→ markdown + json + manifest
→ transcript summary points at manifest
→ future bridges can map from stable files
```

## Scope

Build persistence and bridge-prep seams only.

In scope:

- standard campaign report directory writer
- manifest model with stable schema marker
- Markdown and JSON report paths in the manifest
- transcript summary field for the manifest when present in campaign metadata
- optional CLI `--report-dir` flag for standard report persistence
- tests for files, manifest shape, and transcript linkage
- documentation of testing commands and key takeaways

Out of scope:

- no garak/promptfoo/Strix runtime imports
- no external parser yet
- no new attack, judge, or defense behavior
- no new finding source beyond JudgeAgent-confirmed results
- no report database

## Safety invariant

Persisted reports do not create findings.

Imported or future external evidence must stay weak evidence unless a RedThread JudgeAgent verdict confirms it.

## Implementation checklist

- [x] Add manifest model to `src/redthread/reporting/models.py`.
- [x] Add persistence helper in `src/redthread/reporting/persistence.py`.
- [x] Export persistence helper from `src/redthread/reporting/__init__.py`.
- [x] Add transcript summary field for `operator_report_manifest`.
- [x] Add CLI `--report-dir` flag.
- [x] Add tests for report directory persistence and transcript linkage.
- [x] Update roadmap, wiki index, and wiki log.
- [x] Run focused tests, Ruff, mypy, and wiki lint.

## Artifact layout

```text
<report-dir>/
  <campaign-id>/
    operator-report.md
    operator-report.json
    manifest.json
```

Manifest schema marker:

```text
redthread.operator_report_manifest.v1
```

## Acceptance criteria

- A caller can persist report artifacts under a stable campaign directory.
- The manifest records campaign ID, schema version, Markdown path, JSON path, and bridge-prep notes.
- Transcript summary can include the manifest metadata when report persistence is used.
- All new logic remains pure reporting/export logic.
- Detector hints remain weak-signal context only.
